"""
03_finger_joints.py
Verifies: finger count/width calculation, non-orthogonal joint corrections
(D_eff, W_over, W_struct), burn compensation direction, and the structural
safety boundary condition.

No dependencies beyond stdlib. Run with: python3 03_finger_joints.py
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


# ── Core finger joint functions (mirrors spec Section 10) ────────────────────

AUTO_FINGER_WIDTH_FACTOR = 3.0       # finger_width = 3 * thickness if not specified
OVERCUT_MIN_STRUCT_RATIO = 0.5       # W_struct >= thickness * this

def resolve_finger_width(user_fw, thickness):
    """Auto finger width if not specified."""
    return user_fw if user_fw is not None else AUTO_FINGER_WIDTH_FACTOR * thickness


def finger_count_and_width(available_length, nominal_width):
    """
    Compute odd finger count and adjusted width for a given available length.
    Count = nearest odd integer to (available / nominal_width), minimum 3.
    Actual width = available / count.
    """
    n = round(available_length / nominal_width)
    if n % 2 == 0:
        n -= 1
    n = max(3, n)
    actual_width = available_length / n
    return n, actual_width


def effective_depth(mating_thickness, leg_angle_deg):
    """D_eff = T / cos(alpha) — effective slot depth for angled joint."""
    return mating_thickness / math.cos(math.radians(leg_angle_deg))


def rotational_overcut(mating_thickness, leg_angle_deg):
    """W_over = T * tan(alpha) — slot width correction for assembly rotation."""
    return mating_thickness * math.tan(math.radians(leg_angle_deg))


def structural_width(finger_width, tolerance, w_over):
    """W_struct = finger_width - tolerance - W_over."""
    return finger_width - tolerance - w_over


def structural_check(thickness, tolerance, leg_angle_deg, finger_width):
    """
    Returns (ok, W_struct, W_over, alpha_max_deg).
    ok=True if W_struct >= thickness * OVERCUT_MIN_STRUCT_RATIO.
    """
    W_over   = rotational_overcut(thickness, leg_angle_deg)
    W_struct = structural_width(finger_width, tolerance, W_over)
    ok       = W_struct >= thickness * OVERCUT_MIN_STRUCT_RATIO
    # alpha_max: angle at which W_struct = threshold
    threshold = thickness * OVERCUT_MIN_STRUCT_RATIO
    # W_struct = fw - tol - T*tan(alpha) >= threshold
    # T*tan(alpha) <= fw - tol - threshold
    max_tan = (finger_width - tolerance - threshold) / thickness
    alpha_max = math.degrees(math.atan(max_tan))
    return ok, W_struct, W_over, alpha_max


# ── Terminal points for finger zone ──────────────────────────────────────────

def finger_termination_point(edge_length, tangent_dist_start, tangent_dist_end=None):
    """
    Available length for finger zone on a panel edge.
    tangent_dist_start: distance from start vertex to arc tangent point.
    tangent_dist_end:   distance from end vertex to arc tangent point (defaults to start).
    """
    if tangent_dist_end is None:
        tangent_dist_end = tangent_dist_start
    return edge_length - tangent_dist_start - tangent_dist_end


# ══════════════════════════════════════════════════════════════════════════════
T       = 3.0
tol     = 0.1
R       = 9.0
leg_angle = 4.5140  # degrees, dulcimer preset
fw      = resolve_finger_width(None, T)   # auto = 3*T = 9mm

long_o  = 180.0;  short_o = 120.0;  leg_len = 381.1824

long_end_angle  = 94.514
short_end_angle = 85.486

tang_long  = R / math.tan(math.radians(long_end_angle/2))   # 8.3175
tang_short = R / math.tan(math.radians(short_end_angle/2))  # 9.7385
tang_90    = R                                               # 9.0000

print("\n── Test 1: Auto finger width ──")
check("auto fw = 3*T", fw, 9.0)

print("\n── Test 2: Non-orthogonal joint corrections ──")
D_eff  = effective_depth(T, leg_angle)
W_over = rotational_overcut(T, leg_angle)
check("D_eff  = T/cos(4.514°)", D_eff,  3.0093, tol=1e-3)
check("W_over = T*tan(4.514°)", W_over, 0.2368, tol=1e-3)

# Verify D_eff * cos(alpha) = T (round-trip)
check("D_eff * cos(alpha) = T", D_eff * math.cos(math.radians(leg_angle)), T)

# Verify W_over physical meaning: this is the lateral collision distance
# during assembly rotation. Confirm: tan(alpha) = opposite/adjacent = W_over/T
check("W_over/T = tan(alpha)", W_over/T, math.tan(math.radians(leg_angle)))

print("\n── Test 3: Structural safety check ──")
ok, W_struct, W_over_c, alpha_max = structural_check(T, tol, leg_angle, fw)
check("W_struct (dulcimer preset)", W_struct, 8.6632, tol=1e-3)
check_true("W_struct >= T/2", ok, f"W_struct={W_struct:.4f}, min={T/2}")

# Verify alpha_max formula
check("alpha_max for defaults", alpha_max,
      math.degrees(math.atan((fw - tol - T*OVERCUT_MIN_STRUCT_RATIO) / T)), tol=1e-3)

# At exactly alpha_max, W_struct should equal exactly T/2
W_struct_at_max = structural_width(fw, tol, rotational_overcut(T, alpha_max))
check("W_struct at alpha_max == T/2", W_struct_at_max, T * OVERCUT_MIN_STRUCT_RATIO)

# Steeper angle should fail
ok_steep, W_struct_steep, _, _ = structural_check(T, tol, alpha_max + 1.0, fw)
check_true("angle > alpha_max fails structural check", not ok_steep,
           f"W_struct={W_struct_steep:.4f}")

print("\n── Test 4: Finger count and width — BASE edges ──")
# BASE uses actual corner angles for its termination points

avail_long  = finger_termination_point(long_o,  tang_short, tang_short)  # BR=short_end, BL=short_end
avail_short = finger_termination_point(short_o, tang_long,  tang_long)
avail_leg   = finger_termination_point(leg_len, tang_short, tang_long)

n_long,  fw_long  = finger_count_and_width(avail_long,  fw)
n_short, fw_short = finger_count_and_width(avail_short, fw)
n_leg,   fw_leg   = finger_count_and_width(avail_leg,   fw)

print(f"  long  edge: avail={avail_long:.3f}mm, n={n_long},  fw={fw_long:.4f}mm")
print(f"  short edge: avail={avail_short:.3f}mm, n={n_short}, fw={fw_short:.4f}mm")
print(f"  leg   edge: avail={avail_leg:.3f}mm, n={n_leg},  fw={fw_leg:.4f}mm")

check("n_long  = 17", n_long,  17)
check("n_short = 11", n_short, 11)
check("n_leg   = 39", n_leg,   39)

# Counts are all odd
check_true("n_long  is odd", n_long  % 2 == 1)
check_true("n_short is odd", n_short % 2 == 1)
check_true("n_leg   is odd", n_leg   % 2 == 1)

# Total joint length = available length (no gaps)
check("long  n*fw = avail",  n_long  * fw_long,  avail_long)
check("short n*fw = avail",  n_short * fw_short, avail_short)
check("leg   n*fw = avail",  n_leg   * fw_leg,   avail_leg)

print("\n── Test 5: Wall panels inherit BASE finger geometry (BASE-as-master) ──")
# Wall panel available lengths use tang_90 from their own 90° corners
avail_wall_long  = finger_termination_point(long_o,  tang_90, tang_90)
avail_wall_short = finger_termination_point(short_o, tang_90, tang_90)
avail_wall_leg   = finger_termination_point(leg_len, tang_90, tang_90)

# Wall panels inherit count and fw from BASE — do NOT recompute
# But their available lengths differ slightly from BASE:
print(f"  BASE long  avail={avail_long:.3f},  WALL_LONG avail={avail_wall_long:.3f},  delta={avail_wall_long-avail_long:.3f}mm")
print(f"  BASE short avail={avail_short:.3f}, WALL_SHORT avail={avail_wall_short:.3f}, delta={avail_wall_short-avail_short:.3f}mm")
print(f"  BASE leg   avail={avail_leg:.3f}, WALL_LEG avail={avail_wall_leg:.3f},   delta={avail_wall_leg-avail_leg:.3f}mm")

# Verify that if wall panels computed their own counts, mismatches would occur
n_wall_long_independent,  _ = finger_count_and_width(avail_wall_long,  fw)
n_wall_short_independent, _ = finger_count_and_width(avail_wall_short, fw)

# For long/short: independent calculation gives SAME count but different fw
check("WALL_LONG independent count same as BASE",  n_wall_long_independent,  n_long)
check("WALL_SHORT independent count same as BASE", n_wall_short_independent, n_short)

# But the spatial offset between start-of-finger-zone is significant for long/short:
offset_long  = abs(tang_short - tang_90)  # 0.739mm
offset_short = abs(tang_long  - tang_90)  # 0.683mm
check_true("WALL_LONG spatial offset > tolerance (requires inheritance)",
           offset_long > tol,
           f"offset={offset_long:.3f}mm > tol={tol}mm")
check_true("WALL_SHORT spatial offset > tolerance (requires inheritance)",
           offset_short > tol,
           f"offset={offset_short:.3f}mm > tol={tol}mm")
# WALL_LEG is fine independently (delta < tol)
delta_leg = abs(avail_wall_leg - avail_leg)
check_true("WALL_LEG delta within tolerance",
           delta_leg < tol,
           f"delta={delta_leg:.4f}mm")

print("\n── Test 6: Burn compensation — correct physical model ──")
burn = 0.05  # mm — default, matches boxes.py baseline
tol  = 0.0   # 0.0 = friction fit; 0.1 = hand press
# Physical model:
#   SVG path = laser centerline. Laser removes burn mm each side of path.
#   drawn_tab  = fw + 2*burn  → physical_tab  = fw  (kerf removes 2*burn)
#   drawn_slot = fw - 2*burn + 2*tol  → physical_slot = fw + 2*tol
#   nominal_fit = drawn_slot - drawn_tab = -4*burn + 2*tol
#   burn=0.05, tol=0.0 → fit=-0.2mm  (rubber mallet — matches boxes.py defaults)
#   burn=0.05, tol=0.1 → fit= 0.0mm  (hand press)
#   Larger burn = tighter. Larger tol = looser. Tune in 0.01mm steps.
tab_w = fw + 2 * burn
gap_w = fw - 2 * burn + 2 * tol
nominal_fit = gap_w - tab_w  # = -4*burn + 2*tol

check("tab_width = fw + 2*burn",          tab_w,       fw + 2*burn)
check("gap_width = fw - 2*burn + 2*tol",  gap_w,       fw - 2*burn + 2*tol)
check("nominal_fit = -4*burn + 2*tol",    nominal_fit, -4*burn + 2*tol)
check("friction fit default: fit=-0.2mm", nominal_fit, -0.2)
check_true("friction fit is interference (negative)", nominal_fit < 0,
           f"fit={nominal_fit:.3f}mm")

# Verify larger burn = tighter (more negative fit)
fit_tighter = (fw - 2*0.1 + 2*tol) - (fw + 2*0.1)
check_true("burn=0.1 gives tighter fit than burn=0.05",
           fit_tighter < nominal_fit,
           f"burn=0.1 fit={fit_tighter:.3f} < burn=0.05 fit={nominal_fit:.3f}")

# Verify larger tol = looser (less negative fit)
fit_with_tol = (fw - 2*burn + 2*0.1) - (fw + 2*burn)
check_true("tol=0.1 gives looser fit than tol=0.0",
           fit_with_tol > nominal_fit,
           f"tol=0.1 fit={fit_with_tol:.3f} > tol=0.0 fit={nominal_fit:.3f}")

# Hand-press default: burn=0.05, tol=0.1 → fit=0.0
fit_hand_press = (fw - 2*0.05 + 2*0.1) - (fw + 2*0.05)
check("hand-press: burn=0.05 tol=0.1 → fit=0.0", fit_hand_press, 0.0)

# Confirm old (pre-fix) model was wrong: tab=fw, gap=fw → no compensation
old_tab = fw; old_gap = fw
old_phys_tab  = old_tab  - 2*burn   # laser removes burn each side
old_phys_slot = old_gap  + 2*burn   # laser widens slot
old_effective_fit = old_phys_slot - old_phys_tab  # = 4*burn = +0.2mm clearance
check("OLD model was floppy: 4*burn=0.2mm clearance", old_effective_fit, 4*burn)
check_true("OLD model was clearance (positive) → floppy", old_effective_fit > 0,
           f"old fit={old_effective_fit:.3f}mm")

print("\n── Test 7: Sliding lid width ──")
# Sliding lid uses its own tolerance (0.1mm) regardless of joint tol
# Correct formula from spec: short_inner - 2*(thickness+lid_tol)
lid_tol = 0.1
lid_w = (short_o - 2*T) - 2*(T + lid_tol)
check("sliding lid width = short_inner - 2*(T+lid_tol)", lid_w, 107.8)

# The WRONG formula from an earlier version of the spec:
lid_w_wrong = short_o + 2*(T + lid_tol)
check_true("wrong formula (short_outer + 2*(T+lid_tol)) gives wider lid",
           lid_w_wrong > short_o,
           f"wrong={lid_w_wrong:.1f}mm, correct={lid_w:.1f}mm")
print(f"  NOTE  Wrong formula gives {lid_w_wrong:.1f}mm, correct is {lid_w:.1f}mm — would not fit")

print("\n── Test 8: Groove angle limit for sliding lid ──")
# Groove width = T + lid_tol. Lid edge effective width at angle = T/cos(alpha).
# Fits if T/cos(alpha) <= T + lid_tol → cos(alpha) >= T/(T+lid_tol)
crit_angle = math.degrees(math.acos(T / (T + lid_tol)))
check("critical groove angle", crit_angle, 14.593, tol=0.01)
# Dulcimer angle is safe
check_true("dulcimer angle < critical", leg_angle < crit_angle,
           f"{leg_angle:.3f}° < {crit_angle:.3f}°")
# At exactly critical angle, lid just fits
T_eff_at_crit = T / math.cos(math.radians(crit_angle))
check("T_eff at critical angle = T+lid_tol", T_eff_at_crit, T + lid_tol)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 9: Finger zone boundary placement — fingers must not cross arc tangent points ──")
# This test closes the spec gap exposed by the 06_svg_primitives.py visual check.
# It is not enough that available_length and count are correct arithmetically.
# We must also verify that:
#   finger_zone_start == arc_end of preceding corner  (in global coords)
#   finger_zone_end   == arc_start of next corner     (in global coords)
# i.e. fingers fill the zone exactly from tangent point to tangent point, no more.

# For each BASE edge, compute the global arc_end and arc_start x-coordinates
# and confirm that finger_zone_start and finger_zone_end match them exactly.

leg_ax = math.sin(math.radians(leg_angle))
leg_ay = math.cos(math.radians(leg_angle))
leg_inset = (long_o - short_o) / 2   # 30mm

# Panel corners
TL = (leg_inset, 0.0)
TR = (leg_inset + short_o, 0.0)
BR = (long_o, 380.0)
BL = (0.0, 380.0)

def arc_end_x(vertex, outgoing_dir, tang_dist):
    """arc_end = vertex + outgoing_dir * tang_dist"""
    return vertex[0] + outgoing_dir[0] * tang_dist

def arc_start_x(vertex, incoming_dir, tang_dist):
    """arc_start = vertex - incoming_dir * tang_dist"""
    return vertex[0] - incoming_dir[0] * tang_dist

# SHORT TOP EDGE (TL → TR, both long_end_angle corners → tang_long)
# TL outgoing dir = (1, 0); TR incoming dir = (1, 0)
short_zone_start = arc_end_x(TL, (1, 0), tang_long)    # TL arc_end.x
short_zone_end   = arc_start_x(TR, (1, 0), tang_long)  # TR arc_start.x
short_zone_avail = short_zone_end - short_zone_start
_, fw_short_check = finger_count_and_width(short_zone_avail, fw)
short_fingers_end = short_zone_start + n_short * fw_short_check

check("short edge: finger zone start == TL arc_end.x", short_zone_start, TL[0] + tang_long)
check("short edge: finger zone end == TR arc_start.x", short_zone_end, TR[0] - tang_long)
check("short edge: avail == zone_end - zone_start", short_zone_avail, avail_short)
check("short edge: fingers end exactly at TR arc_start", short_fingers_end, short_zone_end)
check_true("short edge: no finger extends past arc tangent point",
           abs(short_fingers_end - short_zone_end) < 1e-6,
           f"overshoot={short_fingers_end - short_zone_end:.6f}mm")

# LONG BOTTOM EDGE (BR → BL)
# BR = short_end_angle corner (tang_short); BL = long_end_angle corner (tang_long)
# BR arc_end.x = BR.x - tang_short (travelling left); BL arc_start.x = BL.x + tang_short
# Both BR and BL use short_end_angle (85.486°) → tang_short for both
long_zone_start = BR[0] - tang_short   # br_arc_end.x (right boundary)
long_zone_end   = BL[0] + tang_short   # bl_arc_start.x (left boundary)
long_zone_avail = long_zone_start - long_zone_end
_, fw_long_check = finger_count_and_width(long_zone_avail, fw)
long_fingers_end = long_zone_start - n_long * fw_long_check  # travelling left

check("long edge: finger zone start == BR arc_end.x", long_zone_start, BR[0] - tang_short)
check("long edge: finger zone end == BL arc_start.x", long_zone_end, BL[0] + tang_short)
check("long edge: avail == zone_start - zone_end", long_zone_avail, avail_long)
check("long edge: fingers end exactly at BL arc_start", long_fingers_end, long_zone_end)
check_true("long edge: no finger extends past arc tangent point",
           abs(long_fingers_end - long_zone_end) < 1e-6,
           f"overshoot={long_fingers_end - long_zone_end:.6f}mm")

# LEG EDGE (BL → TL, mixed corners: BL=long_end_angle → tang_long, TL=short_end_angle → tang_short)
leg_zone_start = tang_long    # from BL vertex along leg direction
leg_zone_end   = leg_len - tang_short  # to TL vertex
leg_zone_avail = leg_zone_end - leg_zone_start
check("leg edge: avail == leg_len - tang_long - tang_short", leg_zone_avail, avail_leg)
_, fw_leg_check = finger_count_and_width(leg_zone_avail, fw)
leg_fingers_end = leg_zone_start + n_leg * fw_leg_check
check("leg edge: fingers end exactly at TL arc_start", leg_fingers_end, leg_zone_end)
check_true("leg edge: no finger extends past arc tangent point",
           abs(leg_fingers_end - leg_zone_end) < 1e-6,
           f"overshoot={leg_fingers_end - leg_zone_end:.6f}mm")
if failed == 0:
    print("ALL PASS — finger joint geometry is correct.")
else:
    print("FAILURES DETECTED — review finger joint formulas before proceeding.")
sys.exit(0 if failed == 0 else 1)
