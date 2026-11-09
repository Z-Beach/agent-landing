"""Average the normalized shoe meshes into one baseline model.

Voxelize each at REF size, mean the occupancy fields, threshold via
marching cubes on a smoothed field.
"""
import os
import sys
import numpy as np
import trimesh
from scipy.ndimage import binary_fill_holes, gaussian_filter
from skimage.measure import marching_cubes

SRC = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe\sources"
OUT = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe"
PITCH = 1.0
LEVEL = 0.45       # threshold: > single-model 0.25, <= weighted-clown 0.50
                   # (0.5 itself loses to float32 noise on exact plateaus)
SIGMA = 1.2        # smoothing before marching cubes (voxels)

DEFAULT_MODELS = ["infrawiki_sandal_norm", "sloffies_norm", "clown_shoe_norm"]
DEFAULT_WEIGHTS = [0.25, 0.25, 0.50]


def world_to_idx(pts, origin, pitch):
    return np.round((pts - origin) / pitch).astype(int)


def main():
    pairs = list(sys.argv[1:])
    if not pairs:
        pairs = [f"{n}:{w}" for n, w in zip(DEFAULT_MODELS, DEFAULT_WEIGHTS)]
    MODELS = [p.rsplit(":", 1)[0] for p in pairs]
    WEIGHTS = [float(p.rsplit(":", 1)[1]) for p in pairs]
    bounds = []
    meshes = []
    for n in MODELS:
        m = trimesh.load(os.path.join(SRC, n + ".stl"), force="mesh")
        m.merge_vertices()
        m.update_faces(m.unique_faces())
        m.remove_unreferenced_vertices()
        trimesh.repair.fix_normals(m)
        meshes.append(m)
        bounds.append(m.bounds)
    lo = np.min([b[0] for b in bounds], axis=0) - 5
    hi = np.max([b[1] for b in bounds], axis=0) + 5
    dims = np.ceil((hi - lo) / PITCH).astype(int) + 1
    print(f"grid {dims} (x,y,z) at {PITCH}mm, world lo={np.round(lo,1)}")

    occ = np.zeros(tuple(dims), dtype=np.float32)
    for n, m, w in zip(MODELS, meshes, WEIGHTS):
        vox = m.voxelized(pitch=PITCH)
        pts = vox.points
        idx = world_to_idx(pts, lo, PITCH)
        g = np.zeros(tuple(dims), dtype=bool)
        ok = np.all((idx >= 0) & (idx < dims), axis=1)
        g[idx[ok, 0], idx[ok, 1], idx[ok, 2]] = True
        g = binary_fill_holes(g)
        print(f"  {n}: solid voxels {g.sum()} ({g.sum()*PITCH**3/1000:.0f} cm3) weight {w}")
        occ += w * g

    mean = occ  # weights sum to 1
    print(f"weighted field: {np.mean(mean>=LEVEL)*100:.1f}% occupied at >=0.5, "
          f"union {np.mean(mean>0)*100:.1f}%")

    sm = gaussian_filter(mean, SIGMA)
    verts, faces, _, _ = marching_cubes(sm, level=LEVEL)
    verts = verts * PITCH + lo  # voxel index -> world

    base = trimesh.Trimesh(vertices=verts, faces=faces)
    base.merge_vertices()
    base.update_faces(base.nondegenerate_faces())
    trimesh.repair.fill_holes(base)
    trimesh.repair.fix_normals(base)
    if base.volume < 0:
        base.invert()
    out = os.path.join(OUT, "baseline_average.stl")
    base.export(out)
    print(f"baseline_average.stl: extents {np.round(base.extents,1)} "
          f"watertight={base.is_watertight} vol={base.volume/1000:.0f}cm3")

    # ball-station width of baseline (y = 0.7272 * 254)
    by = 0.7272 * 254
    sec = base.section(plane_origin=[0, by, 0], plane_normal=[0, 1, 0])
    if sec is not None:
        w = sec.vertices[:, 0].max() - sec.vertices[:, 0].min()
        print(f"baseline width at ball station y={by:.0f}: {w:.1f} mm")

    np.save(os.path.join(OUT, "mean_field.npy"), mean)
    np.save(os.path.join(OUT, "grid_origin.npy"), lo)
    print("saved mean_field.npy + grid_origin.npy")


if __name__ == "__main__":
    main()
