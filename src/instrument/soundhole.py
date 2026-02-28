"""
instrument/soundhole.py — Sound hole geometry and Helmholtz calculation.

Round hole, f-hole, and rounded-trapezoid soundhole types.
"""

from __future__ import annotations
import math

from constants import (
    SPEED_OF_SOUND_MM_S, HELMHOLTZ_L_EFF_FACTOR, HELMHOLTZ_MAX_ITERATIONS,
    FLOAT_TOLERANCE,
    RTRAP_LONG_TO_BODY_RATIO, RTRAP_ASPECT_RATIO, RTRAP_CORNER_R_MM,
    FHOLE_UPPER_EYE_Y_RATIO, FHOLE_LOWER_EYE_Y_RATIO,
    FHOLE_UPPER_EYE_D_RATIO, FHOLE_LOWER_EYE_D_RATIO,
    FHOLE_WAIST_RATIO, FHOLE_WAIST_Y_RATIO,
    FHOLE_CP1_X_RATIO_UPPER, FHOLE_CP2_X_RATIO_UPPER,
    FHOLE_CP1_Y_RATIO_UPPER, FHOLE_CP2_Y_RATIO_UPPER,
    FHOLE_CP1_X_RATIO_LOWER, FHOLE_CP2_X_RATIO_LOWER,
    FHOLE_CP1_Y_RATIO_LOWER, FHOLE_CP2_Y_RATIO_LOWER,
    FHOLE_PAIR_OFFSET_RATIO,
)
from core.models import (
    Point, Line, Arc, CubicBezier, ClosedPath, ClosedHole, CircleHole,
    Hole, SoundHoleResult, SoundHoleType, SoundHoleOrientation,
    InstrumentConfig,
)
from core.trapezoid import TrapezoidGeometry
from core.utils import nearly_equal
from core.radii import corner_arc_segments


# ── Helmholtz core ─────────────────────────────────────────────────────────────

def helmholtz_freq_round(V_mm3: float, diameter_mm: float, top_thickness_mm: float) -> float:
    """Frequency for a round hole: f = (c/2π) × √(A / (V × L_eff))."""
    L_eff = top_thickness_mm + HELMHOLTZ_L_EFF_FACTOR * diameter_mm
    A     = math.pi * (diameter_mm / 2) ** 2
    return SPEED_OF_SOUND_MM_S / (2 * math.pi) * math.sqrt(A / (V_mm3 * L_eff))


def helmholtz_freq_arbitrary(V_mm3: float, area_mm2: float, D_eq_mm: float,
                              top_thickness_mm: float) -> float:
    """Frequency for arbitrary hole shape using equivalent diameter for L_eff."""
    L_eff = top_thickness_mm + HELMHOLTZ_L_EFF_FACTOR * D_eq_mm
    return SPEED_OF_SOUND_MM_S / (2 * math.pi) * math.sqrt(area_mm2 / (V_mm3 * L_eff))


def solve_diameter(target_hz: float, V_mm3: float, top_thickness_mm: float,
                   max_iter: int = HELMHOLTZ_MAX_ITERATIONS) -> tuple[float, int]:
    """Iterative solver for round-hole diameter.

    Convergence criterion: |D_new - D| < FLOAT_TOLERANCE.
    Returns (diameter, iterations).
    """
    c = SPEED_OF_SOUND_MM_S
    D = 50.0  # starting estimate
    for i in range(max_iter):
        L_eff = top_thickness_mm + HELMHOLTZ_L_EFF_FACTOR * D
        A = (target_hz * 2 * math.pi / c) ** 2 * V_mm3 * L_eff
        D_new = 2 * math.sqrt(A / math.pi)
        if abs(D_new - D) < FLOAT_TOLERANCE:
            return D_new, i + 1
        D = D_new
    return D, max_iter


def solve_area(target_hz: float, V_mm3: float, top_thickness_mm: float,
               max_iter: int = HELMHOLTZ_MAX_ITERATIONS) -> tuple[float, float, int]:
    """Iterative solver for arbitrary hole area and equivalent diameter.

    Returns (area_mm2, D_eq_mm, iterations).
    """
    c = SPEED_OF_SOUND_MM_S
    D_eq = 50.0
    for i in range(max_iter):
        L_eff = top_thickness_mm + HELMHOLTZ_L_EFF_FACTOR * D_eq
        A = (target_hz * 2 * math.pi / c) ** 2 * V_mm3 * L_eff
        D_new = 2 * math.sqrt(max(0.0, A) / math.pi)
        if abs(D_new - D_eq) < FLOAT_TOLERANCE:
            return A, D_new, i + 1
        D_eq = D_new
    A = (target_hz * 2 * math.pi / c) ** 2 * V_mm3 * (top_thickness_mm + HELMHOLTZ_L_EFF_FACTOR * D_eq)
    return A, D_eq, max_iter


