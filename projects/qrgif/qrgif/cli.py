"""QR-GIF command line: encode files into visual streams, recover them back.

    python -m qrgif encode FILE -o out.gif
    python -m qrgif decode STREAM.gif -o recovered.bin
    python -m qrgif info STREAM.gif
    python -m qrgif bench
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .codec import (Collector, StreamConfig, decode_frames, encode_file,
                    grid_capacity_bytes, iter_frames)
from .protocol import sha256


def _cfg_from(args) -> StreamConfig:
    cfg = StreamConfig()
    for attr in ("mode", "modules", "module_px", "ec", "k", "m", "chunk", "fps"):
        v = getattr(args, attr, None)
        if v is not None:
            setattr(cfg, attr, v)
    return cfg


def cmd_encode(args) -> int:
    src = Path(args.file)
    if not src.is_file():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 2
    out = args.output or str(src) + "." + (args.container if args.container != "png" else "png")
    cfg = _cfg_from(args)
    cfg.name = src.name
    if cfg.mode == "grid":
        cap = grid_capacity_bytes(cfg.modules) - 40      # packet header + manifest slack
        if cfg.chunk > cap:
            print(f"error: chunk {cfg.chunk} exceeds grid capacity {cap} "
                  f"for modules={cfg.modules} (raise --modules or lower --chunk)",
                  file=sys.stderr)
            return 2

    t0 = time.perf_counter()
    stats = encode_file(str(src), out, cfg, fmt=args.container)
    dt = time.perf_counter() - t0
    size = (sum(f.stat().st_size for f in Path(out).glob("*.png"))
            if cfg_mode_is_png(args) else Path(out).stat().st_size)
    payload_kbps = stats.payload_bytes * 8 / 1000 / dt

    print(f"encoded   {src}")
    print(f"  payload   {stats.payload_bytes:,} bytes  "
          f"({sha256(src.read_bytes())[:8].hex()}...)")
    print(f"  packets   {stats.data_frames:,} data + {stats.parity_frames:,} parity "
          f"+ {stats.manifest_frames:,} manifest")
    print(f"  frames    {stats.frames:,} at {cfg.fps:g} fps "
          f"({stats.frames / cfg.fps:.1f}s of playback)")
    print(f"  transport {cfg.mode}"
          + (f" {cfg.modules}x{cfg.modules} @ {cfg.module_px}px"
             if cfg.mode == "grid" else f" ec={cfg.ec} @ {cfg.module_px}px")
          + f", FEC {cfg.k}+{cfg.m}")
    print(f"  output    {out}  ({size/1024:.1f} KiB)")
    print(f"  encode    {dt:.2f}s  ({payload_kbps:.1f} kbit/s of payload)")
    if args.container == "png":
        print(f"  playback  {out} is a frame folder; pass a folder or video to decode")
    return 0


def cfg_mode_is_png(args) -> bool:
    return args.container == "png" and Path(args.output or "").suffix == ""


def cmd_decode(args) -> int:
    src = Path(args.stream)
    if not src.exists():
        print(f"error: no such stream: {src}", file=sys.stderr)
        return 2
    cfg = _cfg_from(args)
    col = Collector(k=cfg.k, m=cfg.m)
    loops = max(1, args.loops)

    t0 = time.perf_counter()
    good = bad = fec = 0
    for n in range(loops):
        if args.progress:
            print(f"  loop {n + 1}/{loops}...", flush=True)
        g, b = decode_frames(iter_frames(str(src)), col, cfg)
        good += g
        bad += b
        fec += col.recover()
    dt = time.perf_counter() - t0

    print(f"decoded   {src}")
    fps = (good + bad) / dt if dt else 0.0
    print(f"  scanned   {good + bad} frames in {dt:.2f}s ({fps:.1f} fps decode)")
    print(f"  packets   {len(col.data)}/{col.n_data or '?'} "
          f"({col.percent:.1f}% coverage), {fec} rebuilt by Reed-Solomon")
    print(f"  rejected  {col.rejected} malformed/mismatched payloads")

    if not col.complete:
        print(f"  status    INCOMPLETE - missing {len(col.missing())} packet(s). "
              f"Scan another loop with --loops or point at more captures.")
        if args.loose:
            return 1
        return 1
    try:
        data = col.assemble()
    except ValueError as e:
        print(f"  status    FAILED integrity: {e}", file=sys.stderr)
        return 1
    digest = sha256(data).hex()
    print(f"  status    COMPLETE - sha256 {digest[:16]}... VERIFIED "
          f"({len(data):,} bytes, {len(data) * 8 / 1000 / dt:.1f} kbit/s recovered)")
    dest = args.output or (col.name or "recovered.bin")
    Path(dest).write_bytes(data)
    print(f"  wrote     {dest}")
    return 0


def cmd_info(args) -> int:
    src = Path(args.stream)
    cfg = _cfg_from(args)
    col = Collector(k=cfg.k, m=cfg.m)
    for fr in iter_frames(str(src)):
        from .codec import decode_qr, detect_grid, unpack_grid
        import cv2
        det = cv2.QRCodeDetector()
        p = decode_qr(fr, det)
        if p is None:
            g = detect_grid(fr, cfg.modules)
            p = unpack_grid(g) if g is not None else None
        if p:
            col.add(p)
        if col.n_data and len(col.data) >= col.n_data:
            break
    print(f"{src.name}")
    if not col.n_data:
        print("  no QR-GIF packets recognised (is this the right stream/transport?)")
        return 1
    print(f"  session    {col.session.hex()}")
    print(f"  file       {col.name}")
    print(f"  payload    {col.file_size:,} bytes")
    print(f"  packets    {len(col.data)}/{col.n_data} present "
          f"({col.percent:.1f}%)")
    print(f"  sha256     {(col.digest.hex() if col.digest else '?')[:16]}...")
    if col.complete:
        try:
            col.assemble()
            print("  integrity  VERIFIED")
        except ValueError as e:
            print(f"  integrity  FAILED: {e}")
    else:
        print(f"  integrity  pending - missing {len(col.missing())}")
    return 0


def cmd_bench(args) -> int:
    import runpy
    sys.argv = ["bench.py"] + ([f"--bytes", str(args.bytes)] if args.bytes else [])
    runpy.run_path(str(Path(__file__).parent.parent / "bench.py"), run_name="__main__")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="qrgif",
                                 description="Encode files into visual streams "
                                             "and recover them.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_cfg(p):
        p.add_argument("--mode", choices=["grid", "qr"], default=None)
        p.add_argument("--modules", type=int, default=None,
                       help="grid symbol size (odd, >=21)")
        p.add_argument("--module-px", dest="module_px", type=int, default=None)
        p.add_argument("--ec", choices=["L", "M", "Q", "H"], default=None)
        p.add_argument("--k", type=int, default=None, help="data packets per FEC group")
        p.add_argument("--m", type=int, default=None, help="parity packets per group")
        p.add_argument("--chunk", type=int, default=None, help="payload bytes per packet")
        p.add_argument("--fps", type=float, default=None)

    pe = sub.add_parser("encode", help="encode a file into a visual stream")
    pe.add_argument("file")
    pe.add_argument("-o", "--output")
    pe.add_argument("--container", default="gif",
                    choices=["gif", "mp4", "png"],
                    help="gif = best for sharing, png = lossless folder")
    add_cfg(pe)
    pe.set_defaults(func=cmd_encode)

    pd = sub.add_parser("decode", help="recover a file from a stream")
    pd.add_argument("stream")
    pd.add_argument("-o", "--output")
    pd.add_argument("--loops", type=int, default=1,
                    help="re-scan the stream N times (FEC fills gaps)")
    pd.add_argument("--progress", action="store_true")
    pd.add_argument("--loose", action="store_true",
                    help="exit 1 instead of 2 on incomplete")
    add_cfg(pd)
    pd.set_defaults(func=cmd_decode)

    pi = sub.add_parser("info", help="inspect a stream without decoding")
    pi.add_argument("stream")
    add_cfg(pi)
    pi.set_defaults(func=cmd_info)

    pb = sub.add_parser("bench", help="run the throughput benchmark")
    pb.add_argument("--bytes", type=int, default=0)
    pb.set_defaults(func=cmd_bench)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
