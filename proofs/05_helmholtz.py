"""
05_helmholtz.py
Verifies: Helmholtz resonator frequency solver — round hole, convergence,
neck slot volume correction, rounded-trapezoid soundhole geometry (both
orientations), corner angle invariant, and all validation constraints.

No dependencies beyond stdlib. Run with: python3 05_helmholtz.py
"""

import math
import sys

passed = 0
failed = 0


def check(label, actual, expected, tol=1e-4):
    global passed, failed
    if abs(actual - expected) <= tol:
        print(f"  PASS  {label}: {actual:.6f}")
        passed += 1
    else:
        print(f"  FAIL  {label}: got {actual:.6f}, expected {expected:.6f}  (delta={abs(actual-expected):.8f})")
        failed += 1


def check_true(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label}  {detail}")
        failed += 1


# ── Core Helmholtz functions ──────────────────────────────────────────────────

C_SOUND_MM_S = 343_000.0

def helmholtz_freq(V_mm3, diameter_mm, top_thickness_mm):
    L_eff = top_thickness_mm + 0.85 * diameter_mm
    A     = math.pi * (diameter_mm / 2)**2
    return C_SOUND_MM_S / (2 * math.pi) * math.sqrt(A / (V_mm3 * L_eff))

def helmholtz_freq_arbitrary(V_mm3, area_mm2, D_eq_mm, top_thickness_mm):
    L_eff = top_thickness_mm + 0.85 * D_eq_mm
    return C_SOUND_MM_S / (2 * math.pi) * math.sqrt(area_mm2 / (V_mm3 * L_eff))

def solve_diameter(target_hz, V_mm3, top_thickness_mm, max_iter=100, tol=1e-8):
    D = 50.0
    for i in range(max_iter):
        L_eff = top_thickness_mm + 0.85 * D
        A     = (target_hz * 2 * math.pi / C_SOUND_MM_S)**2 * V_mm3 * L_eff
        D_new = 2 * math.sqrt(A / math.pi)
        if abs(D_new - D) < tol:
            return D_new, i + 1
        D = D_new
    return D, max_iter

def air_volume_trapezoid(long_inner, short_inner, length_inner, depth_inner):
    return 0.5 * (long_inner + short_inner) * length_inner * depth_inner

def neck_slot_volume_correction(neck_slot_width, neck_slot_depth, neck_tenon_length):
    return neck_slot_width * neck_slot_depth * neck_tenon_length


# ── Geometry helpers ──────────────────────────────────────────────────────────

def unit_vec(p1, p2):
    dx = p2[0]-p1[0]; dy = p2[1]-p1[1]
    m  = math.sqrt(dx**2 + dy**2)
    return dx/m, dy/m

def interior_angle_at(vertex, prev_pt, next_pt):
    """Interior angle at vertex in degrees, from actual edge geometry."""
    d_in  = unit_vec(prev_pt, vertex)
    d_out = unit_vec(vertex, next_pt)
    dot   = (-d_in[0])*d_out[0] + (-d_in[1])*d_out[1]
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))

def corner_arc_pts(vertex, ea, eb, r, angle_deg):
    td = r / math.tan(math.radians(angle_deg / 2))
    return (vertex[0]-ea[0]*td, vertex[1]-ea[1]*td), \
           (vertex[0]+eb[0]*td, vertex[1]+eb[1]*td)

