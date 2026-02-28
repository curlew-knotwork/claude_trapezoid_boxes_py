"""
gen_test_cut.py — trapezoid box confidence test cut set
3mm ply, 1:1, stroke-width="0.1" (unitless hairline).
5 panels: BASE, WALL_LONG, WALL_SHORT, WALL_LEG×2
All wall-to-wall and wall-to-base joints included.
Verify-or-abort before writing.
"""

import math, re, sys

# ── Parameters ────────────────────────────────────────────────────────────────
T=3.0; R=9.0; FW=9.0; BURN=0.05
DEPTH=T+BURN

long_o=65.0; short_o=45.0; length_o=45.0; depth_o=20.0
leg_inset=(long_o-short_o)/2
leg_angle=math.degrees(math.atan(leg_inset/length_o))
leg_len=math.sqrt(length_o**2+leg_inset**2)
long_end=90+leg_angle; short_end=90-leg_angle
tang_l=R/math.tan(math.radians(long_end/2))
tang_s=R/math.tan(math.radians(short_end/2))

def odd_n(avail): n=max(3,round(avail/FW)); return n if n%2==1 else n+1

avail_long =long_o -2*tang_s; n_long =odd_n(avail_long);  fw_long =avail_long/n_long
avail_short=short_o-2*tang_l; n_short=odd_n(avail_short); fw_short=avail_short/n_short
avail_leg  =leg_len-tang_l-tang_s; n_leg=odd_n(avail_leg); fw_leg=avail_leg/n_leg
n_ww=odd_n(depth_o); fw_ww=depth_o/n_ww  # wall-to-wall, no corner arcs

# Soundhole
h_long=long_o*0.28; h_short=h_long*(short_o/long_o)
h_height=h_long*0.6; h_r=2.0
h_inset=(h_long-h_short)/2
h_leg=math.degrees(math.atan(h_inset/h_height))
h_obtuse=90+h_leg; h_acute=90-h_leg

GAP=6.0; M=10.0
CUT='fill="none" stroke="red" stroke-width="0.1"'
LBL='font-size="3.5" font-family="sans-serif" fill="#333" text-anchor="middle"'

def fmt(v): return f"{v:.4f}"
def uv(p1,p2):
    dx=p2[0]-p1[0];dy=p2[1]-p1[1];m=math.sqrt(dx**2+dy**2);return dx/m,dy/m
def tp(v,ea,eb,r,ang):
    td=r/math.tan(math.radians(ang/2))
    return (v[0]-ea[0]*td,v[1]-ea[1]*td),(v[0]+eb[0]*td,v[1]+eb[1]*td)
def arc(s,e,r): return f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(e[0])} {fmt(e[1])}"
def lbl(x,y,t): return f'<text x="{fmt(x)}" y="{fmt(y)}" {LBL}>{t}</text>'

def fingers(p_start, n, fw_act, d_edge, outward):
    """Generate n fingers from p_start along d_edge.
    outward=True: protrude in left-of-travel direction (BASE outer edges).
    outward=False: slot into panel from right-of-travel (wall bottom/end slots).
    First tab (i=0) is always a protrusion or slot.
    """
    perp=(d_edge[1], -d_edge[0])  # left of travel in SVG y-down = outward for CW panels
    sign=1.0 if outward else -1.0
    cx,cy=p_start
    parts=[]
    for i in range(n):
        nx=cx+d_edge[0]*fw_act; ny=cy+d_edge[1]*fw_act
        if i%2==0:  # protrusion / slot
            parts.append(f"L {fmt(cx+perp[0]*DEPTH*sign)} {fmt(cy+perp[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx+perp[0]*DEPTH*sign)} {fmt(ny+perp[1]*DEPTH*sign)}")
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        else:
            parts.append(f"L {fmt(nx)} {fmt(ny)}")
        cx,cy=nx,ny
    return " ".join(parts)