# ── Top-level compute ──────────────────────────────────────────────────────────

def compute(config: InstrumentConfig, geom: TrapezoidGeometry) -> tuple[list[Hole], SoundHoleResult] | None:
    """Compute soundhole. Returns (holes, result) or None if no soundhole_type."""
    if config.soundhole_type is None:
        return None

    match config.soundhole_type:
        case SoundHoleType.ROUND:
            return _compute_round(config, geom)
        case SoundHoleType.FHOLE:
            return _compute_fhole(config, geom)
        case SoundHoleType.ROUNDED_TRAPEZOID:
            return _compute_rtrap(config, geom)


# ── Round hole ─────────────────────────────────────────────────────────────────

def _compute_round(config: InstrumentConfig, geom: TrapezoidGeometry) -> tuple[list[Hole], SoundHoleResult]:
    """Single circular soundhole, Helmholtz-tuned."""
    V   = geom.air_volume
    top = config.top_thickness
    target = config.helmholtz_freq

    if config.soundhole_diameter is not None:
        D = config.soundhole_diameter
        achieved = helmholtz_freq_round(V, D, top)
        iters = 0
    else:
        D, iters = solve_diameter(target, V, top)
        achieved = helmholtz_freq_round(V, D, top)

    # Position
    cx = geom.long_outer / 2
    neck_b = (config.neck_block_thickness if config.hardware else 0.0)
    cy = neck_b + config.neck_clearance + D / 2
    if config.soundhole_x is not None:
        cy = config.soundhole_x
    if config.soundhole_y is not None:
        cx = geom.long_outer / 2 + config.soundhole_y

    hole = CircleHole(centre=Point(cx, cy), diameter=D)
    A = math.pi * (D / 2) ** 2
    result = SoundHoleResult(
        type=SoundHoleType.ROUND,
        diameter_or_size_mm=D,
        open_area_mm2=A,
        target_freq_hz=target,
        achieved_freq_hz=achieved,
        iterations=iters,
    )
    return [hole], result


# ── F-hole ─────────────────────────────────────────────────────────────────────

def _compute_fhole(config: InstrumentConfig, geom: TrapezoidGeometry) -> tuple[list[Hole], SoundHoleResult]:
    """Paired f-holes, Helmholtz-tuned."""
    V   = geom.air_volume
    top = config.top_thickness
    target = config.helmholtz_freq

    if config.soundhole_size is not None:
        L_fh = config.soundhole_size
    else:
        # Solve for area, then derive L_fh from proportions
        A_target, D_eq, iters = solve_area(target, V, top)
        # For paired f-holes, area = 2 × single f-hole area
        # Single f-hole area ≈ L_fh × average_width × waist_factor (approximate)
        # Use L_fh such that total area ≈ A_target (simplified: L_fh = sqrt(A_target * 4 / pi))
        L_fh = math.sqrt(A_target * 4 / math.pi) * 2.5  # heuristic scaling

    # Hole positions
    cx = geom.long_outer / 2
    neck_b = config.neck_block_thickness if config.hardware else 0.0
    cy = neck_b + config.neck_clearance + L_fh / 2

    x_left  = cx - FHOLE_PAIR_OFFSET_RATIO * geom.short_outer
    x_right = cx + FHOLE_PAIR_OFFSET_RATIO * geom.short_outer

    holes: list[Hole] = []
    for x_centre in [x_left, x_right]:
        holes.append(_make_fhole_shape(x_centre, cy, L_fh))

    A_total = 2 * _fhole_area(L_fh)
    D_eq = 2 * math.sqrt(A_total / math.pi)
    achieved = helmholtz_freq_arbitrary(V, A_total, D_eq, top)

    result = SoundHoleResult(
        type=SoundHoleType.FHOLE,
        diameter_or_size_mm=L_fh,
        open_area_mm2=A_total,
        target_freq_hz=target,
        achieved_freq_hz=achieved,
        iterations=0,
    )
    return holes, result


def _fhole_area(L_fh: float) -> float:
    """Approximate area of a single f-hole."""
    upper_d = FHOLE_UPPER_EYE_D_RATIO * L_fh
    lower_d = FHOLE_LOWER_EYE_D_RATIO * L_fh
    waist_w = FHOLE_WAIST_RATIO * upper_d
    shaft_len = L_fh * (FHOLE_LOWER_EYE_Y_RATIO - FHOLE_UPPER_EYE_Y_RATIO)
    eye_area = math.pi * (upper_d/2)**2 + math.pi * (lower_d/2)**2
    shaft_area = waist_w * shaft_len
    return eye_area + shaft_area


