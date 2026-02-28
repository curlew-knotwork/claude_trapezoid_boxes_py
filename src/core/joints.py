"""
core/joints.py — All finger joint geometry.

Burn compensation rule (spec §10.5):
Every cut line is offset by burn in the direction that enlarges the feature
being created by that cut. SVG paths are laser centerlines; laser removes burn mm
from each side of every cut path.
  drawn_tab  = fw + 2*burn   → physical_tab  = fw
  drawn_slot = fw - 2*burn + 2*tol → physical_slot = fw + 2*tol
  nominal_fit = -4*burn + 2*tol  (negative = interference)
  burn=0.05, tol=0.0 → fit=-0.2mm (rubber mallet)

WINDING CONVENTION: All panel outlines follow clockwise winding in SVG Y-down space.
Outward for a FingerEdge = 90° clockwise from edge direction in SVG Y-down space.
"""

from __future__ import annotations
import math
import warnings

from constants import AUTO_FINGER_WIDTH_FACTOR, MIN_FINGER_COUNT, FLOAT_TOLERANCE
from core.models import Point, Line, Arc, ClosedPath, FingerEdge, PathSegment
from core.radii import finger_termination_point
from core.utils import normalise, nearly_equal, odd_count, actual_finger_width


def make_finger_edge(
    start:                    Point,
    end:                      Point,
    thickness:                float,
    mating_thickness:         float,    # depth of the mating panel
    protrude_outward:         bool,     # True = outward (instrument); False = inward (box)
    is_slotted:               bool,     # True = slots; False = protruding fingers
    burn:                     float,
    tolerance:                float,
    corner_radius_left:       float,
    corner_radius_right:      float,
    internal_angle_left_deg:  float,    # interior angle at start corner
    internal_angle_right_deg: float,    # interior angle at end corner
) -> FingerEdge:
    """Build a FingerEdge with computed finger count and termination points.

    ⚠ finger_direction (enum) is NOT a parameter here.
    panels.py converts FingerDirection enum to protrude_outward: bool before calling.
    """
    # Edge vector
    dx = end.x - start.x
    dy = end.y - start.y
    edge_length = math.sqrt(dx * dx + dy * dy)
    if nearly_equal(edge_length, 0.0):
        raise ValueError("make_finger_edge: start and end are coincident.")

    edge_dir = Point(dx / edge_length, dy / edge_length)
    neg_dir  = Point(-edge_dir.x, -edge_dir.y)

    # Termination points (where finger zone starts/ends after corner arc tangent)
    term_start = finger_termination_point(start, edge_dir, corner_radius_left,  internal_angle_left_deg)
    term_end   = finger_termination_point(end,   neg_dir,  corner_radius_right, internal_angle_right_deg)

    # Available length for fingers
    tsx = term_start.x; tsy = term_start.y
    tex = term_end.x;   tey = term_end.y
    available_length = math.sqrt((tex - tsx)**2 + (tey - tsy)**2)

    min_needed = mating_thickness + 2 * burn
    if available_length < min_needed:
        warnings.warn(
            f"Edge too short for any finger joints after corner radius termination "
            f"(available={available_length:.3f}mm, need>={min_needed:.3f}mm). "
            "Plain edge produced."
        )
        return FingerEdge(
            start=start, end=end,
            term_start=term_start, term_end=term_end,
            finger_width=0.0, count=0,
            depth=mating_thickness,
            protrude_outward=protrude_outward,
            is_slotted=is_slotted,
            burn=burn, tolerance=tolerance,
        )

    # Target finger count
    auto_width    = AUTO_FINGER_WIDTH_FACTOR * thickness
    target_count  = odd_count(available_length, auto_width)

    # Check if target count is feasible
    max_count = int(available_length / min_needed)
    if max_count < target_count:
        # Reduce to largest odd integer <= max_count (minimum 1)
        if max_count < 1:
            max_count = 1
        count = max_count if max_count % 2 == 1 else max_count - 1
        count = max(1, count)
        warnings.warn(
            f"Edge available ({available_length:.3f}mm) constrains finger count "
            f"from {target_count} to {count}."
        )
    else:
        count = target_count

    fw = actual_finger_width(available_length, count)

    return FingerEdge(
        start=start, end=end,
        term_start=term_start, term_end=term_end,
        finger_width=fw, count=count,
        depth=mating_thickness,
        protrude_outward=protrude_outward,
        is_slotted=is_slotted,
        burn=burn, tolerance=tolerance,
    )


