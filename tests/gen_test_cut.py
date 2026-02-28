"""
gen_test_cut.py — trapezoid box confidence test cut set
3mm ply, 1:1, stroke-width="0.1" (unitless hairline).
5 panels: BASE, WALL_LONG, WALL_SHORT, WALL_LEG×2
All wall-to-wall and wall-to-base joints included.
Verify-or-abort before writing.

BURN MODEL (see spec §10.5 and proof 03 test 6):
  SVG paths are laser centerlines. Laser removes burn mm each side of every cut.
  drawn_tab  = fw + 2*burn  → physical_tab  = fw  (kerf removes 2*burn total)
  drawn_slot = fw - 2*burn + 2*tol  → physical_slot = fw + 2*tol
  nominal_fit = drawn_slot - drawn_tab = -4*burn + 2*tol

  burn=0.05, tol=0.0 → fit=-0.2mm  (rubber mallet — matches boxes.py default)
  burn=0.05, tol=0.1 → fit= 0.0mm  (hand press)
  Larger burn = tighter. Larger tol = looser. Tune in 0.01mm steps.
"""

import math, re, sys

# ── Parameters ────────────────────────────────────────────────────────────────
T    = 3.0
R    = max(5.0, 3.0 * T)   # 9mm corner radius
FW   = 3.0 * T             # 9mm nominal finger width
BURN = 0.05                # default: friction fit at typical CO2 kerf
TOL  = 0.0                 # 0.0=friction, 0.1=hand-press
DEPTH = T + BURN           # 3.05mm finger depth

# Tab/gap widths — correct burn model
TAB_W = FW + 2 * BURN              # 9.10mm drawn
GAP_W = FW - 2 * BURN + 2 * TOL   # 8.90mm drawn
FIT   = GAP_W - TAB_W             # -0.20mm nominal (friction fit)

long_o  = 65.0; short_o = 45.0; length_o = 45.0; depth_o = 20.0
leg_inset  = (long_o - short_o) / 2
leg_angle  = math.degrees(math.atan(leg_inset / length_o))
leg_len    = math.sqrt(length_o**2 + leg_inset**2)
long_end   = 90 + leg_angle
short_end  = 90 - leg_angle
tang_l     = R / math.tan(math.radians(long_end  / 2))
tang_s     = R / math.tan(math.radians(short_end / 2))

def odd_n(avail):
    n = max(3, round(avail / FW))
    return n if n % 2 == 1 else n + 1

avail_long  = long_o  - 2 * tang_s
avail_short = short_o - 2 * tang_l
avail_leg   = leg_len - tang_l - tang_s
n_long,  fw_long  = odd_n(avail_long),  avail_long  / odd_n(avail_long)
n_short, fw_short = odd_n(avail_short), avail_short / odd_n(avail_short)
n_leg,   fw_leg   = odd_n(avail_leg),   avail_leg   / odd_n(avail_leg)
n_ww,    fw_ww    = odd_n(depth_o),     depth_o     / odd_n(depth_o)

# Soundhole
h_long   = long_o * 0.28; h_short = h_long * (short_o / long_o)
h_height = h_long * 0.6;  h_r     = 2.0
h_inset  = (h_long - h_short) / 2
h_leg    = math.degrees(math.atan(h_inset / h_height))
h_obtuse = 90 + h_leg; h_acute = 90 - h_leg

GAP = 6.0; M = 10.0
CUT = 'fill="none" stroke="red" stroke-width="0.1"'
LBL = 'font-size="3.5" font-family="sans-serif" fill="#333" text-anchor="middle"'

def fmt(v): return f"{v:.4f}"
def uv(p1, p2):
    dx=p2[0]-p1[0]; dy=p2[1]-p1[1]; m=math.sqrt(dx**2+dy**2); return dx/m, dy/m
def tp(v, ea, eb, r, ang):
    td = r / math.tan(math.radians(ang / 2))
    return (v[0]-ea[0]*td, v[1]-ea[1]*td), (v[0]+eb[0]*td, v[1]+eb[1]*td)
