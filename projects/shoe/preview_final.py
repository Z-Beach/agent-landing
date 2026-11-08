"""Render preview PNGs of the final shoe (views for human inspection)."""
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import re

OUT = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe"
m = trimesh.load(f"{OUT}\\shoe_hex_10p5_7E.stl", force="mesh")

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# --- side view: sections through x (length vs height) ----------------------
ax = axes[0, 0]
for xv, c in [(0, "k"), (52, "tab:red")]:
    sec = m.section(plane_origin=[xv, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        continue
    for ent in sec.entities:
        p = sec.vertices[ent.points]
        ax.plot(p[:, 1], p[:, 2], color=c, lw=0.9, label=f"x={xv}")
ax.legend(fontsize=8)
ax.set_title("side sections: y vs z at x=0 (black), x=52 (red)")
ax.set_xlabel("y (heel at 0)"); ax.set_ylabel("z")
ax.set_aspect("equal"); ax.grid(alpha=0.3)

# --- top view: outline at several z + hex hole centers ---------------------
ax = axes[0, 1]
for z, c in [(6, "0.4"), (16, "tab:blue"), (40, "tab:red")]:
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        continue
    for ent in s.entities:
        p = s.vertices[ent.points]
        ax.plot(p[:, 1], p[:, 0], color=c, lw=1.0)
scad = open(f"{OUT}\\shoe_hex_10p5_7E.scad").read()
block = scad.split("HOLES = [")[1].split("];")[0]
holes = [[float(a) for a in mm.split(",")] for mm in re.findall(r"\[([^\]]+)\]", block)]
ax.scatter([h[0] for h in holes], [0]*len(holes), marker="x", color="g",
           s=18, label=f"{len(holes)} hex holes (y positions)")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("top view: sections z=6/16/40 (y vs x)")
ax.set_aspect("equal"); ax.grid(alpha=0.3)

# --- front/back profile: x vs z -------------------------------------------
ax = axes[1, 0]
for y, c in [(20, "tab:green"), (143, "tab:blue"), (210, "tab:red")]:
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None:
        continue
    for ent in s.entities:
        p = s.vertices[ent.points]
        ax.plot(p[:, 0], p[:, 2], color=c, lw=1.0, label=f"y={y}")
ax.legend(fontsize=8)
ax.set_title("cross sections: x vs z")
ax.set_aspect("equal"); ax.grid(alpha=0.3)

# --- iso view (downsampled) ------------------------------------------------
ax = axes[1, 1]
step = max(1, len(m.faces) // 12000)
idx = np.arange(0, len(m.faces), step)
tris = m.vertices[m.faces[idx]]
shade = 0.35 + 0.65 * np.clip(m.face_normals[idx] @ np.array([0.4, 0.5, 0.75]), 0, 1)
tris2 = tris[:, :, 1:3]                      # keep (y, z) only
polys = [t for t in tris2]
pc = PolyCollection(polys, facecolors=plt.cm.bone(shade), edgecolors="none")
ax.add_collection(pc)
ax.set_xlim(m.bounds[0][1], m.bounds[1][1])
ax.set_ylim(m.bounds[0][2], m.bounds[1][2])
ax.set_aspect("equal")
ax.set_title("iso (front-left, downsampled)")
ax.set_xlabel("y"); ax.set_ylabel("z")

fig.suptitle("shoe_hex_10p5_7E - US 10.5 7E, TPU")
fig.tight_layout()
fig.savefig(f"{OUT}\\previews\\final_views.png", dpi=110)
print("saved previews\\final_views.png")

# sole-floor plan: cavity footprint at z=16 ring + foot outline
fig2, ax2 = plt.subplots(figsize=(7, 10))
for z, c, lw in [(6, "0.5", 2.5), (14, "tab:blue", 1.0), (16, "tab:cyan", 1.0)]:
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        continue
    for ent in s.entities:
        p = s.vertices[ent.points]
        ax2.plot(p[:, 1], p[:, 0], color=c, lw=lw)
ax2.set_title("sole footprint (black z=6) vs wall ring (z=14/16)")
ax2.set_aspect("equal"); ax2.grid(alpha=0.3)
ax2.set_xlabel("y (heel at 0)"); ax2.set_ylabel("x")
fig2.tight_layout()
fig2.savefig(f"{OUT}\\previews\\sole_plan.png", dpi=110)
print("saved previews\\sole_plan.png")
