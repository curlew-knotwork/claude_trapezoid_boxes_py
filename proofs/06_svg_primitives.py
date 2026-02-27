"""
06_svg_primitives.py
Generates small SVG files you can open in Inkscape or a browser to visually
verify the geometry before writing any production code.

Outputs (in same directory as this script):
  06a_corner_arcs.svg      — all four BASE corners with arcs at 2x scale
  06b_finger_strip.svg     — one finger joint edge (BASE long_bottom)
  06c_full_base.svg        — complete BASE panel outline
  06d_lid_width.svg        — sliding lid cross-section showing groove geometry

Open each in Inkscape. Verify:
  - Arcs are smooth and tangent to edges (no kinks, no gaps)
  - Fingers are regular and centred in available space
  - BASE outline looks like a correct trapezoid
  - Lid width diagram shows lid clearly fitting inside groove span

No dependencies beyond stdlib. Run with: python3 06_svg_primitives.py
"""

import math
import os

# ── SVG helpers ───────────────────────────────────────────────────────────────

def svg_doc(width_mm, height_mm, content, scale=3.0):
    """SVG wrapper. scale=pixels per mm for comfortable screen viewing."""
    w = width_mm  * scale
    h = height_mm * scale
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_mm}mm" height="{height_mm}mm" '
        f'viewBox="0 0 {w:.4f} {h:.4f}">\n'
        f'<rect width="{w:.4f}" height="{h:.4f}" fill="white"/>\n'
        + content +
        f'</svg>\n'
    )


def path(d, stroke="blue", fill="none", width=0.5, scale=3.0):
    return f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{width*scale:.3f}"/>\n'


def text_label(x, y, label, scale=3.0, size=3.5):
    return (f'<text x="{x*scale:.3f}" y="{y*scale:.3f}" '
            f'font-size="{size*scale:.3f}" font-family="monospace" fill="black">'
            f'{label}</text>\n')


def line(x1, y1, x2, y2, scale=3.0, stroke="grey", width=0.3):
    return (f'<line x1="{x1*scale:.3f}" y1="{y1*scale:.3f}" '
            f'x2="{x2*scale:.3f}" y2="{y2*scale:.3f}" '
            f'stroke="{stroke}" stroke-width="{width*scale:.3f}" '
            f'stroke-dasharray="{1.5*scale:.3f},{1.5*scale:.3f}"/>\n')


# ── Geometry functions (identical to earlier scripts) ─────────────────────────

def tang(angle_deg, R):
    return R / math.tan(math.radians(angle_deg / 2))


def centre_offset(angle_deg, R):
    return R / math.sin(math.radians(angle_deg / 2))


def inward_bisector(edge_a_dir, edge_b_dir):
    bx = -edge_a_dir[0] + edge_b_dir[0]
    by = -edge_a_dir[1] + edge_b_dir[1]
    mag = math.sqrt(bx*bx + by*by)
    return bx/mag, by/mag


def arc_path_segment(start, end, R, sweep=1):
    """SVG arc path: A rx ry x-rotation large-arc-flag sweep-flag x y"""
    sx, sy = start;  ex, ey = end
    return f"A {R:.4f} {R:.4f} 0 0 {sweep} {ex:.4f} {ey:.4f}"


def corner_arc_points(vertex, edge_a_dir, edge_b_dir, R, angle_deg):
    td = tang(angle_deg, R)
    arc_start = (vertex[0] - edge_a_dir[0]*td, vertex[1] - edge_a_dir[1]*td)
    arc_end   = (vertex[0] + edge_b_dir[0]*td, vertex[1] + edge_b_dir[1]*td)
    return arc_start, arc_end


def finger_count_and_width(available, nominal):
    n = round(available / nominal)
    if n % 2 == 0: n -= 1
    n = max(3, n)
    return n, available / n


# ── Reference values ──────────────────────────────────────────────────────────

