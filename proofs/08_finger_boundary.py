"""
08_finger_boundary.py
Verifies: finger tab staircase does not overrun the panel corner vertex.

Root cause (spec §10.5a): tab_width = fw + 2*burn. For n tabs in a zone of n*fw,
the total drawn length = n*fw + 2*burn, overrunning term_end by 2*burn.
With corner_radius=0, term_end IS the corner vertex → last tab exits the panel boundary.
With corner_radius≥2*burn, term_end is 2*burn before the corner vertex → last tab
ends at the corner vertex — no overrun.

Check method: for the top edge of a rectangular wall panel, collect all staircase
segment endpoints at face level (|y| ≤ burn). Assert none exceed the panel corner
vertex x-coordinate (w) by more than burn.

Run with: python3 proofs/08_finger_boundary.py
"""

import math
import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from core.models import Point
from core.joints import make_finger_edge, finger_edge_to_path_segments
from core.radii import finger_termination_point
from check_harness import CheckHarness

ch = CheckHarness()

# ── Panel parameters ──────────────────────────────────────────────────────────
W     = 65.0   # panel width (long_outer for a typical wall)
H     = 20.0   # panel height (depth_outer)
T     = 3.0    # thickness
BURN  = 0.05
TOL   = 0.0
ANGLE = 90.0   # all right-angle corners


def max_face_coord_along_edge(edge, panel_dim: float, burn: float) -> float:
    """Max along-edge coordinate among staircase points at panel face level.

    For a vertical edge (TR→BR): along-edge = y, face level = x ≈ panel_width.
    We check y-coordinates of points near the face (|x - panel_width| ≤ burn*2).
    These should stay within [0, panel_height] — the panel boundary in the edge direction.

    Returns the maximum along-edge coordinate found at face level.
    panel_dim: the panel dimension in the along-edge direction (H for vertical edge).
    """
    segs = finger_edge_to_path_segments(edge)
    # For vertical right edge: start=(W,0), end=(W,H). Along-edge = y. Face = x≈W.
    face_along = []
    for seg in segs:
        for pt in (seg.start, seg.end):
            # Face level: x is near panel right face (W), within 2*burn
            if abs(pt.x - W) <= burn * 2:
                face_along.append(pt.y)
    return max(face_along) if face_along else 0.0


R_FIX = 2 * BURN   # = 0.1mm

# Use the RIGHT EDGE of WALL_LONG: TR→BR, is_slotted=False (protruding tabs)
# This is the edge that shows the "protruding horizontal lines" at corners.
TR = Point(W, 0.0)
BR = Point(W, H)

print("\n── Test 1: corner_radius=0, protruding-tab edge (the bug) ──────────────")
edge_r0 = make_finger_edge(
    TR, BR,
    thickness=T, mating_thickness=T,
    protrude_outward=False, is_slotted=False,
    burn=BURN, tolerance=TOL,
    corner_radius_left=0.0, corner_radius_right=0.0,
    internal_angle_left_deg=ANGLE, internal_angle_right_deg=ANGLE,
)

my_r0 = max_face_coord_along_edge(edge_r0, H, BURN)
overrun_r0 = my_r0 - H
print(f"  corner_radius=0.0: max_face_y={my_r0:.4f}  corner_vertex_y={H:.4f}  overrun={overrun_r0:+.4f}mm")

ch.check_true(
    "radius=0 → overrun > 0 (bug demonstrated)",
    overrun_r0 > BURN * 0.5,
    f"overrun={overrun_r0:+.4f}mm expected ~+{2*BURN:.3f}mm",
)
ch.check_true(
    "radius=0 → max_face_y exceeds panel boundary by > burn (fails boundary rule)",
    my_r0 > H + BURN,
    f"max_face_y={my_r0:.4f} should exceed {H + BURN:.4f}",
)


print("\n── Test 2: corner_radius=2*burn, protruding-tab edge (the fix) ──────────")
edge_fix = make_finger_edge(
    TR, BR,
    thickness=T, mating_thickness=T,
    protrude_outward=False, is_slotted=False,
    burn=BURN, tolerance=TOL,
    corner_radius_left=R_FIX, corner_radius_right=R_FIX,
    internal_angle_left_deg=ANGLE, internal_angle_right_deg=ANGLE,
)

