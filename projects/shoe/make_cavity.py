"""Build the cavity solid for the hex shoe from the baseline blob.

Why not simple boxes: the shoe top is a dome in x, so any flat ceiling at
top(y)-4 is ABOVE the dome at |x|>~22 and slices the roof cap free of the
walls (observed: a 5.6cm3 floating strip). Instead:

  cavity = footprint(cavity_w) AND z >= SOLE_Z AND z <= ceiling(x, y)

  ceiling(x, y) = max z where the blob is >= 4mm thick (distance to the
                  outside >= 4), i.e. the surface eroded 4mm inward;
                  ceiling = INF for y < BRIDGE_Y (open entry).

Exported as cavity.stl for OpenSCAD: difference(baseline, cavity, hex).
"""
import sys
import numpy as np
import trimesh
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import marching_cubes
from scale_to_size import cavity_w, SOLE_Z, OUT, REF, TARGET

PITCH = 1.0
ERODE = 4.0        # shell thickness kept above/around the cavity
BRIDGE_Y = float(sys.argv[1]) if len(sys.argv) > 1 else 190.0   # open entry
MOUTH_Y = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0      # entry cylinder center y
MOUTH_R = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0      # entry cylinder radius


def main():
    blob = trimesh.load(f"{OUT}\\baseline_10p5_7E.stl", force="mesh")

    # voxelise blob (filled); axes from the grid transform + matrix shape
    # (point = transform_translation + index * pitch). Pad the grid so the
    # open entry region (ceiling = through-the-top) never touches a grid
    # face - otherwise marching cubes leaves open boundaries.
    PAD = 3
    vg = blob.voxelized(pitch=PITCH).fill()
    solid = np.pad(vg.matrix, PAD, constant_values=False)
    org = vg.transform[:3, 3] - PAD * PITCH
    xs = org[0] + np.arange(solid.shape[0]) * PITCH
    ys = org[1] + np.arange(solid.shape[1]) * PITCH
    zs = org[2] + np.arange(solid.shape[2]) * PITCH
    lo = org.copy()
    print(f"grid {solid.shape} solid={solid.sum()} vox "
          f"lo={np.round(lo,1)} hi=({xs[-1]:.0f},{ys[-1]:.0f},{zs[-1]:.0f})")

    # distance to the nearest empty voxel (>= ERODE => >=4mm inside shell)
    dist = distance_transform_edt(solid) * PITCH
    inner = dist >= ERODE

    # per-(x,y) inner ceiling; -1 where the column never reaches 4mm inside
    ceiling = np.full(solid.shape[:2], -1.0)
    for j in range(solid.shape[1]):
            col = inner[:, j, :]           # (x, z) at this y
            any_ = col.any(axis=1)         # (x,)
            if any_.any():
                # topmost z per x with dist >= ERODE
                idx = col.shape[1] - 1 - col[:, ::-1].argmax(axis=1)
                ceiling[:, j] = np.where(any_, zs[idx], -1.0)

    # footprint mask (analytic cavity outline, exact per voxel center),
    # clamped at y=270 so the toe tip keeps a >=4mm front wall
    Y, X = np.meshgrid(ys, xs, indexing="ij")       # (y, x)
    Y, X = Y.T, X.T                                 # (x, y)
    half = cavity_w(Y) / 2.0
    inside_fp = (np.abs(X) <= half) & (Y <= 270.0)

    OPEN_Z = zs[-1] - 1.0

    if MOUTH_R > 0:
        # tall-shaft types (boot): roof follows the eroded ceiling everywhere;
        # the foot entry is a circular mouth carved through the shaft top at
        # (x=0, y=MOUTH_Y, r=MOUTH_R). The shaft collar stays attached.
        open_col = ceiling.copy()
        open_col[ceiling < 0] = -1
        inside_mouth = np.sqrt(X**2 + (Y - MOUTH_Y) ** 2) <= MOUTH_R
        open_col[inside_mouth] = OPEN_Z
    else:
        # open entry: through-the-top for y < BRIDGE_Y, but kept
        # one cell below the padded grid top so the contour closes inside it
        open_col = ceiling.copy()
        open_col[Y < BRIDGE_Y] = OPEN_Z
        open_col[ceiling < 0] = -1                      # columns outside blob

    cavity = np.zeros(solid.shape, dtype=bool)
    for k, z in enumerate(zs):
        if z < SOLE_Z:
            continue
        cavity[:, :, k] = inside_fp & (z <= open_col)

    # light smoothing so marching cubes does not produce stairs
    field = gaussian_filter(cavity.astype(np.float32), sigma=0.8)
    if field.max() <= 0.5:
        raise SystemExit("empty cavity field")
    verts, faces, _, _ = marching_cubes(field, level=0.5)
    verts = verts * PITCH + lo                     # (i,j,k) -> (x,y,z)
    cav = trimesh.Trimesh(vertices=verts, faces=faces)
    cav.merge_vertices()
    cav.update_faces(cav.nondegenerate_faces())
    trimesh.repair.fill_holes(cav)
    trimesh.repair.fix_normals(cav)
    if cav.volume < 0:
        cav.invert()
    cav.export(f"{OUT}\\cavity.stl")
    print(f"cavity.stl vol={cav.volume/1000:.0f}cm3 "
          f"bounds={np.round(cav.bounds,1).tolist()} watertight={cav.is_watertight}")

    # ceiling report along the centerline and at the wall edge
    print("ceiling z (eroded) at sample (y, x):")
    for y in [195, 210, 230, 250, 265]:
        row = []
        for x in [0, 30, 55]:
            i = int(round((x - lo[0]) / PITCH))
            j = int(round((y - lo[1]) / PITCH))
            row.append(f"x{x}:{ceiling[i, j]:.0f}")
        print(f"  y={y}: " + "  ".join(row))


if __name__ == "__main__":
    main()
