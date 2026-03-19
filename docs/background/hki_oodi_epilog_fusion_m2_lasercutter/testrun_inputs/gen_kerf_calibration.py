#!/usr/bin/env python3
"""
gen_kerf_calibration.py — finger joint kerf calibration SVG for 3mm plywood.

PURPOSE
-------
Cut all 5 pieces. Insert the tab piece into each slot. Pick the tightest fit
that still assembles. That slot_width is the compensated value to use in the
box generator for this laser + 3mm plywood combination.

DESIGN DECISIONS
----------------
Run01 (28 Feb 2026) produced joints that were very loose and tabs too short.
Both failures have distinct causes:

  Failure 1 — Loose joints:
    Cause: laser kerf removes material on both sides of every cut line.
    A 3mm nominal slot ends up ~3.3–3.6mm wide; a 3mm nominal tab ends up
    ~2.4–2.7mm wide. Total gap ≈ 0.6–0.9mm → loose.
    Fix: draw slot widths well below nominal to compensate.
    Range tested: 2.0, 2.4, 2.8, 3.2mm (biased small; 3.2 is the control).

  Failure 2 — Tabs too short:
    Cause: tab depth in SVG was less than material thickness.
    Fix: tab depth = slot depth = MAT_T = 3.0mm (= material thickness).
    This is hardcoded and labeled so it can be verified against the physical piece.

WHAT TO MEASURE AFTER CUTTING
------------------------------
1. Try inserting tab into each slot. Note tightest slot that still assembles.
2. Measure actual tab width and slot widths with calipers → compute actual kerf.
3. Record winning slot_width as the kerf-compensated dimension for box gen.

OUTPUT GEOMETRY
---------------
  5 slot pieces:  slot widths [2.0, 2.4, 2.8, 3.2, 3.6]mm, depth 3.0mm
  1 tab piece:    tab width 3.0mm, depth 3.0mm
  Single row, total ~75 × 22mm
  Cuts: Red #FF0000, stroke-width=0.1
  Etched labels: Black #000000, stroke-width=0.3
"""

from pathlib import Path

# ── Parameters ────────────────────────────────────────────────────────────────
MAT_T = 3.0           # material thickness mm (= tab depth = slot depth)
TAB_WIDTH = 3.0       # nominal tab width mm (fixed)
SLOT_WIDTHS = [2.0, 2.4, 2.8, 3.2, 3.6]  # slot widths to test (mm)

PIECE_W = 10.0        # outer width of each piece (mm)
SLOT_H  = 9.0         # height of slot piece body (mm)
TAB_H   = 6.0         # height of tab piece body above the tab (mm)
GAP     = 2.0         # gap between pieces (mm)

CUT_COL  = '#FF0000'
ETCH_COL = '#000000'
CUT_SW   = '0.1'
ETCH_SW  = '0.3'

TITLE_H  = 5.0        # mm reserved at top for title
LABEL_H  = 4.0        # mm reserved below pieces for labels
MARGIN_B = 2.0        # bottom margin mm

N_PIECES = len(SLOT_WIDTHS) + 1  # 5 slots + 1 tab
PAGE_W = N_PIECES * PIECE_W + (N_PIECES - 1) * GAP
# Tallest piece is tab piece: TAB_H + MAT_T; slot label is below SLOT_H
# Tab label sits below TAB_H + MAT_T
PAGE_H = TITLE_H + max(SLOT_H, TAB_H + MAT_T) + LABEL_H + MARGIN_B


# ── Helpers ───────────────────────────────────────────────────────────────────
def f(v: float) -> str:
    s = f"{v:.3f}"
    # strip trailing zeros but keep at least one decimal for SVG clarity
    s = s.rstrip('0')
    if s.endswith('.'):
        s += '0'
    return s


def path(d: str, col: str, sw: str) -> str:
    return f'  <path d="{d}" stroke="{col}" stroke-width="{sw}" fill="none"/>'


def text(x: float, y: float, s: str, col: str = ETCH_COL,
         anchor: str = 'middle', size: float = 1.2) -> str:
    return (f'  <text x="{f(x)}" y="{f(y)}" font-size="{size}" '
            f'font-family="sans-serif" text-anchor="{anchor}" fill="{col}">{s}</text>')


# ── Path builders ─────────────────────────────────────────────────────────────
def slot_piece(x0: float, y0: float, sw: float) -> str:
    """Rectangle with a slot (opening) cut from the top edge, width=sw, depth=MAT_T."""
    cx = x0 + PIECE_W / 2
    hl = sw / 2
    pts = [
        (x0,            y0),
        (cx - hl,       y0),
        (cx - hl,       y0 + MAT_T),
        (cx + hl,       y0 + MAT_T),
        (cx + hl,       y0),
        (x0 + PIECE_W,  y0),
        (x0 + PIECE_W,  y0 + SLOT_H),
        (x0,            y0 + SLOT_H),
    ]
    d = 'M ' + ' L '.join(f"{f(px)} {f(py)}" for px, py in pts) + ' Z'
    return path(d, CUT_COL, CUT_SW)


