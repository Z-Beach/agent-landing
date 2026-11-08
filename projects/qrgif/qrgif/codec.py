"""Frame encoders, decoders and the stream collector for QR-GIF.

Two transports over the same packet bytes:

  qr    standard QR symbols (interoperable, pays QR's own format + RS overhead)
  grid  custom module grid with QR-style finder corners; every other module is
        payload, error correction is the stream-level Reed-Solomon in protocol

Recovery is erasure-based: a packet that fails its CRC is simply missing, and
m parity packets per group of k data packets absorb up to m losses without
needing a second loop. Loops still help - they are just more erasure samples.
"""
from __future__ import annotations

import math
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator

import cv2
import numpy as np
import qrcode
from PIL import Image, ImageSequence

from .protocol import (MANIFEST_MAGIC, PARITY_MAGIC, Fec, b45decode, b45encode,
                       chunk_layout, make_data, make_manifest, make_parity,
                       parse_data, parse_manifest, parse_parity, sha256, split)

FINDER = np.array([
    [1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1],
], dtype=np.uint8)


# --------------------------------------------------------------- grid layer

def grid_capacity_bytes(modules: int) -> int:
    return int(_grid_mask(modules).sum()) // 8


def _grid_mask(modules: int) -> np.ndarray:
    """True where payload bits live.

    Finders get a 1-module quiet separator (like real QR) so each finder is an
    isolated dark blob for the contour detector; row/col 6 carry timing.
    """
    m = np.ones((modules, modules), dtype=bool)
    for r0, c0 in ((0, 0), (0, modules - 8), (modules - 8, 0)):
        m[r0:r0 + 8, c0:c0 + 8] = False
    m[6, :] = False
    m[:, 6] = False
    return m


def pack_grid(payload: bytes, modules: int) -> np.ndarray:
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    mask = _grid_mask(modules)
    total = int(mask.sum())
    if len(bits) > total:
        raise ValueError("payload %d bits > grid capacity %d" % (len(bits), total))
    if len(bits) < total:
        bits = np.concatenate([bits, np.zeros(total - len(bits), dtype=np.uint8)])
    grid = np.zeros((modules, modules), dtype=np.uint8)
    grid[mask] = bits
    # timing: starts clear of the finder separators
    grid[6, 8:modules - 8] = np.arange(8, modules - 8) % 2
    grid[8:modules - 8, 6] = np.arange(8, modules - 8) % 2
    for r0, c0 in ((0, 0), (0, modules - 7), (modules - 7, 0)):
        grid[r0:r0 + 7, c0:c0 + 7] = FINDER
        # quiet separator ring around the finder
        if r0 == 0 and c0 == 0:
            grid[7, 0:8] = 0
            grid[0:8, 7] = 0
        elif r0 == 0:
            grid[7, modules - 8:] = 0
            grid[0:8, modules - 8] = 0
        else:
            grid[modules - 8, 0:8] = 0
            grid[modules - 8:, 7] = 0
    return grid


