"""Smoke: App() constructs, Encode/Decode workers run their full path.

Kept out of tests/ because it needs a real display (tkinter).
"""
import queue
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import app as appmod
from qrgif.codec import StreamConfig


def drain(q, limit=20000):
    kinds = {}
    last = {}
    n = 0
    while n < limit:
        try:
            k, p = q.get_nowait()
        except queue.Empty:
            break
        kinds[k] = kinds.get(k, 0) + 1
        last[k] = p
        n += 1
    return kinds, last


def main():
    a = appmod.App()
    print("App() constructed ok")

    # --- encode the demo payload through the real worker, gif out
    q = queue.Queue()
    tmp = Path(tempfile.mkdtemp())
    out = str(tmp / "demo.gif")
    cfg = StreamConfig(mode="grid", modules=65, chunk=350, k=16, m=4, fps=10)
    cfg.name = "rickroll.txt"
    appmod.EncodeWorker(appmod.RICKROLL, cfg, out, "gif", q).run()
    kinds, last = drain(q)
    print("encode:", kinds)
    print("  done ->", last.get("done"))
    print("  saved ->", last.get("saved"))
    assert Path(out).is_file() and Path(out).stat().st_size > 0, "gif not written"
    assert "error" not in kinds, last.get("error")

    # --- decode that gif back through the real worker
    q2 = queue.Queue()
    recovered = str(tmp / "back.bin")
    cfg2 = StreamConfig()
    cfg2.modules = 65
    appmod.DecodeWorker(out, cfg2, recovered, q2).run()
    kinds2, last2 = drain(q2)
    print("decode:", kinds2)
    print("  coverage ->", last2.get("coverage"))
    print("  done ->", last2.get("done"))
    assert "error" not in kinds2, last2.get("error")
    back = Path(recovered).read_bytes()
    assert back == appmod.RICKROLL, "payload mismatch"
    print("  payload round-trip VERIFIED (%d bytes)" % len(back))

    # --- encode without saving (preview only) must not crash
    q3 = queue.Queue()
    appmod.EncodeWorker(appmod.RICKROLL, StreamConfig(), None, "gif", q3).run()
    k3, l3 = drain(q3)
    assert "error" not in k3, l3.get("error")
    print("preview-only encode ok:", k3.get("enc_frame"), "frames")

    a.destroy()
    print("ALL GUI WORKER PATHS OK")


if __name__ == "__main__":
    main()
