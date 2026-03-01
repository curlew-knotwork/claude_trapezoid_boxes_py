"""
core/svg_writer.py — Pure serialiser. Zero geometry calculations.
Receives layout triples, produces SVG text.
"""

from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from constants import (
    TOOL_VERSION, SVG_TRAPEZOIDBOX_NS,
    SVG_CUT_COLOUR, SVG_SCORE_COLOUR, SVG_LABEL_COLOUR,
    SVG_CB_CUT_COLOUR, SVG_CB_SCORE_COLOUR,
    SVG_HAIRLINE_MM, SVG_LABEL_STROKE_MM,
    SVG_SCORE_DASH_MM, SVG_SCORE_GAP_MM,
    SVG_COORD_DECIMAL_PLACES, SVG_LABEL_FONT_MM, SVG_ASSEMBLY_NUM_FONT_MM,
    PANEL_GAP_MM,
)
from core.models import (
    Panel, CommonConfig, Point, Line, Arc, CubicBezier, ClosedPath,
    PathSegment, MarkType, CircleHole, ClosedHole,
)

DP = SVG_COORD_DECIMAL_PLACES  # decimal places shorthand


def _f(v: float) -> str:
    """Format a float to SVG_COORD_DECIMAL_PLACES decimal places."""
    return f"{v:.{DP}f}"


def _colour(rgb: tuple[int, int, int]) -> str:
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def path_to_svg_d(path: ClosedPath, origin: Point) -> str:
    """Convert ClosedPath to SVG d attribute, translating all coordinates by origin."""
    dx = origin.x
    dy = origin.y

    def tx(x: float) -> str: return _f(x + dx)
    def ty(y: float) -> str: return _f(y + dy)

    parts: list[str] = []
    first = True
    for seg in path.segments:
        match seg:
            case Line(start=s, end=e):
                if first:
                    parts.append(f"M {tx(s.x)} {ty(s.y)}")
                    first = False
                parts.append(f"L {tx(e.x)} {ty(e.y)}")
            case Arc(start=s, end=e, radius=r, large_arc=la, clockwise=cw):
                if first:
                    parts.append(f"M {tx(s.x)} {ty(s.y)}")
                    first = False
                la_flag = 1 if la else 0
                cw_flag = 1 if cw else 0
                parts.append(f"A {_f(r)} {_f(r)} 0 {la_flag} {cw_flag} {tx(e.x)} {ty(e.y)}")
            case CubicBezier(start=s, cp1=p1, cp2=p2, end=e):
                if first:
                    parts.append(f"M {tx(s.x)} {ty(s.y)}")
                    first = False
                parts.append(f"C {tx(p1.x)} {ty(p1.y)} {tx(p2.x)} {ty(p2.y)} {tx(e.x)} {ty(e.y)}")
    parts.append("Z")
    return " ".join(parts)


def _config_to_json(config: CommonConfig) -> str:
    """Serialize CommonConfig to JSON string for metadata embedding."""
    d = {
        "trapezoid_boxes_version": TOOL_VERSION,
        "common": {
            "long": config.long,
            "short": config.short,
            "length": config.length,
            "leg": config.leg,
            "depth": config.depth,
            "thickness": config.thickness,
            "burn": config.burn,
            "tolerance": config.tolerance,
            "corner_radius": config.corner_radius,
            "finger_width": config.finger_width,
            "sheet_width": config.sheet_width,
            "sheet_height": config.sheet_height,
            "labels": config.labels,
            "dim_mode": config.dim_mode.value,
        },
    }
    return json.dumps(d)


