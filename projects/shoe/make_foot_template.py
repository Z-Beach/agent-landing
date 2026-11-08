import math

FOOT_LEN_MM = 275.0        # US men's 10.5 foot length
BALL_W_MM = 4.75 * 25.4    # 10.5 / 7E ball width, healthyfeetstore chart = 120.65 mm

# Stations: (center_y, width_mm) for US 10.5 7E foot outline.
# y positions are anatomical fractions of foot length from a size-8 reference
# (infrawiki shoe_ver_2.scad cross-sections); widths scaled to 7E except the
# ball station, which is pinned to the chart-verified 120.65 mm.
# toe_width intentionally = ball_width: no toe taper (crushed-toe fix).
HEEL_W = 77.5
ARCH_W = 70.1
MID_W = 93.4
TOE_W = BALL_W_MM

STATIONS = [
    (HEEL_W / 2.0, HEEL_W),          # heel circle: center at r -> back edge = 0
    (0.2987 * FOOT_LEN_MM, ARCH_W),   # arch, narrowest
    (0.5195 * FOOT_LEN_MM, MID_W),   # widening section
    (0.7272 * FOOT_LEN_MM, BALL_W_MM),  # ball (met heads), ~72.7% of length
    (FOOT_LEN_MM - TOE_W / 2.0, TOE_W),  # toe: front edge = FOOT_LEN
]
END_Y = FOOT_LEN_MM


def catmull_rom(points, samples=14):
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


HALF = [(y, w / 2.0) for y, w in STATIONS]
outer = catmull_rom([(y, -hx) for y, hx in HALF])
inner = catmull_rom([(y, hx) for y, hx in HALF])[::-1]


def cap(y0, r, forward):
    # semicircular cap centered at (y0, 0), radius r, bulging away from sole
    pts = []
    for k in range(1, 16):
        a = math.pi * k / 16.0
        dy = r * math.sin(a) if forward else -r * math.sin(a)
        pts.append((y0 + dy, r * math.cos(a)))
    return pts


heel_r = HALF[0][1]
toe_r = HALF[-1][1]
raw = outer + cap(END_Y - toe_r, toe_r, True) + inner + cap(heel_r, heel_r, False)
# clamp Catmull-Rom overshoot so widest point == ball width exactly
M_HALF = BALL_W_MM / 2.0
path_pts = [(y, max(-M_HALF, min(M_HALF, x))) for y, x in raw]

ys = [p[0] for p in path_pts]
xs = [p[1] for p in path_pts]
print(f"outline extent: y {min(ys):.1f}..{max(ys):.1f} (want 0..{FOOT_LEN_MM})")
print(f"outline width : {min(xs):.1f}..{max(xs):.1f} (want +/-{BALL_W_MM/2:.2f})")

MARGIN = 20
PAGE_W, PAGE_H = 210.0, 297.0
OFF_X = PAGE_W / 2
OFF_Y = 14
ball_y = STATIONS[3][0]


def T(x, y):
    return (OFF_X + x, OFF_Y + y)


grid = []
for gx in range(-60, 61, 10):
    grid.append(f'<line x1="{OFF_X+gx}" y1="{OFF_Y}" x2="{OFF_X+gx}" y2="{OFF_Y+END_Y}" class="g"/>')
for gy in range(0, int(END_Y) + 1, 10):
    grid.append(f'<line x1="{OFF_X-62}" y1="{OFF_Y+gy}" x2="{OFF_X+62}" y2="{OFF_Y+gy}" class="g"/>')


def pts_d(pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm"
     viewBox="0 0 {PAGE_W} {PAGE_H}">
  <style>
    .g {{ stroke:#ececec; stroke-width:0.2; }}
    .outline {{ fill:#eef4ff; stroke:#0044cc; stroke-width:0.6; }}
    .dim {{ stroke:#cc0000; stroke-width:0.4; fill:none; }}
    .lbl {{ font-family:sans-serif; font-size:3.2px; fill:#cc0000; }}
    .txt {{ font-family:sans-serif; font-size:4px; fill:#222; }}
    .sm {{ font-family:sans-serif; font-size:2.8px; fill:#555; }}
  </style>
  <rect x="0" y="0" width="{PAGE_W}" height="{PAGE_H}" fill="white"/>
  {''.join(grid)}

  <text class="txt" x="{MARGIN}" y="10">US Men's 10.5 7E - foot outline (print at 100%, do NOT scale)</text>

  <polygon class="outline" points="{pts_d([T(x,y) for x,y in path_pts])}"/>

  <!-- ball width dimension (full width held through toes: no taper) -->
  <line class="dim" x1="{OFF_X-BALL_W_MM/2}" y1="{OFF_Y+ball_y}" x2="{OFF_X+BALL_W_MM/2}" y2="{OFF_Y+ball_y}"/>
  <line class="dim" x1="{OFF_X-BALL_W_MM/2}" y1="{OFF_Y+ball_y-4}" x2="{OFF_X-BALL_W_MM/2}" y2="{OFF_Y+ball_y+4}"/>
  <line class="dim" x1="{OFF_X+BALL_W_MM/2}" y1="{OFF_Y+ball_y-4}" x2="{OFF_X+BALL_W_MM/2}" y2="{OFF_Y+ball_y+4}"/>
  <text class="lbl" x="{OFF_X-16}" y="{OFF_Y+ball_y-3}">ball width 120.65 mm (4.75 in) = 7E</text>

  <!-- length dimension -->
  <line class="dim" x1="{OFF_X+56}" y1="{OFF_Y}" x2="{OFF_X+56}" y2="{OFF_Y+END_Y}"/>
  <line class="dim" x1="{OFF_X+52}" y1="{OFF_Y}" x2="{OFF_X+60}" y2="{OFF_Y}"/>
  <line class="dim" x1="{OFF_X+52}" y1="{OFF_Y+END_Y}" x2="{OFF_X+60}" y2="{OFF_Y+END_Y}"/>
  <text class="lbl" x="{OFF_X+59}" y="{OFF_Y+END_Y/2}">length 275 mm</text>

  <!-- toe splay note -->
  <text class="lbl" x="{OFF_X-30}" y="{OFF_Y+FOOT_LEN_MM-4}">full width held to the tip (no toe taper)</text>

  <!-- scale check bar -->
  <rect x="{MARGIN}" y="274" width="100" height="5" fill="#0044cc"/>
  <text class="sm" x="{MARGIN}" y="272">scale check: this bar must measure exactly 100 mm</text>

  <text class="sm" x="{MARGIN}" y="284">Only length (275 mm) and ball width (120.65 mm) are chart-verified; other
  widths are scaled from a size-8 D reference. Stand on it - if it does not match
  your foot, trace your real foot and we rebuild from the trace.</text>
  <text class="sm" x="{MARGIN}" y="292">Sources: healthyfeetstore.com width chart; infrawiki/Appropedia 3D Printed Shoes.</text>
</svg>
'''

out = r"C:\Users\zutai\OneDrive\Documents\Default Project\shoe\foot_template_10p5_7E.svg"
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print("wrote", out)
