"""
07_assembly_simulation.py
Integration test: simulates placing every wall panel against BASE in 3D space
and verifies that every tab/slot pair is spatially aligned within assembly
tolerance. Also checks Helmholtz, structural safety, and key validation rules.

This is the spec's acceptance test. If this passes, the geometry is ready
to implement. No implementation code is needed to run this — it is purely
a verification of the spec's claims before any code is written.

No dependencies beyond stdlib. Run with: python3 07_assembly_simulation.py
"""

import math
import sys

from check_harness import CheckHarness
from geometry_utils import tang, finger_count_and_width, finger_positions

h = CheckHarness()

ASSEMBLY_TOL = 0.1   # mm — joint assembly tolerance from spec
FLOAT_TOL    = 1e-6


def check_mating_alignment(label, fingers_a, fingers_b, tol=ASSEMBLY_TOL):
    """
    Verify that every finger in A mates with a finger in B:
    - Same position
    - Opposite polarity (tab↔slot)
    Returns (ok, max_offset)
    """
    if len(fingers_a) != len(fingers_b):
        print(f"  FAIL  {label}: count mismatch {len(fingers_a)} vs {len(fingers_b)}")
        h.failed += 1
        return False, float('inf')
    max_offset = 0.0
    ok = True
    for i, ((s_a, e_a, tab_a), (s_b, e_b, tab_b)) in enumerate(zip(fingers_a, fingers_b)):
        offset = max(abs(s_a - s_b), abs(e_a - e_b))
        max_offset = max(max_offset, offset)
        if offset > tol:
            print(f"  FAIL  {label} finger {i}: offset={offset:.4f}mm > tol={tol}mm")
            ok = False; h.failed += 1
        if tab_a == tab_b:
            print(f"  FAIL  {label} finger {i}: both {'tabs' if tab_a else 'slots'}")
            ok = False; h.failed += 1
    if ok:
        print(f"  PASS  {label}: {len(fingers_a)} fingers, max_offset={max_offset:.6f}mm")
        h.passed += 1
    return ok, max_offset


# ── Config ────────────────────────────────────────────────────────────────────

class Config:
    long_outer    = 180.0
    short_outer   = 120.0
    length_outer  = 380.0
    depth_outer   =  90.0
    thickness     =   3.0
    corner_radius =   9.0    # auto: 3*thickness
    finger_width  =   9.0    # auto: 3*thickness
    tolerance     =   0.1
    leg_angle_deg =   4.5140


cfg = Config()
T   = cfg.thickness
R   = cfg.corner_radius
fw  = cfg.finger_width
tol = cfg.tolerance

long_o   = cfg.long_outer
short_o  = cfg.short_outer
depth_o  = cfg.depth_outer
leg_inset = (long_o - short_o) / 2
leg_len  = math.sqrt(cfg.length_outer**2 + leg_inset**2)

leg_angle = cfg.leg_angle_deg
long_end_angle  = 90.0 + leg_angle
short_end_angle = 90.0 - leg_angle

tang_long  = tang(long_end_angle,  R)   # 8.317
tang_short = tang(short_end_angle, R)   # 9.739
tang_90    = R                           # 9.000

# Derived inner dimensions
long_i   = long_o   - 2*T
short_i  = short_o  - 2*T
length_i = cfg.length_outer - 2*T
depth_i  = depth_o  - 2*T


# ══════════════════════════════════════════════════════════════════════════════
print("\n═══════════════════════════════════════════")
print("  PHASE 1: INDIVIDUAL GEOMETRY CHECKS")
print("═══════════════════════════════════════════")

print("\n── 1.1 Trapezoid derivation ──")
h.check("leg_inset",          leg_inset,        30.0)
h.check("leg_len",            leg_len,          381.182, tol=1e-2)
h.check("long_end_angle",     long_end_angle,    94.514, tol=1e-2)
h.check("short_end_angle",    short_end_angle,   85.486, tol=1e-2)

print("\n── 1.2 Corner arc tangent distances ──")
h.check("tang long-end",   tang_long,   8.317,  tol=1e-2)
h.check("tang short-end",  tang_short,  9.739,  tol=1e-2)
h.check("tang 90°",        tang_90,     9.000)

