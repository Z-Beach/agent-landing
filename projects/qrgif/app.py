"""QR-GIF desktop app: encode files into visual streams, recover them back.

    python app.py

Encode tab:  pick a file (or use the Rickroll demo) -> watch an animated stream
             of pure-QR-style frames, optionally save it as GIF / MP4 / PNGs.
Decode tab:  open a stream -> watch packets arrive, watch Reed-Solomon rebuild
             the gaps, get a SHA-256 verified payload.
Static tab:  the distribution screen -- CRT noise with a download QR beside it.
"""
from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

sys.path.insert(0, str(Path(__file__).parent))

from qrgif.codec import (Collector, StreamConfig, _unify_size, _write,
                         build_frames, decode_frames, grid_capacity_bytes,
                         iter_frames, render_qr)

# header slack the CLI also reserves when validating chunk vs grid capacity
HEADER_SLACK = 40

RICKROLL = (
    b"Never gonna give you up\n"
    b"Never gonna let you down\n"
    b"Never gonna run around and desert you\n"
    b"Never gonna make you cry\n"
    b"Never gonna say goodbye\n"
    b"Never gonna tell a lie and hurt you\n"
    b"\n-- a QR-GIF transmission --\n"
)

BG = "#101418"
FG = "#d7dde3"
ACCENT = "#4fd1c5"
WARN = "#f6ad55"
BAD = "#fc8181"
PANEL = "#1a2029"
FONT_M = ("Consolas", 9)
FONT_S = ("Segoe UI", 9, "bold")


def _show(canvas: tk.Label, arr: np.ndarray) -> None:
    """Fit a BGR frame into a tk.Label, preserving aspect."""
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    img = Image.fromarray(arr[..., ::-1])          # BGR -> RGB
    scale = min(w / img.width, h / img.height, 4.0)
    if scale > 0.05:
        img = img.resize((max(1, int(img.width * scale)),
                          max(1, int(img.height * scale))), Image.NEAREST)
    photo = ImageTk.PhotoImage(img)
    canvas.config(image=photo)
    canvas.image = photo                            # keep a reference


class EncodeWorker(threading.Thread):
    """Renders frames off the UI thread, streaming them into the queue."""

    def __init__(self, data: bytes, cfg: StreamConfig, out: str | None,
                 fmt: str, sink: queue.Queue):
        super().__init__(daemon=True)
        self.data, self.cfg, self.out, self.fmt, self.sink = data, cfg, out, fmt, sink

    def run(self) -> None:
        try:
            self.sink.put(("status", "rendering frames..."))
            frames: list[np.ndarray] = []
            for i, fr in enumerate(build_frames(self.data, self.cfg,
                                                progress=self._prog)):
                frames.append(fr)
                self.sink.put(("enc_frame", (i, fr)))
            if self.out:
                self.sink.put(("status", f"writing {Path(self.out).name}..."))
                # frames may vary in size (QR versions); the writer needs one canvas
                _write(_unify_size(frames), self.out, self.cfg, self.fmt)
                size = self._out_size()
                self.sink.put(("saved", f"{self.out}  ({size / 1024:.1f} KiB, "
                                        f"{len(frames)} frames)"))
            n = len(self.data)
            rate = n * 8 / 1000.0
            self.sink.put(("done", f"{len(frames)} frames, {n:,} bytes payload "
                                   f"({rate:.1f} kbit of payload)"))
        except Exception as e:
            self.sink.put(("error", f"{type(e).__name__}: {e}"))

    def _prog(self, done: int, total: int) -> None:
        self.sink.put(("packets", (done, total)))

    def _out_size(self) -> int:
        p = Path(self.out)
        if p.is_dir():
            return sum(f.stat().st_size for f in p.glob("*.png"))
        return p.stat().st_size


