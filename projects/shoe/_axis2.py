import numpy as np
from PIL import Image

def mask(n, size=128):
    im = Image.open(f"previews/{n}.png").convert("L").resize((size, size))
    a = np.array(im) < 245
    return a

base = mask("p_base")
ry = mask("p_ry90")
rz = mask("p_rz90")
base_rot = np.rot90(base)

def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)

print(f"ry90 vs base      : {iou(ry, base):.3f}")
print(f"ry90 vs rot90(base): {iou(ry, base_rot):.3f}")
print(f"rz90 vs base      : {iou(rz, base):.3f}")
print(f"rz90 vs rot90(base): {iou(rz, base_rot):.3f}")
