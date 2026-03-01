"""
instrument/panels.py — Instrument mode Panel assembly.

# WINDING CONVENTION: All panel outlines and FingerEdge directions follow
# clockwise winding in SVG coordinate space (Y increases downward).
# Outward for a FingerEdge = 90° clockwise from edge direction in SVG Y-down space.

# v1 isosceles: WALL_LEG_RIGHT = dataclasses.replace(leg_left, ...).
# No mirroring needed.
# mirror_path_horizontal + reverse_path in transform.py provided for future v2.

# Internal angle mapping for make_finger_edge() on BASE/SOUNDBOARD:
# Edge          | left corner (start)   | right corner (end)
# short_top     | long_end_angle_deg    | long_end_angle_deg
# leg_right     | long_end_angle_deg    | short_end_angle_deg
# long_bottom   | short_end_angle_deg   | short_end_angle_deg
# leg_left      | short_end_angle_deg   | long_end_angle_deg
"""

from __future__ import annotations
import dataclasses
import math

from constants import TEST_STRIP_WIDTH_MM
from core.models import (
    Panel, PanelType, Point, Line, ClosedPath,
    FingerEdge, FingerDirection, Mark, MarkType,
    InstrumentConfig,
)
from core.trapezoid import TrapezoidGeometry
from core.radii import corner_arc_segments
from core.joints import (
    make_finger_edge, make_finger_edge_angled,
    build_panel_outline_straight_corners, build_plain_outline,
)
from instrument import hardware, kerfing, marks


def build(config: InstrumentConfig, geom: TrapezoidGeometry, radius: float) -> list[Panel]:
    """Build all instrument mode panels."""
    protrude_outward = (config.finger_direction == FingerDirection.OUTWARD)
    t    = geom.thickness
    burn = config.common.burn
    tol  = config.common.tolerance

    panels: list[Panel] = []

    panels.append(_make_base(geom, radius, protrude_outward, burn, tol))
    panels.extend(_make_walls(geom, radius, protrude_outward, burn, tol))
    panels.append(_make_soundboard(config, geom, radius))
    panels.append(_make_test_strip(geom, radius, protrude_outward, burn, tol))

    if config.hardware:
        panels.append(hardware.make_neck_block(config, geom))
        panels.append(hardware.make_tail_block(config, geom))

    if config.kerfing:
        panels.extend(kerfing.make_base_kerf_strips(config, geom))
        panels.extend(kerfing.make_soundboard_kerf_strips(config, geom))
        panels.extend(kerfing.make_kerf_fillets(config, geom))

    # Apply brace score lines and scale mark to SOUNDBOARD
    panels = _apply_soundboard_marks(panels, config, geom)

    # Add assembly numbers
    panels = marks.add_assembly_marks(panels)

    return panels