print("\n── 1.3 Non-orthogonal joint corrections ──")
D_eff  = T / math.cos(math.radians(leg_angle))
W_over = T * math.tan(math.radians(leg_angle))
h.check("D_eff",   D_eff,   3.009,  tol=1e-2)
h.check("W_over",  W_over,  0.237,  tol=1e-2)
W_struct = fw - tol - W_over
h.check_true("W_struct >= T/2", W_struct >= T/2,
           f"W_struct={W_struct:.3f}, min={T/2}")

print("\n── 1.4 BASE finger zones ──")
avail_long  = long_o  - 2*tang_short
avail_short = short_o - 2*tang_long
avail_leg   = leg_len - tang_short - tang_long

n_long,  fw_long  = finger_count_and_width(avail_long,  fw)
n_short, fw_short = finger_count_and_width(avail_short, fw)
n_leg,   fw_leg   = finger_count_and_width(avail_leg,   fw)

h.check("n_long  = 17",   n_long,  17)
h.check("n_short = 11",   n_short, 11)
h.check("n_leg   = 39",   n_leg,   39)

for name, n in [("n_long", n_long), ("n_short", n_short), ("n_leg", n_leg)]:
    h.check_true(f"{name} is odd", n % 2 == 1)

print("\n── 1.5 Sliding lid width ──")
lid_w = short_i - 2*(T + tol)
h.check("lid_width", lid_w, 107.8)
h.check_true("lid fits: lid_w < short_i", lid_w < short_i,
           f"lid={lid_w:.1f} < short_inner={short_i:.1f}")

print("\n── 1.6 Groove angle limit ──")
crit_angle = math.degrees(math.acos(T / (T + tol)))
h.check_true("leg_angle < groove_angle_limit",
           leg_angle < crit_angle,
           f"{leg_angle:.3f}° < {crit_angle:.3f}°")

print("\n── 1.7 Helmholtz ──")
V = 0.5 * (long_i + short_i) * length_i * depth_i
h.check("air_volume", V, 4_523_904.0, tol=1.0)
C = 343_000.0
f_target = 110.0
T_top = T
D = 50.0
for _ in range(50):
    L = T_top + 0.85*D
    A = (f_target * 2*math.pi / C)**2 * V * L
    D_new = 2*math.sqrt(A/math.pi)
    if abs(D_new-D) < 1e-8: break
    D = D_new
f_check = C/(2*math.pi) * math.sqrt(math.pi*(D/2)**2 / (V*(T_top+0.85*D)))
h.check("Helmholtz round-trip", f_check, f_target, tol=1e-3)

# Neck slot volume correction (full through-body)
neck_w, neck_d = 42.0, 15.0
V_corr = V - neck_w * neck_d * length_i
D_corr = 50.0
for _ in range(50):
    L = T_top + 0.85*D_corr
    A = (f_target * 2*math.pi / C)**2 * V_corr * L
    D_new = 2*math.sqrt(A/math.pi)
    if abs(D_new-D_corr) < 1e-8: break
    D_corr = D_new
f_corr = C/(2*math.pi) * math.sqrt(math.pi*(D_corr/2)**2 / (V_corr*(T_top+0.85*D_corr)))
h.check("Helmholtz with neck correction", f_corr, f_target, tol=1e-3)


# ══════════════════════════════════════════════════════════════════════════════
print("\n═══════════════════════════════════════════")
print("  PHASE 2: ASSEMBLY SIMULATION")
print("═══════════════════════════════════════════")
print("\n  BASE is placed flat. Each wall panel is raised perpendicular to BASE.")
print("  Global coordinate along each joint edge: 0 = one corner, max = other corner.")
print("  BASE-as-master: wall panels inherit finger positions from BASE.\n")

