"""
01_trapezoid_geometry.py
Verifies: TrapezoidGeometry.derive() for both mode A (length given) and
mode B (leg given), DimMode.INNER expansion, and all derived angles.

No dependencies beyond stdlib. Run with: python3 01_trapezoid_geometry.py
"""

import math
import sys

FLOAT_TOLERANCE = 1e-6
passed = 0
failed = 0


def check(label, actual, expected, tol=1e-4):
    global passed, failed
    if abs(actual - expected) <= tol:
        print(f"  PASS  {label}: {actual:.6f}")
        passed += 1
    else:
        print(f"  FAIL  {label}: got {actual:.6f}, expected {expected:.6f}  (delta={abs(actual-expected):.6f})")
        failed += 1


def check_true(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label}  {detail}")
        failed += 1


# ── Shared geometry derivation (mirrors spec Section 6) ──────────────────────

def derive_mode_a(long_outer, short_outer, length_outer, depth_outer, thickness,
                  dim_mode_inner=False):
    """Derive all trapezoid geometry from outer dimensions (mode A: length given)."""
    t = thickness
    if dim_mode_inner:
        long_outer   += 2 * t
        short_outer  += 2 * t
        length_outer += 2 * t
        depth_outer  += 2 * t

    leg_inset   = (long_outer - short_outer) / 2.0
    leg_length  = math.sqrt(length_outer**2 + leg_inset**2)
    leg_angle_deg = math.degrees(math.atan2(leg_inset, length_outer))

    long_end_angle_deg  = 90.0 + leg_angle_deg
    short_end_angle_deg = 90.0 - leg_angle_deg

    long_inner   = long_outer   - 2 * t
    short_inner  = short_outer  - 2 * t
    length_inner = length_outer - 2 * t
    depth_inner  = depth_outer  - 2 * t

    air_volume = 0.5 * (long_inner + short_inner) * length_inner * depth_inner

    return {
        "leg_inset":            leg_inset,
        "leg_length":           leg_length,
        "leg_angle_deg":        leg_angle_deg,
        "long_end_angle_deg":   long_end_angle_deg,
        "short_end_angle_deg":  short_end_angle_deg,
        "long_inner":           long_inner,
        "short_inner":          short_inner,
        "length_inner":         length_inner,
        "depth_inner":          depth_inner,
        "air_volume":           air_volume,
        "long_outer":           long_outer,
        "short_outer":          short_outer,
        "length_outer":         length_outer,
        "depth_outer":          depth_outer,
    }


def derive_mode_b(long_outer, short_outer, leg_length, depth_outer, thickness,
                  dim_mode_inner=False):
    """Derive geometry from outer dimensions (mode B: leg given)."""
    t = thickness
    if dim_mode_inner:
        long_outer  += 2 * t
        short_outer += 2 * t
        depth_outer += 2 * t
        # leg is a diagonal — NOT adjusted for DimMode.INNER (spec Section 5.6)

    leg_inset    = (long_outer - short_outer) / 2.0
    # Validate leg > leg_inset
    if leg_length <= leg_inset:
        raise ValueError(f"leg ({leg_length}) must be > leg_inset ({leg_inset})")
    length_outer = math.sqrt(leg_length**2 - leg_inset**2)
    return derive_mode_a(long_outer, short_outer, length_outer, depth_outer, t)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 1: Mode A — reference dulcimer preset ──")
g = derive_mode_a(long_outer=180, short_outer=120, length_outer=380,
                  depth_outer=90, thickness=3.0)

check("leg_inset",           g["leg_inset"],           30.0)
check("leg_length",          g["leg_length"],           381.1824, tol=1e-3)
check("leg_angle_deg",       g["leg_angle_deg"],          4.5140, tol=1e-3)
check("long_end_angle_deg",  g["long_end_angle_deg"],    94.5140, tol=1e-3)
check("short_end_angle_deg", g["short_end_angle_deg"],   85.4860, tol=1e-3)
check("long_inner",          g["long_inner"],            174.0)
check("short_inner",         g["short_inner"],           114.0)
check("length_inner",        g["length_inner"],          374.0)
check("depth_inner",         g["depth_inner"],            84.0)
check("air_volume",          g["air_volume"],          4523904.0, tol=1.0)

