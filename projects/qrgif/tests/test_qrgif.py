"""End-to-end tests: every transport, every container, lossy channels, FEC."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bench import degrade, run_case
from qrgif.codec import (Collector, StreamConfig, build_frames, decode_frames,
                         encode_file, grid_capacity_bytes, iter_frames,
                         pack_grid, unpack_grid, _unify_size)
from qrgif.protocol import (Fec, b45decode, b45encode, chunk_layout, kind_of,
                            make_data, make_manifest, make_parity, parse_data,
                            parse_manifest, parse_parity, sha256, split)

PAYLOAD = bytes((i * 7 + 13) % 256 for i in range(9000))


class ProtocolTests(unittest.TestCase):
    def test_base45_roundtrip(self):
        for n in (0, 1, 2, 3, 255, 256, 1000):
            raw = os.urandom(n)
            self.assertEqual(b45decode(b45encode(raw)), raw)

    def test_packet_roundtrip(self):
        digest = sha256(PAYLOAD)
        sess = os.urandom(8)
        chunks = split(PAYLOAD, 200)
        for i, chunk in enumerate(chunks):
            raw = make_data(sess, i, len(chunks), len(PAYLOAD), chunk, digest)
            p = parse_data(raw)
            self.assertIsNotNone(p, f"packet {i} failed to parse")
            self.assertEqual(p.chunk, chunk)
            self.assertEqual(p.index, i)

    def test_corrupt_packet_rejected(self):
        digest = sha256(PAYLOAD)
        chunks = split(PAYLOAD, 200)
        # sanity: the pristine packet parses, so rejection below is the CRC's doing
        self.assertIsNotNone(
            parse_data(make_data(b"12345678", 0, len(chunks), len(PAYLOAD),
                                 chunks[0], digest)))
        raw = bytearray(make_data(b"12345678", 0, len(chunks), len(PAYLOAD),
                                  chunks[0], digest))
        raw[-1] ^= 0xFF
        self.assertIsNone(parse_data(bytes(raw)))

    def test_padding_is_tolerated(self):
        """Transports pad (the grid bit-packs); header length must win."""
        digest = sha256(PAYLOAD)
        chunks = split(PAYLOAD, 200)
        chunk = chunks[0]
        raw = make_data(b"12345678", 0, len(chunks), len(PAYLOAD), chunk, digest)
        p = parse_data(raw + b"\x00" * 37)
        self.assertIsNotNone(p)
        self.assertEqual(p.chunk, chunk)

    def test_chunk_layout_matches_split(self):
        for size, chunk in ((9000, 200), (9000, 350), (1, 200), (199, 200)):
            data = bytes(range(size % 256)) + b"\xab" * (size - size % 256) \
                if size else b""
            data = data[:size]
            parts = split(data, chunk)
            self.assertEqual(sum(chunk_layout(size, len(parts))), size)
            self.assertEqual(b"".join(parts), data)

    def test_manifest_roundtrip(self):
        sess, digest = os.urandom(8), sha256(PAYLOAD)
        m = parse_manifest(make_manifest(sess, 10, 9000, digest, "note.txt"))
        self.assertIsNotNone(m)
        self.assertEqual(m[4], "note.txt")
        self.assertEqual(m[3], digest)

    def test_kind_of(self):
        sess, digest = os.urandom(8), sha256(PAYLOAD)
        self.assertEqual(kind_of(make_data(sess, 0, 8, 9000, b"x", digest)), "data")
        self.assertEqual(kind_of(make_parity(sess, 0, 16, 4, 16, b"y")), "parity")
        self.assertEqual(kind_of(make_manifest(sess, 8, 9000, digest, "f")), "manifest")


class FecTests(unittest.TestCase):
    def test_recovers_up_to_m_losses(self):
        chunks = split(PAYLOAD, 200)[:16]
        fec = Fec(16, 4)
        width = max(len(c) for c in chunks)
        padded = [c + b"\x00" * (width - len(c)) for c in chunks]
        parity = fec.parity(chunks)
        self.assertEqual(len(parity), 4)
        for lost in ((0,), (0, 5), (0, 5, 9), (0, 5, 9, 13)):
            have = {i: padded[i] for i in range(16) if i not in lost}
            for s, p in enumerate(parity):
                have[16 + s] = p + b"\x00" * (width - len(p))
            rec = fec.recover(have, width)
            self.assertIsNotNone(rec, f"failed to recover losses {lost}")
            for i in lost:
                self.assertEqual(rec[i][:len(chunks[i])], chunks[i],
                                 f"recovered chunk {i} mismatched")

    def test_cannot_recover_beyond_m(self):
        chunks = split(PAYLOAD, 200)[:16]
        fec = Fec(16, 4)
        width = max(len(c) for c in chunks)
        padded = [c + b"\x00" * (width - len(c)) for c in chunks]
        parity = fec.parity(chunks)
        have = {i: padded[i] for i in range(16) if i not in (0, 1, 2, 3, 4)}
        for s, p in enumerate(parity):
            have[16 + s] = p + b"\x00" * (width - len(p))
        self.assertIsNone(fec.recover(have, width))

    def test_short_group_zero_padding_is_known(self):
        """A short final group is zero-padded at encode; decoder must know."""
        chunks = split(PAYLOAD, 200)          # 45 packets -> last group short
        fec = Fec(16, 4)
        k, m = 16, 4
        last_start = (len(chunks) // k) * k
        grp = chunks[last_start:]
        width = max(len(c) for c in grp)
        parity = fec.parity(grp)
        have = {}
        for s in range(len(grp)):
            c = grp[s] + b"\x00" * (width - len(grp[s]))
            if s != 1:
                have[s] = c
        for s, p in enumerate(parity):
            have[k + s] = p + b"\x00" * (width - len(p))
        for s in range(len(grp), k):
            have[s] = b"\x00" * width
        rec = fec.recover(have, width)
        self.assertIsNotNone(rec)
        self.assertEqual(rec[1][:len(grp[1])], grp[1])


class GridTests(unittest.TestCase):
    def test_pack_unpack_roundtrip(self):
        for modules in (25, 33, 49, 65, 97):
            cap = grid_capacity_bytes(modules)
            payload = os.urandom(cap)
            self.assertEqual(unpack_grid(pack_grid(payload, modules))[:cap],
                             payload, f"modules={modules}")

    def test_capacity_is_honest(self):
        """Packing exactly `capacity` bytes must never overflow the grid."""
        import numpy as np
        from qrgif.codec import _grid_mask
        for modules in (25, 49, 65, 97):
            cap = grid_capacity_bytes(modules)
            bits_needed = cap * 8
            self.assertLessEqual(bits_needed, int(_grid_mask(modules).sum()))
            # one byte more must raise
            with self.assertRaises(ValueError):
                pack_grid(b"\x00" * (cap + 1), modules)

    def test_render_is_not_inverted(self):
        """Regression: 1 = dark module must render as a BLACK pixel."""
        import numpy as np
        from qrgif.codec import render_grid
        img = render_grid(b"\x00" * 8, 65, 6, quiet=2)
        # quiet border is white
        self.assertEqual(int(img[0, 0]), 255)
        # finder corner (a dark module) must be black
        self.assertEqual(int(img[2 * 6, 2 * 6]), 0)

    def test_unify_size(self):
        import numpy as np
        frames = [np.full((10, 10), 255, np.uint8),
                  np.full((6, 14), 0, np.uint8)]
        out = _unify_size(frames)
        self.assertTrue(all(f.shape == (10, 14) for f in out))

    def test_finders_are_isolated(self):
        """Separator ring means the contour detector can find each finder."""
        import cv2
        from qrgif.codec import _finder_boxes, render_grid
        img = render_grid(os.urandom(200), 65, 6, quiet=2)
        _, bw = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        boxes = _finder_boxes(bw)
        self.assertGreaterEqual(len(boxes), 3)
        for b in boxes[:3]:
            self.assertGreater(b[3], 0.7, "finder template score too low")


class TransportTests(unittest.TestCase):
    """Encode -> decode through real files, every transport x container."""

    def _roundtrip(self, mode, fmt, payload=PAYLOAD, **kw):
        cfg = StreamConfig(mode=mode, chunk=200, k=16, m=4, **kw)
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            src = work / "in.bin"
            src.write_bytes(payload)
            out = work / f"stream.{fmt}"
            encode_file(str(src), str(out), cfg, fmt=fmt)
            col = Collector(k=cfg.k, m=cfg.m)
            decode_frames(iter_frames(str(out)), col, cfg)
            col.recover()
            self.assertTrue(col.complete,
                            f"{mode}/{fmt}: only {len(col.data)}/{col.n_data}")
            self.assertEqual(col.assemble(), payload, f"{mode}/{fmt} mismatch")

    def test_grid_all_containers(self):
        for fmt in ("png", "gif", "mp4"):
            with self.subTest(fmt=fmt):
                self._roundtrip("grid", fmt, **{"modules": 65, "module_px": 6})

    def test_qr_all_containers(self):
        for fmt in ("png", "gif", "mp4"):
            with self.subTest(fmt=fmt):
                self._roundtrip("qr", fmt, **{"ec": "L", "module_px": 4})

    def test_qr_frame_sizes_are_uniform(self):
        """Regression: variable QR versions silently killed parity frames."""
        cfg = StreamConfig(mode="qr", ec="L", module_px=4, chunk=200, k=16, m=4)
        frames = list(build_frames(PAYLOAD, cfg))
        shapes = {f.shape for f in frames}
        self.assertEqual(len(shapes), 1, f"mixed frame sizes: {shapes}")

    def test_fec_survives_frame_loss(self):
        cfg = StreamConfig(mode="grid", modules=65, module_px=6,
                           chunk=200, k=16, m=4)
        frames = list(build_frames(PAYLOAD, cfg))
        lossy = [f for i, f in enumerate(frames) if i % 7 != 3]
        self.assertLess(len(lossy), len(frames))
        col = Collector(k=cfg.k, m=cfg.m)
        decode_frames(iter(lossy), col, cfg)
        col.recover()
        self.assertTrue(col.complete, "FEC failed to fill losses")
        self.assertEqual(col.assemble(), PAYLOAD)

    def test_sha_mismatch_raises(self):
        cfg = StreamConfig(mode="grid", modules=65, module_px=6, chunk=200)
        frames = list(build_frames(PAYLOAD, cfg))
        col = Collector(k=cfg.k, m=cfg.m)
        decode_frames(iter(frames), col, cfg)
        col.data[0] = b"\x00" * len(col.data[0])     # corrupt after decode
        with self.assertRaises(ValueError):
            col.assemble()


class ChannelTests(unittest.TestCase):
    """Simulated camera: blur / downscale / noise / rotation."""

    def _case(self, **degrade_kw):
        cfg = StreamConfig(mode="grid", modules=65, module_px=6,
                           chunk=350, k=16, m=4)
        with tempfile.TemporaryDirectory() as td:
            return run_case(PAYLOAD, cfg, "png", Path(td),
                            degrade_kw=degrade_kw)

    def test_clean(self):
        self.assertTrue(self._case()["verified"])

    def test_blur(self):
        self.assertTrue(self._case(blur=3)["verified"])

    def test_downscale_to_60pct(self):
        self.assertTrue(self._case(scale=0.6)["verified"])

    def test_noise(self):
        self.assertTrue(self._case(noise=12)["verified"])

    def test_rotation(self):
        self.assertTrue(self._case(rot=3.0)["verified"])

    def test_arbitrary_rotations(self):
        """Finder detection must work at any angle, not just cardinals.

        The old contour-template gate found nothing past ~5 degrees (it scored
        an axis-aligned resize of a rotated finder); the radial-profile score
        replaced it. Cardinal angles pass either way, so they are included only
        as a control -- 15/30/45 are the ones that catch the regression.
        """
        for rot in (15.0, 30.0, 45.0, 90.0, 135.0):
            with self.subTest(rot=rot):
                self.assertTrue(self._case(rot=rot)["verified"],
                                f"rotation {rot} deg failed to decode")

    def test_combined_moderate(self):
        self.assertTrue(
            self._case(rot=3.0, blur=2, noise=10)["verified"])

    def test_degrade_helper_shape(self):
        import numpy as np
        img = np.full((50, 50), 255, np.uint8)
        out = degrade(img, blur=2, scale=0.5, noise=5, rot=5)
        self.assertEqual(out.dtype, np.uint8)
        self.assertLess(out.shape[0], 50)     # scaled down


class CliTests(unittest.TestCase):
    def test_encode_decode_cli(self):
        from qrgif.cli import main
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            src = work / "f.bin"
            src.write_bytes(PAYLOAD)
            out = work / "s.gif"
            rc = main(["encode", str(src), "-o", str(out), "--container", "gif",
                       "--mode", "grid", "--modules", "65", "--chunk", "350"])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            dest = work / "back.bin"
            rc = main(["decode", str(out), "-o", str(dest),
                       "--mode", "grid", "--modules", "65", "--chunk", "350"])
            self.assertEqual(rc, 0)
            self.assertEqual(dest.read_bytes(), PAYLOAD)

    def test_decode_incomplete_fails(self):
        from qrgif.cli import main
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            src = work / "f.bin"
            src.write_bytes(PAYLOAD)
            out = work / "s.gif"
            main(["encode", str(src), "-o", str(out), "--container", "gif",
                  "--mode", "grid", "--modules", "65", "--chunk", "350"])
            # wrong module count -> nothing decodable
            rc = main(["decode", str(out), "-o", str(work / "x.bin"),
                       "--mode", "grid", "--modules", "41", "--chunk", "350"])
            self.assertNotEqual(rc, 0)

    def test_info(self):
        from qrgif.cli import main
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            src = work / "f.bin"
            src.write_bytes(PAYLOAD)
            out = work / "s.gif"
            main(["encode", str(src), "-o", str(out), "--container", "gif",
                  "--mode", "grid", "--modules", "65", "--chunk", "350"])
            rc = main(["info", str(out), "--mode", "grid", "--modules", "65"])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
