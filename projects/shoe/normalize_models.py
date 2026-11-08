"""Normalize shoe source meshes to a common size/orientation.

Common frame: length along +Y = REF_LEN, heel at y=0, centered on X,
bottom at z=0, +Z up.
"""
import os
import sys
import numpy as np
import trimesh

SRC = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe\sources"
REF_LEN = 254.0  # mm, common reference length

# Manual heel-flip override after inspection: True = heel is at max y -> flip
# sloffies: auto-heuristic flipped it wrong; strap hump must sit at 50-75%
# from heel, which it does WITHOUT flipping (heel = narrow 72mm end at y=0)
FLIP = {"sloffies": False}


def load(path):
    m = trimesh.load(path, force="mesh")
    m.merge_vertices()
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(m)
    return m


def profile(m, name):
    """Width/height profile along length for heel-vs-toe diagnosis."""
    v = m.vertices
    y0, y1 = v[:, 1].min(), v[:, 1].max()
    L = y1 - y0
    print(f"  {name}: length {L:.1f}")
    for lo, hi in [(0, .25), (.25, .5), (.5, .75), (.75, 1.0)]:
        sel = (v[:, 1] >= y0 + lo * L) & (v[:, 1] <= y0 + hi * L)
        if sel.sum() < 5:
            continue
        w = v[sel, 0].max() - v[sel, 0].min()
        h = v[sel, 2].max()
        print(f"    {lo*100:3.0f}-{hi*100:3.0f}%  width {w:6.1f}  height {h:6.1f}")


def normalize(name, flip=None):
    m = load(os.path.join(SRC, name + ".stl"))

    # length axis -> Y. Use PCA of the in-plane (x,y) points so diagonally
    # printed soles align along their true long axis, not a bbox diagonal.
    xy = m.vertices[:, :2]
    xy -= xy.mean(axis=0)
    cov = np.cov(xy.T)
    vals, vecs = np.linalg.eigh(cov)
    e = vecs[:, int(np.argmax(vals))]
    ang = np.arctan2(e[1], e[0])
    m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
    if m.extents[0] > m.extents[1]:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))

    profile(m, name + " pre ")

    # heel = the end with the taller structure (ankle collar / heel cup)
    if flip is None:
        v = m.vertices
        y0, y1 = v[:, 1].min(), v[:, 1].max()
        L = y1 - y0
        first = v[v[:, 1] <= y0 + 0.25 * L, 2].max()
        last = v[v[:, 1] >= y1 - 0.25 * L, 2].max()
        flip = last > first  # tall end is at max y -> mirror so heel at y=0
        print(f"  {name}: zmax first25={first:.1f} last25={last:.1f} -> flip={flip}")

    if flip:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))

    # scale to reference length
    s = REF_LEN / m.extents[1]
    m.apply_scale(s)

    # place: heel y=0, x centered, sole z=0
    b = m.bounds
    m.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -b[0][2]])

    out = os.path.join(SRC, name + "_norm.stl")
    m.export(out)
    print(f"  -> {name}_norm.stl  extents {np.round(m.extents,1)}  watertight={m.is_watertight}")
    return m


if __name__ == "__main__":
    names = list(sys.argv[1:]) or ["infrawiki_sandal", "sloffies", "clown_shoe"]
    for n in names:
        normalize(n, FLIP.get(n))
        print()
