#!/usr/bin/env python3
"""
gen_corel_calibration.py
Generate 00_corel_calibration.svg — calibration test for CorelDRAW → Epilog routing.

PURPOSE
-------
Import into CorelDRAW and observe which Epilog print profile (Vector Cut vs Raster Engrave)
CorelDRAW auto-assigns to each line. Determines whether stroke-width, colour, or both
control the routing decision.

TEST MATRIX
-----------
5 stroke widths x 3 colours = 15 test lines.
Widths bracket the hypothetical 0.0254mm (0.001 inch) hairline threshold:
  0.001mm  — well below (proposed cut width in constants.py)
  0.005mm  — below
  0.025mm  — approximately at threshold
  0.100mm  — above (proposed etch width)
  0.500mm  — well above

Colours:
  Red   (#FF0000) — proposed vector cut colour
  Black (#000000) — proposed raster etch colour
  Blue  (#0000FF) — prior score colour (baseline comparison)

EXPECTED RESULTS (hypothesis)
------------------------------
If CorelDRAW routes by stroke-width only:
  - All lines with sw < ~0.025mm -> Vector Cut, regardless of colour
  - All lines with sw >= 0.025mm -> Raster Engrave, regardless of colour

If CorelDRAW routes by colour only:
  - Red -> Vector Cut, Black/Blue -> Raster, regardless of stroke-width

Record actual results for each of the 15 lines and report back.
"""
from pathlib import Path

COLOURS = [
    ("#FF0000", "Red"),
    ("#000000", "Black"),
    ("#0000FF", "Blue"),
]
WIDTHS = [0.001, 0.005, 0.025, 0.1, 0.5]

W_MM = 200
X_LABEL = 5
X_LINE_START = 45
X_LINE_END = 195
MARGIN_TOP = 35
LINE_SPACING = 6      # mm between lines within a group
GROUP_SPACING = 10    # mm between width groups


def build_svg() -> str:
    elements: list[str] = []

    # Title block — fill only, no stroke (CorelDRAW will rasterize as text)
    elements.append(
        f'  <text x="{X_LABEL}" y="9" font-size="4.5" font-family="sans-serif" fill="black">'
        f'CorelDRAW / Epilog Fusion M2 Calibration</text>'
    )
    elements.append(
        f'  <text x="{X_LABEL}" y="17" font-size="3" font-family="sans-serif" fill="black">'
        f'Import SVG. Note which Epilog profile each line gets (Vector Cut vs Raster Engrave).</text>'
    )
    elements.append(
        f'  <text x="{X_LABEL}" y="23" font-size="3" font-family="sans-serif" fill="black">'
        f'Threshold hypothesis: stroke-width &lt; 0.025mm = vector; &gt;= 0.025mm = raster.</text>'
    )
    elements.append(
        f'  <text x="{X_LABEL}" y="29" font-size="3" font-family="sans-serif" fill="black">'
        f'Also: does colour (Red/Black/Blue) affect classification independently of width?</text>'
    )

    y = float(MARGIN_TOP)

    for width in WIDTHS:
        # Group header label
        elements.append(
            f'  <text x="{X_LABEL}" y="{y:.1f}" font-size="3.5" font-weight="bold" '
            f'font-family="sans-serif" fill="black">stroke-width = {width} mm</text>'
        )
        y += 5.0  # clearance below group header

        for colour, name in COLOURS:
            # Test line — this is what CorelDRAW classifies
            elements.append(
                f'  <line x1="{X_LINE_START}" y1="{y:.1f}" x2="{X_LINE_END}" y2="{y:.1f}" '
                f'stroke="{colour}" stroke-width="{width}"/>'
            )
            # Colour label — fill only, no stroke → rasterized as text, not routed as cut
            elements.append(
                f'  <text x="{X_LABEL}" y="{y + 1.5:.1f}" font-size="2.8" '
                f'font-family="sans-serif" fill="{colour}">{name}</text>'
            )
            y += LINE_SPACING

        y += GROUP_SPACING

    h_mm = int(y + 8)

    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!-- trapezoid_boxes CorelDRAW calibration — see gen_corel_calibration.py for test matrix -->',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{W_MM}mm" height="{h_mm}mm"',
        f'     viewBox="0 0 {W_MM} {h_mm}">',
    ]

    return '\n'.join(header + elements + ['</svg>', ''])


def main() -> None:
    content = build_svg()
    out = Path(__file__).parent / '00_corel_calibration.svg'
    out.write_text(content, encoding='utf-8')
    print(f"Written: {out}")
    print(f"Dimensions: {W_MM}mm wide, dynamic height")
    print(f"Test lines: {len(WIDTHS)} widths x {len(COLOURS)} colours = {len(WIDTHS) * len(COLOURS)} lines")
    print(f"Widths: {WIDTHS}")
    print(f"Colours: {[c for _, c in COLOURS]}")


if __name__ == "__main__":
    main()