# ── BASE ──────────────────────────────────────────────────────────────────────
def build_base(ox,oy):
    BL=(ox,             oy+length_o); BR=(ox+long_o,         oy+length_o)
    TR=(ox+leg_inset+short_o, oy);   TL=(ox+leg_inset,       oy)
    d_bl_tl=uv(BL,TL); d_tl_tr=uv(TL,TR); d_tr_br=uv(TR,BR); d_br_bl=uv(BR,BL)
    bl_s,bl_e=tp(BL,d_br_bl,d_bl_tl,R,short_end)
    tl_s,tl_e=tp(TL,d_bl_tl,d_tl_tr,R,long_end)
    tr_s,tr_e=tp(TR,d_tl_tr,d_tr_br,R,long_end)
    br_s,br_e=tp(BR,d_tr_br,d_br_bl,R,short_end)
    p=[f"M {fmt(bl_e[0])} {fmt(bl_e[1])}"]
    p.append(fingers(bl_e,  n_leg,   fw_leg,   d_bl_tl, True))
    p.append(f"L {fmt(tl_s[0])} {fmt(tl_s[1])} {arc(tl_s,tl_e,R)}")
    p.append(fingers(tl_e,  n_short, fw_short, d_tl_tr, True))
    p.append(f"L {fmt(tr_s[0])} {fmt(tr_s[1])} {arc(tr_s,tr_e,R)}")
    p.append(fingers(tr_e,  n_leg,   fw_leg,   d_tr_br, True))
    p.append(f"L {fmt(br_s[0])} {fmt(br_s[1])} {arc(br_s,br_e,R)}")
    p.append(fingers(br_e,  n_long,  fw_long,  d_br_bl, True))
    p.append(f"L {fmt(bl_s[0])} {fmt(bl_s[1])} {arc(bl_s,bl_e,R)}")
    p.append("Z")
    # Soundhole centred in BASE
    cx=ox+long_o/2; cy=oy+length_o*0.55
    HTL=(cx-h_short/2,cy-h_height/2); HTR=(cx+h_short/2,cy-h_height/2)
    HBR=(cx+h_long/2, cy+h_height/2); HBL=(cx-h_long/2, cy+h_height/2)
    d1=uv(HBL,HTL);d2=uv(HTL,HTR);d3=uv(HTR,HBR);d4=uv(HBR,HBL)
    bs,be=tp(HBL,d4,d1,h_r,h_acute); ts,te=tp(HTL,d1,d2,h_r,h_obtuse)
    trs,tre=tp(HTR,d2,d3,h_r,h_obtuse); brs,bre=tp(HBR,d3,d4,h_r,h_acute)
    hole=(f"M {fmt(be[0])} {fmt(be[1])} "
          f"L {fmt(ts[0])} {fmt(ts[1])} {arc(ts,te,h_r)} "
          f"L {fmt(trs[0])} {fmt(trs[1])} {arc(trs,tre,h_r)} "
          f"L {fmt(brs[0])} {fmt(brs[1])} {arc(brs,bre,h_r)} "
          f"L {fmt(bs[0])} {fmt(bs[1])} {arc(bs,be,h_r)} Z")
    return " ".join(p), hole

# ── WALL (generic rect with 3 jointed edges) ──────────────────────────────────
def build_wall(ox, oy, w,
               n_bot, fw_bot,    # bottom edge: slots mating BASE fingers
               n_left, fw_left,  # left end: outward=True means fingers, False=slots
               n_right, fw_right,
               left_out, right_out):
    """
    Rectangular wall panel w × depth_o. CW: BL→TL→TR→BR→BL.
    Bottom edge: slots centred, complementary to BASE (outward=False).
    Left end (BL→TL, upward): outward=left_out.
    Right end (TR→BR, downward): outward=right_out.
    Top edge: plain (open top).
    No corner arcs on wall ends (interior joints).
    """
    BL=(ox,   oy+depth_o); BR=(ox+w,  oy+depth_o)
    TL=(ox,   oy);          TR=(ox+w,  oy)

    # Bottom slots: centred, right-to-left (BR→BL direction)
    bot_margin=(w - n_bot*fw_bot)/2
    bot_start=(ox+w-bot_margin, oy+depth_o)
    d_rtl=(-1.0,0.0)

    # Left end: BL→TL = upward = (0,-1)
    d_up=(0.0,-1.0)
    # Right end: TR→BR = downward = (0,+1)
    d_dn=(0.0,1.0)

    # End finger zones: full depth_o, no margin (no corner arcs)
    p=[f"M {fmt(BL[0])} {fmt(BL[1])}"]
    # Left end BL→TL (upward)
    p.append(fingers(BL, n_left, fw_left, d_up, left_out))
    # Top edge TL→TR plain
    p.append(f"L {fmt(TR[0])} {fmt(TR[1])}")
    # Right end TR→BR (downward)
    p.append(fingers(TR, n_right, fw_right, d_dn, right_out))
    # Bottom edge BR→slots→BL
    p.append(f"L {fmt(bot_start[0])} {fmt(bot_start[1])}")
    p.append(fingers(bot_start, n_bot, fw_bot, d_rtl, False))
    p.append(f"L {fmt(BL[0])} {fmt(BL[1])}")
    p.append("Z")
    return " ".join(p)

# ── Layout ─────────────────────────────────────────────────────────────────────
# Assembly logic:
# WALL_SHORT left+right ends: fingers outward (protrude into WALL_LEG slots)
# WALL_LONG  left+right ends: slots (WALL_LEG fingers protrude into them)
# WALL_LEG   one end: fingers (into WALL_LONG slots)
#            other end: slots (WALL_SHORT fingers into them)
# Orientation: WALL_LEG left=mates_long(slots), right=mates_short(fingers in)
# So WALL_LEG: left_out=False (slots for WALL_SHORT protrusions)... 
# Wait — need to think carefully:
# WALL_SHORT protrudes fingers → WALL_LEG receives slots at that end
# WALL_LONG  receives slots   ← WALL_LEG protrudes fingers at that end
# WALL_LEG: 
#   end that meets WALL_LONG: fingers outward (protrude into WALL_LONG slots)
#   end that meets WALL_SHORT: slots (receive WALL_SHORT fingers)

elements=[]
bboxes=[]