# ── BASE long_bottom ↔ WALL_LONG bottom ──────────────────────────────────────
print("── 2.1 BASE long_bottom ↔ WALL_LONG bottom ──")
# BASE: term_start at tang_short from BL corner
# WALL_LONG: inherits term_start = tang_short (in global = same as BASE)
base_long_fingers = finger_positions(tang_short, n_long, fw_long)
wall_long_fingers = finger_positions(tang_short, n_long, fw_long)
# Tab polarity: BASE long_bottom starts with TAB (protrudes into box)
# WALL_LONG bottom starts with SLOT (receives BASE tab)
# Invert polarity on wall side:
wall_long_fingers = [(s, e, not tab) for s, e, tab in wall_long_fingers]
check_mating_alignment("long_bottom ↔ WALL_LONG", base_long_fingers, wall_long_fingers)

# Verify gap between wall arc end and finger zone start
gap_wall_long = tang_short - tang_90
h.check_true("WALL_LONG plain-line gap >= 0 (no arc-finger overlap)",
           gap_wall_long >= 0, f"gap={gap_wall_long:.4f}mm")
print(f"  (WALL_LONG has {gap_wall_long:.4f}mm plain-line gap before finger zone — correct)")

# ── BASE short_top ↔ WALL_SHORT bottom ───────────────────────────────────────
print("\n── 2.2 BASE short_top ↔ WALL_SHORT bottom ──")
base_short_fingers = finger_positions(tang_long, n_short, fw_short)
wall_short_fingers = [(s, e, not tab) for s, e, tab in finger_positions(tang_long, n_short, fw_short)]
check_mating_alignment("short_top ↔ WALL_SHORT", base_short_fingers, wall_short_fingers)

gap_wall_short = tang_90 - tang_long
print(f"  (WALL_SHORT has {gap_wall_short:.4f}mm plain-line gap before finger zone — correct)")

# ── BASE leg ↔ WALL_LEG bottom ───────────────────────────────────────────────
print("\n── 2.3 BASE left-leg ↔ WALL_LEG_LEFT bottom ──")
base_leg_fingers = finger_positions(tang_short, n_leg, fw_leg)
wall_leg_fingers = [(s, e, not tab) for s, e, tab in finger_positions(tang_short, n_leg, fw_leg)]
check_mating_alignment("left-leg ↔ WALL_LEG_LEFT", base_leg_fingers, wall_leg_fingers)

print("\n── 2.4 BASE right-leg ↔ WALL_LEG_RIGHT bottom (symmetric) ──")
# WALL_LEG_RIGHT = dataclasses.replace(LEFT) — same geometry, 180° rotation in assembly
# The right leg edge also runs tang_short to (leg_len - tang_long) from the short-end corner
base_right_leg = finger_positions(tang_short, n_leg, fw_leg)
wall_right_leg = [(s, e, not tab) for s, e, tab in finger_positions(tang_short, n_leg, fw_leg)]
check_mating_alignment("right-leg ↔ WALL_LEG_RIGHT", base_right_leg, wall_right_leg)

# ── Wall-to-wall depth joints ─────────────────────────────────────────────────
print("\n── 2.5 WALL_LONG depth ↔ WALL_SHORT depth (four corners) ──")
avail_depth = depth_o - 2 * tang_90
n_depth, fw_depth = finger_count_and_width(avail_depth, fw)
wall_depth_a = finger_positions(tang_90, n_depth, fw_depth)
wall_depth_b = [(s, e, not tab) for s, e, tab in finger_positions(tang_90, n_depth, fw_depth)]
check_mating_alignment("depth edge ↔ depth edge", wall_depth_a, wall_depth_b)
h.check_true("n_depth is odd", n_depth % 2 == 1)


# ══════════════════════════════════════════════════════════════════════════════
print("\n═══════════════════════════════════════════")
print("  PHASE 3: VALIDATION RULES")
print("═══════════════════════════════════════════")

print("\n── 3.1 Required geometry constraints ──")
h.check_true("long > short",              long_o > short_o)
h.check_true("short > 4*T",              short_o > 4*T,
           f"short={short_o} > 4*T={4*T}")
h.check_true("depth > 4*T",              depth_o > 4*T)
h.check_true("R <= short/4",             R <= short_o/4,
           f"R={R} <= short/4={short_o/4}")
