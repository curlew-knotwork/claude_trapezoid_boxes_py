"""
instrument/marks.py — Grain arrows, brace lines, scale mark, assembly numbers.
"""

from __future__ import annotations

from core.models import Panel, Mark, MarkType, Line, Point, PanelType, InstrumentConfig
from core.trapezoid import TrapezoidGeometry


# Assembly sequence numbers (fixed order per spec §20)
ASSEMBLY_ORDER = {
    PanelType.BASE:           "1",
    PanelType.WALL_LONG:      "2",
    PanelType.WALL_SHORT:     "3",
    PanelType.WALL_LEG_LEFT:  "4",
    PanelType.WALL_LEG_RIGHT: "5",
    PanelType.SOUNDBOARD:     "6",
}


def add_assembly_marks(panels: list[Panel]) -> list[Panel]:
    """Add assembly number marks to panels. Kerfing pieces numbered from 7 upward."""
    import dataclasses

    kerf_num = 7
    result = []
    for p in panels:
        if p.type in ASSEMBLY_ORDER:
            num = ASSEMBLY_ORDER[p.type]
            cx = p.width / 2
            cy = p.height / 2
            mark = Mark(MarkType.ASSEMBLY_NUM, Point(cx, cy), num, 0.0)
            result.append(dataclasses.replace(p, marks=list(p.marks) + [mark]))
        elif p.type in (PanelType.KERF_STRIP, PanelType.KERF_FILLET):
            cx = p.width / 2
            cy = p.height / 2
            mark = Mark(MarkType.ASSEMBLY_NUM, Point(cx, cy), str(kerf_num), 0.0)
            kerf_num += 1
            result.append(dataclasses.replace(p, marks=list(p.marks) + [mark]))
        else:
            result.append(p)
    return result


def add_brace_score_lines(soundboard: Panel, geom: TrapezoidGeometry) -> Panel:
    """Add brace score lines at 0.25 × length and 0.65 × length from short end."""
    import dataclasses

    L = geom.length_outer
    lo = geom.long_outer

    y1 = 0.25 * L
    y2 = 0.65 * L

    # Full-width score lines across soundboard at brace positions
    lines = list(soundboard.score_lines) + [
        Line(Point(0.0, y1), Point(lo, y1)),
        Line(Point(0.0, y2), Point(lo, y2)),
    ]
    return dataclasses.replace(soundboard, score_lines=lines)


def add_scale_mark(soundboard: Panel, geom: TrapezoidGeometry,
                   scale_length: float) -> Panel:
    """Add bridge position score line at scale_length/2 from short end."""
    import dataclasses

    lo = geom.long_outer
    y  = scale_length / 2
    line = Line(Point(0.0, y), Point(lo, y))
    lines = list(soundboard.score_lines) + [line]
    return dataclasses.replace(soundboard, score_lines=lines)
