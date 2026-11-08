"""Rotating turntable GIF of the final shoe (orbit around the vertical axis,
fixed camera elevation/zoom, shaded faces)."""
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image

OUT = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe"
N_FRAMES = 48
ELEV = 22.0                       # degrees above horizon

m = trimesh.load(f"{OUT}\\shoe_hex_10p5_7E.stl", force="mesh")

step = max(1, len(m.faces) // 15000)
idx = np.arange(0, len(m.faces), step)
faces = m.faces[idx]
V = m.vertices - m.vertices.mean(0)
N0 = m.face_normals[idx]

# frame extent (rotation-invariant: use max radius)
rad = np.linalg.norm(V[:, :2], axis=1).max()
zmin, zmax = V[:, 2].min(), V[:, 2].max()
light = np.array([0.4, 0.5, 0.75])
light = light / np.linalg.norm(light)

frames = []
fig, ax = plt.subplots(figsize=(7.2, 6.0), facecolor="white")
for f in range(N_FRAMES):
    az = np.radians(360.0 * f / N_FRAMES)
    ca, sa = np.cos(az), np.sin(az)
    Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1.0]])
    Vr = V @ Rz.T
    Nr = N0 @ Rz.T

    # camera: elevation ELEV, azimuth 0 -> project (simple orthographic)
    el = np.radians(ELEV)
    # view basis: right = x, up = z*cos(el) - y*sin(el)? use standard:
    # camera direction pointing at origin from az=0 elev=el
    fwd = np.array([np.cos(el), 0.0, np.sin(el)])      # toward viewer
    right = np.array([0.0, 1.0, 0.0])                  # world y -> screen x
    up = -fwd * 0 + np.array([-np.sin(el) * 0, 0, np.cos(el)])
    up = np.array([0.0, 0.0, 1.0]) - fwd * fwd[2]      # orthogonalize z-up
    up = up / np.linalg.norm(up)

    P = np.stack([Vr @ right, Vr @ up], axis=-1)       # (n, 2) screen coords
    tris = P[faces]                                    # (k, 3, 2)
    depth = (Vr @ fwd)[faces].mean(axis=1)             # painter order

    shade = 0.35 + 0.65 * np.clip(Nr @ np.array([0.3, -0.75, 0.6]), 0, 1)
    order = np.argsort(depth)                          # far first
    tris = tris[order]
    colors = plt.cm.bone(shade[order])

    ax.clear()
    pc = PolyCollection(tris, facecolors=colors, edgecolors="none")
    ax.add_collection(pc)
    ax.set_xlim(-rad * 1.1, rad * 1.1)
    ax.set_ylim(zmin - rad * 0.15, zmax + rad * 0.15)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    frames.append(Image.fromarray(img).convert("P", palette=Image.ADAPTIVE,
                                               colors=128))
    print(f"\rframe {f + 1}/{N_FRAMES}", end="", flush=True)

plt.close(fig)
gif_path = f"{OUT}\\previews\\shoe_turntable.gif"
frames[0].save(gif_path, save_all=True, append_images=frames[1:],
               duration=90, loop=0, optimize=True)
import os
print(f"\nsaved {gif_path} ({os.path.getsize(gif_path)//1024} KB, "
      f"{N_FRAMES} frames)")
