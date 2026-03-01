"""
box/lids.py — Lid geometry for box mode (lift-off, sliding, hinged, flap).
"""

from __future__ import annotations
import dataclasses
import math

from constants import DEFAULT_HINGE_DIAMETER_MM, HINGE_SPACING_MM
from core.models import (
    Panel, PanelType, Point, Line, Arc, CircleHole, Mark, MarkType,
    BoxConfig, LidType, ClosedPath,
)
from core.trapezoid import TrapezoidGeometry
from core.joints import (
    make_finger_edge, build_panel_outline_straight_corners, build_plain_outline,
)


def make_lid(
    config:   BoxConfig,
    geom:     TrapezoidGeometry,
    radius:   float,
    burn:     float,
    tol:      float,
) -> Panel | None:
    """Dispatch to lid type builder. Returns None for LidType.NONE."""
    match config.lid:
        case LidType.NONE:
            return None
        case LidType.LIFT_OFF:
            return _lift_off_lid(geom, radius, burn, tol)
        case LidType.SLIDING:
            return _sliding_lid(geom, radius, burn, tol)
        case LidType.HINGED:
            return _hinged_lid(geom, radius, burn, tol, config.hinge_diameter)
        case LidType.FLAP:
            return _flap_lid(geom, radius, burn, tol)


def _lift_off_lid(geom: TrapezoidGeometry, radius: float,
                  burn: float, tol: float) -> Panel:
    """Trapezoid lid matching BASE shape. Fingers on LID, slots on wall top edges."""
    t  = geom.thickness
    lo = geom.long_outer
    so = geom.short_outer
    L  = geom.length_outer
    li = geom.leg_inset
    la = geom.leg_angle_deg
    lea = geom.long_end_angle_deg
    sea = geom.short_end_angle_deg

    TL = Point(li,      0.0)
    TR = Point(li + so, 0.0)
    BR = Point(lo,      L)
    BL = Point(0.0,     L)

    leg_ax = math.sin(math.radians(la))
    leg_ay = math.cos(math.radians(la))

    # Lid: true trapezoid outline, straight edges — no corner arcs (cut or etch).
    # corner_radius = 2*burn*tan(angle/2) gives tangent_dist = 2*burn at each corner.
    protrude_outward = False  # box mode: fingers inward
    r_lea = 2 * burn * math.tan(math.radians(lea / 2))
    r_sea = 2 * burn * math.tan(math.radians(sea / 2))
    from core.joints import make_finger_edge_angled
    e_short = make_finger_edge(TL, TR, t, t, protrude_outward, False,
                               burn, tol, r_lea, r_lea, lea, lea)
    e_leg_r = make_finger_edge_angled(TR, BR, t, t, protrude_outward, False,
                                      burn, tol, r_lea, r_sea, lea, sea, la)
    e_long  = make_finger_edge(BR, BL, t, t, protrude_outward, False,
                               burn, tol, r_sea, r_sea, sea, sea)
    e_leg_l = make_finger_edge_angled(BL, TL, t, t, protrude_outward, False,
                                      burn, tol, r_sea, r_lea, sea, lea, la)

    edges = [e_short, e_leg_r, e_long, e_leg_l]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(lo / 2, L / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(li + so / 2, L / 2 - 5), "LID (lift-off)", 0.0),
    ]

    return Panel(
        type=PanelType.LID, name="LID",
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=lo, height=L,
    )


