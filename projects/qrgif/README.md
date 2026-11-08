# QR-GIF

Turn a file into a stream of QR-style frames, then recover it from frames again.

Two transports:

- **`grid`** — a custom module grid (3 QR-style finders, timing row/col, raw bits).
  Fast and dense, but only QR-GIF reads it.
- **`qr`** — actual ISO QR codes, so any phone camera can see the stream. Slower
  and less dense, but interoperable.

Both carry the same packet format, the same stream-level Reed-Solomon parity, and
the same SHA-256-verified manifest, so you can encode in one transport and decode
in the other.

```
python app.py                      # the desktop app (Encode / Decode / Broadcast)
python -m qrgif encode FILE ...    # CLI
python -m qrgif decode STREAM ...
python -m qrgif info FILE
python -m qrgif bench
python -m unittest discover -s tests
```

## Install

Python 3.12+.

```
pip install numpy opencv-python-headless pillow qrcode reedsolo imageio-ffmpeg
```

`tkinter` ships with CPython on Windows; MP4 output needs the `imageio-ffmpeg`
bundled binary.

## The app

- **Encode** — pick a file or tick *Rickroll demo payload*, choose transport /
  module count / bytes per packet / fps / FEC, watch the animated stream, optionally
  save it as GIF, MP4, or a PNG sequence. The capacity readout warns before you
  pick a `chunk` that will not fit the grid.
- **Decode** — open a GIF / MP4 / AVI / PNG folder, watch coverage climb, watch
  Reed-Solomon rebuild the gaps, and get the recovered file plus its SHA-256.
  Detection is per-frame: `grid` and `qr` are both tried, so you only have to get
  the module count right.
- **Broadcast** — the distribution stub: CRT noise with a QR of your download link
  pasted beside it. The screen you leave running.

## How it works

```
data --split--> chunks --packet--> frames --container--> GIF/MP4/PNGs
                      \--RS parity--/                          |
                                                               v
data <--unpack-- Collector <--FEC rebuild <--detect <-- frames --+
         \--SHA-256 check--/
```

**Packets.** Every frame carries one packet with a raw binary header
(`>4s8sIHI8sI`): magic, session id, index, data-packet count, file size, a CRC32,
and the first 8 bytes of the payload's SHA-256. A CRC32 failure is a clean
erasure — the packet is dropped, never half-trusted.

**Why base45 for QR.** OpenCV's QR decoder mangles arbitrary binary through
byte-mode, so QR payloads travel as base45 text in alphanumeric mode.
`grid` packs raw bits and skips base45 entirely.

**Chunk layout is deterministic.** `chunk_layout(file_size, n_data)` derives every
chunk length from the header alone, so receivers never need a side channel and
the transport's padding is ignored in favour of the declared length.

**FEC is stream-level, column-wise.** `Fec(k, m)` builds `m` parity packets for
each group of `k` data packets by Reed-Solomon over the *columns* of the group
(`reedsolo.RSCodec(m, nsize=k+m)`). Any `m` erasures per group are rebuilt. Short
final groups are zero-padded and the padding rows are known, so they are re-inserted
during recovery.

**Manifest + SHA-256.** A manifest frame repeats the session, packet count, file
size, and the full digest every `manifest_every` frames. Recovery is only called
complete when `assemble()` reproduces the digest; otherwise it raises and the app
says so instead of handing you a corrupted file.

**Grid detection is rotation-invariant.** Finders are scored by their *radial
profile* — mean darkness versus radius in module units — which is unchanged by
rotation and scaling, and near-zero for a solid blob. The right-angle vertex of the
three finders anchors the origin at any angle, so all orientations decode.

## Measured numbers

20 KB payload, PNG (lossless) reference, grid 65×65 @ 6 px, chunk 350 B, FEC 16+4,
unless noted. From `python -m qrgif bench`.

| transport | payload/frame | frames | decode rate | throughput |
|---|---|---|---|---|
| grid 65 @ 6px, chunk 350 | 491 B | 82 | 42 fps | **1.95 kbit/s per fps** |
| grid 65 @ 6px, chunk 200 | 245 B | 141 | 52 fps | 1.13 kbit/s per fps |
| grid 97 @ 4px, chunk 350 | 491 B | 82 | 52 fps | 1.95 kbit/s per fps |
| QR, EC L, 4px | 245 B | 141 | 30 fps | 1.13 kbit/s per fps |
| QR, EC H, 4px | 245 B | 141 | 12 fps | 1.13 kbit/s per fps |

"kbit/s per fps" scales linearly: a 20 KB payload in 82 frames delivers 491 B per
frame, so every frame per second of playback is another 491 B/s.

Camera-channel sweep (grid 65/6px, chunk 350): clean, blur 1, blur 3, scale 0.6,
noise 12, rot 3°, and rot 3 + blur 2 + noise 10 all recover **100%**.

### Honest limits

- **Resolution floor ≈ 3 px/module.** Downscaling to 0.50 (3.0 px/module) still
  decodes; 0.45 and below fails. This is the hard constraint on how small the code
  can be on screen.
- **Blur > 3 kills detection** at full resolution. Blur ≤ 3 survives.
- **Blur at half resolution is unforgiving** — scale 0.5 tolerates blur 0–1, and
  fails at blur 2. Scale 0.4 fails even at blur 2 with no noise. Do not stack heavy
  downscale with heavy blur.
- **fps is the real throughput lever.** Every extra frame per second is another
  491 B/s at this density; the encoder is not the bottleneck, the decoder is.
- **The real value is one-to-many broadcast.** A screen decoded by many cameras is
  the point; point-to-point file transfer has better options.
- **MP4 is verified frame-by-frame.** The writer counts frames after writing and
  falls back to MJPG-in-AVI if any were dropped, raising rather than shipping a
  stream with holes. GIF and PNG are the reliable share containers.

## License

Personal project; no warranty.
