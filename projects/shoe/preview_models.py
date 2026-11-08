"""Preview silhouettes of normalized meshes + baseline, and per-model
width at the ball station, to verify orientation before averaging."""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe\sources"
OUT = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe"
PITCH = 2.0
BALL_Y = 0.7272 * 254

MODELS = ["infrawiki_sandal_norm", "sloffies_norm", "clown_shoe_norm"]


def silhouettes(m, lo, dims):
    vox = m.voxelized(pitch=PITCH)
    idx = np.floor((vox.points - lo) / PITCH + 0.5).astype(int)
    g = np.zeros(tuple(dims), bool)
    ok = np.all((idx >= 0) & (idx < dims), axis=1)
    g[idx[ok, 0], idx[ok, 1], idx[ok, 2]] = True
    from scipy.ndimage import binary_fill_holes
    g = binary_fill_holes(g)
    side = g.any(axis=0).T    # y-z (transposed for display: y up)
    top = g.any(axis=2).T     # x-y
    front = g.any(axis=1).T   # x-z
    return side, top, front, g


def ball_width(g, lo):
    iy = int(round((BALL_Y - lo[1]) / PITCH))
    if 0 <= iy < g.shape[1]:
        col = g[:, iy, :]
        xs = np.where(col.any(axis=1))[0]
        if len(xs):
            return (xs.max() - xs.min() + 1) * PITCH
    return -1


bounds, meshes = [], []
for n in MODELS:
    m = trimesh.load(os.path.join(SRC, n + ".stl"), force="mesh")
    meshes.append(m)
    bounds.append(m.bounds)
lo = np.min([b[0] for b in bounds], axis=0) - 5
hi = np.max([b[1] for b in bounds], axis=0) + 5
dims = np.ceil((hi - lo) / PITCH).astype(int) + 1
print("grid", dims, "lo", np.round(lo, 1))

rows = []
for n, m in zip(MODELS, meshes):
    side, top, front, g = silhouettes(m, lo, dims)
    bw = ball_width(g, lo)
    print(f"{n}: ball-station width {bw:.1f} mm")
    rows.append((n, side, top))

# baseline
bpath = os.path.join(OUT, "baseline_average.stl")
if os.path.exists(bpath):
    bm = trimesh.load(bpath, force="mesh")
    side, top, front, g = silhouettes(bm, lo, dims)
    print(f"baseline: ball-station width {ball_width(g, lo):.1f} mm")
    rows.append(("baseline_average", side, top))

fig, axes = plt.subplots(len(rows), 2, figsize=(11, 3.2 * len(rows)))
for r, (n, side, top) in enumerate(rows):
    axes[r, 0].imshow(side, cmap="Blues", origin="lower")
    axes[r, 0].set_title(f"{n} - side (heel left)", fontsize=9)
    axes[r, 1].imshow(top, cmap="Greens", origin="lower")
    axes[r, 1].set_title(f"{n} - top", fontsize=9)
    for c in range(2):
        axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
plt.tight_layout()
png = os.path.join(OUT, "previews", "orientation_check.png")
plt.savefig(png, dpi=90)
print("saved", png)
