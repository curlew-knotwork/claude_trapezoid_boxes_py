"""
02_corner_arcs.py
Verifies: corner_arc_segments() geometry — tangent distances, arc centre
positions, bisector direction, and that arcs are truly tangent to both edges.

No dependencies beyond stdlib. Run with: python3 02_corner_arcs.py
"""

import math
import sys

from check_harness import CheckHarness
from geometry_utils import tang, centre_offset, inward_bisector, corner_arc_start_end

h = CheckHarness()
FLOAT_TOL = 1e-4


def arc_centre(start, end, radius, large_arc, clockwise):
    """
    Compute arc centre from start/end points, radius, and arc flags.
    Mirrors spec Section 7.3 arc_centre() utility.
    """
    sx, sy = start;  ex, ey = end
    mx = (sx + ex) / 2;  my = (sy + ey) / 2
    dx = ex - sx;  dy = ey - sy
    half_chord = math.sqrt(dx*dx + dy*dy) / 2
    if half_chord > radius + FLOAT_TOL:
        raise ValueError(f"chord ({2*half_chord:.4f}) > diameter ({2*radius:.4f})")
    d = math.sqrt(max(0.0, radius*radius - half_chord*half_chord))
    # Perpendicular to chord (normalised)
    px = -dy / (2 * half_chord)
    py =  dx / (2 * half_chord)
    sign = 1.0 if (large_arc != clockwise) else -1.0
    return mx + sign*d*px, my + sign*d*py


# ── Reference values from spec (Section A.5 reference table) ─────────────────

R = 9.0
leg_angle = 4.5140  # degrees, dulcimer preset
long_end_angle  = 90.0 + leg_angle   # 94.514°
short_end_angle = 90.0 - leg_angle   # 85.486°


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 1: Tangent distances ──")
h.check("tang 90°",           tang(90.0, R),          9.0000)
h.check("tang long-end",      tang(long_end_angle, R), 8.3175, tol=1e-3)
h.check("tang short-end",     tang(short_end_angle, R),9.7385, tol=1e-3)

print("\n── Test 2: Centre offsets ──")
h.check("centre 90°",         centre_offset(90.0, R),             12.7279, tol=1e-3)
h.check("centre long-end",    centre_offset(long_end_angle, R),   12.2548, tol=1e-3)
h.check("centre short-end",   centre_offset(short_end_angle, R),  13.2604, tol=1e-3)

print("\n── Test 3: Bisector direction ──")
# 90° corner at TL: edge_a arriving from below (0,-1) → toward TL = dir (0,-1)
# edge_b departing rightward (+1,0)
bisector_90 = inward_bisector((0, -1), (1, 0))
h.check("bisector_90 x", bisector_90[0], math.sqrt(2)/2, tol=1e-6)
h.check("bisector_90 y", bisector_90[1], math.sqrt(2)/2, tol=1e-6)

# TR corner (long_end_angle = 94.514°): edge_a arrives along +X, edge_b departs along leg_right
leg_a_x = math.sin(math.radians(leg_angle))
leg_a_y = math.cos(math.radians(leg_angle))
bisector_TR = inward_bisector((1, 0), (leg_a_x, leg_a_y))
print(f"  bisector_TR: ({bisector_TR[0]:.6f}, {bisector_TR[1]:.6f})")
# Must point INTO the panel: dx < 0, dy > 0 (left and down from TR in Y-down)
h.check_true("bisector_TR dx < 0 (into panel)", bisector_TR[0] < 0,
           f"dx={bisector_TR[0]:.4f}")
h.check_true("bisector_TR dy > 0 (into panel)", bisector_TR[1] > 0,
           f"dy={bisector_TR[1]:.4f}")

# Verify centre is R away from both arc points
TR = (150.0, 0.0)
arc_start_TR, arc_end_TR = corner_arc_start_end(TR, (1, 0), (leg_a_x, leg_a_y),
                                                  R, long_end_angle)
# Centre from bisector formula
co = centre_offset(long_end_angle, R)
centre_TR = (TR[0] + co*bisector_TR[0], TR[1] + co*bisector_TR[1])
d1 = math.sqrt((centre_TR[0]-arc_start_TR[0])**2 + (centre_TR[1]-arc_start_TR[1])**2)
d2 = math.sqrt((centre_TR[0]-arc_end_TR[0])**2   + (centre_TR[1]-arc_end_TR[1])**2)
h.check("centre_TR dist to arc_start = R", d1, R)
h.check("centre_TR dist to arc_end = R",   d2, R)

# Verify arc_centre() function gives same result
cx, cy = arc_centre(arc_start_TR, arc_end_TR, R, large_arc=False, clockwise=True)
h.check("arc_centre() matches bisector formula x", cx, centre_TR[0])
h.check("arc_centre() matches bisector formula y", cy, centre_TR[1])