def unpack_grid(grid: np.ndarray) -> bytes:
    mask = _grid_mask(grid.shape[0])
    bits = grid[mask].astype(np.uint8)
    bits = bits[:len(bits) // 8 * 8]
    return np.packbits(bits).tobytes()


def render_grid(payload: bytes, modules: int, module_px: int, quiet: int = 2) -> np.ndarray:
    """1 = dark module = black pixel (grid uses 1 for dark, image uses 0)."""
    grid = pack_grid(payload, modules)
    big = (1 - grid) * 255
    big = np.kron(big, np.ones((module_px, module_px), dtype=np.uint8)).astype(np.uint8)
    pad = quiet * module_px
    return cv2.copyMakeBorder(big, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)


_RADII = np.arange(0.25, 3.5, 0.2)
_ANG = np.linspace(0.0, 2.0 * np.pi, 64, endpoint=False)
_COS = np.cos(_ANG)
_SIN = np.sin(_ANG)


def _radial_profile(dark: np.ndarray, cx: float, cy: float, pitch: float) -> np.ndarray:
    """Mean darkness vs radius in module units.

    Averaging over full circles makes the profile independent of the pattern's
    rotation, and expressing radius in modules makes it independent of scale --
    which is exactly what is needed to recognise a finder from a camera.
    """
    prof = np.empty(len(_RADII), dtype=np.float32)
    for i, r in enumerate(_RADII):
        xs = cx + r * pitch * _COS
        ys = cy + r * pitch * _SIN
        xi = np.clip(np.round(xs).astype(np.int32), 0, dark.shape[1] - 1)
        yi = np.clip(np.round(ys).astype(np.int32), 0, dark.shape[0] - 1)
        prof[i] = dark[yi, xi].mean()
    return prof


def _build_template_profile() -> np.ndarray:
    ys, xs = np.mgrid[0:7, 0:7].astype(np.float32)
    rad = np.hypot(xs + 0.5 - 3.5, ys + 0.5 - 3.5)
    prof = np.full(len(_RADII), np.nan, dtype=np.float32)
    for i, r in enumerate(_RADII):
        m = np.abs(rad - r) < 0.1
        if m.any():
            prof[i] = FINDER[m].mean()
    idx = np.arange(len(prof))
    ok = ~np.isnan(prof)
    return np.interp(idx, idx[ok], prof[ok]).astype(np.float32)


_TPL_PROFILE = _build_template_profile()
_TPL_Z = _TPL_PROFILE - _TPL_PROFILE.mean()
_TPL_NORM = float(np.linalg.norm(_TPL_Z))


def _finder_score(dark: np.ndarray, cx: float, cy: float, pitch: float) -> float:
    """Correlate a candidate's radial profile with the finder's.

    A solid block scores near zero (flat profile), so this rejects data fields
    without needing a deskew step.
    """
    p = _radial_profile(dark, cx, cy, pitch)
    z = p - p.mean()
    n = float(np.linalg.norm(z))
    if n < 1e-6:
        return 0.0
    return float((z @ _TPL_Z) / (n * _TPL_NORM))


def _finder_boxes(bw: np.ndarray) -> list[tuple[float, float, float, float]]:
    """Find 7x7 finder patterns at any rotation. Returns (cx, cy, pitch, score)."""
    dark = (bw < 128).astype(np.uint8)
    contours, _ = cv2.findContours(255 - bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in contours:
        if len(c) < 4 or cv2.contourArea(c) < 196:
            continue
        (cx, cy), (rw, rh), _ = cv2.minAreaRect(c)
        mn, mx = min(rw, rh), max(rw, rh)
        if mx < 14 or not 0.82 < mn / mx < 1.22:
            continue
        pitch = mx / 7.0
        score = _finder_score(dark, cx, cy, pitch)
        if score < 0.85:
            continue
        out.append((cx, cy, pitch, score))
    out.sort(key=lambda b: -b[3])
    return out


def detect_grid(image: np.ndarray, modules: int) -> np.ndarray | None:
    """Sample the module grid out of a captured frame at any rotation."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    boxes = _finder_boxes(bw)
    if len(boxes) < 3:
        return None

    # Fast path: the three finders form a right triangle; the right-angle vertex
    # is the one opposite the longest side, which is the finder that carries the
    # grid's origin no matter how the frame is rotated. Only the tr/bl assignment
    # (handedness) is ambiguous, so two samples cover every orientation.
    top = boxes[:3]
    pairs = [((0, 1), (top[0][0] - top[1][0]) ** 2 + (top[0][1] - top[1][1]) ** 2),
             ((0, 2), (top[0][0] - top[2][0]) ** 2 + (top[0][1] - top[2][1]) ** 2),
             ((1, 2), (top[1][0] - top[2][0]) ** 2 + (top[1][1] - top[2][1]) ** 2)]
    (li, lj), _ = max(pairs, key=lambda p: p[1])
    vertex = ({0, 1, 2} - {li, lj}).pop()
    rest = sorted({0, 1, 2} - {vertex})
    best = None
    for a, b in ((rest[0], rest[1]), (rest[1], rest[0])):
        grid = _sample(bw, modules, top[vertex], top[a], top[b])
        if grid is None:
            continue
        score = _grid_score(grid, modules)
        if best is None or score > best[0]:
            best = (score, grid)
        if score > 0.90:
            return grid

    # Slow path only when we were close: a wrong module count scores near zero
    # and searching 120 triples would just burn time on every frame.
    if best is None or best[0] < 0.5:
        return None
    cand = boxes[:4]
    for i in range(len(cand)):
        for j in range(len(cand)):
            for k in range(len(cand)):
                if len({i, j, k}) < 3:
                    continue
                grid = _sample(bw, modules, cand[i], cand[j], cand[k])
                if grid is None:
                    continue
                score = _grid_score(grid, modules)
                if best is None or score > best[0]:
                    best = (score, grid)
                if score > 0.985:
                    return grid
    return best[1] if best[0] > 0.85 else None


def _sample(bw, modules, tl, tr, bl, sp: int = 8):
    """Affine-map image -> module grid, area-averaging each module.

    Grid coords put module (r, c)'s centre at (c + 0.5, r + 0.5); finder centres
    therefore sit at (3.5, 3.5) etc. The affine is estimated image->grid, then
    inverted so warpAffine can pull the source into grid space.
    """
    src = np.array([[tl[0], tl[1]], [tr[0], tr[1]], [bl[0], bl[1]]], np.float32)
    dst = np.array([[3.5, 3.5], [modules - 3.5, 3.5], [3.5, modules - 3.5]], np.float32)
    if np.linalg.norm(src[1] - src[0]) < 1 or np.linalg.norm(src[2] - src[0]) < 1:
        return None
    try:
        A, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)
    except Exception:
        return None
    if A is None:
        return None
    Ainv = cv2.invertAffineTransform(A)                       # grid -> image
    S = float(sp)
    to_grid = np.array([[1 / S, 0, 0.5 / S],
                        [0, 1 / S, 0.5 / S],
                        [0, 0, 1]], np.float32)               # hi-res px -> grid
    M = (np.vstack([Ainv, [0, 0, 1]]) @ to_grid).astype(np.float32)[:2]
    # M maps hi-res dst pixel -> source pixel, which is warpAffine's inverse form
    n = modules
    hi = int(n * S)
    warped = cv2.warpAffine(bw, M, (hi, hi),
                            flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    small = cv2.resize(warped, (n, n), interpolation=cv2.INTER_AREA)
    return (small < 128).astype(np.uint8)


def _grid_score(grid: np.ndarray, modules: int) -> float:
    hit = tot = 0
    for r0, c0 in ((0, 0), (0, modules - 7), (modules - 7, 0)):
        sub = grid[r0:r0 + 7, c0:c0 + 7]
        hit += int((sub == FINDER).sum())
        tot += 49
    return hit / tot if tot else 0.0


# ---------------------------------------------------------------- qr layer

def render_qr(payload: bytes, ec: str = "L", module_px: int = 4,
              quiet: int = 2) -> np.ndarray:
    from qrcode.constants import (ERROR_CORRECT_H, ERROR_CORRECT_L,
                                  ERROR_CORRECT_M, ERROR_CORRECT_Q)
    levels = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M,
              "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
    qr = qrcode.QRCode(error_correction=levels.get(ec.upper(), ERROR_CORRECT_L),
                       box_size=module_px, border=quiet)
    qr.add_data(b45encode(payload))          # alphanumeric mode, ASCII-safe
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("1")
    return (np.array(img, dtype=np.uint8) * 255)


def decode_qr(image: np.ndarray, det: cv2.QRCodeDetector) -> bytes | None:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    for img in (gray, cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)):
        try:
            ok, decoded, _, _ = det.detectAndDecodeMulti(img)
            if ok and decoded:
                for d in decoded:
                    if d:
                        try:
                            return b45decode(d)
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            d, _, _ = det.detectAndDecode(img)
            if d:
                return b45decode(d)
        except Exception:
            pass
    return None


# ----------------------------------------------------------------- stream

@dataclass
class StreamConfig:
    mode: str = "grid"        # grid | qr
    modules: int = 65
    module_px: int = 6
    ec: str = "L"
    k: int = 16
    m: int = 4
    chunk: int = 200
    manifest_every: int = 10
    fps: float = 10.0
    quiet: int = 2
    name: str = "payload.bin"


@dataclass
class EncodeStats:
    frames: int = 0
    data_frames: int = 0
    parity_frames: int = 0
    manifest_frames: int = 0
    seconds: float = 0.0
    payload_bytes: int = 0

    def summary(self) -> str:
        s = self.seconds or 1e-9
        return ("frames %d (%d data / %d parity / %d manifest) in %.2fs | "
                "%d payload bytes | %.1f kbit/s of payload at %.1f fps"
                % (self.frames, self.data_frames, self.parity_frames,
                   self.manifest_frames, s, self.payload_bytes,
                   self.payload_bytes * 8 / 1000 / s, self.frames / s))


def _frame(packet: bytes, cfg: StreamConfig) -> np.ndarray:
    if cfg.mode == "qr":
        return render_qr(packet, cfg.ec, cfg.module_px, cfg.quiet)
    return render_grid(packet, cfg.modules, cfg.module_px, cfg.quiet)


def build_frames(data: bytes, cfg: StreamConfig,
                 progress: Callable[[int, int], None] | None = None
                 ) -> Iterator[np.ndarray]:
    session = secrets.token_bytes(8)
    digest = sha256(data)
    chunks = split(data, cfg.chunk)
    n = len(chunks)
    packets = [make_data(session, i, n, len(data), c, digest) for i, c in enumerate(chunks)]
    manifest = make_manifest(session, n, len(data), digest, cfg.name)

    fec = Fec(cfg.k, cfg.m)
    frames: list[np.ndarray] = []
    width = max((len(c) for c in chunks), default=1)
    gi = 0
    for start in range(0, n, cfg.k):
        grp = chunks[start:start + cfg.k]
        frames.extend(_frame(p, cfg) for p in packets[start:start + cfg.k])
        if cfg.m and grp:
            for idx, pp in enumerate(fec.parity(grp)):
                frames.append(_frame(
                    make_parity(session, gi, cfg.k, cfg.m, cfg.k + idx, pp), cfg))
        gi += 1
        if progress:
            progress(min(start + cfg.k, n), n)

    out: list[np.ndarray] = []
    every = max(1, cfg.manifest_every)
    for i, fr in enumerate(frames):
        out.append(fr)
        if (i + 1) % every == 0:
            out.append(_frame(manifest, cfg))
    out.append(_frame(manifest, cfg))
    return iter(_unify_size(out))


def _unify_size(frames: list[np.ndarray]) -> list[np.ndarray]:
    """Pad every frame to one canvas size.

    QR symbols auto-size per payload, so data / parity / manifest frames come
    out different dimensions. Video containers require a fixed frame size and
    silently discard the rest - which here would be every parity frame. A fixed
    canvas is also what a camera wants: no rescaling jitter between frames.
    """
    if not frames:
        return frames
    h = max(f.shape[0] for f in frames)
    w = max(f.shape[1] for f in frames)
    if all(f.shape[0] == h and f.shape[1] == w for f in frames):
        return frames
    out = []
    for f in frames:
        top = (h - f.shape[0]) // 2
        left = (w - f.shape[1]) // 2
        out.append(cv2.copyMakeBorder(f, top, h - f.shape[0] - top,
                                      left, w - f.shape[1] - left,
                                      cv2.BORDER_CONSTANT, value=255))
    return out


def encode_file(src: str, out: str, cfg: StreamConfig,
                fmt: str = "mp4") -> EncodeStats:
    data = Path(src).read_bytes()
    cfg.name = Path(src).name
    t0 = time.time()
    frames: list[np.ndarray] = []
    data_f = parity_f = 0
    for fr in build_frames(data, cfg, progress=lambda a, b: None):
        frames.append(fr)
    n = max(1, (len(data) + cfg.chunk - 1) // cfg.chunk)
    data_f = n
    parity_f = (math.ceil(n / cfg.k) * cfg.m) if cfg.m else 0
    _write(frames, out, cfg, fmt)
    return EncodeStats(frames=len(frames), data_frames=data_f,
                       parity_frames=parity_f,
                       manifest_frames=len(frames) - data_f - parity_f,
                       seconds=time.time() - t0, payload_bytes=len(data))


def _write(frames: list[np.ndarray], out: str, cfg: StreamConfig, fmt: str) -> None:
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    fmt = (fmt or p.suffix.lstrip(".")).lower()
    if fmt in ("gif",):
        _write_gif(frames, out, cfg.fps)
    elif fmt in ("png", "seq"):
        _write_sequence(frames, out, cfg.fps)
    else:
        _write_mp4(frames, out, cfg.fps)


def _write_gif(frames: list[np.ndarray], out: str, fps: float) -> None:
    pil = []
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if f.ndim == 3 else f
        pil.append(Image.fromarray(g).convert("P", palette=Image.ADAPTIVE, colors=2))
    dur = max(20, int(round(1000 / max(0.1, fps))))
    pil[0].save(out, save_all=True, append_images=pil[1:], duration=dur,
                loop=0, disposal=2, optimize=False)


def _write_mp4(frames: list[np.ndarray], out: str, fps: float) -> None:
    """Write a video container and verify no frames were dropped.

    Some OpenCV/FFmpeg builds silently discard frames under mp4v, which would
    strip the parity frames and leave nothing for Reed-Solomon to recover. If
    the count does not match we fall back to MJPG-in-AVI (intra-only, no frame
    dropping) and, failing that, raise rather than ship a truncated stream.
    """
    h, w = frames[0].shape[:2]
    bgr = [cv2.cvtColor(f, cv2.COLOR_GRAY2BGR) if f.ndim == 2 else f for f in frames]

    written = 0
    try:
        vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        if vw.isOpened():
            try:
                for f in bgr:
                    vw.write(f)
            finally:
                vw.release()
            written = _count_frames(out)
    except Exception:
        written = 0
    if written == len(frames):
        return

    avi = str(Path(out).with_suffix(".avi"))
    vw = cv2.VideoWriter(avi, cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    if not vw.isOpened():
        raise RuntimeError("no usable video codec; use --container gif or png")
    try:
        for f in bgr:
            vw.write(f)
    finally:
        vw.release()
    if _count_frames(avi) != len(frames):
        raise RuntimeError("video codec dropped frames; use --container gif or png")
    if Path(out).exists():
        Path(out).unlink()
    os.replace(avi, out)


def _count_frames(path: str) -> int:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return 0
    n = 0
    try:
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            n += 1
    finally:
        cap.release()
    return n


def _write_sequence(frames: list[np.ndarray], out: str, fps: float) -> None:
    d = Path(out)
    if d.exists():
        for old in d.glob("f*.png"):
            old.unlink()
    d.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(frames):
        cv2.imwrite(str(d / ("f%05d.png" % i)), f)
    (d / "fps.txt").write_text(str(fps), encoding="utf-8")


# --------------------------------------------------------------- collector

@dataclass
class Collector:
    k: int = 16
    m: int = 4
    session: bytes | None = None
    n_data: int | None = None
    file_size: int | None = None
    digest: bytes | None = None
    digest8: bytes | None = None
    name: str | None = None
    data: dict[int, bytes] = field(default_factory=dict)
    parity: dict[int, dict[int, bytes]] = field(default_factory=dict)
    group_params: dict[int, tuple[int, int]] = field(default_factory=dict)
    seen: int = 0
    valid: int = 0
    rejected: int = 0
    recovered: int = 0
    loops: int = 0

    def _bind(self, session, n_data, file_size, digest8) -> bool:
        if self.session is None:
            self.session, self.n_data = session, n_data
            self.file_size, self.digest8 = file_size, digest8
            return True
        return (self.session == session and self.n_data == n_data
                and self.file_size == file_size and self.digest8 == digest8)

    def add(self, payload: bytes) -> bool:
        self.seen += 1
        kind = payload[:4]
        if kind == MANIFEST_MAGIC:
            r = parse_manifest(payload)
            if not r:
                self.rejected += 1
                return False
            session, n_data, file_size, digest, name = r
            self._bind(session, n_data, file_size, digest[:8])
            self.digest, self.name = digest, name
            self.valid += 1
            return False
        dp = parse_data(payload)
        if dp is not None:
            if not self._bind(dp.session, dp.n_data, dp.file_size, dp.digest8):
                self.rejected += 1
                return False
            if dp.index in self.data:
                self.rejected += 1
                return False
            self.data[dp.index] = dp.chunk
            self.valid += 1
            return True
        pp = parse_parity(payload)
        if pp is not None:
            if self.session is not None and pp.session != self.session:
                self.rejected += 1
                return False
            self.parity.setdefault(pp.group, {})[pp.slot] = pp.payload
            self.group_params[pp.group] = (pp.k, pp.m)
            self.valid += 1
            return False
        self.rejected += 1
        return False

    @property
    def percent(self) -> float:
        return 100.0 * len(self.data) / self.n_data if self.n_data else 0.0

    @property
    def complete(self) -> bool:
        return bool(self.n_data) and len(self.data) == self.n_data

    def missing(self) -> list[int]:
        if not self.n_data:
            return []
        return [i for i in range(self.n_data) if i not in self.data]

    def recover(self) -> int:
        if self.n_data is None:
            return 0
        got = 0
        for g, slots in list(self.parity.items()):
            k, m = self.group_params.get(g, (self.k, self.m))
            if not m or not slots:
                continue
            fec = Fec(k, m)
            width = max((len(v) for v in slots.values()), default=0)
            if not width:
                continue
            have = {s: v + b"\x00" * (width - len(v)) for s, v in slots.items()}
            start = g * k
            # the last group may be short: encoder zero-padded it up to k rows,
            # so those slots are known and must not count as erasures
            real = max(0, min(k, self.n_data - start))
            for s in range(real, k):
                have[s] = b"\x00" * width
            for s in range(k):
                idx = start + s
                if idx < self.n_data and idx in self.data:
                    c = self.data[idx] + b"\x00" * (width - len(self.data[idx]))
                    have[s] = c
            rec = fec.recover(have, width)
            if not rec:
                continue
            lens = chunk_layout(self.file_size, self.n_data)
            for s, row in rec.items():
                idx = start + s
                if idx < self.n_data and idx not in self.data:
                    self.data[idx] = row[:lens[idx]]
                    got += 1
        self.recovered += got
        return got

    def assemble(self) -> bytes:
        if not self.complete:
            raise ValueError("incomplete: %d/%d packets (%.1f%%)"
                             % (len(self.data), self.n_data or 0, self.percent))
        out = b"".join(self.data[i] for i in range(self.n_data))
        out = out[:self.file_size]
        if self.digest and sha256(out) != self.digest:
            raise ValueError("sha256 mismatch after reassembly")
        return out


# ----------------------------------------------------------- frame sources

def iter_frames(path: str) -> Iterator[np.ndarray]:
    p = Path(path)
    if p.is_dir():
        for f in sorted(p.glob("f*.png")):
            img = cv2.imread(str(f))
            if img is not None:
                yield img
        return
    if p.suffix.lower() == ".gif":
        with Image.open(p) as im:
            for fr in ImageSequence.Iterator(im):
                yield cv2.cvtColor(np.array(fr.convert("RGB")), cv2.COLOR_RGB2BGR)
        return
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise ValueError("cannot open " + str(p))
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            yield fr
    finally:
        cap.release()


def decode_frames(frames: Iterable[np.ndarray], col: Collector, cfg: StreamConfig,
                  on_frame: Callable[[int], None] | None = None) -> tuple[int, int]:
    det = cv2.QRCodeDetector()
    grid_mode = cfg.mode == "grid"
    good = bad = 0
    for i, fr in enumerate(frames):
        payload = None
        if not grid_mode:
            payload = decode_qr(fr, det)
        if payload is None:
            g = detect_grid(fr, cfg.modules)
            if g is not None:
                payload = unpack_grid(g)
            else:
                payload = decode_qr(fr, det)
        if payload and col.add(payload):
            good += 1
        else:
            bad += 1
        if on_frame:
            on_frame(i + 1)
    return good, bad


def decode_file(path: str, cfg: StreamConfig, col: Collector | None = None,
                loops: int = 1, on_frame: Callable[[int], None] | None = None):
    col = col or Collector(k=cfg.k, m=cfg.m)
    for _ in range(loops):
        good, bad = decode_frames(iter_frames(path), col, cfg, on_frame)
        n = col.recover()
        col.loops += 1
        yield col, good, bad, n
    return col
