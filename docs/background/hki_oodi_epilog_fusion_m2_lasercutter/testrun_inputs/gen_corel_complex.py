#!/usr/bin/env python3
"""
gen_corel_complex.py
Generate 01_corel_complex.svg — nested-group / compound-path CorelDRAW import stress test.

STRUCTURE
---------
Outer group
  Inner group (clipped)
    Path A: union of circles 0,1,2 — cut style (Red)
    Path B: union of circles 2,3,4 — etch style (Black)
  Rect 1 — cut style (Red)
  Rect 2 — etch style (Black)

The clip-path applied to the inner group simulates the "intersection/removal" that
Inkscape Path > Intersection would produce (without requiring actual path computation).

WHAT TO CHECK IN CORELDRAW
---------------------------
- Does the outer group import as 1 object or become duplicated?
- Is anything locked or ungroupable?
- Are Red elements routed to Vector Cut, Black to Raster?
- How many objects does "Select All" find?

SIZES: ~17×14mm
"""
import math
from pathlib import Path


def circle_chain_union_path(n: int, r: float, d: float, ox: float, oy: float) -> str:
    """
    SVG path d-string for the outer boundary of a chain of n overlapping circles.
    Circle 0 centre at (ox, oy). All arcs: sweep=1 large_arc=0.
    Requires n >= 2, d < 2r.
    """
    y_int = math.sqrt(r ** 2 - (d / 2) ** 2)

    def pt(x: float, y: float) -> str:
        return f"{ox + x:.4f} {oy + y:.4f}"

    arc = f"A {r:.4f} {r:.4f} 0 0 1"
    segs: list[str] = [f"M {pt(-r, 0)}"]

    # Top edge (left → right)
    segs.append(f"{arc} {pt(d / 2, -y_int)}")
    for i in range(1, n - 1):
        segs.append(f"{arc} {pt(d * i + d / 2, -y_int)}")
    segs.append(f"{arc} {pt(d * (n - 1) + r, 0)}")

    # Bottom edge (right → left)
    segs.append(f"{arc} {pt(d * (n - 1) - d / 2, y_int)}")
    for i in range(n - 2, 0, -1):
        segs.append(f"{arc} {pt(d * i - d / 2, y_int)}")
    segs.append(f"{arc} {pt(-r, 0)}")

    segs.append("Z")
    return " ".join(segs)


def build_svg() -> str:
    r, d = 2.0, 2.5

    # Circle centres
    # Cut circles 0,1,2: centres at ox_cut + 0, d, 2d
    # Etch circles 0,1,2 (= original 2,3,4): centres at ox_etch + 0, d, 2d
    # ox_etch = ox_cut + 2d  →  circle 2 is shared (same physical position)
    margin = 1.5
    oy     = 5.0               # y-centre of all circles
    ox_cut  = margin + r       # = 3.5  →  left pole of cut at x=1.5
    ox_etch = ox_cut + d * 2   # = 8.5  →  left pole of etch at x=6.5

    # Page dimensions
    right_pole_etch = ox_etch + d * 2 + r   # = 15.5
    page_w = right_pole_etch + margin        # = 17.0
    page_h = 14.0

    # Paths
    cut_d  = circle_chain_union_path(n=3, r=r, d=d, ox=ox_cut,  oy=oy)
    etch_d = circle_chain_union_path(n=3, r=r, d=d, ox=ox_etch, oy=oy)

    # Clip rect: trims ~1.5mm from each end of the joined chain, simulating intersection
    cx = ox_cut - r + 1.0      # = 2.5  (trim 1mm off the left cap)
    cy = oy - r - 0.5          # = 2.5
    cw = right_pole_etch - cx - 1.0  # = 12.0  (trim 1mm off the right cap)
    ch = 2 * r + 1.0           # = 5.0

    # Rectangles (visible elements, not clip regions)
    cut_rect  = (margin,            oy - r - 0.5, 4.0, 2 * r + 1.0)  # left side, red
    etch_rect = (page_w - margin - 4.0, oy - r - 0.5, 4.0, 2 * r + 1.0)  # right, black

    text_y1 = oy + r + 3.0
    text_y2 = oy + r + 4.5

    def rect_attrs(x, y, w, h, colour, sw):
        return (f'x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                f'stroke="{colour}" stroke-width="{sw}" fill="none"')

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!-- 01_corel_complex.svg — nested group + compound path CorelDRAW import test -->',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{page_w:.2f}mm" height="{page_h:.2f}mm"',
        f'     viewBox="0 0 {page_w:.2f} {page_h:.2f}">',
        '',
        '<defs>',
        '  <clipPath id="clip1">',
        f'    <rect x="{cx:.2f}" y="{cy:.2f}" width="{cw:.2f}" height="{ch:.2f}"/>',
        '  </clipPath>',
        '</defs>',
        '',
        '<g id="g_outer">',
        '',
        '  <!-- inner group: 5-circle chain (3 cut + 3 etch, overlap at circle 2), clipped -->',
        '  <g id="g_circles" clip-path="url(#clip1)">',
        f'    <path d="{cut_d}"  stroke="#FF0000" stroke-width="0.3" fill="none"/>',
        f'    <path d="{etch_d}" stroke="#000000" stroke-width="0.3" fill="none"/>',
        '  </g>',
        '',
        '  <!-- rect cut (Red) -->',
        f'  <rect {rect_attrs(*cut_rect,  "#FF0000", "0.3")}/>',
        '  <!-- rect etch (Black) -->',
        f'  <rect {rect_attrs(*etch_rect, "#000000", "0.3")}/>',
        '',
        '</g>',
        '',
        f'<text x="1" y="{text_y1:.1f}" font-size="1" font-family="sans-serif" fill="black">'
        f'5-circ cut+etch clipped</text>',
        f'<text x="1" y="{text_y2:.1f}" font-size="1" font-family="sans-serif" fill="black">'
        f'1 obj? not locked?</text>',
        '',
        '</svg>',
        '',
    ]
    return '\n'.join(lines)


def main() -> None:
    content = build_svg()
    out = Path(__file__).parent / '01_corel_complex.svg'
    out.write_text(content, encoding='utf-8')
    print(f"Written: {out}")
    print("Page: 17.0×14.0mm")
    print("Structure: g_outer > g_circles(clipped) [cut_path, etch_path] + rect_cut + rect_etch")


if __name__ == "__main__":
    main()
