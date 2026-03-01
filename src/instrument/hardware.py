"""
instrument/hardware.py — Neck block, tail block, strap pin holes.
"""

from __future__ import annotations

from core.models import (
    Panel, PanelType, Point, Mark, MarkType, InstrumentConfig,
)
from core.trapezoid import TrapezoidGeometry
from core.joints import build_plain_outline


def make_neck_block(config: InstrumentConfig, geom: TrapezoidGeometry) -> Panel:
    """Rectangle neck_block_thickness × depth_outer. Plain outline, no finger joints."""
    w = config.neck_block_thickness
    h = geom.depth_outer

    TL = Point(0.0, 0.0)
    TR = Point(w,   0.0)
    BR = Point(w,   h)
    BL = Point(0.0, h)

    outline = build_plain_outline([TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0])
    marks = [
        Mark(MarkType.LABEL, Point(w / 2, h / 2),
             "NECK BLOCK — glue inside short end.", 0.0),
    ]
    return Panel(
        type=PanelType.NECK_BLOCK, name="NECK_BLOCK",
        outline=outline, finger_edges=[],
        holes=[], score_lines=[], finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=w, height=h,
    )


def make_tail_block(config: InstrumentConfig, geom: TrapezoidGeometry) -> Panel:
    """Rectangle tail_block_thickness × depth_outer. Plain outline, no finger joints."""
    w = config.tail_block_thickness
    h = geom.depth_outer

    TL = Point(0.0, 0.0)
    TR = Point(w,   0.0)
    BR = Point(w,   h)
    BL = Point(0.0, h)

    outline = build_plain_outline([TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0])
    marks = [
        Mark(MarkType.LABEL, Point(w / 2, h / 2),
             "TAIL BLOCK — glue inside long end.", 0.0),
    ]
    return Panel(
        type=PanelType.TAIL_BLOCK, name="TAIL_BLOCK",
        outline=outline, finger_edges=[],
        holes=[], score_lines=[], finger_zone_boundaries=[],
        marks=marks,
        grain_angle_deg=0.0,
        width=w, height=h,
    )