def arc(s, e, r):
    return f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(e[0])} {fmt(e[1])}"
def lbl(x, y, t):
    return f'<text x="{fmt(x)}" y="{fmt(y)}" {LBL}>{t}</text>'

def fingers(p_start, n, fw_act, d_edge, d_out, is_slot):
    """
    Generate finger joint staircase from p_start along d_edge.
    is_slot=False: tabs protrude in d_out at drawn_tab width
    is_slot=True:  slots recessed in -d_out at drawn_gap width
    Burn model: drawn_tab=fw+2*burn (wider), drawn_slot=fw-2*burn+2*tol (narrower)
    First feature (i=0) is always a tab or slot.
    """
    tab_w = fw_act + 2 * BURN
    gap_w = fw_act - 2 * BURN + 2 * TOL
    sign  = 1.0 if not is_slot else -1.0
    cx, cy = p_start
    parts = []
    for i in range(n):
        w = tab_w if i % 2 == 0 else gap_w
        nx = cx + d_edge[0] * w
        ny = cy + d_edge[1] * w
        if i % 2 == 0:  # tab or slot
            parts.append(f"L {fmt(cx + d_out[0]*DEPTH*sign)} {fmt(cy + d_out[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx + d_out[0]*DEPTH*sign)} {fmt(ny + d_out[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        else:            # gap
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        cx, cy = nx, ny
    return " ".join(parts), (cx, cy)

# ── BASE ──────────────────────────────────────────────────────────────────────
def build_base(ox, oy):
    BL=(ox,             oy+length_o); BR=(ox+long_o,        oy+length_o)
    TR=(ox+leg_inset+short_o, oy);   TL=(ox+leg_inset,      oy)
    d_bl_tl=uv(BL,TL); d_tl_tr=uv(TL,TR); d_tr_br=uv(TR,BR); d_br_bl=uv(BR,BL)
    bl_s,bl_e = tp(BL, d_br_bl, d_bl_tl, R, short_end)
    tl_s,tl_e = tp(TL, d_bl_tl, d_tl_tr, R, long_end)
    tr_s,tr_e = tp(TR, d_tl_tr, d_tr_br, R, long_end)
    br_s,br_e = tp(BR, d_tr_br, d_br_bl, R, short_end)
    def out(d): return (-d[1], d[0])  # left of CW travel = outward

    p = [f"M {fmt(bl_e[0])} {fmt(bl_e[1])}"]
    f_segs, _ = fingers(bl_e, n_leg,   fw_leg,   d_bl_tl, out(d_bl_tl), False)
    p.append(f_segs)
    p.append(f"L {fmt(tl_s[0])} {fmt(tl_s[1])} {arc(tl_s,tl_e,R)}")
    f_segs, _ = fingers(tl_e, n_short, fw_short, d_tl_tr, out(d_tl_tr), False)
    p.append(f_segs)
    p.append(f"L {fmt(tr_s[0])} {fmt(tr_s[1])} {arc(tr_s,tr_e,R)}")
    f_segs, _ = fingers(tr_e, n_leg,   fw_leg,   d_tr_br, out(d_tr_br), False)
    p.append(f_segs)
    p.append(f"L {fmt(br_s[0])} {fmt(br_s[1])} {arc(br_s,br_e,R)}")
    f_segs, _ = fingers(br_e, n_long,  fw_long,  d_br_bl, out(d_br_bl), False)
    p.append(f_segs)
    p.append(f"L {fmt(bl_s[0])} {fmt(bl_s[1])} {arc(bl_s,bl_e,R)}")
    p.append("Z")

    cx = ox + long_o / 2; cy = oy + length_o * 0.55
    HTL=(cx-h_short/2, cy-h_height/2); HTR=(cx+h_short/2, cy-h_height/2)
    HBR=(cx+h_long/2,  cy+h_height/2); HBL=(cx-h_long/2,  cy+h_height/2)
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
    return " ".join(p), hole

# ── WALL ──────────────────────────────────────────────────────────────────────
def build_wall(ox, oy, w, n_bot, fw_bot, n_left, fw_left, left_slot,
               n_right, fw_right, right_slot):
    """
    Rectangular wall w × depth_o. CW: BL→TL→TR→BR→slots→BL.
    Top edge: plain (open top, no joints).
    Bottom edge: slots centred, complementary to BASE outward tabs.
    Left end (BL→TL upward): left_slot=True→slot, False→tab.
    Right end (TR→BR downward): right_slot=True→slot, False→tab.
    Explicit outward directions for all edges — no derivation from travel direction.
    """
    BL=(ox,   oy+depth_o); BR=(ox+w, oy+depth_o)
    TL=(ox,   oy);          TR=(ox+w, oy)

    d_up  = (0.0, -1.0); d_out_left  = (-1.0, 0.0)
    d_dn  = (0.0,  1.0); d_out_right = ( 1.0, 0.0)
    d_rtl = (-1.0, 0.0); d_out_bot   = ( 0.0, 1.0)

    # Bottom slot zone centred, matching BASE finger zone nominal width
    bot_zone_w = n_bot * fw_bot
    bot_margin = (w - bot_zone_w) / 2
    bot_start  = (ox + w - bot_margin, oy + depth_o)

    p = [f"M {fmt(BL[0])} {fmt(BL[1])}"]
    f_segs, _ = fingers(BL, n_left, fw_left, d_up, d_out_left, left_slot)
    p.append(f_segs)
    p.append(f"L {fmt(TL[0])} {fmt(TL[1])}")   # snap to TL (tab/gap widths ≠ fw)
    p.append(f"L {fmt(TR[0])} {fmt(TR[1])}")   # top edge plain
    f_segs, _ = fingers(TR, n_right, fw_right, d_dn, d_out_right, right_slot)
    p.append(f_segs)
    p.append(f"L {fmt(BR[0])} {fmt(BR[1])}")
    p.append(f"L {fmt(bot_start[0])} {fmt(bot_start[1])}")
    f_segs, _ = fingers(bot_start, n_bot, fw_bot, d_rtl, d_out_bot, True)
    p.append(f_segs)
    p.append(f"L {fmt(BL[0])} {fmt(BL[1])}")
    p.append("Z")
    return " ".join(p)

# ── Layout ────────────────────────────────────────────────────────────────────
elements = []; bboxes = []
x = M; y = M + 6

bp, hp = build_base(x, y)
elements += [f'<path d="{bp}" {CUT}/>', f'<path d="{hp}" {CUT}/>',
             lbl(x + long_o/2, y - 3, "BASE")]
bboxes.append(("BASE", x, y, long_o, length_o))
x += long_o + GAP

wl = build_wall(x, y, length_o, n_long, fw_long,
                n_ww, fw_ww, True, n_ww, fw_ww, True)
elements += [f'<path d="{wl}" {CUT}/>', lbl(x + length_o/2, y - 3, "WALL_LONG")]
bboxes.append(("WALL_LONG", x, y, length_o, depth_o))
x += length_o + GAP

ws = build_wall(x, y, short_o, n_short, fw_short,
                n_ww, fw_ww, False, n_ww, fw_ww, False)
elements += [f'<path d="{ws}" {CUT}/>', lbl(x + short_o/2, y - 3, "WALL_SHORT")]
bboxes.append(("WALL_SHORT", x, y, short_o, depth_o))
x += short_o + GAP

for i in range(2):
    wleg = build_wall(x, y, leg_len, n_leg, fw_leg,
                      n_ww, fw_ww, False, n_ww, fw_ww, True)
    elements += [f'<path d="{wleg}" {CUT}/>', lbl(x + leg_len/2, y - 3, "WALL_LEG")]
    bboxes.append((f"WALL_LEG_{i}", x, y, leg_len, depth_o))
    x += leg_len + GAP

total_w = x - GAP + M
total_h = y + length_o + M + 6

# ── VERIFY-OR-ABORT ───────────────────────────────────────────────────────────
errors = []
all_paths = re.findall(r'd="([^"]+)"', "\n".join(elements))

for i, path in enumerate(all_paths):
    if not path.strip().endswith("Z"):
        errors.append(f"Path {i}: not closed")
    for tok in path.split():
        try:
            n = float(tok)
            if not math.isfinite(n):
                errors.append(f"Path {i}: non-finite {n}")
            if n < -DEPTH - 2 or n > total_w + DEPTH + 2:
                errors.append(f"Path {i}: coord {n:.3f} out of bounds")
        except ValueError:
            pass

# Burn model sanity
expected_fit = -4*BURN + 2*TOL
if abs(FIT - expected_fit) > 1e-9:
    errors.append(f"Burn model: FIT={FIT:.4f} ≠ -4*BURN+2*TOL={expected_fit:.4f}")
if TOL == 0.0 and FIT >= 0:
    errors.append(f"Burn model: tol=0 but fit={FIT:.3f}mm is not interference")

# Soundhole corner angles
cx_sh = M + long_o/2; cy_sh = y + length_o * 0.55
HTL=(cx_sh-h_short/2, cy_sh-h_height/2); HTR=(cx_sh+h_short/2, cy_sh-h_height/2)
HBR=(cx_sh+h_long/2,  cy_sh+h_height/2); HBL=(cx_sh-h_long/2,  cy_sh+h_height/2)
def ia(v, prev, nxt):
    def u(a, b):
        dx=b[0]-a[0]; dy=b[1]-a[1]; m=math.sqrt(dx**2+dy**2); return dx/m, dy/m
    di=u(prev,v); do_=u(v,nxt)
    return math.degrees(math.acos(max(-1.0, min(1.0, (-di[0])*do_[0]+(-di[1])*do_[1]))))
for name, v, prev, nxt, exp in [
    ("HTL",HTL,HBL,HTR,h_obtuse), ("HTR",HTR,HTL,HBR,h_obtuse),
    ("HBR",HBR,HTR,HBL,h_acute),  ("HBL",HBL,HBR,HTL,h_acute)
]:
    a = ia(v, prev, nxt)
    if abs(a - exp) > 0.1:
        errors.append(f"Soundhole {name}: {a:.2f}° ≠ {exp:.2f}°")

if errors:
    print("VERIFICATION FAILED — SVG not written")
    for e in errors: print(f"  ERROR: {e}")
    sys.exit(1)

print(f"Verification passed: {len(all_paths)} paths, 0 errors")
print(f"Burn model: drawn_tab={TAB_W:.3f}mm  drawn_slot={GAP_W:.3f}mm  "
      f"nominal_fit={FIT:+.3f}mm  depth={DEPTH:.3f}mm")

# ── WRITE ─────────────────────────────────────────────────────────────────────
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{fmt(total_w)}mm" height="{fmt(total_h)}mm"
     viewBox="0 0 {fmt(total_w)} {fmt(total_h)}">
<!-- trapezoid_box test cut — 3mm ply — 1:1 scale
     burn={BURN}mm  tol={TOL}mm
     drawn_tab={TAB_W:.3f}mm  drawn_slot={GAP_W:.3f}mm  nominal_fit={FIT:+.3f}mm
     burn=0.05,tol=0.0 -> fit=-0.2mm (friction). burn=0.05,tol=0.1 -> fit=0.0mm (hand press) -->
<rect width="{fmt(total_w)}" height="{fmt(total_h)}" fill="white"/>
''' + "\n".join(elements) + "\n</svg>"

out = "/mnt/user-data/outputs/test_cut_set.svg"
with open(out, "w") as f:
    f.write(svg)
print(f"Written: {out}  ({total_w:.1f}×{total_h:.1f}mm)")
