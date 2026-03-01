"""
instrument/kerfing.py — Kerfing strip and fillet geometry.

All pieces are undersized by KERF_UNDERSIZE_MM to accommodate hand-rounding
and provide glue gap.
"""

from __future__ import annotations

from constants import KERF_UNDERSIZE_MM
from core.models import (
    Panel, PanelType, Point, Mark, MarkType, InstrumentConfig,
)
from core.trapezoid import TrapezoidGeometry
from core.joints import build_plain_outline


def make_base_kerf_strips(config: InstrumentConfig, geom: TrapezoidGeometry) -> list[Panel]:
    """One base-level kerfing strip per wall, 4 total.

    kerf_height × inner_wall_length × kerf_thickness.
    """
    strips = []
    t = config.kerf_thickness
    h = config.kerf_height - KERF_UNDERSIZE_MM
    lo = geom.long_outer;  so = geom.short_outer;  ll = geom.leg_length;  T = geom.thickness

    inner_lengths = {
        "LONG":      lo - 2 * T,
        "SHORT":     so - 2 * T,
        "LEG_LEFT":  ll - 2 * T,   # acceptable approximation (within KERF_UNDERSIZE_MM)
        "LEG_RIGHT": ll - 2 * T,
    }

    for label, inner_len in inner_lengths.items():
        w = inner_len - KERF_UNDERSIZE_MM
        TL = Point(0.0, 0.0); TR = Point(w, 0.0)
        BR = Point(w, h);     BL = Point(0.0, h)
        outline = build_plain_outline([TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0])
        marks = [Mark(MarkType.LABEL, Point(w / 2, h / 2),
                      f"KERF BASE {label}", 0.0)]
        strips.append(Panel(
            type=PanelType.KERF_STRIP, name=f"KERF_BASE_{label}",
            outline=outline, finger_edges=[],
            holes=[], score_lines=[], finger_zone_boundaries=[],
            marks=marks,
            grain_angle_deg=0.0,
            width=w, height=h,
        ))
    return strips


def make_soundboard_kerf_strips(config: InstrumentConfig, geom: TrapezoidGeometry) -> list[Panel]:
    """One soundboard-level kerfing strip per wall, 4 total."""
    strips = []
    t = config.kerf_thickness
    h = config.kerf_top_height - KERF_UNDERSIZE_MM
    lo = geom.long_outer;  so = geom.short_outer;  ll = geom.leg_length;  T = geom.thickness

    inner_lengths = {
        "LONG":      lo - 2 * T,
        "SHORT":     so - 2 * T,
        "LEG_LEFT":  ll - 2 * T,
        "LEG_RIGHT": ll - 2 * T,
    }

    for label, inner_len in inner_lengths.items():
        w = inner_len - KERF_UNDERSIZE_MM
        TL = Point(0.0, 0.0); TR = Point(w, 0.0)
        BR = Point(w, h);     BL = Point(0.0, h)
        outline = build_plain_outline([TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0])
        marks = [Mark(MarkType.LABEL, Point(w / 2, h / 2),
                      f"KERF TOP {label}", 0.0)]
        strips.append(Panel(
            type=PanelType.KERF_STRIP, name=f"KERF_TOP_{label}",
            outline=outline, finger_edges=[],
            holes=[], score_lines=[], finger_zone_boundaries=[],
            marks=marks,
            grain_angle_deg=0.0,
            width=w, height=h,
        ))
    return strips


def make_kerf_fillets(config: InstrumentConfig, geom: TrapezoidGeometry) -> list[Panel]:
    """Corner fillet pieces for airtight sealing at internal corners.

    Right-angle triangle cross-section. One per internal corner.
    Length = depth_outer. Undersized 0.5mm.
    """
    # Four wall-to-wall corners: two long-end corners, two short-end corners.
    # Simple rectangular fillet approximation (triangular cross-section is
    # hand-trimmed by builder).
    fillets = []
    kw = config.kerf_width - KERF_UNDERSIZE_MM
    h  = geom.depth_outer - KERF_UNDERSIZE_MM

    for i, label in enumerate(["TL", "TR", "BL", "BR"]):
        TL = Point(0.0, 0.0); TR = Point(kw, 0.0)
        BR = Point(kw, h);    BL = Point(0.0, h)
        outline = build_plain_outline([TL, TR, BR, BL], 0.0, [90.0, 90.0, 90.0, 90.0])
        marks = [Mark(MarkType.LABEL, Point(kw / 2, h / 2),
                      f"FILLET {label}", 0.0)]
        fillets.append(Panel(
            type=PanelType.KERF_FILLET, name=f"KERF_FILLET_{label}",
            outline=outline, finger_edges=[],
            holes=[], score_lines=[], finger_zone_boundaries=[],
            marks=marks,
            grain_angle_deg=0.0,
            width=kw, height=h,
        ))
    return fillets