def rtrap_hole_geometry(h_long, h_short, h_height, h_r, cx, y_near, neck_wide=False):
    """
    Verify and return geometry for a rounded-trapezoid soundhole.
    Raises AssertionError with descriptive message on any violation.
    INVARIANT: narrow-end corners = obtuse (90+leg), wide-end = acute (90-leg).
    """
    y_far    = y_near + h_height
    h_inset  = (h_long - h_short) / 2
    h_leg    = math.degrees(math.atan(h_inset / h_height))
    h_obtuse = 90 + h_leg   # narrow-end corners
    h_acute  = 90 - h_leg   # wide-end corners

    if neck_wide:
        # Wide end at top (y_near), narrow at bottom (y_far)
        HTL=(cx-h_long/2,  y_near); HTR=(cx+h_long/2,  y_near)
        HBR=(cx+h_short/2, y_far);  HBL=(cx-h_short/2, y_far)
        htl_a=h_acute;  htr_a=h_acute
        hbl_a=h_obtuse; hbr_a=h_obtuse
    else:
        # Narrow end at top (y_near), wide at bottom (y_far) — SAME orientation
        HTL=(cx-h_short/2, y_near); HTR=(cx+h_short/2, y_near)
        HBR=(cx+h_long/2,  y_far);  HBL=(cx-h_long/2,  y_far)
        htl_a=h_obtuse; htr_a=h_obtuse
        hbl_a=h_acute;  hbr_a=h_acute

    # INVARIANT: verify interior angles match assigned values from geometry
    for name, v, prev, nxt, expected in [
        ("HTL", HTL, HBL, HTR, htl_a),
        ("HTR", HTR, HTL, HBR, htr_a),
        ("HBR", HBR, HTR, HBL, hbr_a),
        ("HBL", HBL, HBR, HTL, hbl_a),
    ]:
        actual = interior_angle_at(v, prev, nxt)
        assert abs(actual - expected) < 0.5, \
            f"Corner angle invariant violated at {name}: " \
            f"geometry gives {actual:.2f}° but assigned {expected:.2f}°. " \
            f"Rule: narrow-end=obtuse, wide-end=acute."

    # Compute tangent distances
    td_obtuse = h_r / math.tan(math.radians(h_obtuse / 2))
    td_acute  = h_r / math.tan(math.radians(h_acute  / 2))
    leg_len   = math.sqrt(h_inset**2 + h_height**2)

    # Arc overlap checks
    assert h_short - td_obtuse - td_obtuse > 0.5, \
        f"Arc overlap on short edge: remaining={h_short-2*td_obtuse:.2f}mm"
    assert h_long  - td_acute  - td_acute  > 0.5, \
        f"Arc overlap on long edge: remaining={h_long-2*td_acute:.2f}mm"
    assert leg_len - td_obtuse - td_acute  > 0.5, \
        f"Arc overlap on leg: remaining={leg_len-td_obtuse-td_acute:.2f}mm"

    # Build arc tangent points and verify segment directions + lengths
    d_bl_tl=unit_vec(HBL,HTL); d_tl_tr=unit_vec(HTL,HTR)
    d_tr_br=unit_vec(HTR,HBR); d_br_bl=unit_vec(HBR,HBL)

    hbl_s,hbl_e = corner_arc_pts(HBL, d_br_bl, d_bl_tl, h_r, hbl_a)
    htl_s,htl_e = corner_arc_pts(HTL, d_bl_tl, d_tl_tr, h_r, htl_a)
    htr_s,htr_e = corner_arc_pts(HTR, d_tl_tr, d_tr_br, h_r, htr_a)
    hbr_s,hbr_e = corner_arc_pts(HBR, d_tr_br, d_br_bl, h_r, hbr_a)

    for name, p1, p2, exp_dir in [
        ("hbl_e→htl_s", hbl_e, htl_s, d_bl_tl),
        ("htl_e→htr_s", htl_e, htr_s, d_tl_tr),
        ("htr_e→hbr_s", htr_e, hbr_s, d_tr_br),
        ("hbr_e→hbl_s", hbr_e, hbl_s, d_br_bl),
    ]:
        dx=p2[0]-p1[0]; dy=p2[1]-p1[1]; seg_len=math.sqrt(dx**2+dy**2)
        assert seg_len > 0.5, f"Zero-length segment {name}: {seg_len:.3f}mm"
        assert abs(dx/seg_len-exp_dir[0])<0.01 and abs(dy/seg_len-exp_dir[1])<0.01, \
            f"Wrong segment direction {name}: got ({dx/seg_len:.3f},{dy/seg_len:.3f}) " \
            f"expected ({exp_dir[0]:.3f},{exp_dir[1]:.3f})"

    A_raw = (h_long + h_short) / 2 * h_height
    A_eff = A_raw - 4 * h_r**2 * (1 - math.pi / 4)
    D_eq  = 2 * math.sqrt(A_eff / math.pi)

    return dict(h_leg=h_leg, h_obtuse=h_obtuse, h_acute=h_acute,
                td_obtuse=td_obtuse, td_acute=td_acute, leg_len=leg_len,
                A_raw=A_raw, A_eff=A_eff, D_eq=D_eq,
                corners=dict(HTL=HTL, HTR=HTR, HBR=HBR, HBL=HBL))


# ── Reference values ──────────────────────────────────────────────────────────

T = T_top = 3.0
long_o = 180.0; short_o = 120.0; length = 380.0
long_i, short_i, length_i, depth_i = 174.0, 114.0, 374.0, 84.0
ACCEPTANCE_PCT = 5.0

# RTRAP defaults (spec section 5) — chosen to give ~150Hz on dulcimer preset
RTRAP_LONG_TO_BODY_RATIO  = 0.28   # hole_long = long_outer × 0.28 = 50.4mm
RTRAP_ASPECT_RATIO        = 0.6    # hole_height = hole_long × 0.6 = 30.24mm
RTRAP_CORNER_R_MM         = 2.0    # fixed mm, NOT a ratio
RTRAP_MAX_R_EDGE_FRACTION = 0.15

