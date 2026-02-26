# claude_trapezoid_box_py

Parametric laser-cut box generator for:
- generic: trapezoidal boxes, or
- special case: trapezoidal music instrument bodies (stringed instruments, drums, etc.).

Note: This project is an experiment in collaborating with Claude Code to
see if it can be made to generate good, correct code, on the first try by
having a sufficiently detailed analysis and specification phase: applied
to a bounded problem of laser cutting trapezoid boxes with a laser cutter
that only works with a bed and orthogonal laser.

Version: **v0.20** — spec complete, geometry verified, implementation pending.

Status: Code, etc. is from Claude "as is" with no warranty of any kind whatsoever.
None of it has been tried or tested yet with a real laser cutter. 26 Feb 2026

License: No License at the present time

---

## What it does

Generates a DXF/SVG sheet layout for a six-panel finger-jointed box with:

- Trapezoidal planform (long end wider than short end)
- Angled leg walls (non-orthogonal)
- Rounded corners (arcs tangent to edges)
- Sliding lid or lift-off lid
- Optional soundboard with Helmholtz-tuned sound hole (round, slot, or triskele)
- Optional neck slot with kerfing plugs
- Kerf compensation on all joints
- TEST_STRIP panel for physical kerf calibration before full cut

All finger joints inherit position from BASE (BASE-as-master rule). Wall panels do not recompute their own finger zones independently.

---

## Project structure

```
trapezoid_box/
│
├── README.md                        ← this file
│
├── trapezoid_box.py                 ← main generator (NOT YET IMPLEMENTED)
│
├── proofs/                          ← geometry verification scripts (run before implementing)
│   ├── README.txt
│   ├── 01_trapezoid_geometry.py     ← 27 checks: trapezoid derivation, leg angle, volumes
│   ├── 02_corner_arcs.py            ← 30 checks: arc tangent points, bisector formula
│   ├── 03_finger_joints.py          ← 33 checks: fw, D_eff, W_over, BASE-as-master offset
│   ├── 04_panel_alignment.py        ← 10 checks: spatial tab/slot alignment all 4 wall pairs
│   ├── 05_helmholtz.py              ← 23 checks: resonator solver, neck correction, triskele
│   ├── 06_svg_primitives.py         ← visual: generates 4 SVG files for Inkscape inspection
│   └── 07_assembly_simulation.py    ← 48 checks: full assembly integration test
│
├── docs/
│   ├── trapezoid_box_specification_v2.0.docx   ← authoritative spec (the contract)
│   ├── trapezoid_box_build_manual.docx         ← operator manual, phases 0–5
│   └── trapezoid_box_test_strip_guide.docx     ← kerf calibration procedure (standalone)
│
└── diagrams/
    ├── D1_panel_overview.svg/png
    ├── D2_joint_crosssection.svg/png
    ├── D3_corner_arcs.svg/png
    ├── D4_test_strip.svg/png
    ├── D4b_test_pieces.svg/png
    ├── D5_assembly_sequence.svg/png
    └── D6_sliding_lid.svg/png
```

---

## Before implementing

Run all seven proof scripts in order. They require Python 3.9+, stdlib only, no pip installs.

```bash
cd proofs/
python3 01_trapezoid_geometry.py
python3 02_corner_arcs.py
python3 03_finger_joints.py
python3 04_panel_alignment.py
python3 05_helmholtz.py
python3 06_svg_primitives.py   # generates SVG files — open in Inkscape
python3 07_assembly_simulation.py
```

All seven must reach `ALL PASS` before any implementation begins. If any fail, the script prints the failing check with expected vs actual values. The spec is the reference — fix the spec formula first, then re-run.

**Current status: all 7 pass.** 171 checks total, 0 failures.

---

## Reference preset (dulcimer)

```
--long 180 --short 120 --length 380 --depth 90 --thickness 3.0
```

