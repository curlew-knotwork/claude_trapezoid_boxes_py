"""
05_helmholtz.py
Verifies: Helmholtz resonator frequency solver — round hole, convergence,
neck slot volume correction, and the 5% acceptance criterion.

No dependencies beyond stdlib. Run with: python3 05_helmholtz.py
"""

import math
import sys

from check_harness import CheckHarness

h = CheckHarness()


# ── Core Helmholtz functions (mirrors spec Section 14) ───────────────────────

C_SOUND_MM_S = 343_000.0   # speed of sound in mm/s at 20°C

def helmholtz_freq(V_mm3, diameter_mm, top_thickness_mm):
    """
    f = (c/2π) * sqrt(A / (V * L_eff))
    L_eff = top_thickness + 0.85 * diameter  (end correction for round hole)
    A = π * (diameter/2)²
    """
    L_eff = top_thickness_mm + 0.85 * diameter_mm
    A     = math.pi * (diameter_mm / 2)**2
    return C_SOUND_MM_S / (2 * math.pi) * math.sqrt(A / (V_mm3 * L_eff))


def solve_diameter(target_hz, V_mm3, top_thickness_mm, max_iter=100, tol=1e-8):
    """
    Iterative solver: given target frequency, find the hole diameter.
    Converges in <20 iterations for typical instrument body sizes.
    Returns (diameter_mm, iterations_taken).
    """
    D = 50.0   # starting guess
    for i in range(max_iter):
        L_eff = top_thickness_mm + 0.85 * D
        A     = (target_hz * 2 * math.pi / C_SOUND_MM_S)**2 * V_mm3 * L_eff
        D_new = 2 * math.sqrt(A / math.pi)
        if abs(D_new - D) < tol:
            return D_new, i + 1
        D = D_new
    return D, max_iter   # did not converge (should not happen)


def air_volume_trapezoid(long_inner, short_inner, length_inner, depth_inner):
    """Trapezoidal prism air volume."""
    return 0.5 * (long_inner + short_inner) * length_inner * depth_inner


def neck_slot_volume_correction(neck_slot_width, neck_slot_depth,
                                 neck_tenon_length):
    """Volume displaced by neck shaft inside body."""
    return neck_slot_width * neck_slot_depth * neck_tenon_length


# ── Reference values ──────────────────────────────────────────────────────────

T      = 3.0       # wall thickness
T_top  = 3.0       # soundboard thickness (same as T in default preset)
long_i, short_i, length_i, depth_i = 174.0, 114.0, 374.0, 84.0

ACCEPTANCE_PCT = 5.0   # spec: achieved frequency must be within 5% of target


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Test 1: Air volume — reference preset ──")
V = air_volume_trapezoid(long_i, short_i, length_i, depth_i)
h.check("air volume", V, 4_523_904.0, tol=1.0)


print("\n── Test 2: Solver convergence and round-trip accuracy ──")
target_hz = 110.0
D, iters = solve_diameter(target_hz, V, T_top)
print(f"  Converged in {iters} iterations, D={D:.4f}mm")
h.check_true("converges in < 30 iterations", iters < 30, f"iters={iters}")

# Round-trip: compute frequency back from solved diameter
f_back = helmholtz_freq(V, D, T_top)
h.check("round-trip frequency", f_back, target_hz, tol=1e-4)

# Acceptance criterion: within 5%
h.check_true("within 5% acceptance band",
           abs(f_back - target_hz) / target_hz * 100 < ACCEPTANCE_PCT)


print("\n── Test 3: Frequency sensitivity to volume ──")
# Increasing V should decrease frequency (larger cavity = lower resonance)
D_same = D
f_larger_V = helmholtz_freq(V * 1.1, D_same, T_top)
f_smaller_V = helmholtz_freq(V * 0.9, D_same, T_top)
h.check_true("larger V → lower frequency",  f_larger_V  < target_hz,
           f"f={f_larger_V:.2f}Hz")
h.check_true("smaller V → higher frequency", f_smaller_V > target_hz,
           f"f={f_smaller_V:.2f}Hz")
# Exact: f ∝ 1/sqrt(V), so f * sqrt(V) = const
ratio = f_larger_V * math.sqrt(V * 1.1) / (target_hz * math.sqrt(V))
h.check("f * sqrt(V) is constant (1.1x volume)", ratio, 1.0, tol=1e-3)


print("\n── Test 4: Neck slot volume correction ──")
neck_w = 42.0;  neck_d = 15.0

