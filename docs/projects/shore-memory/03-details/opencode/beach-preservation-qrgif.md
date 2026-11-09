# Beach Preservation — QR-GIF Session (2026-10-20 to 2026-11-02)

> Manual archive. The auto-compaction for this period failed
> (`compaction.summary reached the output token limit` and `compaction.interrupted`)
> because session `ses_003b39e05ffeNtA04zkTy2Ai9g` had grown to 17,841 messages
> / 730K tokens. This file preserves the narrative that the 3-tier system could
> not capture. The project files themselves are durable in
> `C:\Users\zutai\Documents\Default Project\qrgif\`.

## Objective
Build "QR-GIF": a Windows desktop app that encodes a file into a visual stream
(standard QR + a custom high-speed grid format) and decodes it back, with
stream-level Reed-Solomon FEC, verified by SHA-256. Distribute covertly via a
CRT-static screen with a download QR beside it.

## Requirements (user's vision)
- Pure QR dots (no decorative static), first payload a Rickroll.
- App is both encoder and decoder.
- Adaptive profiles: QR vs custom code, resolution, fps, ECC.
- Progress UI with recovered/verified percentages.
- Distributed via a CRT-static screen with a download QR.

## Architecture decisions
1. Raw binary packet headers (`>4s8sIHI8sI`); QR mode base45-encodes to survive
   OpenCV's QR decoder mangling arbitrary binary; grid mode packs raw bits.
2. Stream-level column-wise Reed-Solomon: `Fec(k, m)` = `RSCodec(m, nsize=k+m)`,
   default k=16, m=4. Any m erasures per group rebuilt. Short groups zero-padded
   with known padding rows re-inserted during recovery.
3. Per-packet CRC32 → any decode failure is a clean erasure. Final SHA-256 from a
   manifest frame verified before reporting completion.
4. Deterministic `chunk_layout` so receivers derive chunk lengths from headers alone.
5. Two transports: standard QR (interoperable) and custom `grid` (module grid, 3
   QR-style finder corners with 1-module quiet separators, timing row/col,
   1 = dark module).
6. No camera for now: benchmark via encode→MP4/GIF/PNG-sequence→decode round-trip
   plus simulated degradation (blur/scale/noise/rotation).
7. GIF/PNG are the reliable share containers; MP4 supported but verified
   frame-by-frame with fallback (MJPG-in-AVI) and hard error if frames dropped.
8. `decode_qr` retries with a 2× cubic upscale (OpenCV flaky ~1/14 frames).

## Bugs found and fixed
1. Grid render polarity inverted (1 = dark module = black pixel). Fixed.
2. `_grid_mask`/`pack_grid` needed 1-module quiet separators around finders;
   timing row/col starts clear of finders.
3. `_finder_boxes` used contour fill heuristics → replaced with template
   verification (score ≥ 0.70).
4. `_sample` needed correct hi-res pull mapping + `WARP_INVERSE_MAP` (2×3 matrix).
5. `_unify_size` pads every frame to one canvas — variable QR versions silently
   dropped 18/58 parity frames in video containers before this fix.
6. `_write_mp4` counts frames after writing, falls back to MJPG-in-AVI, raises if
   frames dropped; stale PNG-sequence files cleared before writing.
7. `Collector`: parity stored as `dict[group][slot]` + `group_params`; `recover()`
   re-inserts known zero-padding rows for short groups.
8. Finder detection only worked at 0°/90°/180°/270° (axis-aligned resize of a
   rotated finder scored below gate). Replaced with radial-profile score
   (rotation- and scale-invariant; near-zero for solid blobs).
9. `degrade()` filled 3-channel frames with black (borderValue=255 interpreted as
   scalar, not tuple) → ink fraction 0.58 instead of 0.22. Fixed by expanding
   white to match channel count.
10. Benchmark failure label said "lost 0" when zero packets recognised → now says
    "no packets recognised".

## Measured numbers (20 KB, PNG reference)
- Grid 65 @ 6px, chunk 350: 82 frames, 42 fps decode, 1.95 kbit/s per fps
- Grid 97 @ 4px, chunk 350: 82 frames, 52 fps decode, 1.95 kbit/s per fps
- QR EC L: 141 frames, 30 fps, 1.13 kbit/s per fps
- QR EC H: 141 frames, 12 fps, 1.13 kbit/s per fps
- Camera sweep: clean, blur 1, blur 3, scale 0.6, noise 12, rot 3°, rot 3 + blur 2
  + noise 10 all recover 100%
- Resolution floor ≈ 3 px/module (scale 0.50 ok, 0.45 fails)
- Blur > 3 kills detection at full res; blur at half-res tolerates 0–1 only

## Verification
- 31/31 unit tests pass (unittest discover)
- GUI worker paths verified end-to-end: Rickroll → GIF → decode → SHA-256 match
- CLI round-trips via documented flags
- Benchmark: 17 cases, all VERIFIED

## Files
- `qrgif/qrgif/protocol.py`: packet framing, base45, chunk_layout/split, Fec
- `qrgif/qrgif/codec.py`: grid/QR renderers, detection, stream build/encode/decode,
  Collector, _unify_size, _write_mp4
- `qrgif/qrgif/cli.py`: CLI encode/decode/info/bench
- `qrgif/app.py`: Tkinter GUI (Encode/Decode/Broadcast tabs)
- `qrgif/bench.py`: throughput benchmark + degrade helpers
- `qrgif/tests/test_qrgif.py`: 31 tests
- `qrgif/README.md`: usage, numbers, honest limits

## Pending
- Distributed covertly via CRT-static screen with download QR (Broadcast tab exists)
- Camera hardware not available; experiments use video-file channel only
- No automatic hook from audit.record() to runObservationPass (kept separate)