| Parameter | Value | Derived |
|---|---|---|
| long_outer | 180 mm | given |
| short_outer | 120 mm | given |
| length_outer | 380 mm | given |
| depth_outer | 90 mm | given |
| thickness (T) | 3.0 mm | given |
| corner_radius (R) | 9.0 mm | default = 3×T |
| finger_width (fw) | 9.4425 mm | auto from n_long=17 |
| leg_angle | 4.514° | derived |
| leg_length | 381.182 mm | derived |
| air_volume | 4,523,904 mm³ | derived |
| n_long | 17 | BASE long edge fingers |
| n_short | 11 | BASE short edge fingers |
| n_leg | 39 | BASE leg edge fingers |
| sliding lid width | 107.8 mm | short_inner − 2×(T+tol) |

---

## Key geometry rules

**BASE-as-master:** All wall panel finger zones inherit from BASE. Wall panels do not compute their own finger start positions. Independent computation produces a 0.739 mm offset — 7× the 0.1 mm assembly tolerance.

**Angled joint corrections:**
- `D_eff = T / cos(α)` — effective slot depth for leg walls
- `W_over = T × tan(α)` — rotational clearance consumed during assembly

**Corner arc bisector:** `normalise(−edge_a_dir + edge_b_dir)` — the wrong formula `normalise(−edge_a_dir − edge_b_dir)` produces a centre 8.35 mm from arc_start instead of 9.00 mm. Arc will not be tangent.

**Sliding lid width:** `short_inner − 2×(T+tol)` — NOT `short_outer + 2×(T+tol)`. Wrong formula gives 126.2 mm, which is 18.4 mm wider than the groove span.

---

## Material requirements (dulcimer preset)

| Mode | Sheet size | Qty |
|---|---|---|
| Box only (no soundboard) | 600 × 400 mm, 3 mm ply/MDF | 1 |
| Instrument (with soundboard + kerfing) | 600 × 400 mm, 3 mm ply/MDF | 2 |
| Kerf calibration test strips only | ~120 × 270 mm offcut | — |

Largest single panel: BASE at 180 × 380 mm. Minimum laser bed: 400 × 400 mm.

---

## Kerf calibration

Before cutting full panels, cut two copies of the TEST_STRIP panel and test fit. See `docs/trapezoid_box_test_strip_guide.docx` for the full procedure.

Short version:
1. Cut two TEST_STRIP pieces from scrap (same material as box)
2. Offset one by one finger width (~9.44 mm), press together by thumb
3. Too tight → **decrease** kerf_compensation. Too loose → **increase** kerf_compensation
4. Iterate until snug. Record value.

---

## Error codes

| Code | Cause |
|---|---|
| ERR_VALIDATION_LONG_NOT_GT_SHORT | long ≤ short |
| ERR_VALIDATION_RADIUS_TOO_LARGE | R > short/4 or R > depth/4 |
| ERR_VALIDATION_FINGER_WIDTH_TOO_SMALL | fw < T |
| ERR_VALIDATION_STRUCTURAL_TAB | W_struct < T/2 at current leg angle |
| ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP | sliding lid + angle > 14.6° |
| ERR_VALIDATION_NECK_SLOT_TOO_WIDE | neck slot ≥ short − 4×T |
| ERR_VALIDATION_NECK_SLOT_TOO_DEEP | neck slot ≥ depth/2 |
| ERR_VALIDATION_SLIDING_LID_NECK_SLOT_CONFLICT | --neck-slot-both-ends + sliding lid |

---

## Spec document

`docs/trapezoid_box_specification_v2.0.docx` is the authoritative source of truth. The code must conform to the spec. If there is a conflict between code and spec, fix the code.

---

## Status

| Component | Status |
|---|---|
| Specification | ✅ Complete (v2.0) |
| Geometry proof scripts | ✅ All 7 passing (171 checks) |
| Build operator manual | ✅ Complete |
| Test strip guide | ✅ Complete (3 audits, all errors corrected) |
| trapezoid_box.py implementation | ⬜ Not started |
| SVG output validation | ⬜ Pending implementation |
| Physical cut validation | ⬜ Pending first cut |
