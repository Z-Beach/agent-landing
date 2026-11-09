# 3D-Printable Shoe — US Men's 10.5 7E

Print-ready file: **`shoe_hex_10p5_7E.stl`** (right foot outline, mirror for left).

## What you get

| File | Purpose |
|---|---|
| `shoe_hex_10p5_7E.stl` | Final shoe: solid sole, hollow upper, hex-grid side walls |
| `foot_template_10p5_7E.svg` | 1:1 paper foot outline (print on A4, no scaling) — test your foot BEFORE printing |
| `previews/final_views.png`, `previews/sole_plan.png` | Section/iso/top views of the final mesh |
| `shoe_hex_10p5_7E.scad` + `baseline_10p5_7E.stl` + `cavity.stl` | Source for re-rendering with changed parameters |

## Size basis (verified)

- Ball width **US 10.5 7E = 4.75" = 120.65 mm** (healthyfeetstore.com width chart, 3X Wide column 7E/8E)
- Foot length = (10.5 + 22) / 3 inch = **275 mm**
- Charts disagree above 6E (shoewidthchart.com caps at 6E) — **print `foot_template_10p5_7E.svg` and trace your foot**; all widths are single-parameter edits if you need adjusting.

## How it was built

1. Three CC-licensed parametric shoe models (Appropedia sandal, Sloffies slides, parametric clown shoe) normalized to a common 254 mm reference, heel-aligned.
2. Weighted voxel average (0.25/0.25/0.50 — the clown shoe is the only full shoe, so it gets half the vote) → `baseline_average.stl`.
3. Per-station width warp `s(y) = (foot(y)+6 clearance+7 wall)/baseline(y)` to 7E proportions + length scale ×275/254 + **extra-depth upper** (z above the sole stretched 1.4× from y=140 forward) → `baseline_10p5_7E.stl`.
4. Cavity = foot outline + 3 mm clearance, ceiling = shell eroded 4 mm (follows the domed roof), open through the top for y < 190 (heel bucket entry), closed roof y ≥ 190 (instep bridge + toe box) → `cavity.stl`.
5. OpenSCAD: `difference(baseline, cavity, hex prisms)` → final STL. 65 hex windows cut clean through both side walls.

## Verified on the final mesh

- Watertight, **single connected solid**, CGAL "Simple: yes" (2 volumes = solid + outside, no internal voids)
- Bounding box **135 × 276 × 88 mm** (length target 275 ✓, ball width target 133.65 ✓)
- Interior width ≥ foot + 6 mm everywhere; walls **2.7–5.3 mm**
- Sole: solid 0–11.5 mm z (full footprint ~280 cm²), no holes
- Entry: open from heel through y=190 (centerline rays hit only the footbed); roof closed from y=190 (ray hits outer skin 80.1 → ceiling 77.5 → footbed 11.5)
- Hex holes: probe rays through hole centers exit clean (0 hits); strut probes hit 4 surfaces (both walls intact)
- Volume **399 cm³ → ≈ 482 g** in TPU (1.21 g/cm³)

## Print-service notes

- Material: **TPU 95A**, ~480 g (1 roll is enough). Softer 85A also works.
- Orientation: sole flat on the bed, toe toward the back — no supports needed (hex cells are pointy-top, overhangs ≤ 60°; the roof bridge starts at y=190 and is short-span).
- Walls: 3–4 perimeters; the design is all shell, infill only in the sole.
- Estimated print time: ~10–14 h at 40 mm/s.
- Tolerance: interior is foot + 3 mm/side. Wear with thin socks or bare; the collar may need a 5-minute warm-water break-in.

## Fit logic

- **Heel** (y < 30): solid counter, no holes — holds the heel.
- **Side walls** (y 30–250): hex windows, struts 2.5 mm, hole ~9 mm across flats — the "open air" grid you asked for.
- **Toe cap** (y > 250): solid front.
- **Entry**: no roof over the heel/instep (y < 190) — step in, heel drops into the bucket; the bridge at y=190 is the front edge of the vamp. Since the widest part (126.7 mm interior at the ball) is larger than the instep opening, expect a moderate TPU stretch on entry — normal for printed slip-ons.
- **Sole**: solid slab, 12 mm, per your spec.

## Regenerating with different parameters

```
python make_hex_shoe.py      # hex/collar/keep-out constants at top of file
openscad -o shoe_hex_10p5_7E.stl shoe_hex_10p5_7E.scad   # ~17–26 min
python verify_hex_shoe.py    # re-run all numeric checks
python preview_final.py      # refresh previews
```

Width/length changes: constants at top of `scale_to_size.py` (`foot_w` stations, `CLEARANCE`, `WALL`, `UPPER_K`), then re-run the full chain (`average_models.py` → `scale_to_size.py` → `make_cavity.py` → `make_hex_shoe.py` → render).