def _make_fhole_shape(x: float, y_centre: float, L_fh: float) -> ClosedHole:
    """Build a single f-hole as one continuous closed outline.

    CW traversal: top-of-upper-eye → right side of upper eye → right shaft wall
    → large CW arc around lower eye → left shaft wall → left side of upper eye → close.

    CW arcs are used throughout so the outline traces the exterior of the shape.
    Shaft width = FHOLE_WAIST_RATIO × upper eye diameter.
    """
    y_top = y_centre - L_fh / 2
    uy    = y_top + FHOLE_UPPER_EYE_Y_RATIO * L_fh
    ur    = FHOLE_UPPER_EYE_D_RATIO * L_fh / 2
    ly    = y_top + FHOLE_LOWER_EYE_Y_RATIO * L_fh
    lr    = FHOLE_LOWER_EYE_D_RATIO * L_fh / 2

    shaft_half_w = min(FHOLE_WAIST_RATIO * ur, ur * 0.95, lr * 0.95)

    # Vertical clearance at junction circles
    ur_gap = math.sqrt(max(0.0, ur**2 - shaft_half_w**2))
    lr_gap = math.sqrt(max(0.0, lr**2 - shaft_half_w**2))

    ue_t     = Point(x,                 uy - ur)      # top of upper eye
    ue_r_jct = Point(x + shaft_half_w,  uy + ur_gap)  # upper eye, right shaft junction
    ue_l_jct = Point(x - shaft_half_w,  uy + ur_gap)  # upper eye, left shaft junction
    le_r_jct = Point(x + shaft_half_w,  ly - lr_gap)  # lower eye, right shaft junction
    le_l_jct = Point(x - shaft_half_w,  ly - lr_gap)  # lower eye, left shaft junction

    # Both eye junctions are in the upper half of the lower eye circle → large arc
    # (goes CW from upper-right, down right side, around bottom, up left side)
    segs = [
        Arc(ue_t,     ue_r_jct, ur, False, True),  # CW: top → right junction (upper eye)
        Line(ue_r_jct, le_r_jct),                   # right shaft wall
        Arc(le_r_jct, le_l_jct, lr, True,  True),  # CW large arc around lower eye
        Line(le_l_jct, ue_l_jct),                   # left shaft wall
        Arc(ue_l_jct, ue_t,     ur, False, True),  # CW: left junction → top (upper eye)
    ]
    return ClosedHole(path=ClosedPath(tuple(segs)))


# ── Rounded-trapezoid hole ─────────────────────────────────────────────────────

def _compute_rtrap(config: InstrumentConfig, geom: TrapezoidGeometry) -> tuple[list[Hole], SoundHoleResult]:
    """Rounded-trapezoid soundhole, Helmholtz-tuned."""
    lo = geom.long_outer
    so = geom.short_outer
    top = config.top_thickness
    V   = geom.air_volume
    target = config.helmholtz_freq

    # Dimensions
    long_ratio = config.soundhole_long_ratio if config.soundhole_long_ratio is not None else RTRAP_LONG_TO_BODY_RATIO
    aspect     = config.soundhole_aspect     if config.soundhole_aspect is not None     else RTRAP_ASPECT_RATIO
    r_mm       = config.soundhole_r_mm       if config.soundhole_r_mm is not None       else RTRAP_CORNER_R_MM

    if config.soundhole_size is not None:
        h_long = config.soundhole_size
    else:
        h_long = lo * long_ratio

    h_short  = h_long * (so / lo)   # inherit body taper ratio
    h_height = h_long * aspect

    # Acoustic area
    A = (h_long + h_short) / 2 * h_height - 4 * r_mm**2 * (1 - math.pi / 4)
    D_eq = 2 * math.sqrt(max(0.0, A) / math.pi)
    achieved = helmholtz_freq_arbitrary(V, A, D_eq, top)

    # Positioning
    cx = lo / 2
    neck_b = config.neck_block_thickness if config.hardware else 0.0
    y_near = neck_b + config.neck_clearance
    if config.soundhole_x is not None:
        y_near = config.soundhole_x
    if config.soundhole_y is not None:
        cx = lo / 2 + config.soundhole_y

    # Orientation
    flipped = (config.soundhole_orientation == SoundHoleOrientation.FLIPPED)

    hole_path = _build_rtrap_path(h_long, h_short, h_height, r_mm, cx, y_near, flipped)
    hole = ClosedHole(path=hole_path)

    result = SoundHoleResult(
        type=SoundHoleType.ROUNDED_TRAPEZOID,
        diameter_or_size_mm=h_long,
        open_area_mm2=A,
        target_freq_hz=target,
        achieved_freq_hz=achieved,
        iterations=0,
    )
    return [hole], result


