"""Warp + scale baseline_average to US 10.5 7E.

The averaged baseline is D-proportioned. A 7E foot needs more width than a
uniform ball-driven scale gives (especially heel/arch), so the width scale
s(y) is solved per station:

    exterior(y) = foot_w(y) + 2*(clearance + wall)
    s(y) = exterior(y) / baseline_w(y)

which guarantees the foot fits inside the walls everywhere.
Interior  = foot + 3 mm/side clearance
Wall      = 3.5 mm
Foot profile = the same stations used in foot_template_10p5_7E (ball width
120.65 and length 275 chart-verified; other stations estimated).
"""
import os
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter1d

OUT = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe"
REF = 254.0
TARGET = 275.0
YSCALE = TARGET / REF
CLEARANCE = 3.0
WALL = 3.5
UPPER_K = 1.4      # extra-depth: z above sole stretched 40% from y=140 on
SOLE_Z = 12.0      # below this: solid sole (never stretched)

# Foot width profile in FINAL coords. Ball (120.65 @ y=200) and length (275)
# are chart-verified; heel/arch/intermediate stations are estimated from the
# size-8 reference (same stations as foot_template_10p5_7E.svg). Heel and toe
# ends are rounded (circle caps), like the printed template.
R_HEEL = 38.6      # heel circle radius (heel width 77.5)
C_HEEL = 38.6      # heel circle center y
Y_ARCH, W_ARCH = 82.1, 70.1
Y_MID, W_MID = 142.9, 93.4
Y_BALL, W_BALL = 200.0, 120.65
R_TOE = 60.3       # toe circle radius (toe width 120.65)
C_TOE = 214.7      # toe circle center y


def foot_w(y):
    y = np.asarray(y, dtype=float)
    w = np.empty_like(y)
    heel = y < C_HEEL
    toe = y > C_TOE
    mid = ~(heel | toe)
    w[heel] = 2 * np.sqrt(np.maximum(R_HEEL**2 - (y[heel] - C_HEEL) ** 2, 0))
    wm = y[mid]
    w[mid] = np.interp(wm, [C_HEEL, Y_ARCH, Y_MID, Y_BALL],
                       [2 * R_HEEL, W_ARCH, W_MID, W_BALL])
    w[toe] = 2 * np.sqrt(np.maximum(R_TOE**2 - (y[toe] - C_TOE) ** 2, 0))
    return w


def cavity_w(y):
    """Foot outline offset by CLEARANCE on each side (what the cavity needs).

    At the rounded heel/toe this is a concentric circle (radial offset), which
    is wider horizontally than foot_w + 2*clearance - using foot_w here is
    what punched through the heel wall in the first attempt.
    """
    y = np.asarray(y, dtype=float)
    w = np.empty_like(y)
    heel = y < C_HEEL
    toe = y > C_TOE
    mid = ~(heel | toe)
    rh = R_HEEL + CLEARANCE
    w[heel] = 2 * np.sqrt(np.maximum(rh**2 - (y[heel] - C_HEEL) ** 2, 0))
    wm = y[mid]
    w[mid] = np.interp(wm, [C_HEEL, Y_ARCH, Y_MID, Y_BALL],
                       [2 * rh, W_ARCH, W_MID, W_BALL]) + 2 * CLEARANCE
    rt = R_TOE + CLEARANCE
    w[toe] = 2 * np.sqrt(np.maximum(rt**2 - (y[toe] - C_TOE) ** 2, 0))
    return w


def section_width(mesh, y):
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sec is None:
        return -1.0
    v = sec.vertices
    return float(v[:, 0].max() - v[:, 0].min())


def main():
    base = trimesh.load(os.path.join(OUT, "baseline_average.stl"), force="mesh")

    # 1. measure baseline width along ref length
    ys = np.arange(2.0, REF, 4.0)
    bw = np.array([section_width(base, y) for y in ys])
    bw = np.clip(bw, 1.0, None)

    # 2. required exterior = cavity width + 2*wall (same station)
    req = cavity_w(ys * YSCALE) + 2 * WALL

    # 3. width scale, smoothed (straps/heel collars make bw jumpy)
    s = req / bw
    s = np.clip(s, 1.0, 2.2)
    s = gaussian_filter1d(s, sigma=3, mode="nearest")

    # 4. warp vertices in ref coords, then scale y/z to target length
    v = base.vertices.copy()
    v[:, 0] *= np.interp(v[:, 1], ys, s)
    v[:, 1] *= YSCALE
    v[:, 2] *= YSCALE

    # 4b. extra-depth upper: stretch everything above the sole (z > SOLE_Z)
    # in y > 90 so a real instep/toe box fits (7E / extra-depth style).
    yy = v[:, 1]
    k = np.interp(yy, [0.0, 90.0, 140.0], [1.0, 1.0, UPPER_K])
    up = v[:, 2] > SOLE_Z
    v[up, 2] = SOLE_Z + (v[up, 2] - SOLE_Z) * k[up]

    shoe = trimesh.Trimesh(vertices=v, faces=base.faces, process=True)
    trimesh.repair.fix_normals(shoe)
    if shoe.volume < 0:
        shoe.invert()

    out = os.path.join(OUT, "baseline_10p5_7E.stl")
    shoe.export(out)

    # 5. report
    print(f"{'y':>6} {'foot':>7} {'req ext':>8} {'got ext':>8} {'interior':>8} {'wall':>6}")
    for yf in [5, 20, 50, 82, 143, 200, 240, 270]:
        fw = foot_w(yf)
        ext = section_width(shoe, yf)
        interior = ext - 2 * WALL
        wall_ok = (interior - fw) / 2
        print(f"{yf:6.0f} {fw:7.1f} {fw+2*(CLEARANCE+WALL):8.1f} {ext:8.1f} "
              f"{interior:8.1f} {wall_ok:6.1f}")
    b = shoe.bounds
    print(f"\nextents {np.round(shoe.extents,1)}  (len want {TARGET}, "
          f"ball ext want {120.65+2*(CLEARANCE+WALL)})")
    print(f"bounds {np.round(b[0],1)} .. {np.round(b[1],1)}  watertight={shoe.is_watertight} "
          f"vol={shoe.volume/1000:.0f}cm3")

    # 6. top profile (center-ish max z per y band) for the cavity roof table
    step = 5.0
    ytab = np.arange(0.0, TARGET + step, step)
    ztop = []
    for yy in ytab:
        sel = np.abs(shoe.vertices[:, 1] - yy) <= step / 2
        ztop.append(shoe.vertices[sel, 2].max() if sel.any() else 0.0)
    ztop = gaussian_filter1d(np.array(ztop), sigma=1.0, mode="nearest")
    table = np.column_stack([ytab, ztop])
    np.savetxt(os.path.join(OUT, "roof_table.txt"), table, fmt="%.2f",
               header="y_mm  top_z_mm (final coords, after z-scale)")
    print("roof table saved; sample:", [f"{a:.0f}:{b:.0f}" for a, b in table[::6]])


if __name__ == "__main__":
    main()