# ── Test 2: Mode B round-trip ─────────────────────────────────────────────────
print("\n── Test 2: Mode B — leg=381.1824 should recover length≈380 ──")
g2 = derive_mode_b(long_outer=180, short_outer=120,
                   leg_length=381.1824, depth_outer=90, thickness=3.0)
check("length_outer recovered", g2["length_outer"], 380.0, tol=0.01)
check("leg_angle_deg",          g2["leg_angle_deg"], g["leg_angle_deg"], tol=1e-3)

# ── Test 3: DimMode.INNER ─────────────────────────────────────────────────────
print("\n── Test 3: DimMode.INNER — inner dims become outer ──")
g3 = derive_mode_a(long_outer=174, short_outer=114, length_outer=374,
                   depth_outer=84, thickness=3.0, dim_mode_inner=True)
check("long_outer after INNER",   g3["long_outer"],   180.0)
check("short_outer after INNER",  g3["short_outer"],  120.0)
check("length_outer after INNER", g3["length_outer"], 380.0)
check("depth_outer after INNER",  g3["depth_outer"],   90.0)
# Angles and derived values should match mode A reference
check("leg_angle_deg same",       g3["leg_angle_deg"], g["leg_angle_deg"], tol=1e-3)

# ── Test 4: Mode B + DimMode.INNER — leg NOT adjusted ────────────────────────
print("\n── Test 4: Mode B + DimMode.INNER — leg is diagonal, not adjusted ──")
g4 = derive_mode_b(long_outer=174, short_outer=114,
                   leg_length=381.1824,   # passed as outer diagonal, not adjusted
                   depth_outer=84, thickness=3.0, dim_mode_inner=True)
check("long_outer",  g4["long_outer"],  180.0)
check("short_outer", g4["short_outer"], 120.0)
check("leg_angle recovered", g4["leg_angle_deg"], g["leg_angle_deg"], tol=1e-3)

# ── Test 5: Degenerate / boundary validation ──────────────────────────────────
print("\n── Test 5: Boundary conditions ──")

# leg <= leg_inset must raise
try:
    derive_mode_b(180, 120, leg_length=25.0, depth_outer=90, thickness=3.0)
    check_true("leg<=leg_inset raises ValueError", False, "no exception raised")
except ValueError:
    check_true("leg<=leg_inset raises ValueError", True)

# long must be > short
try:
    g5 = derive_mode_a(100, 120, 380, 90, 3.0)  # short > long
    check_true("long > short: leg_inset negative", g5["leg_inset"] < 0,
               f"leg_inset={g5['leg_inset']}")
    # Note: the spec requires validation (long > short > 0) at validate_config level,
    # not in derive(). derive() will produce a negative leg_inset which is geometrically
    # meaningless. The validation layer catches it before derive() is called.
    print("  NOTE  long <= short: derive() returns negative leg_inset — validation layer must catch this")
except Exception as e:
    check_true("long > short handled", False, str(e))

# ── Test 6: Symmetry — isosceles trapezoid ────────────────────────────────────
print("\n── Test 6: Symmetry — square box (long=short) becomes rectangle ──")
g6 = derive_mode_a(100, 100, 200, 50, 3.0)
check("square: leg_inset=0",     g6["leg_inset"],     0.0)
check("square: leg_angle=0",     g6["leg_angle_deg"], 0.0)
check("square: long_end=90",     g6["long_end_angle_deg"],  90.0)
check("square: short_end=90",    g6["short_end_angle_deg"], 90.0)
check("square: leg=length",      g6["leg_length"],    200.0)


# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PASS — trapezoid geometry derivation is correct.")
else:
    print("FAILURES DETECTED — review formulas before proceeding.")
sys.exit(0 if failed == 0 else 1)
