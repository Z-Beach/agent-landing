import numpy as np
from PIL import Image
for n in ["p_base", "p_ry90", "p_rz90"]:
    im = np.array(Image.open(f"previews/{n}.png").convert("L"))
    ys, xs = np.where(im < 245)          # non-background pixels
    pts = np.stack([xs, ys], 1).astype(float)
    pts -= pts.mean(0)
    cov = pts.T @ pts / len(pts)
    w, v = np.linalg.eigh(cov)
    ax = v[:, -1]
    ang = np.degrees(np.arctan2(abs(ax[1]), abs(ax[0])))  # 0=horiz, 90=vert
    print(f"{n}: principal axis angle = {ang:5.1f} deg from horizontal")