T         = 3.0
R         = 9.0
fw        = 9.0    # 3*T
burn      = 0.05
leg_angle = 4.5140
long_o    = 180.0
short_o   = 120.0
leg_inset = (long_o - short_o) / 2
leg_len   = math.sqrt(380.0**2 + leg_inset**2)

long_end_angle  = 90.0 + leg_angle
short_end_angle = 90.0 - leg_angle

tang_long  = tang(long_end_angle,  R)
tang_short = tang(short_end_angle, R)

leg_ax = math.sin(math.radians(leg_angle))
leg_ay = math.cos(math.radians(leg_angle))

# Panel corners in mm (Y-down, origin at top-left of bounding box)
TL = (leg_inset,      0.0  )
TR = (leg_inset+short_o, 0.0)
BR = (long_o,         380.0)
BL = (0.0,            380.0)

script_dir = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
print("Generating 06a_corner_arcs.svg ...")

SCALE = 3.0
PAD   = 20.0   # padding mm
CORNER_SIZE = 60.0

def draw_corner(cx, cy, vertex, ea, eb, angle_deg, label, scale=SCALE):
    """Draw one corner with its arc at position (cx,cy) in mm."""
    arc_s, arc_e = corner_arc_points(vertex, ea, eb, R, angle_deg)

    # Translate so corner is at (cx,cy)
    ox = cx - vertex[0]
    oy = cy - vertex[1]

    def t(p): return (p[0]+ox, p[1]+oy)
    def ts(p, scale=scale): return (t(p)[0]*scale, t(p)[1]*scale)

    v  = t(vertex)
    s  = t(arc_s)
    e  = t(arc_e)

    # Two edges from vertex (use full length 40mm for visibility)
    # Incoming edge: from arc_start toward vertex, extend 40mm past arc_start
    e1_far = (arc_s[0] - ea[0]*40, arc_s[1] - ea[1]*40)
    e2_far = (arc_e[0] + eb[0]*40, arc_e[1] + eb[1]*40)

    d = ""
    # Edge a (arriving)
    d += f"M {t(e1_far)[0]*scale:.3f},{t(e1_far)[1]*scale:.3f} "
    d += f"L {s[0]*scale:.3f},{s[1]*scale:.3f} "
    # Arc
    d += arc_path_segment((s[0]*scale, s[1]*scale), (e[0]*scale, e[1]*scale), R*scale)
    d += f" L {t(e2_far)[0]*scale:.3f},{t(e2_far)[1]*scale:.3f}"

    content = path(d, stroke="blue", width=0.4, scale=1)

    # Mark vertex with a small cross
    content += (f'<line x1="{v[0]*scale-3:.3f}" y1="{v[1]*scale:.3f}" '
                f'x2="{v[0]*scale+3:.3f}" y2="{v[1]*scale:.3f}" '
                f'stroke="red" stroke-width="0.8"/>\n')
    content += (f'<line x1="{v[0]*scale:.3f}" y1="{v[1]*scale-3:.3f}" '
                f'x2="{v[0]*scale:.3f}" y2="{v[1]*scale+3:.3f}" '
                f'stroke="red" stroke-width="0.8"/>\n')

    # Label
    content += (f'<text x="{v[0]*scale+5:.3f}" y="{v[1]*scale-5:.3f}" '
                f'font-size="12" font-family="monospace" fill="black">'
                f'{label} ({angle_deg:.1f}°)</text>\n')
    return content

W, H = 280, 280
content = ""

# Place four corners in a 2×2 grid
grid = [
    (PAD+CORNER_SIZE/2, PAD+CORNER_SIZE/2, TL, (leg_ax,-leg_ay), (1,0), long_end_angle, "TL"),
    (PAD+CORNER_SIZE*2, PAD+CORNER_SIZE/2, TR, (1,0), (leg_ax,leg_ay), long_end_angle,  "TR"),
    (PAD+CORNER_SIZE/2, PAD+CORNER_SIZE*2, BL, (-1,0), (leg_ax,-leg_ay), short_end_angle,  "BL"),
    (PAD+CORNER_SIZE*2, PAD+CORNER_SIZE*2, BR, (leg_ax,leg_ay), (-1,0), short_end_angle, "BR"),
]

