"""
gen_test_cut.py — trapezoid box confidence test cut set
3mm ply, 1:1, stroke-width="0.1" (unitless hairline).
5 panels: BASE, WALL_LONG, WALL_SHORT, WALL_LEG×2
All wall-to-wall and wall-to-base joints included.
Verify-or-abort before writing.
"""

import math, os, re, sys

T = 3.0; R = 9.0; BURN = 0.05
DEPTH = T + BURN          # slot/finger protrusion depth (kerf-compensated)
GAP = 6.0; M = 10.0
CUT = 'fill="none" stroke="red" stroke-width="0.1"'
LBL = 'font-size="3.5" font-family="sans-serif" fill="#333" text-anchor="middle"'


def fmt(v): return f"{v:.4f}"
def uv(p1, p2):
    dx = p2[0]-p1[0]; dy = p2[1]-p1[1]; m = math.sqrt(dx**2+dy**2)
    return dx/m, dy/m
def tp(v, ea, eb, r, ang):
    """Tangent points for corner arc at v: arrive along ea, depart along eb."""
    td = r / math.tan(math.radians(ang / 2))
    return (v[0]-ea[0]*td, v[1]-ea[1]*td), (v[0]+eb[0]*td, v[1]+eb[1]*td)
def arc(s, e, r): return f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(e[0])} {fmt(e[1])}"
def lbl(x, y, t): return f'<text x="{fmt(x)}" y="{fmt(y)}" {LBL}>{t}</text>'
def odd_n(avail, fw=9.0):
    n = max(3, round(avail / fw)); return n if n % 2 == 1 else n + 1