print("\n── Test 4: Wrong bisector formula gives wrong answer ──")
# Verify that the OLD (wrong) formula: normalise(-a + -b) gives different/wrong centre
bx_wrong = -1.0 + (-leg_a_x)
by_wrong = 0.0  + (-leg_a_y)
mag_wrong = math.sqrt(bx_wrong**2 + by_wrong**2)
bisector_wrong = (bx_wrong/mag_wrong, by_wrong/mag_wrong)
centre_wrong = (TR[0] + co*bisector_wrong[0], TR[1] + co*bisector_wrong[1])
d_wrong = math.sqrt((centre_wrong[0]-arc_start_TR[0])**2 + (centre_wrong[1]-arc_start_TR[1])**2)
h.check_true("wrong bisector gives wrong distance (not R)",
           abs(d_wrong - R) > 0.1,
           f"distance={d_wrong:.4f}, should differ from R={R}")
print(f"  NOTE  Wrong formula centre is {d_wrong:.4f}mm from arc_start (correct is {R}mm)")

print("\n── Test 5: 90° corner — arc_centre() spot check ──")
# Arc from (10,0) to (0,10), R=10, clockwise, should give centre (0,0)
cx, cy = arc_centre((10,0), (0,10), 10.0, large_arc=False, clockwise=True)
h.check("90° arc centre x", cx, 0.0)
h.check("90° arc centre y", cy, 0.0)

print("\n── Test 6: arc_centre() — chord > diameter raises ──")
try:
    arc_centre((0,0), (100,0), 10.0, False, True)
    h.check_true("chord > diameter raises ValueError", False, "no exception")
except ValueError:
    h.check_true("chord > diameter raises ValueError", True)

print("\n── Test 7: All four BASE corners — centres inside panel ──")
# Panel: long=180, short=120, length=380 (trapezoid BASE)
# Corners: TL=(30,0), TR=(150,0), BR=(180,380), BL=(0,380)
# TL: short_end_angle (85.486°), TR: long_end_angle (94.514°)
# BL: long_end_angle, BR: short_end_angle
TL = (30.0,   0.0)
TR = (150.0,  0.0)
BR = (180.0, 380.0)
BL = (  0.0, 380.0)

leg_a_x = math.sin(math.radians(leg_angle))  # ~0.0787
leg_a_y = math.cos(math.radians(leg_angle))  # ~0.9969

# TL: edge_a = left leg arriving (from BL toward TL): normalise(TL-BL) = (-leg_a_x, -leg_a_y)
# Actually: in panel coords, the outline goes CW: TL→TR→BR→BL→TL (for BASE)
# Wait — BASE outline traversal is specific to the panel. Let me use edge directions.
# For each corner, edge_a = direction of incoming edge, edge_b = direction of outgoing edge.

# CW traversal: BL→TL→TR→BR→BL (going around the trapezoid CW from bottom-left)
# Actually BASE outline in spec: starts at BL, goes up left-leg to TL, right along short to TR,
# down right-leg to BR, left along long to BL.

corners = [
    # (name, vertex, edge_a_dir toward V, edge_b_dir away from V, angle, expected_interior)
    # TL: arriving from BL (up-left leg), departing toward TR (rightward)
    ("TL", TL, (-leg_a_x, -leg_a_y), (1,0), short_end_angle,
     lambda c: c[0] > TL[0] and c[1] > TL[1]),   # centre is right+below = into panel
    # TR: arriving from TL (rightward), departing toward BR (down-right leg)
    ("TR", TR, (1, 0), (leg_a_x, leg_a_y), long_end_angle,
     lambda c: c[0] < TR[0] and c[1] > TR[1]),   # left+below = into panel
    # BR: arriving from TR (down-right leg), departing toward BL (leftward)
    ("BR", BR, (leg_a_x, leg_a_y), (-1, 0), short_end_angle,
     lambda c: c[0] < BR[0] and c[1] < BR[1]),   # left+above = into panel
    # BL: arriving from BR (leftward), departing toward TL (up-left leg)
    ("BL", BL, (-1, 0), (-leg_a_x, -leg_a_y), long_end_angle,
     lambda c: c[0] > BL[0] and c[1] < BL[1]),   # right+above = into panel
]

for name, V, ea, eb, angle, interior_test in corners:
    b = inward_bisector(ea, eb)
    co = centre_offset(angle, R)
    cx = V[0] + co*b[0];  cy = V[1] + co*b[1]
    interior = interior_test((cx, cy))
    h.check_true(f"corner {name} centre inside panel", interior,
               f"centre=({cx:.3f},{cy:.3f})")
    # Also verify arc start/end are R from centre
    arc_s, arc_e = corner_arc_start_end(V, ea, eb, R, angle)
    d_s = math.sqrt((cx-arc_s[0])**2 + (cy-arc_s[1])**2)
    d_e = math.sqrt((cx-arc_e[0])**2 + (cy-arc_e[1])**2)
    h.check(f"corner {name} arc_start dist", d_s, R)
    h.check(f"corner {name} arc_end dist",   d_e, R)


# ══════════════════════════════════════════════════════════════════════════════
h.summary()
if h.failed == 0:
    print("ALL PASS — corner arc geometry is correct.")
else:
    print("FAILURES DETECTED — review corner arc formulas before proceeding.")
h.exit()