for cx, cy, V, ea, eb, ang, lbl in grid:
    content += draw_corner(cx, cy, V, ea, eb, ang, lbl, scale=1)

with open(os.path.join(script_dir, "06a_corner_arcs.svg"), "w") as f:
    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
            f'viewBox="0 0 {W} {H}">\n'
            f'<rect width="{W}" height="{H}" fill="white"/>\n'
            + content +
            f'</svg>\n')
print("  Written 06a_corner_arcs.svg")


# ══════════════════════════════════════════════════════════════════════════════
print("Generating 06b_finger_strip.svg ...")

# Draw BASE long_bottom edge as a finger strip
# Available zone starts at tang_short from each end
avail_long  = long_o - 2*tang_short
n_long, fw_long = finger_count_and_width(avail_long, fw)

SCALE_B = 2.0
STRIP_H = 30.0   # mm tall strip

d_finger = ""
x = 0.0

# Plain line from 0 to tang_short
d_finger += f"M {0},{STRIP_H/2} L {tang_short:.4f},{STRIP_H/2} "

# Fingers
is_tab = True
for i in range(n_long):
    x0 = tang_short + i * fw_long
    x1 = x0 + fw_long
    if is_tab:
        # Tab protrudes downward (toward base interior)
        d_finger += (f"L {x0:.4f},{STRIP_H/2} "
                     f"L {x0:.4f},{STRIP_H/2+T} "
                     f"L {x1:.4f},{STRIP_H/2+T} "
                     f"L {x1:.4f},{STRIP_H/2} ")
    else:
        # Slot — stays at midline
        d_finger += f"L {x1:.4f},{STRIP_H/2} "
    is_tab = not is_tab

# Plain line from end of fingers to far edge
d_finger += f"L {long_o:.4f},{STRIP_H/2}"

SVG_W = long_o + 20
SVG_H = STRIP_H + 20
strip_content = (
    f'<rect width="{SVG_W*SCALE_B:.3f}" height="{SVG_H*SCALE_B:.3f}" fill="white"/>\n'
    f'<g transform="translate({10*SCALE_B:.3f},{5*SCALE_B:.3f}) scale({SCALE_B})">\n'
    + f'<path d="{d_finger}" stroke="blue" fill="none" stroke-width="0.3"/>\n'
    + f'<text x="0" y="{STRIP_H+8}" font-size="4" font-family="monospace" fill="black">'
    + f'BASE long_bottom: n={n_long} fingers, fw={fw_long:.4f}mm, avail={avail_long:.3f}mm'
    + f'</text>\n'
    + f'</g>\n'
)
with open(os.path.join(script_dir, "06b_finger_strip.svg"), "w") as f:
    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{SVG_W*SCALE_B:.3f}mm" height="{SVG_H*SCALE_B:.3f}mm" '
            f'viewBox="0 0 {SVG_W*SCALE_B:.3f} {SVG_H*SCALE_B:.3f}">\n'
            + strip_content + f'</svg>\n')
print(f"  Written 06b_finger_strip.svg  ({n_long} fingers)")


# ══════════════════════════════════════════════════════════════════════════════
print("Generating 06c_full_base.svg ...")

PAD_C = 15.0
SVG_W_C = long_o + 2*PAD_C
SVG_H_C = 380.0  + 2*PAD_C
SCALE_C  = 1.5