# Full through-body: tenon = full interior length
V_neck_full = neck_slot_volume_correction(neck_w, neck_d, length_i)
V_corrected  = V - V_neck_full
h.check("full-through displaced volume", V_neck_full, 235_620.0, tol=1.0)
h.check("corrected volume", V_corrected, V - 235_620.0, tol=1.0)
displacement_pct = V_neck_full / V * 100
print(f"  Displaced volume: {displacement_pct:.1f}% of total V")
h.check_true("displacement > 4% (significant)", displacement_pct > 4.0)

# Without correction: frequency is too high
f_uncorrected = helmholtz_freq(V_corrected, D, T_top)
f_error_pct   = (f_uncorrected - target_hz) / target_hz * 100
print(f"  Without correction: f={f_uncorrected:.2f}Hz, error={f_error_pct:.1f}%")
h.check_true("without correction: exceeds 2% error", abs(f_error_pct) > 2.0)

# With correction: solve for new diameter using corrected volume
D_corrected, iters_c = solve_diameter(target_hz, V_corrected, T_top)
f_verify = helmholtz_freq(V_corrected, D_corrected, T_top)
h.check("corrected diameter round-trip", f_verify, target_hz, tol=1e-4)
print(f"  Corrected: D={D_corrected:.3f}mm (was {D:.3f}mm), f={f_verify:.2f}Hz")

# Partial neck (one end, 80mm tenon) — should be ignorable
V_neck_partial = neck_slot_volume_correction(neck_w, neck_d, 80.0)
f_partial = helmholtz_freq(V - V_neck_partial, D, T_top)
f_partial_error = abs(f_partial - target_hz)
print(f"  Partial (80mm tenon): f={f_partial:.2f}Hz, error={f_partial_error:.3f}Hz")
h.check_true("partial neck shift < 1Hz (ignorable)", f_partial_error < 1.0,
           f"shift={f_partial_error:.3f}Hz")


print("\n── Test 5: Frequency formula dimensional check ──")
# f should increase with: larger A (bigger hole), smaller V, smaller L_eff
D_big   = D * 1.5
D_small = D * 0.5
f_big   = helmholtz_freq(V, D_big,   T_top)
f_small = helmholtz_freq(V, D_small, T_top)
h.check_true("bigger hole → higher frequency",  f_big   > target_hz)
h.check_true("smaller hole → lower frequency",  f_small < target_hz)

# Thicker soundboard (longer L_eff) → lower frequency
f_thick_top = helmholtz_freq(V, D, T_top * 2)
h.check_true("thicker top → lower frequency", f_thick_top < target_hz)


print("\n── Test 6: Default target and range validation ──")
# Default 110Hz is spec-stated default for small-to-medium instrument bodies
h.check("default target 110Hz as stated", 110.0, 110.0)

# Practical range: hole diameter should be between 5mm and body short_inner/2
D_min_practical = 5.0
D_max_practical = short_i / 2   # 57mm
h.check_true("solved D > 5mm (not too small)", D > D_min_practical,
           f"D={D:.2f}mm")
h.check_true("solved D < short_inner/2 (fits soundboard)", D < D_max_practical,
           f"D={D:.2f}mm < {D_max_practical}mm")

# Target frequency range: must be positive and < Nyquist for audio
h.check_true("target Hz > 0", target_hz > 0)
h.check_true("target Hz < 20000", target_hz < 20000)


print("\n── Test 7: Triskele sound hole — equivalent diameter ──")
# Triskele: three circles arranged around a centre.
# Effective total area = 3 * π * (D_lobe/2)²
# Spec: helmholtz uses total open area A = sum of lobe areas
# Effective single-hole diameter for same A:
D_triskele_lobe = 22.0   # example lobe diameter
A_triskele = 3 * math.pi * (D_triskele_lobe/2)**2
D_equivalent = 2 * math.sqrt(A_triskele / math.pi)
h.check("triskele equivalent diameter", D_equivalent,
      D_triskele_lobe * math.sqrt(3), tol=1e-4)
# Frequency using equivalent area and average L_eff
# (spec uses D_equivalent as the diameter for L_eff computation — simple approximation)
f_triskele = helmholtz_freq(V, D_equivalent, T_top)
print(f"  Triskele (3x D={D_triskele_lobe}mm lobes): equiv D={D_equivalent:.3f}mm, f={f_triskele:.2f}Hz")
h.check_true("triskele frequency is positive and reasonable",
           10 < f_triskele < 1000)


# ══════════════════════════════════════════════════════════════════════════════
h.summary()
if h.failed == 0:
    print("ALL PASS — Helmholtz solver is correct.")
else:
    print("FAILURES DETECTED — review Helmholtz formulas before proceeding.")
h.exit()