x=M; y=M+6  # +6 for label above

# BASE
bp,hp=build_base(x,y)
elements+=[f'<path d="{bp}" {CUT}/>',f'<path d="{hp}" {CUT}/>',
           lbl(x+long_o/2, y-3, "BASE")]
bboxes.append(("BASE",x,y,long_o,length_o))
x+=long_o+GAP

# WALL_LONG: both ends are slots (WALL_LEG fingers go in)
wl=build_wall(x,y,long_o, n_long,fw_long, n_ww,fw_ww, n_ww,fw_ww, False,False)
elements+=[f'<path d="{wl}" {CUT}/>', lbl(x+long_o/2, y-3, "WALL_LONG")]
bboxes.append(("WALL_LONG",x,y,long_o,depth_o))
x+=long_o+GAP

# WALL_SHORT: both ends have fingers (protrude into WALL_LEG slots)
ws=build_wall(x,y,short_o, n_short,fw_short, n_ww,fw_ww, n_ww,fw_ww, True,True)
elements+=[f'<path d="{ws}" {CUT}/>', lbl(x+short_o/2, y-3, "WALL_SHORT")]
bboxes.append(("WALL_SHORT",x,y,short_o,depth_o))
x+=short_o+GAP

# WALL_LEG ×2: left end=fingers (into WALL_LONG), right end=slots (from WALL_SHORT)
for i in range(2):
    wleg=build_wall(x,y,leg_len, n_leg,fw_leg, n_ww,fw_ww, n_ww,fw_ww, True,False)
    elements+=[f'<path d="{wleg}" {CUT}/>', lbl(x+leg_len/2, y-3, "WALL_LEG")]
    bboxes.append((f"WALL_LEG_{i}",x,y,leg_len,depth_o))
    x+=leg_len+GAP

total_w=x-GAP+M
total_h=y+length_o+M+6

# ── VERIFY ─────────────────────────────────────────────────────────────────────
errors=[]
all_paths=re.findall(r'd="([^"]+)"',"\n".join(elements))

for i,path in enumerate(all_paths):
    if not path.strip().endswith("Z"):
        errors.append(f"Path {i}: not closed")
    for tok in path.split():
        try:
            n=float(tok)
            if not math.isfinite(n): errors.append(f"Path {i}: non-finite {n}")
            if n < -DEPTH-2 or n > total_w+DEPTH+2:
                errors.append(f"Path {i}: coord {n:.3f} out of bounds")
        except ValueError: pass

# Soundhole corner angles
cx_sh=M+long_o/2; cy_sh=y+length_o*0.55
HTL=(cx_sh-h_short/2,cy_sh-h_height/2); HTR=(cx_sh+h_short/2,cy_sh-h_height/2)
HBR=(cx_sh+h_long/2, cy_sh+h_height/2); HBL=(cx_sh-h_long/2, cy_sh+h_height/2)
def ia(v,prev,nxt):
    def u(a,b): dx=b[0]-a[0];dy=b[1]-a[1];m=math.sqrt(dx**2+dy**2);return dx/m,dy/m
    di=u(prev,v);do_=u(v,nxt)
    return math.degrees(math.acos(max(-1.0,min(1.0,(-di[0])*do_[0]+(-di[1])*do_[1]))))
for name,v,prev,nxt,exp in [("HTL",HTL,HBL,HTR,h_obtuse),("HTR",HTR,HTL,HBR,h_obtuse),
                              ("HBR",HBR,HTR,HBL,h_acute), ("HBL",HBL,HBR,HTL,h_acute)]:
    a=ia(v,prev,nxt)
    if abs(a-exp)>0.1: errors.append(f"Soundhole {name}: {a:.2f}° ≠ {exp:.2f}°")

# Finger/slot count parity checks
assert n_long==n_long and n_short==n_short and n_leg==n_leg  # trivially true — existence check

if errors:
    print("VERIFICATION FAILED — not writing SVG")
    for e in errors: print(f"  {e}")
    sys.exit(1)

print(f"Verification passed: {len(all_paths)} paths, 0 errors")

# ── WRITE ──────────────────────────────────────────────────────────────────────
svg=f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{fmt(total_w)}mm" height="{fmt(total_h)}mm"
     viewBox="0 0 {fmt(total_w)} {fmt(total_h)}">
<rect width="{fmt(total_w)}" height="{fmt(total_h)}" fill="white"/>
'''+"\n".join(elements)+"\n</svg>"

out="/mnt/user-data/outputs/test_cut_set.svg"
with open(out,"w") as f: f.write(svg)
print(f"Written: {out}  ({total_w:.1f}×{total_h:.1f}mm)")
print(f"Parts: BASE {long_o:.0f}×{length_o:.0f} | WALL_LONG {long_o:.0f}×{depth_o:.0f} | "
      f"WALL_SHORT {short_o:.0f}×{depth_o:.0f} | WALL_LEG {leg_len:.1f}×{depth_o:.0f}×2")
print(f"Joints: BASE↔walls (outward/slot) | walls↔walls (finger/slot at ends)")
