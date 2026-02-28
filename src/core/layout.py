"""
core/layout.py — Next Fit Decreasing Height (NFDH) bin-packing.
Simple, deterministic, well-understood.
"""

from __future__ import annotations

from constants import PANEL_GAP_MM
from core.models import Panel, PanelType, Point
from core import reporter
from core.transform import rotate_panel_90cw


def layout_panels(
    panels:       list[Panel],
    sheet_width:  float,
    sheet_height: float,
) -> list[tuple[Panel, Point, int]]:
    """Pack panels onto sheets using NFDH algorithm.

    Returns (Panel, origin: Point, sheet_index) triples.
    Panel objects are never mutated — rotate_panel_90cw() used for rotation.

    Grain direction constraint: BASE and SOUNDBOARD never rotated.
    TEST_STRIP always on last sheet.
    """
    FIXED_GRAIN = {PanelType.BASE, PanelType.SOUNDBOARD}

    # Separate TEST_STRIP from rest
    test_strips = [p for p in panels if p.type == PanelType.TEST_STRIP]
    other       = [p for p in panels if p.type != PanelType.TEST_STRIP]

    # Sort by longest dimension descending (NFDH: tallest items first)
    def longest(p: Panel) -> float:
        return max(p.width, p.height)

    other_sorted = sorted(other, key=longest, reverse=True)

    result: list[tuple[Panel, Point, int]] = []
    sheet_index = 0
    x = PANEL_GAP_MM
    y = PANEL_GAP_MM
    row_height = 0.0

    def try_place(panel: Panel) -> tuple[Panel, float, float] | None:
        """Try to place panel in current row; rotate if needed. Returns (panel, x, y) or None."""
        nonlocal x, y, row_height

        w, h = panel.width, panel.height

        # Try natural orientation
        if x + w + PANEL_GAP_MM <= sheet_width + PANEL_GAP_MM:
            return panel, x, y

        # Try rotated (only if not fixed grain)
        if panel.type not in FIXED_GRAIN:
            w_r, h_r = h, w
            if x + w_r + PANEL_GAP_MM <= sheet_width + PANEL_GAP_MM:
                rotated = rotate_panel_90cw(panel)
                return rotated, x, y

        return None

    for panel in other_sorted:
        w, h = panel.width, panel.height

        # Check if panel exceeds sheet_width entirely (even in natural orientation)
        if w > sheet_width:
            reporter.print_warning(
                f"Panel {panel.name} ({w:.1f}mm wide) exceeds sheet_width ({sheet_width:.1f}mm). "
                "Placing on its own row."
            )
            # Start new row
            y += row_height + PANEL_GAP_MM if row_height > 0 else 0
            if y + h + PANEL_GAP_MM > sheet_height and y > PANEL_GAP_MM:
                sheet_index += 1
                y = PANEL_GAP_MM
            result.append((panel, Point(PANEL_GAP_MM, y), sheet_index))
            y += h + PANEL_GAP_MM
            row_height = 0.0
            x = PANEL_GAP_MM
            continue

        placed = try_place(panel)
        if placed is not None:
            p, px, py = placed
            result.append((p, Point(px, py), sheet_index))
            row_height = max(row_height, p.height)
            x += p.width + PANEL_GAP_MM
        else:
            # Start new row
            y += row_height + PANEL_GAP_MM
            x = PANEL_GAP_MM
            row_height = 0.0

            if y + h + PANEL_GAP_MM > sheet_height:
                # New sheet
                sheet_index += 1
                y = PANEL_GAP_MM
                x = PANEL_GAP_MM
                row_height = 0.0

            # Try in new row
            placed2 = try_place(panel)
            if placed2 is not None:
                p, px, py = placed2
                result.append((p, Point(px, py), sheet_index))
                row_height = max(row_height, p.height)
                x += p.width + PANEL_GAP_MM
            else:
                # Force place in natural orientation
                result.append((panel, Point(x, y), sheet_index))
                row_height = max(row_height, panel.height)
                x += panel.width + PANEL_GAP_MM

    # Place TEST_STRIPs on last sheet
    last_sheet = max((idx for _, _, idx in result), default=0) if result else 0
    # Start a new row on the last sheet for test strips
    if result:
        last_on_sheet = [(p, pt, idx) for p, pt, idx in result if idx == last_sheet]
        if last_on_sheet:
            _, last_pt, _ = last_on_sheet[-1]
            ts_y = last_pt.y + max(p.height for p, pt, idx in last_on_sheet) + PANEL_GAP_MM
        else:
            ts_y = PANEL_GAP_MM
    else:
        ts_y = PANEL_GAP_MM

    ts_x = PANEL_GAP_MM
    for ts in test_strips:
        if ts_y + ts.height + PANEL_GAP_MM > sheet_height:
            last_sheet += 1
            ts_y = PANEL_GAP_MM
        result.append((ts, Point(ts_x, ts_y), last_sheet))
        ts_x += ts.width + PANEL_GAP_MM

    return result
