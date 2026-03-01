"""
box/panels.py — Box mode Panel assembly.

# WINDING CONVENTION: All panel outlines and FingerEdge directions follow
# clockwise winding in SVG coordinate space (Y increases downward).
# Outward for a FingerEdge = 90° clockwise from edge direction in SVG Y-down space.

# v1 isosceles: WALL_LEG_RIGHT = dataclasses.replace(leg_left, type=WALL_LEG_RIGHT, name="WALL_LEG_RIGHT").
# No mirroring needed.
# mirror_path_horizontal + reverse_path in transform.py is provided for future v2 general trapezoid.

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

from constants import TEST_STRIP_WIDTH_MM, AUTO_FINGER_WIDTH_FACTOR
from core.models import (
    Panel, PanelType, Point, Line, Arc, ClosedPath,
    FingerEdge, FingerDirection, Mark, MarkType,
    BoxConfig, LidType,
)
from core.trapezoid import TrapezoidGeometry
from core.radii import corner_arc_segments
from core.joints import (
    make_finger_edge, make_finger_edge_angled,
    build_panel_outline_straight_corners, build_plain_outline,
)
from box import lids


def build(config: BoxConfig, geom: TrapezoidGeometry, radius: float) -> list[Panel]:
    """Build all box mode panels.

    All box mode panels: fingers protrude INWARD (hardcoded, not configurable).
    """
    t   = geom.thickness
    c   = config.common
    burn = c.burn
    tol  = c.tolerance

    # In box mode all fingers are INWARD (protrude_outward=False)
    protrude_outward = False

    panels: list[Panel] = []
    panels.append(_make_base(geom, radius, protrude_outward, burn, tol))
    panels.extend(_make_walls(geom, radius, protrude_outward, burn, tol))
    panels.append(_make_test_strip(geom, radius, protrude_outward, burn, tol))

    # Lid
    lid_panel = lids.make_lid(config, geom, radius, burn, tol)
    if lid_panel is not None:
        panels.append(lid_panel)

    return panels


def _make_base(geom: TrapezoidGeometry, radius: float,
               protrude_outward: bool, burn: float, tol: float) -> Panel:
    """BASE — trapezoid with finger tabs on all four edges. Corner radii applied."""
    t  = geom.thickness
    lo = geom.long_outer
    so = geom.short_outer
    L  = geom.length_outer
    li = geom.leg_inset
    la = geom.leg_angle_deg
    lea = geom.long_end_angle_deg   # interior angle at long/narrow end (TL, TR)
    sea = geom.short_end_angle_deg  # interior angle at short/wide end  (BL, BR)
    ll  = geom.leg_length

    # Panel corners — short at top (TL/TR), long at bottom (BL/BR)
    TL = Point(li,      0.0)
    TR = Point(li + so, 0.0)
    BR = Point(lo,      L)
    BL = Point(0.0,     L)

    # Leg direction vectors (unit)
    leg_ax =  math.sin(math.radians(la))
    leg_ay =  math.cos(math.radians(la))

    # Edge directions (clockwise: BL→TL→TR→BR→BL)
    # TL corner: arriving from BL (direction: -leg_ax, -leg_ay toward TL)
    #            departing toward TR (direction: +1, 0)
    # TR corner: arriving from TL (direction: +1, 0)
    #            departing toward BR (direction: +leg_ax, +leg_ay)
    # BR corner: arriving from TR  (direction: +leg_ax, +leg_ay)
    #            departing toward BL (direction: -1, 0)
    # BL corner: arriving from BR  (direction: -1, 0)
    #            departing toward TL (direction: -leg_ax, -leg_ay)

    # Corner arcs — computed for finger zone boundary markers (etch only, not cut)
    _, arc_TL, _ = corner_arc_segments(TL,
        Point(leg_ax, -leg_ay), Point(1.0, 0.0), radius, lea)
    _, arc_TR, _ = corner_arc_segments(TR,
        Point(1.0, 0.0), Point(leg_ax, leg_ay), radius, lea)
    _, arc_BR, _ = corner_arc_segments(BR,
        Point(leg_ax, leg_ay), Point(-1.0, 0.0), radius, sea)
    _, arc_BL, _ = corner_arc_segments(BL,
        Point(-1.0, 0.0), Point(-leg_ax, -leg_ay), radius, sea)

    # BASE edges: tabs. Walls have slots. Finger depth = wall thickness.
    e_short = make_finger_edge(
        TL, TR, t, t, protrude_outward, False,
        burn, tol, radius, radius, lea, lea)
    e_leg_r = make_finger_edge_angled(
        TR, BR, t, t, protrude_outward, False,
        burn, tol, radius, radius, lea, sea, la)
    e_long = make_finger_edge(
        BR, BL, t, t, protrude_outward, False,
        burn, tol, radius, radius, sea, sea)
    e_leg_l = make_finger_edge_angled(
        BL, TL, t, t, protrude_outward, False,
        burn, tol, radius, radius, sea, lea, la)

    edges = [e_short, e_leg_r, e_long, e_leg_l]
    # Straight trapezoid outline; corner arcs are etch marks only
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(lo / 2, L / 2), "", 0.0),
        Mark(MarkType.ASSEMBLY_NUM, Point(lo / 2, L / 2 + 10), "1", 0.0),
        Mark(MarkType.LABEL, Point(li + so / 2, L / 2 - 5), "BASE", 0.0),
    ]

    return Panel(
        type=PanelType.BASE, name="BASE",
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[arc_TL, arc_TR, arc_BR, arc_BL],
        marks=marks,
        grain_angle_deg=0.0,
        width=lo, height=L,
    )


def _make_walls(geom: TrapezoidGeometry, radius: float,
                protrude_outward: bool, burn: float, tol: float) -> list[Panel]:
    """Build WALL_LONG, WALL_SHORT, WALL_LEG_LEFT, WALL_LEG_RIGHT."""
    t  = geom.thickness
    lo = geom.long_outer
    so = geom.short_outer
    d  = geom.depth_outer
    la = geom.leg_angle_deg
    ll = geom.leg_length
    lea = geom.long_end_angle_deg
    sea = geom.short_end_angle_deg

    walls = []

    # ── WALL_LONG (rectangle lo × d) ──────────────────────────────────────────
    # Slots on bottom (mates with BASE long_bottom), slots on top (mates with lid).
    # Fingers on left/right ends (wall-to-wall joints, 90°).
    walls.append(_make_rect_wall(
        PanelType.WALL_LONG, "WALL_LONG", lo, d, t,
        radius, protrude_outward, burn, tol,
        # bottom slots (mates with BASE), top slots (mates with lid)
        bottom_slotted=True, top_slotted=True,
        asm_num="2",
    ))

    # ── WALL_SHORT (rectangle so × d) ─────────────────────────────────────────
    walls.append(_make_rect_wall(
        PanelType.WALL_SHORT, "WALL_SHORT", so, d, t,
        radius, protrude_outward, burn, tol,
        bottom_slotted=True, top_slotted=True,
        asm_num="3",
    ))

    # ── WALL_LEG_LEFT (rectangle ll × d) ──────────────────────────────────────
    leg_left = _make_leg_wall(
        PanelType.WALL_LEG_LEFT, "WALL_LEG_LEFT", ll, d, t,
        radius, protrude_outward, burn, tol, la, asm_num="4",
    )
    walls.append(leg_left)

    # ── WALL_LEG_RIGHT — isosceles: copy of leg_left ──────────────────────────
    leg_right = dataclasses.replace(
        leg_left, type=PanelType.WALL_LEG_RIGHT, name="WALL_LEG_RIGHT",
        marks=[dataclasses.replace(m, content="5") if m.type == MarkType.ASSEMBLY_NUM
               else m for m in leg_left.marks],
    )
    walls.append(leg_right)

    return walls


def _make_rect_wall(
    ptype: PanelType, name: str,
    width: float, height: float, thickness: float,
    radius: float, protrude_outward: bool,
    burn: float, tol: float,
    bottom_slotted: bool, top_slotted: bool,
    asm_num: str = "",
) -> Panel:
    """Build a rectangular wall panel."""
    w, h, t = width, height, thickness

    TL = Point(0.0, 0.0)
    TR = Point(w,   0.0)
    BR = Point(w,   h)
    BL = Point(0.0, h)

    # Wall panels: plain rectangles — no corner arcs (cut or etch).
    # radius=0 → full depth_outer available for wall-to-wall finger zone.
    e_top = make_finger_edge(
        TL, TR, t, t, protrude_outward, top_slotted,
        burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right = make_finger_edge(
        TR, BR, t, t, protrude_outward, False,
        burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_bottom = make_finger_edge(
        BR, BL, t, t, protrude_outward, bottom_slotted,
        burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_left = make_finger_edge(
        BL, TL, t, t, protrude_outward, False,
        burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(w / 2, h / 2), "", 0.0),
    ]
    if asm_num:
        marks.append(Mark(MarkType.ASSEMBLY_NUM, Point(w / 2, h / 2 + 10), asm_num, 0.0))
    marks.append(Mark(MarkType.LABEL, Point(w / 2, h / 2 - 5), name, 0.0))

    return Panel(
        type=ptype, name=name,
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=w, height=h,
    )


def _make_leg_wall(
    ptype: PanelType, name: str,
    width: float, height: float, thickness: float,
    radius: float, protrude_outward: bool,
    burn: float, tol: float, leg_angle_deg: float,
    asm_num: str = "",
) -> Panel:
    """Build a leg wall panel (bottom edge uses angled joint correction)."""
    w, h, t = width, height, thickness

    TL = Point(0.0, 0.0)
    TR = Point(w,   0.0)
    BR = Point(w,   h)
    BL = Point(0.0, h)

    # Wall panels: plain rectangles — no corner arcs (cut or etch). radius=0.
    e_top    = make_finger_edge(TL, TR, t, t, protrude_outward, True,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right  = make_finger_edge(TR, BR, t, t, protrude_outward, False,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)
    # Bottom edge: angled joint correction (mates with BASE leg edge)
    e_bottom = make_finger_edge_angled(BR, BL, t, t, protrude_outward, True,
                                       burn, tol, 0.0, 0.0, 90.0, 90.0,
                                       leg_angle_deg)
    e_left   = make_finger_edge(BL, TL, t, t, protrude_outward, False,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks = [
        Mark(MarkType.GRAIN_ARROW, Point(w / 2, h / 2), "", 0.0),
    ]
    if asm_num:
        marks.append(Mark(MarkType.ASSEMBLY_NUM, Point(w / 2, h / 2 + 10), asm_num, 0.0))
    marks.append(Mark(MarkType.LABEL, Point(w / 2, h / 2 - 5), name, 0.0))

    return Panel(
        type=ptype, name=name,
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=w, height=h,
    )


def _make_test_strip(geom: TrapezoidGeometry, radius: float,
                     protrude_outward: bool, burn: float, tol: float) -> Panel:
    """TEST_STRIP — 60mm × (3 × depth). One edge matches WALL_LONG bottom joint profile."""
    t  = geom.thickness
    d  = geom.depth_outer
    w  = TEST_STRIP_WIDTH_MM
    h  = 3.0 * d

    TL = Point(0.0, 0.0)
    TR = Point(w,   0.0)
    BR = Point(w,   h)
    BL = Point(0.0, h)

    # TEST_STRIP: plain rectangle, no corner arcs. radius=0.
    e_top    = make_finger_edge(TL, TR, t, t, protrude_outward, True,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_right  = make_finger_edge(TR, BR, t, t, protrude_outward, False,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_bottom = make_finger_edge(BR, BL, t, t, protrude_outward, True,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)
    e_left   = make_finger_edge(BL, TL, t, t, protrude_outward, False,
                                burn, tol, 0.0, 0.0, 90.0, 90.0)

    edges = [e_top, e_right, e_bottom, e_left]
    outline = build_panel_outline_straight_corners(edges, [TL, TR, BR, BL])

    marks = [
        Mark(MarkType.LABEL, Point(w / 2, h / 2), "TEST STRIP", 0.0),
    ]

    return Panel(
        type=PanelType.TEST_STRIP, name="TEST_STRIP",
        outline=outline, finger_edges=edges,
        holes=[], score_lines=[],
        finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=w, height=h,
    )