def build_base_outline():
    """Full BASE outline with finger joints and corner arcs. Returns SVG path d."""
    # Corners
    tl = TL;  tr = TR;  br = BR;  bl = BL

    # Corner arc start/end points
    tl_s, tl_e = corner_arc_points(tl, (leg_ax,-leg_ay), (1,0), R, long_end_angle)
    tr_s, tr_e = corner_arc_points(tr, (1,0), (leg_ax,leg_ay), R, long_end_angle)
    br_s, br_e = corner_arc_points(br, (leg_ax,leg_ay), (-1,0), R, short_end_angle)
    bl_s, bl_e = corner_arc_points(bl, (-1,0), (leg_ax,-leg_ay), R, short_end_angle)

    def p(x, y): return f"{(x+PAD_C)*SCALE_C:.3f},{(y+PAD_C)*SCALE_C:.3f}"
    def a(s, e): return f"A {R*SCALE_C:.3f} {R*SCALE_C:.3f} 0 0 1 {p(*e)}"

    d = f"M {p(*bl_e)} "

    # BL → TL (left leg): finger zone
    avail_leg = leg_len - tang_short - tang_long
    n_leg, fw_leg_c = finger_count_and_width(avail_leg, fw)
    leg_dx = -leg_ax * fw_leg_c
    leg_dy = -leg_ay * fw_leg_c

    # Start after BL arc end, travel up left leg
    cx, cy = bl_e
    # Plain line to start of finger zone
    fz_start_x = bl_e[0] + (-leg_ax) * tang_long  # BL arc end + tang distance
    # Actually: bl_e is already tang_long from BL vertex along the -X direction...
    # Simplification: just draw the leg edge as a straight line for the SVG
    # (fingers on diagonals are complex to render — skip detailed finger rendering
    #  on legs, just show straight edge)
    d += f"L {p(*tl_s)} "
    d += a(tl_s, tl_e) + " "  # TL arc

    # TL → TR (short top): finger zone
    # tl_e is the arc END point — it IS the finger zone start. Do NOT add tang again.
    # tr_s is the arc START point of the TR corner — it IS the finger zone end.
    # Available length = tr_s.x - tl_e.x (both x-coords, y=0 on this edge)
    avail_short_c = tr_s[0] - tl_e[0]
    n_short_c, fw_short_c = finger_count_and_width(avail_short_c, fw)
    # No plain-line segment here — tl_e IS the start of the finger zone
    is_tab = True
    for i in range(n_short_c):
        x0 = tl_e[0] + i*fw_short_c
        x1 = x0 + fw_short_c
        if is_tab:
            d += (f"L {p(x0, 0)} L {p(x0, -T)} L {p(x1, -T)} L {p(x1, 0)} ")
        else:
            d += f"L {p(x1, 0)} "
        is_tab = not is_tab
    d += f"L {p(*tr_s)} "
    d += a(tr_s, tr_e) + " "  # TR arc

    # TR → BR (right leg): straight
    d += f"L {p(*br_s)} "
    d += a(br_s, br_e) + " "  # BR arc

    # BR → BL (long bottom): finger zone
    # BR corner is short_end_angle → tang_short. BL corner is long_end_angle → tang_long.
    # br_e is the arc END of the BR corner — finger zone starts here.
    # bl_s is the arc START of the BL corner — finger zone ends here.
    # Available = br_e.x - bl_s.x (travelling right to left, y=380)
    avail_long_c = br_e[0] - bl_s[0]
    n_long_c, fw_long_c = finger_count_and_width(avail_long_c, fw)
    x_pos = br_e[0]
    is_tab = True
    for i in range(n_long_c):
        x0 = br_e[0] - i*fw_long_c
        x1 = x0 - fw_long_c
        if is_tab:
            d += (f"L {p(x0, 380)} L {p(x0, 380+T)} L {p(x1, 380+T)} L {p(x1, 380)} ")
        else:
            d += f"L {p(x1, 380)} "
        is_tab = not is_tab
    d += f"L {p(*bl_s)} "
    d += a(bl_s, bl_e) + " "  # BL arc
    d += "Z"
    return d