def _render_panel(panel: Panel, origin: Point, config: CommonConfig) -> str:
    """Render a single panel to SVG elements."""
    colorblind   = config.colorblind
    labels_on    = config.labels
    cut_colour   = _colour(SVG_CB_CUT_COLOUR   if colorblind else SVG_CUT_COLOUR)
    score_colour = _colour(SVG_CB_SCORE_COLOUR if colorblind else SVG_SCORE_COLOUR)
    cut_stroke   = config.display_stroke_mm if config.display_stroke_mm > 0 else SVG_HAIRLINE_MM

    score_dash = f"{_f(SVG_SCORE_DASH_MM)} {_f(SVG_SCORE_GAP_MM)}" if colorblind else f"{_f(SVG_SCORE_DASH_MM)} {_f(SVG_SCORE_GAP_MM)}"
    score_dash_attr = f'stroke-dasharray="{score_dash}"' if colorblind else f'stroke-dasharray="{_f(SVG_SCORE_DASH_MM)} {_f(SVG_SCORE_GAP_MM)}"'

    out: list[str] = []
    ox, oy = origin.x, origin.y

    def tx(x: float) -> str: return _f(x + ox)
    def ty(y: float) -> str: return _f(y + oy)

    # Panel outline — cut path
    d = path_to_svg_d(panel.outline, origin)
    out.append(
        f'<path d="{d}" stroke="{cut_colour}" fill="none" '
        f'stroke-width="{_f(cut_stroke)}"/>'
    )

    # Holes
    for hole in panel.holes:
        match hole:
            case CircleHole(centre=c, diameter=diam):
                r = diam / 2
                out.append(
                    f'<circle cx="{tx(c.x)}" cy="{ty(c.y)}" r="{_f(r)}" '
                    f'stroke="{cut_colour}" fill="none" '
                    f'stroke-width="{_f(cut_stroke)}"/>'
                )
            case ClosedHole(path=p):
                hd = path_to_svg_d(p, origin)
                out.append(
                    f'<path d="{hd}" stroke="{cut_colour}" fill="none" '
                    f'stroke-width="{_f(cut_stroke)}"/>'
                )

    # Score lines
    for sl in panel.score_lines:
        out.append(
            f'<line x1="{tx(sl.start.x)}" y1="{ty(sl.start.y)}" '
            f'x2="{tx(sl.end.x)}" y2="{ty(sl.end.y)}" '
            f'stroke="{score_colour}" stroke-width="{_f(SVG_HAIRLINE_MM)}" '
            f'{score_dash_attr}/>'
        )

    # Marks — grain arrows always rendered; labels only if labels_on
    cx = ox + panel.width / 2
    cy = oy + panel.height / 2
    longest = max(panel.width, panel.height)
    arrow_len = longest * 0.2

    for mark in panel.marks:
        match mark.type:
            case MarkType.GRAIN_ARROW:
                # Double-headed arrow along grain_angle_deg
                angle_rad = math.radians(panel.grain_angle_deg)
                dx2 = math.cos(angle_rad) * arrow_len / 2
                dy2 = math.sin(angle_rad) * arrow_len / 2
                x1 = cx - dx2; y1 = cy - dy2
                x2 = cx + dx2; y2 = cy + dy2
                out.append(
                    f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
                    f'stroke="{_colour(SVG_LABEL_COLOUR)}" '
                    f'stroke-width="{_f(SVG_LABEL_STROKE_MM)}" '
                    f'marker-start="url(#arrow)" marker-end="url(#arrow)"/>'
                )
            case MarkType.LABEL if labels_on:
                tx_ = _f(mark.position.x + ox)
                ty_ = _f(mark.position.y + oy)
                rot_attr = (f' transform="rotate({_f(mark.angle_deg)},{tx_},{ty_})"'
                            if mark.angle_deg else "")
                out.append(
                    f'<text x="{tx_}" y="{ty_}" '
                    f'font-size="{_f(SVG_LABEL_FONT_MM)}" font-family="sans-serif" '
                    f'fill="{_colour(SVG_LABEL_COLOUR)}"{rot_attr}>{mark.content}</text>'
                )
            case MarkType.ASSEMBLY_NUM if labels_on:
                tx_ = _f(mark.position.x + ox)
                ty_ = _f(mark.position.y + oy)
                rot_attr = (f' transform="rotate({_f(mark.angle_deg)},{tx_},{ty_})"'
                            if mark.angle_deg else "")
                out.append(
                    f'<text x="{tx_}" y="{ty_}" '
                    f'font-size="{_f(SVG_ASSEMBLY_NUM_FONT_MM)}" font-family="sans-serif" '
                    f'text-anchor="middle" fill="{_colour(SVG_LABEL_COLOUR)}"{rot_attr}>{mark.content}</text>'
                )

    return "\n".join(out)


