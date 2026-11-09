"""Where is the real resolution floor for the grid transport?"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from bench import run_case, degrade
from qrgif.codec import StreamConfig

payload = bytes((i * 7 + 13) % 256 for i in range(12000))
cfg = StreamConfig(mode="grid", modules=65, module_px=6, chunk=350, k=16, m=4)

with tempfile.TemporaryDirectory() as td:
    work = Path(td)
    print("pure downscale (no blur) — how small can the symbol get:")
    for s in (1.0, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2):
        r = run_case(payload, cfg, "png", work, degrade_kw=dict(scale=s))
        px = int(414 * s)
        print(f"  scale {s:4.2f} ({px:3d}px, {6*s:4.1f} px/module) "
              f"-> {r['coverage_pct']:6.2f}%  {'ok' if r['verified'] else 'FAIL'}")

    print("\nblur only at scale 1.0:")
    for b in (1, 2, 3, 4, 5, 7):
        r = run_case(payload, cfg, "png", work, degrade_kw=dict(blur=b))
        print(f"  blur {b} -> {r['coverage_pct']:6.2f}%  {'ok' if r['verified'] else 'FAIL'}")

    print("\nblur at scale 0.5 (3 px/module):")
    for b in (0, 1, 2, 3):
        r = run_case(payload, cfg, "png", work, degrade_kw=dict(scale=0.5, blur=b))
        print(f"  scale0.5 blur {b} -> {r['coverage_pct']:6.2f}%  {'ok' if r['verified'] else 'FAIL'}")
