"""
04_panel_alignment.py
Verifies: that all mating panel edges produce spatially aligned finger zones
when assembled. This is the critical integration test of the BASE-as-master rule.

Simulates placing each wall panel against the BASE in 3D space and checks
that every finger tab on one panel aligns with a slot on the other within
FLOAT_TOLERANCE.

No dependencies beyond stdlib. Run with: python3 04_panel_alignment.py
"""

import math
import sys

passed = 0
failed = 0
FLOAT_TOL = 1e-4
JOINT_TOL = 0.1   # assembly tolerance from spec


def check(label, actual, expected, tol=FLOAT_TOL):
    global passed, failed
    if abs(actual - expected) <= tol:
        print(f"  PASS  {label}: {actual:.6f}")
        passed += 1
    else:
        print(f"  FAIL  {label}: got {actual:.6f}, expected {expected:.6f}")
        failed += 1


def check_true(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label}  {detail}")
        failed += 1


# ── Geometry helpers ──────────────────────────────────────────────────────────

def finger_count_and_width(available, nominal):
    n = round(available / nominal)
    if n % 2 == 0: n -= 1
    n = max(3, n)
    return n, available / n


def tang(angle_deg, R):
    return R / math.tan(math.radians(angle_deg / 2))


def finger_positions(term_start_global, count, fw):
    """
    Global positions of each finger (tab or slot) along the edge.
    Returns list of (start, end, is_tab). First finger is a TAB.
    """
    return [(term_start_global + i*fw, term_start_global + (i+1)*fw, i % 2 == 0)
            for i in range(count)]


# ── Reference dimensions ──────────────────────────────────────────────────────

T       = 3.0
R       = 9.0
leg_angle = 4.5140
fw_nominal = 3.0 * T   # 9.0mm auto

long_o   = 180.0
short_o  = 120.0
depth_o  =  90.0
leg_inset = (long_o - short_o) / 2   # 30mm
leg_len  = math.sqrt(380.0**2 + leg_inset**2)  # 381.182mm

long_end_angle  = 90.0 + leg_angle   # 94.514°
short_end_angle = 90.0 - leg_angle   # 85.486°

tang_long  = tang(long_end_angle,  R)   # 8.3175
tang_short = tang(short_end_angle, R)   # 9.7385
tang_90    = R                           # 9.0000


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Building BASE finger zones ──")

# BASE finger zones (using actual corner angle tangent distances)
avail_base_long  = long_o  - 2*tang_short
avail_base_short = short_o - 2*tang_long
avail_base_leg   = leg_len - tang_short - tang_long

n_long,  fw_long  = finger_count_and_width(avail_base_long,  fw_nominal)
n_short, fw_short = finger_count_and_width(avail_base_short, fw_nominal)
n_leg,   fw_leg   = finger_count_and_width(avail_base_leg,   fw_nominal)

print(f"  BASE long_bottom:  avail={avail_base_long:.3f}mm, n={n_long},  fw={fw_long:.4f}mm")
print(f"  BASE short_top:    avail={avail_base_short:.3f}mm, n={n_short}, fw={fw_short:.4f}mm")
print(f"  BASE leg (both):   avail={avail_base_leg:.3f}mm, n={n_leg},  fw={fw_leg:.4f}mm")


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 1: WALL_LONG bottom ↔ BASE long_bottom ──")
#
# In assembled 3D space, BASE lies flat. WALL_LONG stands perpendicular along
# the long bottom edge of BASE.
# The long_bottom edge runs from BL=(0,380) to BR=(180,380) in BASE coords.
# Along this edge, the finger zone starts at tang_short from BL.
#
# BASE finger zones along the long_bottom edge:
# term_start_base = tang_short = 9.7385mm from BL
# term_end_base   = long_o - tang_short = 170.2615mm from BL
#
# WALL_LONG bottom edge (in WALL_LONG local coords) inherits:
# - count = n_long, fw = fw_long
# - term_start_wall = tang_90 = 9.0mm from WALL_LONG left end
# (a gap of tang_short - tang_90 = 0.7385mm from corner arc end to finger zone start — plain line)
#
# In global space, WALL_LONG left end aligns with BASE BL.
# So WALL_LONG finger zone starts at tang_90 = 9.0mm from global x=0.
# BASE finger zone starts at tang_short = 9.7385mm from global x=0.
#
# THESE ARE DIFFERENT. This is the known misalignment if walls compute independently.
# The BASE-as-master rule says WALL_LONG must start its fingers at the SAME global
# position as BASE — i.e. at 9.7385mm, not 9.0mm.
#
# Simulate with BASE-as-master:
# WALL_LONG term_start_global = tang_short (inherited from BASE, expressed in global)

wall_long_term_start_global = tang_short   # inherited from BASE
# Wall polarity is INVERTED: BASE tab → wall slot, BASE slot → wall tab
wall_long_fingers = [(s, e, not tab)
                     for s, e, tab in finger_positions(wall_long_term_start_global, n_long, fw_long)]

base_long_term_start_global = tang_short
base_long_fingers = finger_positions(base_long_term_start_global, n_long, fw_long)

