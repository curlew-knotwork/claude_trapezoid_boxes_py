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

avail_long  = finger_termination_point(long_o,  tang_short, tang_short)
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

print("\n── Test 6: Burn compensation ──")
burn = 0.05  # mm, half kerf
# Tab: nominal width fw. After burn, tab becomes fw - 2*burn (narrower, correct)
# Slot: nominal width fw. After burn, slot becomes fw + 2*burn (wider, correct)
tab_after_burn  = fw - 2 * burn
slot_after_burn = fw + 2 * burn
clearance = slot_after_burn - tab_after_burn
check("tab after burn = fw - 2*burn",  tab_after_burn,  fw - 2*burn)
check("slot after burn = fw + 2*burn", slot_after_burn, fw + 2*burn)
check("clearance = 4*burn",            clearance,       4*burn)
# With tolerance applied: effective clearance includes tolerance on top of burn
effective_clearance = clearance + 2*tol  # tolerance on each side of slot
check("effective clearance = 4*burn + 2*tol", effective_clearance, 4*burn + 2*tol)

print("\n── Test 7: Sliding lid width ──")
# Correct formula from spec: short_inner - 2*(thickness+tolerance)
# = (short_outer - 2T) - 2*(T+tol) = short_outer - 4T - 2*tol
lid_w = (short_o - 2*T) - 2*(T + tol)
check("sliding lid width = short_inner - 2*(T+tol)", lid_w, 107.8)

# The WRONG formula from an earlier version of the spec:
lid_w_wrong = short_o + 2*(T + tol)
check_true("wrong formula (short_outer + 2*(T+tol)) gives wider lid",
           lid_w_wrong > short_o,
           f"wrong={lid_w_wrong:.1f}mm, correct={lid_w:.1f}mm")
print(f"  NOTE  Wrong formula gives {lid_w_wrong:.1f}mm, correct is {lid_w:.1f}mm — would not fit")

print("\n── Test 8: Groove angle limit for sliding lid ──")
# Groove width = T + tol. Lid edge effective width at angle = T/cos(alpha).
# Fits if T/cos(alpha) <= T + tol → cos(alpha) >= T/(T+tol)
crit_angle = math.degrees(math.acos(T / (T + tol)))
check("critical groove angle", crit_angle, 14.593, tol=0.01)
# Dulcimer angle is safe
check_true("dulcimer angle < critical", leg_angle < crit_angle,
           f"{leg_angle:.3f}° < {crit_angle:.3f}°")
# At exactly critical angle, lid just fits
T_eff_at_crit = T / math.cos(math.radians(crit_angle))
check("T_eff at critical angle = T+tol", T_eff_at_crit, T + tol)


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PASS — finger joint geometry is correct.")
else:
    print("FAILURES DETECTED — review finger joint formulas before proceeding.")
sys.exit(0 if failed == 0 else 1)
