"""Numeric verification of shoe_hex_10p5_7E.stl (no image viewing available)."""
import numpy as np
import trimesh

m = trimesh.load(r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe\shoe_hex_10p5_7E.stl",
                 force="mesh")
print(f"watertight={m.is_watertight} vol={m.volume/1000:.0f}cm3 "
      f"extents={np.round(m.extents,1)}")
print(f"bounds {np.round(m.bounds[0],1)} .. {np.round(m.bounds[1],1)}")

# connected components (floating pieces would fail printing)
comps = m.split(only_watertight=False)
print(f"components: {len(comps)} sizes={[round(c.volume/1000,1) for c in comps]}")
if len(comps) > 1:
    for c in sorted(comps, key=lambda c: c.volume)[:3]:
        print(f"  piece vol={c.volume/1000:.2f}cm3 bounds={np.round(c.bounds,1).tolist()}")

# sole solidity: cross-section area at z=6 (mid sole) vs z=0.5 footprint
for z in (0.5, 6.0, 11.0, 13.5, 16.0):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        print(f"z={z:5.1f}  EMPTY")
        continue
    p, _ = sec.to_planar()
    print(f"z={z:5.1f}  area={p.area:8.0f}mm2  bbox={np.round(p.bounds[1]-p.bounds[0],1)}")

# wall thickness check: interior = cavity_w, exterior = section width
from scale_to_size import cavity_w, foot_w
print(f"\n{'y':>6} {'foot':>7} {'cavity':>7} {'ext':>7} {'wall':>6}")
for y in [5, 20, 50, 82, 143, 175, 200, 240, 265]:
    sec = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sec is None:
        print(f"{y:6} no section")
        continue
    v = sec.vertices
    ext = v[:, 0].max() - v[:, 0].min()
    cav = cavity_w(y)
    # wall only meaningful where closed; at open-collar y<110 compare to cavity
    print(f"{y:6d} {foot_w(y):7.1f} {cav:7.1f} {ext:7.1f} {(ext-cav)/2:6.1f}")

# cavity present? ray straight down at foot center should hit interior ceiling
# or pass through (open) - probe points along centerline
print("\ncenterline top-of-material (ray down from z=120):")
for y in [20, 60, 100, 130, 160, 185, 205, 235, 260]:
    loc, idx, _ = m.ray.intersects_location(
        ray_origins=[[0, y, 120]], ray_directions=[[0, 0, -1]])
    hits = sorted(loc[:, 2], reverse=True) if len(loc) else []
    print(f"  y={y:3d} hits_z={[round(h,1) for h in hits[:4]]}")

# hex windows: ray along X through a hole center vs through a strut
import re
scad = open("shoe_hex_10p5_7E.scad").read()
block = scad.split("HOLES = [")[1].split("];")[0]
hole_list = [[float(a) for a in mm.split(",")]
             for mm in re.findall(r"\[([^\]]+)\]", block)]
print(f"\nhex holes in scad: {len(hole_list)}")
# probe: ray along +X at hole center (expect ~0 hits = clean window) and at
# the strut between two holes (expect 4 hits = two walls)
for hy, hz in hole_list[::max(1, len(hole_list)//5)][:5]:
    loc, _, _ = m.ray.intersects_location(
        ray_origins=[[-90, hy, hz]], ray_directions=[[1, 0, 0]])
    xs = np.round(sorted(loc[:, 0]), 1).tolist() if len(loc) else []
    print(f"  hole  ({hy:6.1f},{hz:5.1f}) hits={len(loc)} xs={xs}")
    sy = hy + 5.75                      # midpoint to next hole (pitch 11.5)
    loc2, _, _ = m.ray.intersects_location(
        ray_origins=[[-90, sy, hz]], ray_directions=[[1, 0, 0]])
    xs2 = np.round(sorted(loc2[:, 0]), 1).tolist() if len(loc2) else []
    print(f"  strut ({sy:6.1f},{hz:5.1f}) hits={len(loc2)} xs={xs2}")

# estimate print mass: TPU 1.21 g/cm3
print(f"\nest mass @1.21 g/cm3: {m.volume/1000*1.21:.0f} g")