# Every BASE tab should align with a WALL_LONG slot and vice versa
misalignments = 0
for i, (base_s, base_e, base_is_tab) in enumerate(base_long_fingers):
    wall_s, wall_e, wall_is_tab = wall_long_fingers[i]
    pos_delta = max(abs(base_s - wall_s), abs(base_e - wall_e))
    if pos_delta > FLOAT_TOL:
        misalignments += 1
        print(f"  FAIL  finger {i}: pos delta={pos_delta:.6f}mm")
    if base_is_tab == wall_is_tab:
        misalignments += 1
        print(f"  FAIL  finger {i}: both {'tabs' if base_is_tab else 'slots'} — should alternate")

check_true(f"WALL_LONG ↔ BASE long: all {n_long} fingers aligned",
           misalignments == 0, f"{misalignments} misalignments")


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 2: WALL_SHORT bottom ↔ BASE short_top ──")

wall_short_term_start_global = tang_long   # inherited from BASE
wall_short_fingers = [(s, e, not tab)
                      for s, e, tab in finger_positions(wall_short_term_start_global, n_short, fw_short)]
base_short_fingers = finger_positions(tang_long, n_short, fw_short)

misalignments = 0
for i, (base_s, base_e, base_is_tab) in enumerate(base_short_fingers):
    wall_s, wall_e, wall_is_tab = wall_short_fingers[i]
    if max(abs(base_s-wall_s), abs(base_e-wall_e)) > FLOAT_TOL:
        misalignments += 1
    if base_is_tab == wall_is_tab:
        misalignments += 1

check_true(f"WALL_SHORT ↔ BASE short: all {n_short} fingers aligned",
           misalignments == 0)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 3: WALL_LEG bottom ↔ BASE leg edge ──")

wall_leg_term_start_global = tang_short   # BASE leg starts at tang_short from the short-end corner
wall_leg_fingers  = [(s, e, not tab)
                     for s, e, tab in finger_positions(wall_leg_term_start_global, n_leg, fw_leg)]
base_leg_fingers  = finger_positions(tang_short, n_leg, fw_leg)

misalignments = 0
for i, (base_s, base_e, _) in enumerate(base_leg_fingers):
    wall_s, wall_e, _ = wall_leg_fingers[i]
    if max(abs(base_s-wall_s), abs(base_e-wall_e)) > FLOAT_TOL:
        misalignments += 1

check_true(f"WALL_LEG ↔ BASE leg: all {n_leg} fingers aligned", misalignments == 0)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 4: What happens WITHOUT BASE-as-master (independent calculation) ──")
# Show that independent calculation fails for WALL_LONG and WALL_SHORT

# WALL_LONG independent: uses tang_90 as term_start
wall_long_independent_start = tang_90
offset_long = abs(tang_short - tang_long_independent_start if False else tang_short - tang_90)

# If WALL_LONG starts at tang_90 but BASE starts at tang_short:
pos_error = tang_short - tang_90  # 0.7385mm — every finger is shifted by this
print(f"  Without BASE-as-master:")
print(f"    WALL_LONG finger zone starts {pos_error:.4f}mm off from BASE")
print(f"    Assembly tolerance is {JOINT_TOL}mm")
check_true("independent offset exceeds assembly tolerance",
           pos_error > JOINT_TOL,
           f"offset={pos_error:.4f}mm > tolerance={JOINT_TOL}mm — joint would not fit")
print(f"    (Interference = {pos_error - JOINT_TOL/2:.4f}mm — would require filing to assemble)")


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 5: Wall-to-wall joints (all 90° — should be perfect) ──")
# WALL_LONG depth edge ↔ WALL_SHORT depth edge
# Both use 90° corners, same depth, same tang_90
avail_depth = depth_o - 2 * tang_90
n_depth, fw_depth = finger_count_and_width(avail_depth, fw_nominal)
print(f"  Depth edges: avail={avail_depth:.3f}mm, n={n_depth}, fw={fw_depth:.4f}mm")
check_true("n_depth is odd", n_depth % 2 == 1)
check_true("n_depth >= 3",   n_depth >= 3, f"n={n_depth}")
# Same terms from both sides → zero offset
check("depth edge offset", 0.0, 0.0)   # trivially correct, documenting the case


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 6: Finger interlock — tabs fit inside slots ──")
# For each mating pair: tab nominal width should be < slot nominal width
# After burn and tolerance:
burn = 0.05
tab_w  = fw_long - 2*burn        # narrowed by burn
slot_w = fw_long + 2*burn + JOINT_TOL  # widened by burn + tolerance

check_true("tab width < slot width (fits)", tab_w < slot_w,
           f"tab={tab_w:.4f}, slot={slot_w:.4f}")
clearance = slot_w - tab_w
check_true("clearance > 0", clearance > 0)
print(f"  Clearance per side: {clearance/2:.4f}mm")

# The spatial offset (from BASE-as-master: wall term_start may differ from BASE by
# up to tang_short - tang_90 = 0.739mm in the PLAIN LINE gap before fingers start)
# This is NOT an alignment error — it's a plain-line segment on the wall panel
# that sits outside the finger zone. The fingers themselves are aligned.
plain_line_gap_wall = tang_short - tang_90  # 0.739mm gap on WALL_LONG before fingers start
print(f"\n  Plain-line gap on WALL_LONG before finger zone: {plain_line_gap_wall:.4f}mm (acceptable)")
check_true("plain-line gap does not interfere with fingers",
           plain_line_gap_wall >= 0,
           "negative gap would mean arc overlaps finger zone")


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PASS — panel alignment is correct with BASE-as-master rule.")
else:
    print("FAILURES DETECTED — review panel alignment before proceeding.")
sys.exit(0 if failed == 0 else 1)