def fingers(p_start, n, fw_act, d_edge, outward):
    """Generate n fingers from p_start along d_edge.

    outward=True:  protrude left-of-travel (BASE outer edges protrude outside panel).
    outward=False: slot right-of-travel (wall slots pocket into panel).
    First tab (i=0) is always protrusion or slot; last tab (i=n-1, n odd) same.
    SVG y-down: left-of-travel = (d[1], -d[0]).  Check: d=(1,0)→(0,-1)=up ✓
    """
    perp = (d_edge[1], -d_edge[0])   # left-of-travel in SVG y-down
    sign = 1.0 if outward else -1.0
    cx, cy = p_start
    parts = []
    for i in range(n):
        nx = cx + d_edge[0]*fw_act; ny = cy + d_edge[1]*fw_act
        if i % 2 == 0:   # protrusion / slot
            parts.append(f"L {fmt(cx+perp[0]*DEPTH*sign)} {fmt(cy+perp[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx+perp[0]*DEPTH*sign)} {fmt(ny+perp[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        else:
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        cx, cy = nx, ny
    return " ".join(parts)


def derive(long_o, short_o, length_o, depth_o):
    """Derive all geometry for one box variant."""
    leg_inset = (long_o - short_o) / 2
    leg_angle  = math.degrees(math.atan(leg_inset / length_o))
    leg_len    = math.sqrt(length_o**2 + leg_inset**2)
    long_end   = 90 + leg_angle   # obtuse — at narrow (short) end
    short_end  = 90 - leg_angle   # acute  — at wide  (long)  end
    tang_l = R / math.tan(math.radians(long_end  / 2))   # at obtuse corner
    tang_s = R / math.tan(math.radians(short_end / 2))   # at acute  corner

    avail_long  = long_o  - 2*tang_s
    avail_short = short_o - 2*tang_l
    avail_leg   = leg_len - tang_l - tang_s

    n_long=odd_n(avail_long);   fw_long  = avail_long  / n_long
    n_short=odd_n(avail_short); fw_short = avail_short / n_short
    n_leg=odd_n(avail_leg);     fw_leg   = avail_leg   / n_leg
    n_ww=odd_n(depth_o);        fw_ww    = depth_o     / n_ww

    return dict(leg_inset=leg_inset, leg_angle=leg_angle, leg_len=leg_len,
                long_end=long_end, short_end=short_end,
                tang_l=tang_l, tang_s=tang_s,
                n_long=n_long, fw_long=fw_long,
                n_short=n_short, fw_short=fw_short,
                n_leg=n_leg, fw_leg=fw_leg,
                n_ww=n_ww, fw_ww=fw_ww)


def build_base(ox, oy, long_o, short_o, length_o, g):
    leg_inset = g['leg_inset']
    BL=(ox,                    oy+length_o)
    BR=(ox+long_o,             oy+length_o)
    TR=(ox+leg_inset+short_o,  oy)
    TL=(ox+leg_inset,          oy)

    d_bl_tl=uv(BL,TL); d_tl_tr=uv(TL,TR); d_tr_br=uv(TR,BR); d_br_bl=uv(BR,BL)
    bl_s,bl_e = tp(BL, d_br_bl, d_bl_tl, R, g['short_end'])
    tl_s,tl_e = tp(TL, d_bl_tl, d_tl_tr, R, g['long_end'])
    tr_s,tr_e = tp(TR, d_tl_tr, d_tr_br, R, g['long_end'])
    br_s,br_e = tp(BR, d_tr_br, d_br_bl, R, g['short_end'])

    p = [f"M {fmt(bl_e[0])} {fmt(bl_e[1])}"]
    p.append(fingers(bl_e, g['n_leg'],   g['fw_leg'],   d_bl_tl, True))
    p.append(f"L {fmt(tl_s[0])} {fmt(tl_s[1])} {arc(tl_s,tl_e,R)}")
    p.append(fingers(tl_e, g['n_short'], g['fw_short'], d_tl_tr, True))
    p.append(f"L {fmt(tr_s[0])} {fmt(tr_s[1])} {arc(tr_s,tr_e,R)}")
    p.append(fingers(tr_e, g['n_leg'],   g['fw_leg'],   d_tr_br, True))
    p.append(f"L {fmt(br_s[0])} {fmt(br_s[1])} {arc(br_s,br_e,R)}")
    p.append(fingers(br_e, g['n_long'],  g['fw_long'],  d_br_bl, True))
    p.append(f"L {fmt(bl_s[0])} {fmt(bl_s[1])} {arc(bl_s,bl_e,R)}")
    p.append("Z")
    return " ".join(p)


def build_soundhole(ox, oy, long_o, short_o, length_o):
    """Rounded-trapezoid soundhole centred in BASE."""
    h_r = 2.0
    h_long   = long_o  * 0.28
    h_short  = h_long  * (short_o / long_o)
    h_height = h_long  * 0.6
    h_inset  = (h_long - h_short) / 2
    h_leg    = math.degrees(math.atan(h_inset / h_height))
    h_obtuse = 90 + h_leg   # at narrow (top) corners
    h_acute  = 90 - h_leg   # at wide  (bottom) corners

    cx = ox + long_o / 2; cy = oy + length_o * 0.55
    HBL=(cx-h_long/2,  cy+h_height/2)
    HTL=(cx-h_short/2, cy-h_height/2)
    HTR=(cx+h_short/2, cy-h_height/2)
    HBR=(cx+h_long/2,  cy+h_height/2)

    d1=uv(HBL,HTL); d2=uv(HTL,HTR); d3=uv(HTR,HBR); d4=uv(HBR,HBL)
    bs,be   = tp(HBL, d4, d1, h_r, h_acute)
    ts,te   = tp(HTL, d1, d2, h_r, h_obtuse)
    trs,tre = tp(HTR, d2, d3, h_r, h_obtuse)
    brs,bre = tp(HBR, d3, d4, h_r, h_acute)

    hole = (f"M {fmt(be[0])} {fmt(be[1])} "
            f"L {fmt(ts[0])} {fmt(ts[1])} {arc(ts,te,h_r)} "
            f"L {fmt(trs[0])} {fmt(trs[1])} {arc(trs,tre,h_r)} "
            f"L {fmt(brs[0])} {fmt(brs[1])} {arc(brs,bre,h_r)} "
            f"L {fmt(bs[0])} {fmt(bs[1])} {arc(bs,be,h_r)} Z")
    return hole, (HBL, HTL, HTR, HBR), h_obtuse, h_acute


def build_wall(ox, oy, w, depth_o, n_bot, fw_bot,
               n_left, fw_left, n_right, fw_right,
               left_out, right_out, bot_margin_right=None):
    """Rectangular wall panel w × depth_o. CW winding.

    bot_margin_right: right-side margin of slot zone from BR.
      If None: centred (symmetric). For WALL_LEG: pass tang_l (TL/narrow-end corner).
    """
    BL=(ox,   oy+depth_o); BR=(ox+w, oy+depth_o)
    TL=(ox,   oy);          TR=(ox+w, oy)
    if bot_margin_right is None:
        bot_margin_right = (w - n_bot*fw_bot) / 2
    bot_start = (ox+w - bot_margin_right, oy+depth_o)
    d_rtl=(-1.0, 0.0); d_up=(0.0,-1.0); d_dn=(0.0, 1.0)

    p = [f"M {fmt(BL[0])} {fmt(BL[1])}"]
    p.append(fingers(BL, n_left,  fw_left,  d_up,  left_out))
    p.append(f"L {fmt(TR[0])} {fmt(TR[1])}")
    p.append(fingers(TR, n_right, fw_right, d_dn,  right_out))
    p.append(f"L {fmt(bot_start[0])} {fmt(bot_start[1])}")
    p.append(fingers(bot_start, n_bot, fw_bot, d_rtl, False))
    p.append(f"L {fmt(BL[0])} {fmt(BL[1])}")
    p.append("Z")
    return " ".join(p)


def build_sheet(label, long_o, short_o, length_o, depth_o, soundhole):
    g = derive(long_o, short_o, length_o, depth_o)
    elements = []; bboxes = []
    x = M; y = M + 6

    # BASE
    bp = build_base(x, y, long_o, short_o, length_o, g)
    elements += [f'<path d="{bp}" {CUT}/>', lbl(x+long_o/2, y-3, f"BASE")]
    bboxes.append(("BASE", x, y, long_o, length_o))
    sh_corners = sh_obtuse = sh_acute = None
    if soundhole:
        hp, corners, h_obt, h_acu = build_soundhole(x, y, long_o, short_o, length_o)
        elements.append(f'<path d="{hp}" {CUT}/>')
        sh_corners = corners; sh_obtuse = h_obt; sh_acute = h_acu
    x += long_o + GAP

    # WALL_LONG: both ends slots (WALL_LEG fingers enter)
    wl = build_wall(x, y, long_o, depth_o,
                    g['n_long'], g['fw_long'],
                    g['n_ww'],   g['fw_ww'],
                    g['n_ww'],   g['fw_ww'],
                    False, False)
    elements += [f'<path d="{wl}" {CUT}/>', lbl(x+long_o/2, y-3, "WALL_LONG")]
    bboxes.append(("WALL_LONG", x, y, long_o, depth_o))
    x += long_o + GAP

    # WALL_SHORT: both ends fingers (protrude into WALL_LEG slots)
    ws = build_wall(x, y, short_o, depth_o,
                    g['n_short'], g['fw_short'],
                    g['n_ww'],    g['fw_ww'],
                    g['n_ww'],    g['fw_ww'],
                    True, True)
    elements += [f'<path d="{ws}" {CUT}/>', lbl(x+short_o/2, y-3, "WALL_SHORT")]
    bboxes.append(("WALL_SHORT", x, y, short_o, depth_o))
    x += short_o + GAP

    # WALL_LEG ×2: left=fingers(into WALL_LONG slots), right=slots(for WALL_SHORT fingers)
    # Bottom margin: tang_l from BR (= TL/narrow corner), tang_s falls out on BL side.
    # This aligns slots with BASE leg finger zone: [tang_s, leg_len-tang_l] from BL.
    for i in range(2):
        wleg = build_wall(x, y, g['leg_len'], depth_o,
                          g['n_leg'], g['fw_leg'],
                          g['n_ww'],  g['fw_ww'],
                          g['n_ww'],  g['fw_ww'],
                          True, False,
                          bot_margin_right=g['tang_l'])
        elements += [f'<path d="{wleg}" {CUT}/>', lbl(x+g['leg_len']/2, y-3, f"WALL_LEG_{i+1}")]
        bboxes.append((f"WALL_LEG_{i+1}", x, y, g['leg_len'], depth_o))
        x += g['leg_len'] + GAP

    total_w = x - GAP + M
    total_h = y + length_o + M

    # ── VERIFY ────────────────────────────────────────────────────────────────
    errors = []
    all_paths = re.findall(r'd="([^"]+)"', "\n".join(elements))

    for i, path in enumerate(all_paths):
        if not path.strip().endswith("Z"):
            errors.append(f"Path {i}: not closed")
        for tok in path.split():
            try:
                v = float(tok)
                if not math.isfinite(v):
                    errors.append(f"Path {i}: non-finite {v}")
                elif v < -DEPTH - 2 or v > max(total_w, total_h) + DEPTH + 2:
                    errors.append(f"Path {i}: coord {v:.3f} out of bounds")
            except ValueError:
                pass

    # Soundhole corner angles
    if sh_corners is not None:
        HBL, HTL, HTR, HBR = sh_corners
        def ia(v, prev, nxt):
            def u(a, b):
                dx=b[0]-a[0]; dy=b[1]-a[1]; m=math.sqrt(dx**2+dy**2); return dx/m, dy/m
            di=u(prev,v); do_=u(v,nxt)
            return math.degrees(math.acos(max(-1.0, min(1.0, (-di[0])*do_[0]+(-di[1])*do_[1]))))
        for name, v, prev, nxt, exp in [
            ("HTL", HTL, HBL, HTR, sh_obtuse),
            ("HTR", HTR, HTL, HBR, sh_obtuse),
            ("HBR", HBR, HTR, HBL, sh_acute),
            ("HBL", HBL, HBR, HTL, sh_acute),
        ]:
            a = ia(v, prev, nxt)
            if abs(a - exp) > 0.1:
                errors.append(f"Soundhole {name}: {a:.2f}° ≠ {exp:.2f}°")

    if errors:
        print(f"VERIFICATION FAILED ({label}) — not writing SVG")
        for e in errors: print(f"  {e}")
        sys.exit(1)

    print(f"Verification passed ({label}): {len(all_paths)} paths, 0 errors")

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{fmt(total_w)}mm" height="{fmt(total_h)}mm"
     viewBox="0 0 {fmt(total_w)} {fmt(total_h)}">
<rect width="{fmt(total_w)}" height="{fmt(total_h)}" fill="white"/>
''' + "\n".join(elements) + "\n</svg>"

    return svg, total_w, total_h, g


# ── Variants ──────────────────────────────────────────────────────────────────
VARIANTS = [
    # (label, long_o, short_o, length_o, depth_o, soundhole, filename)
    ("student",    65.0, 45.0,  45.0, 20.0, False, "test_cut_student.svg"),
    ("instrument", 80.0, 55.0, 100.0, 40.0, True,  "test_cut_instrument.svg"),
]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
os.makedirs(OUT_DIR, exist_ok=True)

for label, long_o, short_o, length_o, depth_o, soundhole, fname in VARIANTS:
    svg, w, h, g = build_sheet(label, long_o, short_o, length_o, depth_o, soundhole)
    out = os.path.join(OUT_DIR, fname)
    with open(out, "w") as f:
        f.write(svg)
    print(f"Written: {out}  ({w:.1f}×{h:.1f}mm)")
    print(f"  long={long_o:.0f} short={short_o:.0f} length={length_o:.0f} depth={depth_o:.0f} "
          f"leg_len={g['leg_len']:.1f} leg_angle={g['leg_angle']:.2f}°")
    print(f"  tang_s={g['tang_s']:.3f} tang_l={g['tang_l']:.3f}  "
          f"n_long={g['n_long']} n_short={g['n_short']} n_leg={g['n_leg']} n_ww={g['n_ww']}")
    print()