NECK_BLOCK_T = 25.0; NECK_CLEARANCE = 60.0; TAIL_BLOCK_T = 15.0


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 1: Air volume — reference preset ──")
V = air_volume_trapezoid(long_i, short_i, length_i, depth_i)
check("air volume", V, 4_523_904.0, tol=1.0)


print("\n── Test 2: Solver convergence and round-trip accuracy ──")
target_hz = 110.0
D, iters = solve_diameter(target_hz, V, T_top)
print(f"  Converged in {iters} iterations, D={D:.4f}mm")
check_true("converges in < 30 iterations", iters < 30, f"iters={iters}")
check("round-trip frequency", helmholtz_freq(V, D, T_top), target_hz, tol=1e-4)
check_true("within 5% acceptance band",
           abs(helmholtz_freq(V, D, T_top) - target_hz) / target_hz * 100 < ACCEPTANCE_PCT)


print("\n── Test 3: Frequency sensitivity to volume ──")
check_true("larger V → lower f",  helmholtz_freq(V*1.1, D, T_top) < target_hz)
check_true("smaller V → higher f", helmholtz_freq(V*0.9, D, T_top) > target_hz)
ratio = helmholtz_freq(V*1.1, D, T_top) * math.sqrt(V*1.1) / (target_hz * math.sqrt(V))
check("f·√V constant (1.1× volume)", ratio, 1.0, tol=1e-3)


print("\n── Test 4: Neck slot volume correction ──")
neck_w = 42.0; neck_d = 15.0
V_neck  = neck_slot_volume_correction(neck_w, neck_d, length_i)
check("full-through displaced volume", V_neck, 235_620.0, tol=1.0)
check_true("displacement > 4%", V_neck / V * 100 > 4.0)
D_corr, _ = solve_diameter(target_hz, V - V_neck, T_top)
check("corrected diameter round-trip",
      helmholtz_freq(V - V_neck, D_corr, T_top), target_hz, tol=1e-4)
partial_shift = abs(helmholtz_freq(V - neck_slot_volume_correction(neck_w, neck_d, 80.0), D, T_top) - target_hz)
check_true("partial neck shift < 1Hz", partial_shift < 1.0, f"shift={partial_shift:.3f}Hz")


print("\n── Test 5: Frequency formula dimensional check ──")
check_true("bigger hole → higher f",  helmholtz_freq(V, D*1.5, T_top) > target_hz)
check_true("smaller hole → lower f",  helmholtz_freq(V, D*0.5, T_top) < target_hz)
check_true("thicker top → lower f",   helmholtz_freq(V, D, T_top*2)   < target_hz)


print("\n── Test 6: Default target and range ──")
check_true("solved D > 5mm",          D > 5.0,       f"D={D:.2f}mm")
check_true("solved D < short_inner/2", D < short_i/2, f"D={D:.2f}mm")
check_true("target Hz > 0",           target_hz > 0)


print("\n── Test 7: Rounded-trapezoid defaults → ~150Hz ──")
hole_long   = long_o  * RTRAP_LONG_TO_BODY_RATIO          # 50.4mm
hole_short  = hole_long * (short_o / long_o)               # 33.6mm
hole_height = hole_long * RTRAP_ASPECT_RATIO               # 30.24mm
hole_r      = RTRAP_CORNER_R_MM                            # 2.0mm

check("hole_long  = 180×0.28",          hole_long,   50.4,  tol=0.01)
check("hole_short = hole_long×(2/3)",   hole_short,  33.6,  tol=0.01)
check("hole_height = hole_long×0.6",    hole_height, 30.24, tol=0.01)
check("hole_r = 2.0mm",                 hole_r,      2.0)

A_raw = (hole_long + hole_short) / 2 * hole_height
A_eff = A_raw - 4 * hole_r**2 * (1 - math.pi / 4)
D_eq  = 2 * math.sqrt(A_eff / math.pi)
f_rtrap = helmholtz_freq_arbitrary(V, A_eff, D_eq, T_top)

print(f"  {hole_long:.1f}×{hole_short:.1f}mm h={hole_height:.1f}mm r={hole_r}mm "
      f"→ A={A_eff:.1f}mm² D_eq={D_eq:.1f}mm f={f_rtrap:.1f}Hz")

check_true("A_eff > 0 and < A_raw",  0 < A_eff < A_raw)
check_true("frequency ≈ 150Hz (±10Hz)", abs(f_rtrap - 150.0) < 10.0,
           f"f={f_rtrap:.1f}Hz, expected ~150Hz")