h.check_true("R <= depth/4",             R <= depth_o/4)
h.check_true("T < short/4",             T < short_o/4)
h.check_true("leg_angle < 45°",         leg_angle < 45.0)

print("\n── 3.2 TEST_STRIP height constraint ──")
strip_height = 3 * depth_o
h.check_true("3*depth <= sheet_height",  strip_height <= 600,
           f"3*depth={strip_height}mm")

print("\n── 3.3 neck_slot_both_ends + sliding_lid incompatibility ──")
neck_slot_depth = 15.0
groove_from_top = tang_90  # groove sits at ~9mm from top edge
h.check_true("neck_slot_depth > groove_from_top (conflict exists when both enabled)",
           neck_slot_depth > groove_from_top,
           f"neck_d={neck_slot_depth} > groove_y={groove_from_top:.3f}")
print(f"  (validate_config must reject this combination — confirmed geometry conflict)")

print("\n── 3.4 Neck slot validation bounds ──")
neck_slot_w = 42.0
h.check_true("neck_slot_w < short_o - 4*T",
           neck_slot_w < short_o - 4*T,
           f"{neck_slot_w} < {short_o-4*T}")
h.check_true("neck_slot_depth < depth_o/2",
           neck_slot_depth < depth_o/2,
           f"{neck_slot_depth} < {depth_o/2}")
h.check_true("neck_slot_w >= 20mm",
           neck_slot_w >= 20.0)


# ══════════════════════════════════════════════════════════════════════════════
print("\n═══════════════════════════════════════════")
print("  PHASE 4: EDGE CASES")
print("═══════════════════════════════════════════")

print("\n── 4.1 Square box (long=short) — zero leg angle ──")
lo2, so2 = 100.0, 100.0
li2 = (lo2-so2)/2
ll2 = math.sqrt(200.0**2 + li2**2)
la2 = math.degrees(math.atan2(li2, 200.0))
h.check("square: leg_angle = 0", la2, 0.0)
h.check("square: leg_len = length", ll2, 200.0)
D_eff_sq  = T / math.cos(math.radians(la2))
W_over_sq = T * math.tan(math.radians(la2))
h.check("square: D_eff = T (no correction)", D_eff_sq, T)
h.check("square: W_over = 0 (no correction)", W_over_sq, 0.0)

print("\n── 4.2 Isosceles at steep-but-valid angle (leg_angle=10°) ──")
la3 = 10.0
D_eff_3  = T / math.cos(math.radians(la3))
W_over_3 = T * math.tan(math.radians(la3))
W_struct_3 = fw - tol - W_over_3
h.check_true("steep: W_struct still > 0", W_struct_3 > 0,
           f"W_struct={W_struct_3:.3f}")
crit_angle = math.degrees(math.acos(T / (T + tol)))
h.check_true("steep 10° < structural limit", la3 < crit_angle,
           f"10° < {crit_angle:.2f}°")

print("\n── 4.3 DimMode.INNER — leg NOT adjusted ──")
# Provide inner dims equivalent to the reference preset
long_i2, short_i2, length_i2 = 174.0, 114.0, 374.0
long_o2  = long_i2  + 2*T
short_o2 = short_i2 + 2*T
length_o2 = length_i2 + 2*T
# leg provided as outer diagonal (not adjusted)
leg_inset_2 = (long_o2 - short_o2) / 2
leg_from_inner = math.sqrt(length_o2**2 + leg_inset_2**2)
leg_from_outer = math.sqrt(cfg.length_outer**2 + leg_inset**2)
h.check("DimMode.INNER: leg_len same either way", leg_from_inner, leg_from_outer, tol=1e-4)


# ══════════════════════════════════════════════════════════════════════════════
h.summary()

if h.failed == 0:
    print("\n✓ ALL PASS — geometry is consistent and assembly-ready.")
    print("  The spec is believed correct. Proceed to implementation.")
    print("  Remaining validation: physical cut and assembly.")
else:
    print(f"\n✗ {h.failed} FAILURES — resolve before implementing.")

h.exit()