my_fix = max_face_coord_along_edge(edge_fix, H, BURN)
overrun_fix = my_fix - H
print(f"  corner_radius={R_FIX:.3f}: max_face_y={my_fix:.4f}  corner_vertex_y={H:.4f}  overrun={overrun_fix:+.4f}mm")

ch.check_true(
    "radius=2*burn → max_face_y ≤ panel corner vertex (no overrun)",
    my_fix <= H + BURN * 0.1,
    f"max_face_y={my_fix:.4f} should be ≤ {H:.4f}",
)
ch.check_true(
    "radius=2*burn → satisfies boundary rule (max_face_y ≤ H + burn)",
    my_fix <= H + BURN,
    f"max_face_y={my_fix:.4f} ≤ {H + BURN:.4f}",
)


print("\n── Test 3: term_end positions ───────────────────────────────────────────")
td_r0  = 0.0   / math.tan(math.radians(45.0))
td_fix = R_FIX / math.tan(math.radians(45.0))

ch.check("tangent_dist with radius=0",      td_r0,  0.0)
ch.check("tangent_dist with radius=2*burn", td_fix, 2 * BURN)
ch.check("term_end_y with radius=0",    edge_r0.term_end.y,  H - td_r0)
ch.check("term_end_y with radius=2*burn", edge_fix.term_end.y, H - td_fix)


print("\n── Test 4: both ends of fixed edge stay within boundary ─────────────────")
segs = finger_edge_to_path_segments(edge_fix)
all_face_pts_y = [
    pt.y for seg in segs for pt in (seg.start, seg.end)
    if abs(pt.x - W) <= BURN * 2
]
min_y = min(all_face_pts_y)
max_y = max(all_face_pts_y)

ch.check_true(
    "top end: min_face_y ≥ 0 (no top overrun)",
    min_y >= -BURN * 0.1,
    f"min_face_y={min_y:.4f}",
)
ch.check_true(
    "bottom end: max_face_y ≤ H (no bottom overrun)",
    max_y <= H + BURN * 0.1,
    f"max_face_y={max_y:.4f}",
)


print("\n── Test 5: production wall panel — tangent_dist ≥ 2*burn at all corners ──")
# This test catches the bug in production code: if panels.py passes corner_radius=0,
# tangent_dist=0 < 2*burn=0.1 → FAIL. After fix (radius=2*burn) → PASS.
import sys as _sys
_src2 = str(Path(__file__).resolve().parent.parent / "src")
if _src2 not in _sys.path:
    _sys.path.insert(0, _src2)

from core.models import CommonConfig, BoxConfig, DimMode, LidType
from core.trapezoid import derive
from core.radii import resolve_corner_radius
from box import panels as box_panels

common = CommonConfig(
    long=W, short=45.0, length=45.0, leg=None,
    depth=H, thickness=T,
    burn=BURN, tolerance=TOL,
    corner_radius=None, finger_width=None,
    sheet_width=600.0, sheet_height=600.0,
    labels=False, dim_mode=DimMode.OUTER,
    colorblind=False, json_errors=False,
    output="/tmp/proof08.svg",
)
config  = BoxConfig(common=common, lid=LidType.NONE)
geom    = derive(common)
radius  = resolve_corner_radius(common, geom)
panels  = box_panels.build(config, geom, radius)

def tangent_dist(pt_a: Point, pt_b: Point) -> float:
    """Euclidean distance between two points."""
    return math.sqrt((pt_a.x - pt_b.x)**2 + (pt_a.y - pt_b.y)**2)

min_td = float("inf")
worst = ""
for panel in panels:
    for edge in panel.finger_edges:
        td_s = tangent_dist(edge.start,   edge.term_start)
        td_e = tangent_dist(edge.end,     edge.term_end)
        for td, label in [(td_s, "term_start"), (td_e, "term_end")]:
            if td < min_td:
                min_td = td
                worst = f"{panel.name} {label} td={td:.4f}mm"

print(f"  Minimum tangent_dist across all production edges: {min_td:.4f}mm")
print(f"  Worst case: {worst}")
print(f"  Required minimum: 2*burn = {2*BURN:.4f}mm")

ch.check_true(
    f"all production finger edges: tangent_dist ≥ 2*burn ({2*BURN:.3f}mm)",
    min_td >= 2 * BURN - 1e-6,
    f"min tangent_dist={min_td:.4f}mm, worst: {worst}",
)


ch.summary("08_finger_boundary")
ch.exit()