def _build_rtrap_path(h_long: float, h_short: float, h_height: float,
                       r: float, cx: float, y_near: float,
                       flipped: bool = False) -> ClosedPath:
    """Build a ClosedPath for a rounded-trapezoid hole.

    SAME (flipped=False): narrow end at top (y_near), wide at bottom.
      TL/TR = narrow-end corners = obtuse = 90 + leg_angle
      BL/BR = wide-end corners   = acute  = 90 - leg_angle

    FLIPPED (flipped=True): wide end at top (y_near), narrow at bottom.
      TL/TR = wide-end corners   = acute  = 90 - leg_angle
      BL/BR = narrow-end corners = obtuse = 90 + leg_angle
    """
    y_far = y_near + h_height
    h_inset = (h_long - h_short) / 2
    leg_angle_deg = math.degrees(math.atan2(h_inset, h_height))
    h_obtuse = 90.0 + leg_angle_deg
    h_acute  = 90.0 - leg_angle_deg

    if not flipped:
        # SAME: narrow top, wide bottom
        HTL = Point(cx - h_short / 2, y_near)
        HTR = Point(cx + h_short / 2, y_near)
        HBR = Point(cx + h_long  / 2, y_far)
        HBL = Point(cx - h_long  / 2, y_far)
        angle_TL = h_obtuse; angle_TR = h_obtuse
        angle_BR = h_acute;  angle_BL = h_acute
    else:
        # FLIPPED: wide top, narrow bottom
        HTL = Point(cx - h_long  / 2, y_near)
        HTR = Point(cx + h_long  / 2, y_near)
        HBR = Point(cx + h_short / 2, y_far)
        HBL = Point(cx - h_short / 2, y_far)
        angle_TL = h_acute;  angle_TR = h_acute
        angle_BR = h_obtuse; angle_BL = h_obtuse

    def unit(a: Point, b: Point) -> Point:
        dx = b.x - a.x; dy = b.y - a.y
        m = math.sqrt(dx*dx + dy*dy)
        return Point(dx/m, dy/m)

    # Edge directions (clockwise traversal for hole: HTL→HTR→HBR→HBL→HTL)
    # For hole path (CCW winding per spec §26): HTL→HBL→HBR→HTR→HTL
    # Use clockwise traversal internally then the winding comes from arc direction.
    # Build CW and use CCW arcs (sweep=0) to get CCW hole path.

    # CW vertex order: HTL → HTR → HBR → HBL → (back to HTL)
    # Corner arc at HTL: arriving from HBL, departing toward HTR
    d_bl_tl = unit(HBL, HTL)
    d_tl_tr = unit(HTL, HTR)
    d_tr_br = unit(HTR, HBR)
    d_br_bl = unit(HBR, HBL)

    def arc_at(vertex, arr, dep, angle_deg) -> tuple[Point, Arc, Point]:
        td = r / math.tan(math.radians(angle_deg / 2))
        arc_s = Point(vertex.x - arr.x * td, vertex.y - arr.y * td)
        arc_e = Point(vertex.x + dep.x * td, vertex.y + dep.y * td)
        # CW arc: center inside hole, bows toward corner vertex — correct rounding.
        # CCW arc (False,False) bows toward hole center = biscuit at corner.
        arc = Arc(arc_s, arc_e, r, False, True)
        return arc_s, arc, arc_e

    a_TL = arc_at(HTL, d_bl_tl, d_tl_tr, angle_TL)
    a_TR = arc_at(HTR, d_tl_tr, d_tr_br, angle_TR)
    a_BR = arc_at(HBR, d_tr_br, d_br_bl, angle_BR)
    a_BL = arc_at(HBL, d_br_bl, d_bl_tl, angle_BL)

    segs: list = []
    corners = [a_TL, a_TR, a_BR, a_BL]
    for i in range(4):
        arc_s_i, arc_i, arc_e_i = corners[i]
        arc_s_next, _, _ = corners[(i + 1) % 4]

        # Arc at this corner
        segs.append(arc_i)
        # Line to next corner's arc start
        if not (nearly_equal(arc_e_i.x, arc_s_next.x) and nearly_equal(arc_e_i.y, arc_s_next.y)):
            segs.append(Line(arc_e_i, arc_s_next))

    # Close
    first_s = _seg_start(segs[0])
    last_e  = _seg_end(segs[-1])
    if not (nearly_equal(first_s.x, last_e.x) and nearly_equal(first_s.y, last_e.y)):
        segs.append(Line(last_e, first_s))

    return ClosedPath(tuple(segs))


def _seg_start(seg) -> Point:
    match seg:
        case Line(start=s): return s
        case Arc(start=s):  return s
        case CubicBezier(start=s): return s


def _seg_end(seg) -> Point:
    match seg:
        case Line(end=e): return e
        case Arc(end=e):  return e
        case CubicBezier(end=e): return e