def _svg_for_sheet(
    sheet_panels: list[tuple[Panel, Point]],
    config: CommonConfig,
    sheet_index: int,
    mode: str = "",
) -> str:
    """Generate SVG text for a single sheet."""
    w = config.sheet_width
    h = config.sheet_height
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    config_json = _config_to_json(config)

    scale_warning = (
        "<!-- trapezoid_boxes v2.0 — dimensions in millimetres\n"
        "     IMPORTANT: Verify scale before cutting.\n"
        "     Open in Inkscape and confirm Document Properties shows correct physical dimensions.\n"
        "     If your laser software scales incorrectly, use Inkscape to export\n"
        "     at 96 dpi with explicit mm units before importing. -->"
    )

    arrow_marker = (
        '<defs>'
        '<marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" '
        'orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L6,3 z" fill="black"/>'
        '</marker>'
        '</defs>'
    )

    body_parts = [arrow_marker]
    for panel, origin in sheet_panels:
        body_parts.append(f'<!-- Panel: {panel.name} at ({origin.x:.3f},{origin.y:.3f}) -->')
        body_parts.append(_render_panel(panel, origin, config))

    body = "\n".join(body_parts)

    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     xmlns:trapezoidbox="{SVG_TRAPEZOIDBOX_NS}"\n'
        f'     width="{_f(w)}mm" height="{_f(h)}mm"\n'
        f'     viewBox="0 0 {_f(w)} {_f(h)}">\n'
        f'{scale_warning}\n'
        f'<metadata>\n'
        f'  <trapezoidbox:version>{TOOL_VERSION}</trapezoidbox:version>\n'
        f'  <trapezoidbox:mode>{mode}</trapezoidbox:mode>\n'
        f'  <trapezoidbox:generated>{timestamp}</trapezoidbox:generated>\n'
        f'  <trapezoidbox:config><![CDATA[{config_json}]]></trapezoidbox:config>\n'
        f'</metadata>\n'
        f'{body}\n'
        f'</svg>\n'
    )
    return svg


def write(
    layout:       list[tuple[Panel, Point, int]],
    config:       CommonConfig,
    output_paths: list[Path],
    mode:         str = "",
) -> None:
    """Groups by sheet_index, produces one SVG per sheet, writes to output_paths."""
    # Group by sheet
    sheets: dict[int, list[tuple[Panel, Point]]] = {}
    for panel, origin, idx in layout:
        sheets.setdefault(idx, []).append((panel, origin))

    for sheet_idx in sorted(sheets.keys()):
        svg_text = _svg_for_sheet(sheets[sheet_idx], config, sheet_idx, mode)
        path = output_paths[sheet_idx]
        path.write_text(svg_text, encoding="utf-8")


def extract_config(svg_path: Path) -> str:
    """Open SVG, parse with xml.etree.ElementTree, return text of <trapezoidbox:config> CDATA."""
    import xml.etree.ElementTree as ET
    ns = {"trapezoidbox": SVG_TRAPEZOIDBOX_NS}
    tree = ET.parse(svg_path)
    root = tree.getroot()
    meta = root.find("metadata")
    if meta is None:
        raise ValueError(f"Not a trapezoidbox SVG or metadata absent: {svg_path}")
    cfg = meta.find("trapezoidbox:config", ns)
    if cfg is None:
        raise ValueError(f"No trapezoidbox:config element in metadata: {svg_path}")
    return cfg.text or ""
