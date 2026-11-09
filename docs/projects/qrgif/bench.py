"""QR-GIF throughput benchmark.

Encodes a payload, writes it to a real container (PNG sequence / GIF / MP4),
then decodes it back and measures recovered payload throughput. Optionally
degrades every frame (blur, downscale, noise, rotation) to model a camera
looking at a screen, which is the channel that actually matters.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from qrgif.codec import (Collector, StreamConfig, build_frames, decode_frames,
                         encode_file, iter_frames)
from qrgif.protocol import sha256


def degrade(frame: np.ndarray, blur: int = 0, scale: float = 1.0,
            noise: int = 0, rot: float = 0.0) -> np.ndarray:
    """Simulate a camera capturing a screen.

    Rotation pads first: the symbol fills the frame, and a bare warpAffine
    would crop the corner-anchored finders off the canvas -- an artefact no
    real camera produces, since a camera that loses a corner simply loses
    the frame.
    """
    h, w = frame.shape[:2]
    if rot:
        # Work on a padded canvas so no corner is cropped. The pad colour must
        # be a white that OpenCV honours for both gray and BGR input: a bare
        # scalar 255 is treated inconsistently across versions/channel counts,
        # so it is expanded to match the frame's depth explicitly.
        white = 255 if frame.ndim == 2 else (255,) * frame.shape[2]
        pad = int(max(w, h) * 0.35)
        frame = cv2.copyMakeBorder(frame, pad, pad, pad, pad,
                                   cv2.BORDER_CONSTANT, value=white)
        h, w = frame.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
        frame = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=white)
        # crop back to the largest centred square that still holds the symbol
        side = int(min(h, w) / 1.35)
        y0, x0 = (h - side) // 2, (w - side) // 2
        frame = frame[y0:y0 + side, x0:x0 + side]
    if scale != 1.0:
        frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    if blur:
        k = blur * 2 + 1
        frame = cv2.GaussianBlur(frame, (k, k), 0)
    if noise:
        rng = np.random.default_rng(0)
        n = rng.normal(0, noise, frame.shape).astype(np.float32)
        frame = np.clip(frame.astype(np.float32) + n, 0, 255).astype(np.uint8)
    return frame


def run_case(payload: bytes, cfg: StreamConfig, fmt: str, work: Path,
             degrade_kw: dict | None = None, loops: int = 1) -> dict:
    src = work / "payload.bin"
    src.write_bytes(payload)
    out = work / ("stream." + ("png" if fmt == "png" else fmt))

    t0 = time.perf_counter()
    encode_file(str(src), str(out), cfg, fmt=fmt)
    t_enc = time.perf_counter() - t0

    if degrade_kw:
        frames = [degrade(f, **degrade_kw) for f in iter_frames(str(out))]
        gen = iter(frames)
        n_frames = len(frames)
    else:
        gen = iter_frames(str(out))
        n_frames = None

    col = Collector(k=cfg.k, m=cfg.m)
    t0 = time.perf_counter()
    good = bad = 0
    for _ in range(loops):
        g, b = decode_frames(gen if loops == 1 else iter_frames(str(out)), col, cfg)
        good += g
        bad += b
        col.recover()
    t_dec = time.perf_counter() - t0

    verified = False
    try:
        verified = col.assemble() == payload
    except Exception:
        verified = False

    n_frames = n_frames if n_frames is not None else (good + bad)
    return {
        "mode": cfg.mode,
        "modules": cfg.modules if cfg.mode == "grid" else None,
        "chunk": cfg.chunk,
        "k": cfg.k, "m": cfg.m,
        "fmt": fmt,
        "payload_bytes": len(payload),
        "data_packets": col.n_data or 0,
        "packets_recovered": len(col.data),
        "recovered_via_fec": col.recovered,
        "frames": n_frames,
        "encode_s": round(t_enc, 3),
        "decode_s": round(t_dec, 3),
        "frames_per_s": round(n_frames / t_dec, 1) if t_dec else None,
        "verified": verified,
        "coverage_pct": round(col.percent, 2),
        "kbit_s_payload": round(len(payload) * 8 / 1000 / t_dec, 1) if t_dec else None,
        "kbit_s_per_fps": round(len(payload) * 8 / 1000 / n_frames, 2) if n_frames else None,
        "degrade": degrade_kw or {},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="QR-GIF throughput benchmark")
    ap.add_argument("--bytes", type=int, default=20000, help="payload size")
    ap.add_argument("--container", default="png",
                    choices=["png", "gif", "mp4"], help="png = lossless reference")
    ap.add_argument("--loops", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    payload = bytes((i * 7 + 13) % 256 for i in range(args.bytes))
    results = []

    configs = [
        ("grid 65 mod, 6px, chunk200, fec 16+4",
         StreamConfig(mode="grid", modules=65, module_px=6, chunk=200, k=16, m=4)),
        ("grid 65 mod, 6px, chunk350, fec 16+4",
         StreamConfig(mode="grid", modules=65, module_px=6, chunk=350, k=16, m=4)),
        ("grid 49 mod, 8px, chunk200, fec 16+4",
         StreamConfig(mode="grid", modules=49, module_px=8, chunk=200, k=16, m=4)),
        ("grid 97 mod, 4px, chunk350, fec 16+4",
         StreamConfig(mode="grid", modules=97, module_px=4, chunk=350, k=16, m=4)),
        ("grid 65 mod, 6px, chunk200, fec 16+2",
         StreamConfig(mode="grid", modules=65, module_px=6, chunk=200, k=16, m=2)),
        ("qr (standard), ec L, 4px",
         StreamConfig(mode="qr", ec="L", module_px=4, chunk=200, k=16, m=4)),
        ("qr (standard), ec H, 4px",
         StreamConfig(mode="qr", ec="H", module_px=4, chunk=200, k=16, m=4)),
    ]

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        print(f"payload: {args.bytes:,} bytes | container: {args.container} "
              f"(lossless reference) | loops: {args.loops}\n")
        for label, cfg in configs:
            try:
                r = run_case(payload, cfg, args.container, work, loops=args.loops)
            except Exception as e:
                print(f"{label:44s} FAILED: {e}")
                continue
            r["label"] = label
            results.append(r)
            print(f"{label:44s} {r['frames']:4d} fr  "
                  f"{r['frames_per_s'] or 0:6.1f} fps  "
                  f"{r['packets_recovered']:3d}/{r['data_packets']:<3d} pkt  "
                  f"fec+{r['recovered_via_fec']:<3d}  "
                  f"{r['kbit_s_per_fps'] or 0:7.2f} kbit/s per fps  "
                  f"{'VERIFIED' if r['verified'] else 'FAIL'}")

        # channel degradation sweep on the best grid config
        print("\ncamera-channel sweep (grid 65/6px, chunk350):")
        base = StreamConfig(mode="grid", modules=65, module_px=6,
                            chunk=350, k=16, m=4)
        sweeps = [
            ("clean", {}),
            ("blur 1", dict(blur=1)),
            ("blur 3", dict(blur=3)),
            ("scale 0.6", dict(scale=0.6)),
            ("scale 0.4 + blur 2", dict(scale=0.4, blur=2)),
            ("noise 12", dict(noise=12)),
            ("noise 12 + blur 1", dict(noise=12, blur=1)),
            ("rot 3deg", dict(rot=3.0)),
            ("rot 3 + blur 2 + noise 10", dict(rot=3.0, blur=2, noise=10)),
            ("scale 0.4 + blur2 + noise12 + rot2",
             dict(scale=0.4, blur=2, noise=12, rot=2.0)),
        ]
        for label, kw in sweeps:
            try:
                r = run_case(payload, base, args.container, work, degrade_kw=kw)
            except Exception as e:
                print(f"  {label:36s} FAILED: {e}")
                continue
            r["label"] = f"sweep: {label}"
            results.append(r)
            mark = ("VERIFIED" if r["verified"]
                    else (f"lost {r['data_packets'] - r['packets_recovered']}"
                          if r["packets_recovered"] else "no packets recognised"))
            print(f"  {label:36s} {r['frames']:4d} fr  "
                  f"{r['coverage_pct']:6.2f}%  fec+{r['recovered_via_fec']:<3d}  "
                  f"{mark}")

    (Path(__file__).parent / "bench_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote bench_results.json ({len(results)} cases)")


if __name__ == "__main__":
    main()