def make_finger_edge_angled(
    start: Point, end: Point, thickness: float, mating_thickness: float,
    protrude_outward: bool, is_slotted: bool, burn: float, tolerance: float,
    corner_radius_left: float, corner_radius_right: float,
    internal_angle_left_deg: float, internal_angle_right_deg: float,
    leg_angle_deg: float,
) -> FingerEdge:
    """Wrapper for angled joints (leg wall ↔ base).

    Applies D_eff and W_over corrections before calling make_finger_edge().
    Only for leg-wall-to-base joints. All 90° joints use make_finger_edge() directly.
    """
    alpha  = math.radians(abs(leg_angle_deg))
    D_eff  = mating_thickness / math.cos(alpha)   # effective slot depth
    W_over = mating_thickness * math.tan(alpha)   # rotational overcut width
    # W_over implemented as additional tolerance on slot width
    effective_tolerance = tolerance + W_over
    return make_finger_edge(
        start, end, thickness, D_eff, protrude_outward, is_slotted,
        burn, effective_tolerance, corner_radius_left, corner_radius_right,
        internal_angle_left_deg, internal_angle_right_deg,
    )


def finger_edge_to_path_segments(edge: FingerEdge) -> list[PathSegment]:
    """Convert FingerEdge to Line segments from term_start to term_end.

    Convention: centre finger is a tab. For count=2k+1, finger k is centre.
    Fingers at even distance from centre are tabs; odd = gaps.
    Edge starts and ends with a tab.

    If edge.count == 0: return [Line(edge.start, edge.end)] (plain edge).
    """
    if edge.count == 0:
        return [Line(edge.start, edge.end)]

    dx = edge.end.x - edge.start.x
    dy = edge.end.y - edge.start.y
    elen = math.sqrt(dx * dx + dy * dy)
    edge_dir    = Point(dx / elen, dy / elen)
    # Outward = 90° CW from edge direction in SVG Y-down space
    # (y,−x) for CW rotation of (x,y): outward = (edge_dir.y, -edge_dir.x)
    edge_outward = Point(edge_dir.y, -edge_dir.x)

    if edge.protrude_outward:
        out_sign = 1.0
    else:
        out_sign = -1.0

    fw = edge.finger_width
    burn = edge.burn
    tol  = edge.tolerance
    depth = edge.depth

    tab_width = fw + 2 * burn          # drawn wider; laser removes 2*burn → physical fw
    gap_width = fw - 2 * burn + 2 * tol  # drawn narrower; laser widens by 2*burn → physical fw+2*tol
    depth_out = depth + burn           # slot/finger depth with kerf compensation

    if edge.is_slotted:
        # Slotted panel: even features are slots (use gap_width), odd are lands (use tab_width)
        tab_width, gap_width = gap_width, tab_width

    # Staircase from term_start to term_end
    pts: list[Point] = [edge.term_start]
    cur = Point(edge.term_start.x, edge.term_start.y)

    def move_along(p: Point, dist: float) -> Point:
        return Point(p.x + edge_dir.x * dist, p.y + edge_dir.y * dist)

    def move_out(p: Point, dist: float) -> Point:
        return Point(p.x + edge_outward.x * dist * out_sign,
                     p.y + edge_outward.y * dist * out_sign)

    segs: list[PathSegment] = []
    finger_start = edge.term_start

    for i in range(edge.count):
        is_tab = (i % 2 == 0)  # first finger is tab
        w = tab_width if is_tab else gap_width

        x0 = finger_start
        x1 = move_along(x0, w)

        if is_tab and not edge.is_slotted:
            # Tab protrudes outward
            p_out0 = move_out(x0, depth_out)
            p_out1 = move_out(x1, depth_out)
            segs.append(Line(x0, p_out0))
            segs.append(Line(p_out0, p_out1))
            segs.append(Line(p_out1, x1))
        elif not is_tab and not edge.is_slotted:
            # Gap: straight along (no protrusion)
            segs.append(Line(x0, x1))
        elif is_tab and edge.is_slotted:
            # Slot (even feature on slotted edge): protrudes outward
            p_out0 = move_out(x0, depth_out)
            p_out1 = move_out(x1, depth_out)
            segs.append(Line(x0, p_out0))
            segs.append(Line(p_out0, p_out1))
            segs.append(Line(p_out1, x1))
        else:
            # Land (odd feature on slotted edge): straight
            segs.append(Line(x0, x1))

        finger_start = x1

    # Ensure we end exactly at term_end (floating point closure)
    if segs:
        last_end = segs[-1].end if isinstance(segs[-1], Line) else segs[-1].end
        if not (nearly_equal(last_end.x, edge.term_end.x) and
                nearly_equal(last_end.y, edge.term_end.y)):
            segs.append(Line(last_end, edge.term_end))

    return segs