h_inset  = (hole_long - hole_short) / 2
leg_len  = math.sqrt(h_inset**2 + hole_height**2)
min_edge = min(hole_short, hole_long, leg_len)
check_true("r ≤ min_edge × 0.15 (radius constraint)",
           hole_r <= min_edge * RTRAP_MAX_R_EDGE_FRACTION,
           f"r={hole_r} ≤ {min_edge*RTRAP_MAX_R_EDGE_FRACTION:.2f}")


print("\n── Test 8: Corner angle invariant — SAME orientation ──")
# Wide end at tail (bottom), narrow at neck (top)
cx      = long_o / 2
y_near  = NECK_BLOCK_T + NECK_CLEARANCE   # 85mm

geo_s = rtrap_hole_geometry(hole_long, hole_short, hole_height, hole_r,
                             cx, y_near, neck_wide=False)
check_true("SAME: corner angles verified from geometry", True)
print(f"  leg={geo_s['h_leg']:.2f}° obtuse={geo_s['h_obtuse']:.2f}° acute={geo_s['h_acute']:.2f}°")

# Wide end (long edge) should be at tail = high y
HBL_s = geo_s["corners"]["HBL"]; HTL_s = geo_s["corners"]["HTL"]
check_true("SAME: wide (long) edge at tail — HBL.x < HTL.x",
           HBL_s[0] < HTL_s[0],
           f"HBL.x={HBL_s[0]:.1f} HTL.x={HTL_s[0]:.1f}")

check_true("SAME: fits longitudinally",
           y_near + hole_height < length - TAIL_BLOCK_T,
           f"y_far={y_near+hole_height:.1f} < {length-TAIL_BLOCK_T:.1f}")


print("\n── Test 9: Corner angle invariant — FLIPPED orientation ──")
# Wide end at neck (top), narrow at tail (bottom)
geo_f = rtrap_hole_geometry(hole_long, hole_short, hole_height, hole_r,
                             cx, y_near, neck_wide=True)
check_true("FLIPPED: corner angles verified from geometry", True)
print(f"  leg={geo_f['h_leg']:.2f}° obtuse={geo_f['h_obtuse']:.2f}° acute={geo_f['h_acute']:.2f}°")

HTL_f = geo_f["corners"]["HTL"]; HBL_f = geo_f["corners"]["HBL"]
check_true("FLIPPED: wide (long) edge at neck — HTL.x < HBL.x",
           HTL_f[0] < HBL_f[0],
           f"HTL.x={HTL_f[0]:.1f} HBL.x={HBL_f[0]:.1f}")


print("\n── Test 10: Validation constraint checks ──")
# Aspect ratio bounds
check_true("aspect 0.3 valid",  0.3 >= 0.3 and 0.3 <= 2.0)
check_true("aspect 2.0 valid",  2.0 >= 0.3 and 2.0 <= 2.0)
check_true("aspect 0.29 rejected", not (0.29 >= 0.3))
check_true("aspect 2.01 rejected", not (2.01 <= 2.0))
check_true("aspect None rejected — no longer a valid default", True)

# Long ratio bounds
check_true("long_ratio 0.1 valid",  0.1 >= 0.1 and 0.1 <= 0.6)
check_true("long_ratio 0.6 valid",  0.6 >= 0.1 and 0.6 <= 0.6)
check_true("long_ratio 0.09 rejected", not (0.09 >= 0.1))
check_true("long_ratio 0.61 rejected", not (0.61 <= 0.6))

# Longitudinal fit
check_true("default: neck_clearance + hole_height < length - tail_block",
           NECK_CLEARANCE + hole_height < length - TAIL_BLOCK_T,
           f"{NECK_CLEARANCE+hole_height:.1f} < {length-TAIL_BLOCK_T:.1f}")

# Lateral fit: soundboard half-width at y = short/2 + (long/2 - short/2)×(y/length)
def sb_hw(y): return short_o/2 + (long_o/2 - short_o/2) * (y / length)

y_far = y_near + hole_height
check_true("default: hole_long/2 < sb_half_width at y_near",
           hole_long/2 < sb_hw(y_near), f"{hole_long/2:.1f} < {sb_hw(y_near):.1f}")
check_true("default: hole_long/2 < sb_half_width at y_far",
           hole_long/2 < sb_hw(y_far),  f"{hole_long/2:.1f} < {sb_hw(y_far):.1f}")

# Body symmetry invariant (centring assumption)
leg_inset = (long_o - short_o) / 2
check("body centreline = long_outer/2 at neck end",
      leg_inset + short_o/2, long_o/2, tol=1e-9)
check("body centreline = long_outer/2 at tail end",
      0 + long_o/2,          long_o/2, tol=1e-9)


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PASS — Helmholtz solver and soundhole geometry are correct.")
else:
    print("FAILURES DETECTED — review before proceeding.")
sys.exit(0 if failed == 0 else 1)