base_d = build_base_outline()
with open(os.path.join(script_dir, "06c_full_base.svg"), "w") as f:
    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{SVG_W_C*SCALE_C:.3f}mm" height="{SVG_H_C*SCALE_C:.3f}mm" '
            f'viewBox="0 0 {SVG_W_C*SCALE_C:.3f} {SVG_H_C*SCALE_C:.3f}">\n'
            f'<rect width="{SVG_W_C*SCALE_C:.3f}" height="{SVG_H_C*SCALE_C:.3f}" fill="white"/>\n'
            f'<path d="{base_d}" stroke="blue" fill="none" stroke-width="0.6"/>\n'
            f'<text x="10" y="{SVG_H_C*SCALE_C-10:.3f}" '
            f'font-size="8" font-family="monospace" fill="black">'
            f'BASE panel — long={long_o}mm short={short_o}mm length=380mm T={T}mm R={R}mm'
            f'</text>\n'
            f'</svg>\n')
print("  Written 06c_full_base.svg")


# ══════════════════════════════════════════════════════════════════════════════
print("Generating 06d_lid_width.svg ...")

# Cross-section diagram at short end showing lid groove geometry
tol = 0.1
groove_depth  = T + tol   # how deep groove goes into wall from interior face
lid_thickness = T

# Dimensions:
# Box outer width at short end = short_o = 120mm
# Left leg wall: x=0..T (outer face to interior face)
# Right leg wall: x=short_o-T..short_o
# Left groove: from T to T+groove_depth  (interior face inward)
# Right groove: from short_o-T-groove_depth to short_o-T
# Lid width: from T+groove_depth to short_o-T-groove_depth

lid_left  = T + groove_depth   # 6.1mm from left
lid_right = short_o - T - groove_depth  # 113.9mm from left
lid_w     = lid_right - lid_left

SCALE_D = 3.0
PAD_D   = 15.0
H_D     = 40.0
W_D     = short_o + 2*PAD_D

def rx(x): return (x + PAD_D) * SCALE_D
def ry(y): return (y + PAD_D) * SCALE_D

svg_d = ""
# Left wall (filled grey)
svg_d += (f'<rect x="{rx(0):.3f}" y="{ry(0):.3f}" '
          f'width="{T*SCALE_D:.3f}" height="{H_D*SCALE_D:.3f}" '
          f'fill="#cccccc" stroke="black" stroke-width="0.5"/>\n')
# Right wall
svg_d += (f'<rect x="{rx(short_o-T):.3f}" y="{ry(0):.3f}" '
          f'width="{T*SCALE_D:.3f}" height="{H_D*SCALE_D:.3f}" '
          f'fill="#cccccc" stroke="black" stroke-width="0.5"/>\n')
# Left groove (white notch in wall)
svg_d += (f'<rect x="{rx(T):.3f}" y="{ry(5):.3f}" '
          f'width="{groove_depth*SCALE_D:.3f}" height="{lid_thickness*SCALE_D:.3f}" '
          f'fill="white" stroke="blue" stroke-width="0.5"/>\n')
# Right groove
svg_d += (f'<rect x="{rx(short_o-T-groove_depth):.3f}" y="{ry(5):.3f}" '
          f'width="{groove_depth*SCALE_D:.3f}" height="{lid_thickness*SCALE_D:.3f}" '
          f'fill="white" stroke="blue" stroke-width="0.5"/>\n')
# Lid (green)
svg_d += (f'<rect x="{rx(lid_left):.3f}" y="{ry(5):.3f}" '
          f'width="{lid_w*SCALE_D:.3f}" height="{lid_thickness*SCALE_D:.3f}" '
          f'fill="#90ee90" stroke="darkgreen" stroke-width="0.5"/>\n')
# Dimension arrows and labels
svg_d += (f'<text x="{rx(lid_left + lid_w/2):.3f}" y="{ry(25):.3f}" '
          f'font-size="{3.5*SCALE_D:.3f}" font-family="monospace" fill="darkgreen" '
          f'text-anchor="middle">lid width = {lid_w:.1f}mm</text>\n')