def build_panel_outline(
    edges:        list[FingerEdge],
    corner_arcs:  list[tuple[Point, Arc, Point]],
) -> ClosedPath:
    """Build a closed panel outline from finger edges and corner arcs.

    edges and corner_arcs have equal length n.
    corner_arcs[i] connects edges[i-1] to edges[i] (modulo n).

    Assembly per corner:
      Line(prev_finger_end → arc_start)   (omit if zero-length)
      arc
      Line(arc_end → first_finger_start)  (omit if zero-length)
      finger_edge_to_path_segments(edges[i])
    """
    n = len(edges)
    assert len(corner_arcs) == n, "edges and corner_arcs must have equal length."

    all_segs: list[PathSegment] = []

    for i in range(n):
        arc_start, arc, arc_end = corner_arcs[i]

        # Last point of previous edge's finger segments
        if i == 0:
            # First corner: we'll handle closure at the end
            prev_end = _last_path_point(edges[n - 1], all_segs if i > 0 else None)
        else:
            prev_end = _finger_edge_last_point(edges[i - 1])

        # Line from previous finger end to arc start (omit if zero-length)
        if not (nearly_equal(prev_end.x, arc_start.x) and nearly_equal(prev_end.y, arc_start.y)):
            all_segs.append(Line(prev_end, arc_start))

        # Arc itself
        all_segs.append(arc)

        # Line from arc end to first finger start (omit if zero-length)
        edge_term_start = edges[i].term_start
        if not (nearly_equal(arc_end.x, edge_term_start.x) and nearly_equal(arc_end.y, edge_term_start.y)):
            all_segs.append(Line(arc_end, edge_term_start))

        # Finger segments for this edge
        all_segs.extend(finger_edge_to_path_segments(edges[i]))

    # Verify closure
    if all_segs:
        first_pt = _get_segment_start(all_segs[0])
        last_pt  = _get_segment_end(all_segs[-1])
        if not (nearly_equal(first_pt.x, last_pt.x) and nearly_equal(first_pt.y, last_pt.y)):
            all_segs.append(Line(last_pt, first_pt))

    return ClosedPath(tuple(all_segs))


def _finger_edge_last_point(edge: FingerEdge) -> Point:
    """Return the last point of a finger edge's path segments."""
    segs = finger_edge_to_path_segments(edge)
    if not segs:
        return edge.term_end
    return _get_segment_end(segs[-1])


def _last_path_point(edge: FingerEdge, existing: list | None) -> Point:
    """For first corner, return the last point of the LAST edge (which hasn't been rendered yet)."""
    return _finger_edge_last_point(edge)


def _get_segment_start(seg: PathSegment) -> Point:
    match seg:
        case Line(start=s): return s
        case Arc(start=s):  return s
        case _:             return seg.start  # type: ignore[union-attr]


def _get_segment_end(seg: PathSegment) -> Point:
    match seg:
        case Line(end=e): return e
        case Arc(end=e):  return e
        case _:           return seg.end  # type: ignore[union-attr]


def build_plain_outline(
    vertices:           list[Point],
    corner_radius:      float,
    corner_angles_deg:  list[float],
) -> ClosedPath:
    """Build a plain outline (no finger joints) for SOUNDBOARD, blocks, etc.

    If corner_radius == 0.0: returns n Line segments (polygon).
    If > 0.0: alternates Lines and Arcs with corner arcs via corner_arc_segments().

    corner_angles_deg[i] is the interior angle at vertices[i].
    Vertices are in clockwise order.
    """
    from core.radii import corner_arc_segments

    n = len(vertices)
    if nearly_equal(corner_radius, 0.0):
        segs: list[PathSegment] = []
        for i in range(n):
            segs.append(Line(vertices[i], vertices[(i + 1) % n]))
        return ClosedPath(tuple(segs))

    # Compute arriving and departing unit vectors at each vertex
    def unit_vec(a: Point, b: Point) -> Point:
        dx = b.x - a.x; dy = b.y - a.y
        m = math.sqrt(dx*dx + dy*dy)
        return Point(dx / m, dy / m)

    segs = []
    # Pre-compute arc data for all corners
    arc_data: list[tuple[Point, Arc, Point]] = []
    for i in range(n):
        prev_v = vertices[(i - 1) % n]
        curr_v = vertices[i]
        next_v = vertices[(i + 1) % n]
        # arriving direction: from prev toward curr
        a_dir = unit_vec(prev_v, curr_v)
        # departing direction: from curr toward next
        b_dir = unit_vec(curr_v, next_v)
        arc_s, arc, arc_e = corner_arc_segments(
            curr_v, a_dir, b_dir, corner_radius, corner_angles_deg[i]
        )
        arc_data.append((arc_s, arc, arc_e))

    # Assemble: for each edge i→i+1, emit Line(arc_end_i → arc_start_{i+1}) + arc at i+1
    for i in range(n):
        arc_end_i    = arc_data[i][2]           # arc_end at vertex i
        arc_start_i1 = arc_data[(i + 1) % n][0] # arc_start at vertex i+1

        # Line from arc_end at i to arc_start at i+1
        if not (nearly_equal(arc_end_i.x, arc_start_i1.x) and
                nearly_equal(arc_end_i.y, arc_start_i1.y)):
            segs.append(Line(arc_end_i, arc_start_i1))

        # Arc at vertex i+1
        segs.append(arc_data[(i + 1) % n][1])

    return ClosedPath(tuple(segs))