def _sliding_lid(geom: TrapezoidGeometry, radius: float,
                 burn: float, tol: float) -> Panel:
    """Sliding lid: panel that slides into grooves in both leg walls.

    Width = short_inner - 2*(thickness+tolerance).
    Spec §16.2: Panel width = short_outer + 2*(thickness+tolerance)? Let me check.
    Actually spec says: "Panel width = short_outer + 2*(thickness+tolerance)" — but the
    proof 03 says lid_width = short_inner - 2*(T+tol) = short_outer - 2*T - 2*(T+tol).
    The 06d_lid_width.svg proof shows: lid_w = short_inner - 2*(T+tol).
    Spec text "short_outer + 2*(T+tol)" looks like a typo — proof is the authority.
    """
    t  = geom.thickness
    lo = geom.long_outer
    so = geom.short_outer
    L  = geom.length_outer

    # Lid slides in the short-end direction
    # Width = short_inner - 2*(T+tol) (proof-verified, see proof 03 test 7)
    lid_w = geom.short_inner - 2 * (t + tol)
    lid_h = L  # full length

    TL = Point(0.0,   0.0)
    TR = Point(lid_w, 0.0)
    BR = Point(lid_w, lid_h)
    BL = Point(0.0,   lid_h)

    # Plain rectangular outline (no finger joints — sliding lid has no fingers)
    outline = build_plain_outline(
        [TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0]
    )

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(lid_w / 2, lid_h / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(lid_w / 2, lid_h / 2 - 5), "LID (sliding)", 0.0),
    ]

    return Panel(
        type=PanelType.LID, name="LID",
        outline=outline, finger_edges=[],
        holes=[], score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=lid_w, height=lid_h,
    )


def _hinged_lid(geom: TrapezoidGeometry, radius: float,
                burn: float, tol: float, hinge_diameter: float) -> Panel:
    """Trapezoid lid with barrel hinge holes."""
    t  = geom.thickness
    lo = geom.long_outer
    so = geom.short_outer
    L  = geom.length_outer
    li = geom.leg_inset
    la = geom.leg_angle_deg
    lea = geom.long_end_angle_deg
    sea = geom.short_end_angle_deg

    TL = Point(li,      0.0)
    TR = Point(li + so, 0.0)
    BR = Point(lo,      L)
    BL = Point(0.0,     L)

    leg_ax = math.sin(math.radians(la))
    leg_ay = math.cos(math.radians(la))

    # Lid: true trapezoid outline, straight edges — no corner arcs.
    # corner_radius = 2*burn*tan(angle/2) gives tangent_dist = 2*burn at each corner.
    protrude_outward = False
    r_lea = 2 * burn * math.tan(math.radians(lea / 2))
    r_sea = 2 * burn * math.tan(math.radians(sea / 2))
    from core.joints import make_finger_edge_angled
    e_short = make_finger_edge(TL, TR, t, t, protrude_outward, False,
                               burn, tol, r_lea, r_lea, lea, lea)
    e_leg_r = make_finger_edge_angled(TR, BR, t, t, protrude_outward, False,
                                      burn, tol, r_lea, r_sea, lea, sea, la)
    e_long  = make_finger_edge(BR, BL, t, t, protrude_outward, False,
                               burn, tol, r_sea, r_sea, sea, sea)
    e_leg_l = make_finger_edge_angled(BL, TL, t, t, protrude_outward, False,
                                      burn, tol, r_sea, r_lea, sea, lea, la)

    edges = [e_short, e_leg_r, e_long, e_leg_l]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    # Hinge holes: count = floor(long_outer / 80), min 2
    hinge_count = max(2, int(lo / HINGE_SPACING_MM))
    holes = []
    for i in range(hinge_count):
        hx = lo * (i + 1) / (hinge_count + 1)
        hy = t / 2  # near long edge
        holes.append(CircleHole(centre=Point(hx, hy), diameter=hinge_diameter))

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(lo / 2, L / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(li + so / 2, L / 2 - 5), "LID (hinged)", 0.0),
    ]

    return Panel(
        type=PanelType.LID, name="LID",
        outline=outline, finger_edges=edges,
        holes=holes, score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=lo, height=L,
    )


def _flap_lid(geom: TrapezoidGeometry, radius: float,
              burn: float, tol: float) -> Panel:
    """Flap lid: as hinged but without hinge holes. Score line along long edge."""
    panel = _hinged_lid(geom, radius, burn, tol, DEFAULT_HINGE_DIAMETER_MM)
    # Remove holes, add score line along long bottom edge
    lo = geom.long_outer
    L  = geom.length_outer
    score_line = Line(Point(0.0, L), Point(lo, L))
    marks = [m for m in panel.marks if "hinged" not in (m.content or "")]
    marks.append(Mark(MarkType.LABEL, Point(lo / 2 - 15, L / 2 - 5), "LID (flap)", 0.0))
    return dataclasses.replace(
        panel,
        holes=[],
        score_lines=[score_line],
        marks=marks,
    )