svg_d += (f'<text x="{rx(short_o/2):.3f}" y="{ry(33):.3f}" '
          f'font-size="{3*SCALE_D:.3f}" font-family="monospace" fill="black" '
          f'text-anchor="middle">'
          f'short_outer={short_o}mm  T={T}mm  groove_depth={groove_depth:.1f}mm  '
          f'lid = short_inner - 2*(T+tol) = {lid_w:.1f}mm'
          f'</text>\n')

with open(os.path.join(script_dir, "06d_lid_width.svg"), "w") as f:
    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{W_D*SCALE_D:.3f}mm" height="{H_D*SCALE_D+2*PAD_D*SCALE_D:.3f}mm" '
            f'viewBox="0 0 {W_D*SCALE_D:.3f} {(H_D+2*PAD_D)*SCALE_D:.3f}">\n'
            f'<rect width="{W_D*SCALE_D:.3f}" height="{(H_D+2*PAD_D)*SCALE_D:.3f}" fill="white"/>\n'
            + svg_d + '</svg>\n')
print("  Written 06d_lid_width.svg")

print(f"\nAll SVG files written to: {script_dir}")
print("\nOpen in Inkscape and verify:")
print("  06a: arcs are smooth and tangent, red cross marks vertex, no gaps at arc-line joins")
print("  06b: regular finger pattern, centred in available space")
print("  06c: trapezoid BASE with arcs at all four corners, fingers on short and long edges")
print("  06d: green lid fits inside grey walls with groove seats visible")
print("\nIf it looks right visually, the SVG generator is working correctly.")

# ══════════════════════════════════════════════════════════════════════════════
# Corner angle invariant verification (numeric, not visual)
# INVARIANT: for any clockwise-wound trapezoid, narrow-end corners = obtuse
# (90+leg_angle), wide-end corners = acute (90-leg_angle).
# Verify this holds for the body panel corners TL, TR, BL, BR.

print("\n── Corner angle invariant — body panel ──")

passed_ca = 0
failed_ca = 0

def unit_v(p1, p2):
    dx=p2[0]-p1[0]; dy=p2[1]-p1[1]; m=math.sqrt(dx**2+dy**2); return dx/m, dy/m

def interior_angle(vertex, prev_pt, next_pt):
    d_in  = unit_v(prev_pt, vertex)
    d_out = unit_v(vertex,  next_pt)
    dot   = (-d_in[0])*d_out[0] + (-d_in[1])*d_out[1]
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))

# Body panel corners (CW order: BL → TL → TR → BR → BL)
# TL, TR = narrow end = should be obtuse = long_end_angle
# BL, BR = wide end   = should be acute  = short_end_angle
corner_cases = [
    ("TL", TL, BL, TR, long_end_angle,  "narrow → obtuse"),
    ("TR", TR, TL, BR, long_end_angle,  "narrow → obtuse"),
    ("BL", BL, BR, TL, short_end_angle, "wide → acute"),
    ("BR", BR, TL, BL, short_end_angle, "wide → acute"),  # CW: BR prev=TL? No:
]

# CW traversal: BL→TL→TR→BR→BL, so:
# TL: prev=BL, next=TR
# TR: prev=TL, next=BR
# BR: prev=TR, next=BL
# BL: prev=BR, next=TL
corner_cases = [
    ("TL", TL, BL, TR, long_end_angle,  "narrow-end → obtuse"),
    ("TR", TR, TL, BR, long_end_angle,  "narrow-end → obtuse"),
    ("BR", BR, TR, BL, short_end_angle, "wide-end → acute"),
    ("BL", BL, BR, TL, short_end_angle, "wide-end → acute"),
]

for name, v, prev, nxt, expected, desc in corner_cases:
    actual = interior_angle(v, prev, nxt)
    ok     = abs(actual - expected) < 0.01
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {name} ({desc}): geometry={actual:.4f}° assigned={expected:.4f}°")
    if ok: passed_ca += 1
    else:  failed_ca += 1

if failed_ca == 0:
    print("  Corner angle invariant holds for all four body panel corners.")
else:
    print(f"  *** {failed_ca} corner angle invariant FAILURES — geometry is wrong ***")
