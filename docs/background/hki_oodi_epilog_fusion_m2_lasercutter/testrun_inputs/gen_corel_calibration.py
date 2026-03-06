#!/usr/bin/env python3
"""
gen_corel_calibration.py
Generate 00_corel_calibration.svg — stroke-width / colour routing test for CorelDRAW.

PURPOSE
-------
Import into CorelDRAW. Observe which Epilog profile (Vector Cut vs Raster Engrave)
each line gets. Determines whether stroke-width, colour, or both control routing.

TEST MATRIX
-----------
5 stroke widths × 3 colours = 15 lines.
Widths bracket the hypothetical 0.0254mm (0.001 inch) hairline threshold:
  0.001mm  — well below
  0.005mm  — below
  0.025mm  — at threshold
  0.100mm  — above
  0.500mm  — well above

Colours: R=#FF0000, Bk=#000000, Bu=#0000FF

EXPECTED RESULT (hypothesis)
  stroke-width only: sw < ~0.025mm → Vector Cut, >= 0.025mm → Raster
  colour only:       Red → Vector Cut, others → Raster

SIZE: 16×15mm (compact — plywood is expensive)
"""
from pathlib import Path

COLOURS = [
    ("#FF0000", "R"),
    ("#000000", "Bk"),
    ("#0000FF", "Bu"),
]
WIDTHS = [0.001, 0.005, 0.025, 0.1, 0.5]

PAGE_W = 16.0   # mm
PAGE_H = 15.0   # mm

MARGIN      = 0.5
LABEL_COL_W = 4.5   # x-width reserved for width label (e.g. "0.025")
LINE_LEN    = 3.0   # length of each test segment
COL_GAP     = 0.5   # gap between colour columns

FONT_TITLE  = 1.2   # mm
FONT_HDR    = 0.9
FONT_LABEL  = 1.0

# X start position for each colour column
_x0 = MARGIN + LABEL_COL_W + COL_GAP          # = 5.5
X_COLS = [_x0 + i * (LINE_LEN + COL_GAP) for i in range(3)]
# X_COLS = [5.5, 9.0, 12.5]  →  line ends at 8.5 / 12.0 / 15.5, right margin 0.5 ✓

ROW_Y_START = 5.5
ROW_Y_STEP  = 2.0


def build_svg() -> str:
    els: list[str] = []

    # Title
    els.append(
        f'  <text x="{MARGIN}" y="2.0" font-size="{FONT_TITLE}" '
        f'font-family="sans-serif" fill="black">Corel cal</text>'
    )

    # Column headers
    for (colour, name), x in zip(COLOURS, X_COLS):
        cx = x + LINE_LEN / 2
        els.append(
            f'  <text x="{cx:.2f}" y="4.2" font-size="{FONT_HDR}" '
            f'font-family="sans-serif" text-anchor="middle" fill="{colour}">{name}</text>'
        )

    # Data rows
    y = ROW_Y_START
    for width in WIDTHS:
        w_label = f"{width}"
        els.append(
            f'  <text x="{MARGIN}" y="{y:.2f}" font-size="{FONT_LABEL}" '
            f'font-family="sans-serif" fill="black">{w_label}</text>'
        )
        for (colour, _name), x in zip(COLOURS, X_COLS):
            els.append(
                f'  <line x1="{x:.2f}" y1="{y - 0.4:.2f}" '
                f'x2="{x + LINE_LEN:.2f}" y2="{y - 0.4:.2f}" '
                f'stroke="{colour}" stroke-width="{width}"/>'
            )
        y += ROW_Y_STEP

    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- 00_corel_calibration.svg: {len(WIDTHS)} widths × {len(COLOURS)} colours = {len(WIDTHS)*len(COLOURS)} lines -->',
        f'<!-- Widths: {WIDTHS} -->',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{PAGE_W}mm" height="{PAGE_H}mm"',
        f'     viewBox="0 0 {PAGE_W} {PAGE_H}">',
    ]
    return '\n'.join(header + els + ['</svg>', ''])


def main() -> None:
    content = build_svg()
    out = Path(__file__).parent / '00_corel_calibration.svg'
    out.write_text(content, encoding='utf-8')
    print(f"Written: {out}")
    print(f"Size: {PAGE_W}×{PAGE_H}mm  ({len(WIDTHS)*len(COLOURS)} test lines)")


if __name__ == "__main__":
    main()