def _make_base(geom: TrapezoidGeometry, radius: float,
               protrude_outward: bool, burn: float, tol: float) -> Panel:
    """BASE trapezoid with finger joints all four edges."""
    t  = geom.thickness
    lo = geom.long_outer; so = geom.short_outer
    L  = geom.length_outer; li = geom.leg_inset
    la = geom.leg_angle_deg
    lea = geom.long_end_angle_deg; sea = geom.short_end_angle_deg

    TL = Point(li,      0.0)
    TR = Point(li + so, 0.0)
    BR = Point(lo,      L)
    BL = Point(0.0,     L)

    leg_ax = math.sin(math.radians(la))
    leg_ay = math.cos(math.radians(la))

    # Corner arcs — etch marks only (non-cut), stored in finger_zone_boundaries
    _, arc_TL, _ = corner_arc_segments(TL, Point(leg_ax, -leg_ay), Point(1.0, 0.0),  radius, lea)
    _, arc_TR, _ = corner_arc_segments(TR, Point(1.0, 0.0), Point(leg_ax, leg_ay),   radius, lea)
    _, arc_BR, _ = corner_arc_segments(BR, Point(leg_ax, leg_ay), Point(-1.0, 0.0),  radius, sea)
    _, arc_BL, _ = corner_arc_segments(BL, Point(-1.0, 0.0), Point(-leg_ax, -leg_ay), radius, sea)

    e_short = make_finger_edge(TL, TR, t, t, protrude_outward, False,
                               burn, tol, radius, radius, lea, lea)
    e_leg_r = make_finger_edge_angled(TR, BR, t, t, protrude_outward, False,
                                      burn, tol, radius, radius, lea, sea, la)
    e_long  = make_finger_edge(BR, BL, t, t, protrude_outward, False,
                               burn, tol, radius, radius, sea, sea)
    e_leg_l = make_finger_edge_angled(BL, TL, t, t, protrude_outward, False,
                                      burn, tol, radius, radius, sea, lea, la)

    edges = [e_short, e_leg_r, e_long, e_leg_l]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks_list = [
        Mark(MarkType.GRAIN_ARROW, Point(lo / 2, L / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(li + so / 2, L / 2 - 5), "BASE", 0.0),
    ]

    return Panel(
        type=PanelType.BASE, name="BASE",
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[arc_TL, arc_TR, arc_BR, arc_BL],
        marks=marks_list,
        grain_angle_deg=0.0,
        width=lo, height=L,
    )


def _make_walls(geom: TrapezoidGeometry, radius: float,
                protrude_outward: bool, burn: float, tol: float) -> list[Panel]:
    """Build WALL_LONG, WALL_SHORT, WALL_LEG_LEFT, WALL_LEG_RIGHT."""
    t  = geom.thickness
    lo = geom.long_outer; so = geom.short_outer
    d  = geom.depth_outer; la = geom.leg_angle_deg; ll = geom.leg_length

    panels = []

    # WALL_LONG
    panels.append(_rect_wall(PanelType.WALL_LONG, "WALL_LONG", lo, d, t,
                              radius, protrude_outward, burn, tol))
    # WALL_SHORT
    panels.append(_rect_wall(PanelType.WALL_SHORT, "WALL_SHORT", so, d, t,
                              radius, protrude_outward, burn, tol))
    # WALL_LEG_LEFT
    leg_left = _leg_wall(PanelType.WALL_LEG_LEFT, "WALL_LEG_LEFT", ll, d, t,
                          radius, protrude_outward, burn, tol, la)
    panels.append(leg_left)
    # WALL_LEG_RIGHT: isosceles copy — fix label text copied from leg_left
    from core.models import MarkType
    fixed_marks = [
        dataclasses.replace(m, content="WALL_LEG_RIGHT")
        if m.type == MarkType.LABEL else m
        for m in leg_left.marks
    ]
    leg_right = dataclasses.replace(
        leg_left, type=PanelType.WALL_LEG_RIGHT, name="WALL_LEG_RIGHT",
        marks=fixed_marks)
    panels.append(leg_right)

    return panels


def _rect_wall(ptype, name, width, height, t, radius, protrude_outward, burn, tol) -> Panel:
    w, h = width, height
    TL = Point(0.0, 0.0); TR = Point(w, 0.0)
    BR = Point(w, h);     BL = Point(0.0, h)

    # Wall panels: plain rectangles — no corner arcs. radius=0.
    e_top    = make_finger_edge(TL, TR, t, t, protrude_outward, True,  burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right  = make_finger_edge(TR, BR, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_bottom = make_finger_edge(BR, BL, t, t, protrude_outward, True,  burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_left   = make_finger_edge(BL, TL, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks_list = [
        Mark(MarkType.GRAIN_ARROW, Point(w / 2, h / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(w / 2, h / 2 - 5), name, 0.0),
    ]
    return Panel(type=ptype, name=name, outline=outline, finger_edges=edges,
                 holes=[], score_lines=[], finger_zone_boundaries=[],
                 marks=marks_list, grain_angle_deg=0.0, width=w, height=h)


def _leg_wall(ptype, name, width, height, t, radius, protrude_outward, burn, tol, la) -> Panel:
    w, h = width, height
    TL = Point(0.0, 0.0); TR = Point(w, 0.0)
    BR = Point(w, h);     BL = Point(0.0, h)

    # Wall panels: plain rectangles — no corner arcs. radius=0.
    e_top    = make_finger_edge(TL, TR, t, t, protrude_outward, True,  burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right  = make_finger_edge(TR, BR, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_bottom = make_finger_edge_angled(BR, BL, t, t, protrude_outward, True,
                                       burn, tol, 0.0, 0.0, 90.0, 90.0, la)
    e_left   = make_finger_edge(BL, TL, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks_list = [
        Mark(MarkType.GRAIN_ARROW, Point(w / 2, h / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(w / 2, h / 2 - 5), name, 0.0),
    ]
    return Panel(type=ptype, name=name, outline=outline, finger_edges=edges,
                 holes=[], score_lines=[], finger_zone_boundaries=[],
                 marks=marks_list, grain_angle_deg=0.0, width=w, height=h)


def _make_soundboard(config: InstrumentConfig, geom: TrapezoidGeometry, radius: float) -> Panel:
    """SOUNDBOARD — trapezoid, NO finger joints, straight outline + corner arc etch marks."""
    lo = geom.long_outer; so = geom.short_outer
    L  = geom.length_outer; li = geom.leg_inset
    la = geom.leg_angle_deg
    lea = geom.long_end_angle_deg; sea = geom.short_end_angle_deg

    TL = Point(li,      0.0)
    TR = Point(li + so, 0.0)
    BR = Point(lo,      L)
    BL = Point(0.0,     L)

    leg_ax = math.sin(math.radians(la))
    leg_ay = math.cos(math.radians(la))

    # Straight trapezoid outline (radius=0)
    outline = build_plain_outline([TL, TR, BR, BL], 0.0, [lea, lea, sea, sea])

    # Corner arc etch marks (non-cut), matching BASE
    _, arc_TL, _ = corner_arc_segments(TL, Point(leg_ax, -leg_ay), Point(1.0, 0.0),  radius, lea)
    _, arc_TR, _ = corner_arc_segments(TR, Point(1.0, 0.0), Point(leg_ax, leg_ay),   radius, lea)
    _, arc_BR, _ = corner_arc_segments(BR, Point(leg_ax, leg_ay), Point(-1.0, 0.0),  radius, sea)
    _, arc_BL, _ = corner_arc_segments(BL, Point(-1.0, 0.0), Point(-leg_ax, -leg_ay), radius, sea)

    marks_list = [
        Mark(MarkType.GRAIN_ARROW, Point(lo / 2, L / 2), "", 0.0),
        Mark(MarkType.LABEL, Point(li + so / 2, L / 2 - 5), "SOUNDBOARD", 0.0),
    ]

    return Panel(
        type=PanelType.SOUNDBOARD, name="SOUNDBOARD",
        outline=outline, finger_edges=[],
        holes=[], score_lines=[],
        finger_zone_boundaries=[arc_TL, arc_TR, arc_BR, arc_BL],
        marks=marks_list,
        grain_angle_deg=0.0,
        width=lo, height=L,
    )


def _make_test_strip(geom: TrapezoidGeometry, radius: float,
                     protrude_outward: bool, burn: float, tol: float) -> Panel:
    """TEST_STRIP — 60mm × (3 × depth). Plain rectangle, no corner arcs."""
    t = geom.thickness; d = geom.depth_outer
    w = TEST_STRIP_WIDTH_MM; h = 3.0 * d

    TL = Point(0.0, 0.0); TR = Point(w, 0.0)
    BR = Point(w, h);     BL = Point(0.0, h)

    e_top    = make_finger_edge(TL, TR, t, t, protrude_outward, True,  burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right  = make_finger_edge(TR, BR, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_bottom = make_finger_edge(BR, BL, t, t, protrude_outward, True,  burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_left   = make_finger_edge(BL, TL, t, t, protrude_outward, False, burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks_list = [Mark(MarkType.LABEL, Point(w / 2, h / 2), "TEST STRIP", 0.0)]
    return Panel(type=PanelType.TEST_STRIP, name="TEST_STRIP",
                 outline=outline, finger_edges=edges,
                 holes=[], score_lines=[], finger_zone_boundaries=[],
                 marks=marks_list, grain_angle_deg=0.0, width=w, height=h)


def _apply_soundboard_marks(panels: list[Panel], config: InstrumentConfig,
                             geom: TrapezoidGeometry) -> list[Panel]:
    """Apply brace lines and scale mark to SOUNDBOARD panel."""
    result = []
    for p in panels:
        if p.type == PanelType.SOUNDBOARD:
            if config.braces:
                p = marks.add_brace_score_lines(p, geom)
            if config.scale_length is not None:
                p = marks.add_scale_mark(p, geom, config.scale_length)
        result.append(p)
    return result