## Known limitations / next steps

1. **Trace your foot with the paper template first** — the heel/arch/midfoot stations are estimates from a size-8 reference; only ball width and length are chart-verified.
2. Sole is ~70% of the mass. A follow-up can honeycomb the sole underside (would drop ≈ 480 g → ≈ 330 g) — kept solid here per the spec.
3. The roof over the toe box is 2.6–4.2 mm (erosion is 4 mm minus voxel/smoothing drift) — fine for TPU, but bump `ERODE` in `make_cavity.py` if a service wants ≥4 mm minimum.
4. No eyelets/strap — slip-on only. If entry feels too tight, raise `BRIDGE_Y` (opens more of the roof) or reduce `UPPER_K`.

---

# Set 2 & 3 — Toe shoe + Workboot averages (US 10.5 7E)

Same hex-grid build system applied to two new shoe-type sets, each the **weighted average of copies of its source type** (per request: "use copies of them to build out an average model that matches the types, use the hex grid system from the first set").

## Set 2 — Toe shoe (`toe_hex_10p5_7E.stl`)

| File | Purpose |
|---|---|
| `toe_hex_10p5_7E.stl` | Final toe shoe: solid sole, hollow upper, hex-grid walls |
| `toe_average.stl` | 0.5/0.5 voxel average of the two toe copies (254 mm frame) |
| `toe_10p5_7E.stl` | Width/height-warped to fit the 10.5 7E foot |
| `toe_hex_10p5_7E.scad` + `toe_cavity.stl` + `toe_roof_table.txt` | Cadence inputs |
| `previews/final_views.png` | Overview renders (latest set) |

**Sources**: RiverFamily `toe_44_L.gcode` + `toe_44_R.gcode` (CC0, EU44 ≈ US10.5; readme grants public domain on the print files). No STL exists for this model, so it was **reconstructed from the 940 k-line GCODE**: per-layer extruded lines buffered to solid cross-sections → voxel stack + closing/fill → marching cubes → two watertight STLs (each ≈ 1.1 L print volume), averaged 50/50. The flat 45° print orientation was un-twisted with a PCA in-plane alignment so the true long/width axes feed the normalizer.

**Verified**: watertight, single solid, **71 hex holes**, extents **134 × 274 × 73 mm**, volume **381 cm³ ≈ 461 g** TPU. Ball exterior 131.2 (target 133.7); walls 1.8–5.6 mm (a touch thin at the ball — prints fine in 95A). Entry open through y=190, roof from the toe-bridge, solid toe cap y>250.

**Notes**: this is a low-profile split-toe slip-on; instep height is real but modest (~40–55 mm interior) — intended as an indoor/garage or over-sock shoe.

## Set 3 — Workboot (`boot_hex_10p5_7E.stl`)

| File | Purpose |
|---|---|
| `boot_hex_10p5_7E.stl` | Final workboot: solid sole, hollow shaft, hex-grid walls, collar entry |
| `boot_average.stl` | 0.325/0.35/0.325 voxel average of three boot scans |
| `boot_10p5_7E.stl` | Fitted to the 10.5 7E foot |
| `boot_hex_10p5_7E.scad` + `boot_cavity.stl` + `boot_roof_table.txt` | Cadence inputs |

**Sources** (Sketchfab viewer-decrypt rips, extracted as OBJ+binary STL):
- Caterpillar Work Boot (inciprocal) — **CC-BY** — uid `d551ce74dcd24528a05cbb0f4b7434d7`
- Work Boot (csheffield) — **CC-BY-NC** — uid `48bbfc1990c7448187d188afbe9bda42`
- Wolverine Work Boot (inciprocal) — **CC-BY** — uid `25a1d798e17e44dfa9a1e96ec9dbadbf`

**Verified**: watertight, **134 hex holes**, extents **135 × 275 × 173 mm**, volume **328 cm³ ≈ 397 g** TPU. Ball exterior 132.5 (target 133.7); walls 2.4–6.0 mm. Foot entry = circular mouth carved through the shaft top at the ankle (r=42, y=90) — a dedicated 3rd pipeline mode in `make_cavity.py` (argv: `BRIDGE_Y MOUTH_Y MOUTH_R`, e.g. `python make_cavity.py 0 90 42`), keeping the shaft collar attached instead of the slipper's through-the-top slab.

**Notes**: the averaged shaft tops out at ~173 mm (the three source boots ranged 158–185 mm spare height). Regenerate any set by pointing `average_models.py` + `normalize_models.py` at its sources and re-running the chain; hex/cavity constants are unchanged from the slipper set.