def tab_piece(x0: float, y0: float) -> str:
    """Rectangle with a tab protruding from the bottom edge, width=TAB_WIDTH, depth=MAT_T."""
    cx = x0 + PIECE_W / 2
    hl = TAB_WIDTH / 2
    pts = [
        (x0,            y0),
        (x0 + PIECE_W,  y0),
        (x0 + PIECE_W,  y0 + TAB_H),
        (cx + hl,       y0 + TAB_H),
        (cx + hl,       y0 + TAB_H + MAT_T),
        (cx - hl,       y0 + TAB_H + MAT_T),
        (cx - hl,       y0 + TAB_H),
        (x0,            y0 + TAB_H),
    ]
    d = 'M ' + ' L '.join(f"{f(px)} {f(py)}" for px, py in pts) + ' Z'
    return path(d, CUT_COL, CUT_SW)


# ── Verification ──────────────────────────────────────────────────────────────
def verify(page_w: float, page_h: float) -> list[str]:
    errors = []

    # All slot widths positive and narrower than piece
    for sw in SLOT_WIDTHS:
        if sw <= 0:
            errors.append(f"slot_width {sw} <= 0")
        if sw >= PIECE_W:
            errors.append(f"slot_width {sw} >= PIECE_W {PIECE_W}")

    # Tab width positive and narrower than piece
    if TAB_WIDTH <= 0:
        errors.append("TAB_WIDTH <= 0")
    if TAB_WIDTH >= PIECE_W:
        errors.append(f"TAB_WIDTH {TAB_WIDTH} >= PIECE_W {PIECE_W}")

    # Mat_T > 0
    if MAT_T <= 0:
        errors.append("MAT_T <= 0")

    # Pieces within page bounds
    last_x = (N_PIECES - 1) * (PIECE_W + GAP) + PIECE_W
    if last_x > page_w + 0.001:
        errors.append(f"pieces extend to x={last_x:.3f} > PAGE_W={page_w:.3f}")

    tallest = TITLE_H + max(SLOT_H, TAB_H + MAT_T)
    if tallest > page_h - MARGIN_B + 0.001:
        errors.append(f"pieces extend to y={tallest:.3f} > PAGE_H-margin={page_h - MARGIN_B:.3f}")

    # No piece overlaps (uniform spacing, just check GAP > 0)
    if GAP <= 0:
        errors.append("GAP <= 0: pieces overlap")

    return errors


# ── Build SVG ─────────────────────────────────────────────────────────────────
def build() -> str:
    errors = verify(PAGE_W, PAGE_H)
    if errors:
        raise ValueError("Verification failed:\n" + "\n".join(f"  {e}" for e in errors))

    els: list[str] = []

    els.append(text(PAGE_W / 2, 3.5,
                    f'Kerf cal 3mm ply | tab={TAB_WIDTH}mm depth={MAT_T}mm | insert tab, find tightest fit',
                    size=1.3))

    y0 = TITLE_H

    for i, sw in enumerate(SLOT_WIDTHS):
        x0 = i * (PIECE_W + GAP)
        els.append(slot_piece(x0, y0, sw))
        # Label: slot width and offset from nominal
        offset = sw - TAB_WIDTH
        sign = '+' if offset >= 0 else ''
        els.append(text(x0 + PIECE_W / 2, y0 + SLOT_H + 2.5,
                        f'{sw}mm ({sign}{offset:.1f})'))

    # Tab piece (rightmost)
    i = len(SLOT_WIDTHS)
    x0 = i * (PIECE_W + GAP)
    els.append(tab_piece(x0, y0))
    els.append(text(x0 + PIECE_W / 2, y0 + TAB_H + MAT_T + 2.5,
                    f'TAB {TAB_WIDTH}mm'))

    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- 02_kerf_calibration.svg: {len(SLOT_WIDTHS)} slot widths x 1 tab, 3mm plywood kerf cal -->',
        f'<!-- Slot widths: {SLOT_WIDTHS} | Tab: {TAB_WIDTH}mm | Depth: {MAT_T}mm -->',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{f(PAGE_W)}mm" height="{f(PAGE_H)}mm"',
        f'     viewBox="0 0 {f(PAGE_W)} {f(PAGE_H)}">',
    ]
    return '\n'.join(header + els + ['</svg>', ''])


def main() -> None:
    svg = build()
    out = Path(__file__).parent / '02_kerf_calibration.svg'
    out.write_text(svg, encoding='utf-8')
    print(f"Written: {out}")
    print(f"Size: {f(PAGE_W)}x{f(PAGE_H)}mm")
    print(f"Slot widths: {SLOT_WIDTHS}")
    print(f"Tab width: {TAB_WIDTH}mm  Depth (both): {MAT_T}mm")


if __name__ == '__main__':
    main()