class DecodeWorker(threading.Thread):
    """Scans a stream frame by frame, reporting coverage as it goes."""

    def __init__(self, path: str, cfg: StreamConfig, out: str, sink: queue.Queue):
        super().__init__(daemon=True)
        self.path, self.cfg, self.out, self.sink = path, cfg, out, sink

    def run(self) -> None:
        try:
            col = Collector(k=self.cfg.k, m=self.cfg.m)
            self.sink.put(("status", "scanning frames..."))

            def preview():
                for fr in iter_frames(self.path):
                    self.sink.put(("dec_frame", fr))
                    yield fr

            def on_frame(i: int) -> None:
                if i % 3 == 0:
                    self.sink.put(("scanned", (i, col.percent, len(col.data),
                                               col.n_data, col.recovered)))

            good, bad = decode_frames(preview(), col, self.cfg, on_frame=on_frame)
            n = col.recover()
            self.sink.put(("scanned", (col.seen, col.percent, len(col.data),
                                       col.n_data, col.recovered)))
            self.sink.put(("coverage", (len(col.data), col.n_data or 0,
                                        col.percent, n, col.recovered, good, bad)))

            if not col.complete:
                self.sink.put(("error",
                               f"INCOMPLETE - {len(col.missing())} of {col.n_data} "
                               f"packets never arrived ({col.percent:.1f}% coverage). "
                               f"Re-encode with more parity (m) or a bigger grid."))
                return

            data = col.assemble()          # raises if the SHA-256 does not match
            Path(self.out).write_bytes(data)
            from qrgif.protocol import sha256
            self.sink.put(("done", f"VERIFIED - sha256 {sha256(data).hex()[:16]}...\n"
                                   f"{len(data):,} bytes -> {self.out}"))
        except ValueError as e:
            self.sink.put(("error", f"INTEGRITY FAILURE - {e}"))
        except Exception as e:
            self.sink.put(("error", f"{type(e).__name__}: {e}"))


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("QR-GIF")
        self.configure(bg=BG)
        self.minsize(900, 640)
        self.q: queue.Queue = queue.Queue()
        self.frames: list[np.ndarray] = []
        self.latest_frame: np.ndarray | None = None
        self.play_idx = 0
        self.encoding = False
        self.decoding = False
        self.static_on = False

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.enc_tab = ttk.Frame(self.nb)
        self.dec_tab = ttk.Frame(self.nb)
        self.stc_tab = ttk.Frame(self.nb)
        self.nb.add(self.enc_tab, text="  Encode  ")
        self.nb.add(self.dec_tab, text="  Decode  ")
        self.nb.add(self.stc_tab, text="  Broadcast  ")
        self.nb.bind("<<NotebookTabChanged>>", self._tab_changed)

        self._build_encode()
        self._build_decode()
        self._build_static()
        self.after(33, self._tick)

    # ------------------------------------------------------------- encode
    def _build_encode(self) -> None:
        p = self.enc_tab
        left = tk.Frame(p, bg=PANEL)
        left.pack(side="left", fill="y", padx=(0, 8), pady=4)

        tk.Label(left, text="PAYLOAD", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(10, 2))
        row = tk.Frame(left, bg=PANEL)
        row.pack(fill="x", padx=10)
        self.src_var = tk.StringVar(value="(demo payload)")
        tk.Entry(row, textvariable=self.src_var, width=32, state="readonly",
                 readonlybackground=BG, fg=FG).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Browse...", command=self._pick_file).pack(
            side="left", padx=(6, 0))

        self.demo_var = tk.BooleanVar(value=True)
        self._check(left, "Rickroll demo payload", self.demo_var)

        tk.Label(left, text="TRANSPORT", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(12, 2))
        self.mode_var = tk.StringVar(value="grid")
        mt = tk.Frame(left, bg=PANEL)
        mt.pack(fill="x", padx=10)
        for label, val in (("grid (fast)", "grid"), ("QR (standard)", "qr")):
            tk.Radiobutton(mt, text=label, value=val, variable=self.mode_var,
                           bg=PANEL, fg=FG, selectcolor=BG, activebackground=PANEL,
                           activeforeground=FG, command=self._refresh_cap).pack(
                side="left")

        self.modules_var = tk.IntVar(value=65)
        self.chunk_var = tk.IntVar(value=350)
        self.fps_var = tk.IntVar(value=10)
        self._spin(left, "Module count (grid)", self.modules_var, 21, 201, 2)
        self._spin(left, "Bytes per packet", self.chunk_var, 50, 600, 5)
        self._spin(left, "Frames per second", self.fps_var, 1, 60, 1)

        tk.Label(left, text="FEC: k data + m parity packets per group",
                 bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(8, 0))
        fec = tk.Frame(left, bg=PANEL)
        fec.pack(fill="x", padx=10)
        self.k_var = tk.IntVar(value=16)
        self.m_var = tk.IntVar(value=4)
        tk.Spinbox(fec, from_=4, to=32, textvariable=self.k_var, width=4,
                   readonlybackground=BG, fg=FG).pack(side="left")
        tk.Label(fec, text=" + ", bg=PANEL, fg=FG).pack(side="left")
        tk.Spinbox(fec, from_=0, to=16, textvariable=self.m_var, width=4,
                   readonlybackground=BG, fg=FG).pack(side="left")

        self.cap_lbl = tk.Label(left, text="", bg=PANEL, fg=FG, wraplength=250,
                                justify="left", font=FONT_M)
        self.cap_lbl.pack(anchor="w", padx=10, pady=(8, 0))

        tk.Label(left, text="OUTPUT", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(12, 2))
        self.fmt_var = tk.StringVar(value="gif")
        fo = tk.Frame(left, bg=PANEL)
        fo.pack(fill="x", padx=10)
        for label, val in (("GIF", "gif"), ("MP4", "mp4"), ("PNGs", "png")):
            tk.Radiobutton(fo, text=label, value=val, variable=self.fmt_var,
                           bg=PANEL, fg=FG, selectcolor=BG, activebackground=PANEL,
                           activeforeground=FG).pack(side="left")

        self.save_var = tk.BooleanVar(value=False)
        self._check(left, "Also save to file", self.save_var)

        self.enc_btn = tk.Button(left, text="Encode", command=self._encode,
                                 bg=ACCENT, fg="#08201e", activebackground="#3fb5aa",
                                 font=("Segoe UI", 10, "bold"), relief="flat", width=18)
        self.enc_btn.pack(padx=10, pady=14, fill="x")

        right = tk.Frame(p, bg=BG)
        right.pack(side="left", fill="both", expand=True, pady=4)
        self.enc_canvas = tk.Label(right, bg="#000", relief="sunken")
        self.enc_canvas.pack(fill="both", expand=True)
        self.enc_bar = ttk.Progressbar(right, maximum=1)
        self.enc_bar.pack(fill="x", pady=(6, 2))
        self.enc_status = tk.Label(right, text="ready", bg=BG, fg=FG, font=FONT_M,
                                   anchor="w")
        self.enc_status.pack(fill="x")
        self._refresh_cap()

    def _build_decode(self) -> None:
        p = self.dec_tab
        left = tk.Frame(p, bg=PANEL)
        left.pack(side="left", fill="y", padx=(0, 8), pady=4)

        tk.Label(left, text="STREAM", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(10, 2))
        row = tk.Frame(left, bg=PANEL)
        row.pack(fill="x", padx=10)
        self.stream_var = tk.StringVar(value="(none)")
        tk.Entry(row, textvariable=self.stream_var, width=32, state="readonly",
                 readonlybackground=BG, fg=FG).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Browse...", command=self._pick_stream).pack(
            side="left", padx=(6, 0))
        tk.Button(row, text="Folder...", command=self._pick_stream_dir).pack(
            side="left", padx=(4, 0))

        tk.Label(left, text="DETECTION", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(12, 2))
        self.dmodules_var = tk.IntVar(value=65)
        self._spin(left, "Module count (grid)", self.dmodules_var, 21, 201, 2)
        tk.Label(left, text="Transport is auto-detected per frame; the module\n"
                            "count must match what the encoder used.",
                 bg=PANEL, fg=FG, wraplength=250, justify="left",
                 font=FONT_M).pack(anchor="w", padx=10, pady=(4, 0))

        self.dec_btn = tk.Button(left, text="Decode", command=self._decode,
                                 bg=ACCENT, fg="#08201e", activebackground="#3fb5aa",
                                 font=("Segoe UI", 10, "bold"), relief="flat", width=18)
        self.dec_btn.pack(padx=10, pady=16, fill="x")

        self.cov_lbl = tk.Label(left, text="coverage: -", bg=PANEL, fg=FG,
                                font=FONT_M, anchor="w", justify="left")
        self.cov_lbl.pack(fill="x", padx=10)
        self.res_lbl = tk.Label(left, text="", bg=PANEL, fg=FG, wraplength=250,
                                justify="left", font=FONT_M)
        self.res_lbl.pack(fill="x", padx=10, pady=(6, 10))

        right = tk.Frame(p, bg=BG)
        right.pack(side="left", fill="both", expand=True, pady=4)
        self.dec_canvas = tk.Label(right, bg="#000", relief="sunken")
        self.dec_canvas.pack(fill="both", expand=True)
        self.dec_bar = ttk.Progressbar(right, maximum=100)
        self.dec_bar.pack(fill="x", pady=(6, 2))
        self.dec_status = tk.Label(right, text="ready", bg=BG, fg=FG, font=FONT_M,
                                   anchor="w")
        self.dec_status.pack(fill="x")

    def _build_static(self) -> None:
        p = self.stc_tab
        left = tk.Frame(p, bg=PANEL)
        left.pack(side="left", fill="y", padx=(0, 8), pady=4)
        tk.Label(left, text="CRT BROADCAST", bg=PANEL, fg=ACCENT,
                 font=FONT_S).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(left, text="Static noise with a download code beside it --\n"
                            "the screen you leave running while the file\n"
                            "travels. Anyone who scans keeps a copy.",
                 bg=PANEL, fg=FG, wraplength=250, justify="left",
                 font=FONT_M).pack(anchor="w", padx=10, pady=(0, 8))

        tk.Label(left, text="Link in the QR", bg=PANEL, fg=FG).pack(
            anchor="w", padx=10)
        self.url_var = tk.StringVar(value="https://example.com/drop/qrgif.gif")
        tk.Entry(left, textvariable=self.url_var, width=34, bg=BG, fg=FG,
                 insertbackground=FG).pack(fill="x", padx=10, pady=(2, 8))
        self.fps_static_var = tk.IntVar(value=12)
        self._spin(left, "Static frames/sec", self.fps_static_var, 1, 30, 1)

        self.stc_btn = tk.Button(left, text="Start broadcast",
                                 command=self._toggle_static, bg=ACCENT, fg="#08201e",
                                 activebackground="#3fb5aa",
                                 font=("Segoe UI", 10, "bold"), relief="flat",
                                 width=18)
        self.stc_btn.pack(padx=10, pady=12, fill="x")

        right = tk.Frame(p, bg=BG)
        right.pack(side="left", fill="both", expand=True, pady=4)
        self.stc_canvas = tk.Label(right, bg="#000", relief="sunken")
        self.stc_canvas.pack(fill="both", expand=True)

    # ------------------------------------------------------------- widgets
    def _check(self, parent, text: str, var) -> None:
        tk.Checkbutton(parent, text=text, variable=var, bg=PANEL, fg=FG,
                       selectcolor=BG, activebackground=PANEL,
                       activeforeground=FG).pack(anchor="w", padx=10)

    def _spin(self, parent, label: str, var, lo: int, hi: int, step: int) -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(3, 0))
        tk.Label(row, text=label, bg=PANEL, fg=FG).pack(side="left")
        tk.Spinbox(row, from_=lo, to=hi, textvariable=var, width=5, increment=step,
                   readonlybackground=BG, fg=FG).pack(side="right")

    def _refresh_cap(self) -> None:
        if self.mode_var.get() == "grid":
            m = int(self.modules_var.get()) | 1
            cap = grid_capacity_bytes(m) - HEADER_SLACK
            chunk = int(self.chunk_var.get())
            ok = chunk <= cap
            self.cap_lbl.config(
                text=f"grid {m}x{m} = {cap + HEADER_SLACK} B/frame\n"
                     f"chunk {chunk} B/packet -> "
                     + ("ok" if ok else f"TOO BIG (max {cap}; raise modules)"),
                fg=FG if ok else BAD)
        else:
            self.cap_lbl.config(
                text="standard QR: any phone camera can\nread this stream. Slower, "
                     "interoperable.", fg=FG)

    def _pick_file(self) -> None:
        p = filedialog.askopenfilename(title="Choose a file to transmit")
        if p:
            self.src_var.set(p)
            self.demo_var.set(False)
        self._refresh_cap()

    def _pick_stream(self) -> None:
        p = filedialog.askopenfilename(
            title="Choose a stream",
            filetypes=[("QR-GIF streams", "*.gif *.mp4 *.avi"), ("All", "*.*")])
        if p:
            self.stream_var.set(p)

    def _pick_stream_dir(self) -> None:
        p = filedialog.askdirectory(title="Choose a PNG frame folder")
        if p:
            self.stream_var.set(p)

    def _cfg(self) -> StreamConfig:
        cfg = StreamConfig(mode=self.mode_var.get(),
                           chunk=int(self.chunk_var.get()),
                           k=max(1, int(self.k_var.get())),
                           m=max(0, int(self.m_var.get())),
                           fps=float(self.fps_var.get()))
        cfg.modules = int(self.modules_var.get()) | 1
        return cfg

    # ------------------------------------------------------------- actions
    def _encode(self) -> None:
        if self.encoding:
            return
        if self.demo_var.get():
            data, name = RICKROLL, "rickroll.txt"
        else:
            p = self.src_var.get()
            if p.startswith("("):
                messagebox.showwarning("QR-GIF",
                                       "Pick a file, or tick the demo payload.")
                return
            data, name = Path(p).read_bytes(), Path(p).name

        cfg = self._cfg()
        cfg.name = name
        if cfg.mode == "grid":
            cap = grid_capacity_bytes(cfg.modules) - HEADER_SLACK
            if cfg.chunk > cap:
                messagebox.showerror("QR-GIF",
                                     f"chunk {cfg.chunk} B exceeds the {cap} B "
                                     f"available at modules={cfg.modules}.\n"
                                     f"Raise the module count or lower the chunk.")
                return

        out = None
        if self.save_var.get():
            stem = Path(name).stem
            ftypes = {"gif": [("QR-GIF animation", "*.gif")],
                      "mp4": [("MP4 video", "*.mp4")],
                      "png": [("PNG frame folder", "*.png")]}[self.fmt_var.get()]
            out = filedialog.asksaveasfilename(
                title="Save stream", initialfile=f"{stem}.qrgif",
                defaultextension=(".png" if self.fmt_var.get() == "png" else ""),
                filetypes=ftypes + [("All", "*.*")])
            if not out:
                return
            if self.fmt_var.get() == "png":
                out = str(Path(out).with_suffix(""))

        self.encoding = True
        self.frames = []
        self.latest_frame = None
        self.play_idx = 0
        self.enc_btn.config(state="disabled", text="Encoding...")
        self.enc_bar.config(maximum=1, value=0)
        self.enc_status.config(text="rendering frames...", fg=FG)
        EncodeWorker(data, cfg, out, self.fmt_var.get(), self.q).start()

    def _decode(self) -> None:
        if self.decoding:
            return
        path = self.stream_var.get()
        if path.startswith("("):
            messagebox.showwarning("QR-GIF", "Pick a stream to decode.")
            return
        out = filedialog.asksaveasfilename(title="Save recovered file",
                                           initialfile="recovered.bin")
        if not out:
            return
        cfg = StreamConfig()
        cfg.modules = int(self.dmodules_var.get()) | 1
        self.decoding = True
        self.dec_btn.config(state="disabled", text="Decoding...")
        self.dec_bar.config(value=0)
        self.cov_lbl.config(text="coverage: -")
        self.res_lbl.config(text="")
        self.dec_status.config(text="scanning frames...", fg=FG)
        DecodeWorker(path, cfg, out, self.q).start()

    def _toggle_static(self) -> None:
        self.static_on = not self.static_on
        self.stc_btn.config(text="Stop broadcast" if self.static_on
                            else "Start broadcast")

    def _tab_changed(self, _event) -> None:
        if self.nb.select() != str(self.stc_tab):
            self.static_on = False
            self.stc_btn.config(text="Start broadcast")
            self.stc_canvas.config(image="")

    # ------------------------------------------------------------- pump
    def _tick(self) -> None:
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "enc_frame":
                    i, fr = payload
                    self.frames.append(fr)
                    self.latest_frame = fr
                    self.enc_bar.config(maximum=len(self.frames), value=len(self.frames))
                    self.enc_status.config(text=f"frame {i + 1}")
                elif kind == "packets":
                    done, total = payload
                    self.enc_bar.config(maximum=total, value=done)
                    self.enc_status.config(text=f"packets {done}/{total}")
                elif kind == "dec_frame":
                    self.latest_frame = payload
                elif kind == "status":
                    self.enc_status.config(text=payload, fg=FG)
                    self.dec_status.config(text=payload, fg=FG)
                elif kind == "saved":
                    self.enc_status.config(text=f"saved {payload}", fg=ACCENT)
                elif kind == "scanned":
                    i, pct, have, total, fec = payload
                    self.dec_bar.config(value=pct)
                    t = f"/{total}" if total else "/?"
                    self.cov_lbl.config(
                        text=f"coverage: {pct:.1f}%  ({have}{t} packets)\n"
                             f"rebuilt by Reed-Solomon: {fec}")
                    self.dec_status.config(text=f"scanned {i} frames")
                elif kind == "coverage":
                    have, total, pct, fresh, fec, good, bad = payload
                    self.dec_bar.config(value=pct)
                    self.cov_lbl.config(
                        text=f"coverage: {pct:.1f}%  ({have}/{total} packets)\n"
                             f"decoded {good} packets, dropped {bad}\n"
                             f"rebuilt by Reed-Solomon: {fresh} new, {fec} total")
                elif kind == "done":
                    if self.encoding:
                        self.enc_status.config(text=payload, fg=ACCENT)
                        self._finish_encode()
                    if self.decoding:
                        self.dec_status.config(text=payload, fg=ACCENT)
                        self.res_lbl.config(text=payload, fg=ACCENT)
                        self._finish_decode()
                elif kind == "error":
                    if self.encoding:
                        self.enc_status.config(text=payload, fg=BAD)
                        self._finish_encode()
                    if self.decoding:
                        self.dec_status.config(text=payload, fg=BAD)
                        self.res_lbl.config(text=payload, fg=WARN)
                        self._finish_decode()
        except queue.Empty:
            pass

        if self.encoding and self.latest_frame is not None:
            _show(self.enc_canvas, self.latest_frame)
        elif self.encoding:
            pass
        elif self.frames:
            _show(self.enc_canvas, self.frames[self.play_idx % len(self.frames)])
            self.play_idx += 1

        if self.decoding and self.latest_frame is not None:
            _show(self.dec_canvas, self.latest_frame)

        if self.static_on:
            self._draw_static()

        self.after(33, self._tick)

    def _finish_encode(self) -> None:
        self.encoding = False
        self.enc_btn.config(state="normal", text="Encode")

    def _finish_decode(self) -> None:
        self.decoding = False
        self.dec_btn.config(state="normal", text="Decode")

    def _draw_static(self) -> None:
        w = self.stc_canvas.winfo_width() or 640
        h = self.stc_canvas.winfo_height() or 480
        w, h = max(160, w - w % 8), max(120, h - h % 8)
        rng = np.random.default_rng()
        noise = rng.integers(0, 256, (h // 2, w // 2), dtype=np.uint8)
        noise = np.kron(noise, np.ones((2, 2), dtype=np.uint8))
        rgb = np.repeat(noise[..., None], 3, axis=2)
        # a QR with the download link, pasted top-right with a white margin
        qr = render_qr(self.url_var.get().encode(), ec="M", module_px=6, quiet=2)
        qh, qw = qr.shape[:2]
        y0, x0 = 12, max(12, w - qw - 12)
        if y0 + qh < h and x0 + qw < w:
            rgb[y0:y0 + qh, x0:x0 + qw] = np.repeat(qr[..., None], 3, axis=2)
        self._show(self.stc_canvas, rgb[..., ::-1])
        self.after(max(16, int(1000 / max(1, self.fps_static_var.get()))),
                   self._draw_static)


if __name__ == "__main__":
    App().mainloop()
