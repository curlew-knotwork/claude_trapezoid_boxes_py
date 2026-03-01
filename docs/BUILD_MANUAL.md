# trapezoid_boxes — Build Validation Manual


**trapezoid_boxes.py**

Build Validation Manual

v0.20 — From first Python run to first cut

**This document covers:**

Phase 0  Prerequisites and material checklist

Phase 1  Proof scripts — 7 pass/fail gates before any cutting

Phase 2  Generate and inspect SVG output

Phase 3  Test strip cut and kerf calibration loop

Phase 4  Full panel cut and dry-fit assembly

Phase 5  Instrument mode additions (soundboard, kerfing)

Appendix  Error codes, troubleshooting, material reference

## Phase 0 — Prerequisites
### 0.1  Software checklist
Install and verify each item before proceeding. All are free.

| Item | How to verify |
|---|---|
| Python 3.9+ | python3 --version  →  3.9 or higher |
| No extra libraries needed | Scripts use stdlib only (math, sys, os) |
| Inkscape 1.0+ | inkscape --version  →  opens and renders SVG |
| Your laser cutter software | Can import SVG and set cut vs engrave layers |
| trapezoid_boxes_proofs/ folder | Contains 01_trapezoid_geometry.py through 07_assembly_simulation.py |


### 0.2  Material checklist — dulcimer preset (reference dimensions)
> ℹ️ These quantities are for the reference dulcimer preset: long=180mm, short=120mm, length=380mm, depth=90mm, thickness=3mm. If you change any dimension, re-run the tool with --estimate-material to get updated quantities.


| Material | Quantity |
|---|---|
| 3mm laser-grade plywood or MDF | 1 sheet 600 × 400 mm  (box mode, no soundboard) — 600×600 is NOT needed |
| 3mm laser-grade plywood or MDF | 2 sheets 600 × 400 mm  (instrument mode with soundboard) |
| Wood glue (PVA) | Small bottle — finger joints need very little |
| Clamps or rubber bands | 4–6 corner clamps or heavy rubber bands for glue-up |
| Calipers (0.01mm resolution) | Essential for measuring test strip fingers |
| Scrap material (same sheet) | ~60 × 340mm offcut of 3mm ply/MDF — the TEST_STRIP (60×270mm) plus a small mating slot strip (60×60mm). Any workshop scrap works. You do NOT need a full sheet for test cuts. |


> ⚠️ Sheet size note: the 180×380mm BASE panel is the largest single piece. Your laser bed must accommodate at least 400×400mm. Standard 600×400mm laser bed is comfortable. If your bed is smaller, adjust long/short/length dimensions and re-run.


### 0.3  Material quantities — detailed breakdown
Panel bounding boxes for the dulcimer preset (actual panel areas are less due to trapezoid shape and finger joints):

| Panel | Bounding box (mm) | Count |
|---|---|---|
| BASE | 180 × 380 | 1 |
| SOUNDBOARD (instrument mode) | 180 × 380 | 1 |
| WALL_LONG | 180 × 90 | 1 |
| WALL_SHORT | 120 × 90 | 1 |
| WALL_LEG_LEFT / RIGHT | 381 × 90 each | 2 |
| NECK_BLOCK / TAIL_BLOCK | 25 × 90, 15 × 90 | 1 each |
| TEST_STRIP | 60 × 270 | 1 |
| KERF_STRIP (instrument mode) | 374 × 12 each | ~8 |
| NECK_SLOT_PLUG (if neck slot) | 42 × 15 each | 1 or 2 |
| Total (box mode, no soundboard) | ~130,000 mm² | ≈ 0.13 m² |
| Total (instrument mode) | ~257,000 mm² | ≈ 0.26 m² |


## Phase 1 — Proof Scripts
Run all seven scripts in order. Each script is independent — no installation required beyond Python 3.9+. A script either exits with ALL PASS or prints the failing check with expected vs actual values.

> ℹ️ Purpose: these scripts verify that the geometry spec is arithmetically correct before any code is written or material is cut. They are not unit tests for an implementation — they are proofs of the specification itself.


### 1.1  Script 01 — Trapezoid geometry derivation
**Step 1.  **Run the script:  — cd trapezoid_boxes_proofs &amp;&amp; python3 01_trapezoid_geometry.py

Checks: mode A (length given), mode B (leg given), DimMode.INNER expansion, boundary conditions, square-box degenerate case.

> ✅ All 27 checks pass. Output ends: ALL PASS — trapezoid geometry derivation is correct.


> ❌ Any FAIL line: note the label and delta. The label maps to a formula in spec Section 6. Most likely cause: leg_angle_deg or long/short_end_angle formula error.


### 1.2  Script 02 — Corner arc geometry
**Step 2.  **Run:  — python3 02_corner_arcs.py

Checks: tangent distances, arc centre offsets, bisector directions for all four BASE corners, proves wrong bisector formula gives wrong answer.

> ✅ All 30 checks pass. Key values confirmed: tang long-end = 8.317mm, tang short-end = 9.739mm.


> ❌ centre_TR dist to arc_start fails: bisector formula is wrong. Correct formula: normalise(-edge_a_dir + edge_b_dir). The old wrong formula normalise(-edge_a_dir + -edge_b_dir) gives a centre 8.35mm from arc_start instead of 9.00mm — arc will not be tangent.


D3 — Corner arc geometry. Red cross marks the vertex. Arc is tangent to both edges at the tangent-distance points. Centre is on the inward bisector.

### 1.3  Script 03 — Finger joint geometry
**Step 3.  **Run:  — python3 03_finger_joints.py

Checks: auto finger width, D_eff and W_over corrections, structural safety, BASE finger counts, BASE-as-master spatial offset, burn compensation, sliding lid width formula, groove angle limit.

> ✅ All 33 checks pass. Confirmed: n_long=17, n_short=11, n_leg=39. Sliding lid width = 107.8mm. W_struct = 8.66mm (well above minimum 1.5mm).


> ❌ sliding lid width check fails: formula must be short_inner - 2*(T+tol), not short_outer + 2*(T+tol). The wrong formula gives 126.2mm which is 18.4mm wider than the groove span and will not fit.


> ⚠️ BASE-as-master: the test confirms WALL_LONG finger zone starts 0.739mm laterally offset from BASE if computed independently. That is 7x the 0.1mm assembly tolerance. Wall panels must inherit finger positions from BASE, not recompute them.


### 1.4  Script 04 — Panel alignment simulation
**Step 4.  **Run:  — python3 04_panel_alignment.py

Simulates assembling each wall panel against BASE in global coordinates. Verifies every tab/slot pair is spatially aligned and has opposite polarity.

> ✅ All 10 checks pass. All 4 mating pairs aligned: WALL_LONG (17 fingers), WALL_SHORT (11 fingers), WALL_LEG_LEFT (39 fingers), WALL_LEG_RIGHT (39 fingers). Max offset: 0.000mm.


> ❌ Any polarity fail (both tabs / both slots): the wall panel bottom edge polarity assignment is inverted — first finger of BASE bottom is a TAB, so the mating wall edge must start with a SLOT.


D2 — Angled joint cross-section. D_eff = T/cos(α) is the effective slot depth. W_over = T·tan(α) is consumed by the rotation during assembly. For dulcimer preset these are 3.009mm and 0.237mm respectively — small but non-negligible in the SVG path generation.

### 1.5  Script 05 — Helmholtz solver
**Step 5.  **Run:  — python3 05_helmholtz.py

Checks: solver convergence, round-trip accuracy, volume sensitivity, neck slot volume correction (full through-body and partial), triskele equivalent diameter.

> ✅ All 23 checks pass. Converges in &lt;30 iterations. Round-trip frequency error &lt; 0.0001Hz. Full through-body neck correction: 5.2% volume displaced, corrected diameter 21.883mm vs uncorrected 22.938mm.


> ❌ round-trip frequency fails tolerance: the iterative solver is not converging. Check the L_eff formula: L_eff = T_top + 0.85 * diameter (end correction for a flanged circular aperture).


> ⚠️ Neck slot correction is only needed for --neck-slot-both-ends (full through-body). One-end-only with tenon length under 100mm shifts frequency by less than 1Hz — within the spec 5% acceptance band.


### 1.6  Script 06 — SVG primitives (visual check)
**Step 6.  **Run:  — python3 06_svg_primitives.py

Generates four SVG files in the same directory. Open each in Inkscape or a browser.

| File | What to look for |
|---|---|
| 06a_corner_arcs.svg | All four BASE corners. Arcs smooth, no kinks. Red cross at vertex. No gap between arc end and edge start. |
| 06b_finger_strip.svg | BASE long_bottom finger profile. Fingers regular width, centred in available space. Plain-line gaps at each end. |
| 06c_full_base.svg | Complete BASE panel. Correct trapezoid shape. Arcs at all four corners. Fingers on short and long edges only (legs are plain line in this render). |
| 06d_lid_width.svg | Cross-section: green lid fits inside the groove span with visible clearance. Groove notches visible in grey walls. |


> ✅ All four SVGs open and look geometrically correct as described above.


> ❌ 06a: arc has a kink or gap at the joint with the edge line — arc_start/end point calculation is wrong. 06c: panel looks rectangular, not trapezoidal — leg_inset is zero or geometry derivation is wrong.


### 1.7  Script 07 — Full assembly simulation (the integration test)
**Step 7.  **Run:  — python3 07_assembly_simulation.py

Three phases: individual geometry checks, full assembly simulation across all four mating pairs, validation rule checks, edge cases. 48 checks total.

> ✅ Output ends: ALL PASS — geometry is consistent and assembly-ready. 48 passed, 0 failed, 0 warnings.


> ❌ Any failure in Phase 2 (assembly simulation): the BASE-as-master finger inheritance rule is not implemented correctly. The spatial positions of all finger centres must be identical between BASE and mating wall panels.


> ℹ️ If all seven scripts pass: the geometry is verified. Proceed to Phase 2. The remaining risk is the physical cut — material thickness variance, actual kerf width, and assembly fit. These are addressed in Phase 3.


## Phase 2 — Generate and Inspect SVG
### 2.1  Generate your first SVG
Once implementation exists, generate the box SVG with the reference preset:

```
python3 trapezoid_boxes.py --long 180 --short 120 --length 380 --depth 90 --thickness 3.0 --output my_box.svg
```


Expected stdout output (reference preset):

```
trapezoid_boxes v0.20
```


```
long=180  short=120  length=380  depth=90  thickness=3.0  R=9.0  fw=9.0
```


```
leg_angle=4.514 deg   leg_length=381.182mm
```


```
BASE: long=17 fingers  short=11 fingers  legs=39 fingers
```


```
air_volume=4,523,904 mm3   (no sound hole — Helmholtz not computed)
```


```
sheets: 1 of 1  written: my_box.svg
```


> ✅ File my_box.svg written, no ERR_ lines in output, finger counts match 17/11/39.


> ❌ Any ERR_ line: look up the error code in the Appendix. Most common at this stage: ERR_VALIDATION_GEOMETRY_LONG_TOO_SMALL (long must be &gt; short) or ERR_VALIDATION_RADIUS_TOO_LARGE (R must be &lt;= short/4).


### 2.2  Inspect SVG in Inkscape — panel-by-panel checklist
> ℹ️ Open my_box.svg in Inkscape. All panels are on a single sheet. Use Edit &gt; Find to select panels by label. Zoom to 100% actual size to check dimensions.


D1 — Panel overview. Arrows show which edges mate. Blue = BASE. Orange = wall panels. Green = leg walls. Purple = test strip.

#### Checklist — run through each item before cutting
| Check | Expected |
|---|---|
| BASE shape | Trapezoid: long bottom edge wider than short top edge. Four rounded corners. |
| BASE finger count long edge | 17 fingers, alternating tabs/slots, regular spacing. |
| BASE finger count short edge | 11 fingers. Plain-line gaps at each end before first finger. |
| BASE finger count leg edges | 39 fingers each. |
| WALL_LONG width | Equals long_outer = 180mm (measure in Inkscape with ruler). |
| WALL_LONG height | Equals depth_outer = 90mm. |
| WALL_SHORT finger count | 11 fingers — must match BASE short edge. |
| WALL_LEG width | ~381mm (diagonal length). Parallelogram shape, not rectangle. |
| Corner arcs | All eight wall corners have smooth arcs. No sharp right-angle cuts. |
| TEST_STRIP present | 60 × 270mm panel on the sheet. One long edge has finger profile. |
| Labels | Each panel has a laser-engraved label: BASE, WALL_LONG, etc. plus assembly number. |
| Sheet fits bed | Entire sheet outline fits within your laser bed dimensions. |


> ✅ All 13 items confirmed. Proceed to Phase 3 (test strip cut).


> ❌ Any item wrong: do not cut. Identify the failing panel and cross-reference with the proof script that covers that geometry. Fix the implementation, re-generate, re-check.


## Phase 3 — Test Strip Cut and Kerf Calibration
> ℹ️ This phase consumes only a small piece of scrap material. It is the most important physical gate. A 30-minute test cut here saves you from a full-sheet failure.


### 3.1  What the test strip tells you
The TEST_STRIP panel has one edge matching the WALL_LONG bottom finger profile (which inherits from BASE long_bottom). Cutting and testing this single strip validates your kerf compensation setting for all box joints. If the test strip fits correctly into a BASE slot, all joints will fit.

D4 — Test strip measurement guide. Only a 60×340mm offcut of your box material is needed — essentially free scrap. Do NOT buy a full sheet just for this.

### 3.2  Kerf calibration loop
**Step 1.  **Export TEST_STRIP and one BASE long_bottom strip to your laser software.  — Use same cut settings you will use for full panels.

**Step 2.  **Cut both pieces from a 60×340mm offcut of the same material and thickness as your planned box panels. This is the only material consumed in Phase 3 — you do not need a full sheet.

**Step 3.  **Measure the actual cut finger width with calipers.  — Should be approximately 9.4mm for dulcimer preset. Note the delta from nominal.

**Step 4.  **Attempt to push the TEST_STRIP tab into the BASE slot by hand. No tools.

| Result | Action |
|---|---|
| Snug: slight resistance, no gap, no cracking, removable by hand | PASS — record kerf_compensation. Proceed to Phase 4. |
| Too tight: cannot push in without force, or material cracks | Increase kerf_compensation by 0.05mm. Re-cut. Repeat from Step 1. |
| Too loose: tabs rattle in slots, visible gap | Decrease kerf_compensation by 0.05mm. Re-cut. Repeat from Step 1. |
| Tabs shear off during insertion | Check material grain direction. Leg wall tabs on angled edges are vulnerable — ensure grain runs along the long axis of the wall panel. |


> ⚠️ Typical starting kerf_compensation for a 40W CO2 laser on 3mm ply: 0.05 to 0.15mm. MDF cuts slightly wider than ply. Birch ply and poplar ply often differ by 0.05mm. Always re-calibrate when changing material or laser settings.


**Step 5.  **Record your working kerf_compensation value and add it to your standard laser profile for this material.

> ✅ Test strip fits snugly by hand. Tab is flush with slot face. No gap visible.


> ❌ Fit does not converge after 3–4 iterations: check actual material thickness with calipers. If it is not 3.0mm, re-run trapezoid_boxes.py with --thickness set to the actual measured value.


## Phase 4 — Full Panel Cut and Dry-Fit Assembly
### 4.1  Cut sequence
Send the full SVG to your laser software. Cut order matters — cut interior features (finger joints, sound holes) before outer profiles. Raster-engrave labels first.

| Order | Layer / operation |
|---|---|
| 1st | Raster engrave — panel labels and assembly numbers (low power) |
| 2nd | Vector cut — sound holes, neck slot, all interior cuts |
| 3rd | Vector cut — panel outer profiles (last, so panels do not shift) |


> ✅ All panels fall free cleanly. No charring on finger surfaces. Kerf is consistent with test strip calibration.


> ❌ Panel does not fall free: increase power or decrease speed by 5%. Re-cut. Do not force panels out — tearing damages finger tabs.


> ⚠️ Leg walls (WALL_LEG_LEFT, WALL_LEG_RIGHT) are parallelograms, not rectangles. Verify in Inkscape before cutting — they should be visibly angled, not square.


### 4.2  Dry-fit assembly — go/no-go gates
> ℹ️ Dry-fit means: assemble the entire box with no glue. All joints must fit by hand. This is your last gate before committing to glue.


D5 — Assembly sequence. Follow numbered order. Rotate leg walls into position — do not force straight down.

**Step 1.  **Lay BASE flat on a clean surface, cut-face UP.

**Step 2.  **Stand WALL_SHORT on the BASE short (top) edge.  — Press tabs gently into slots. Should engage by hand with light pressure.

**Step 3.  **Stand WALL_LONG on the BASE long (bottom) edge.  — Same as above.

**Step 4.  **Stand WALL_LEG_LEFT on the BASE left-leg edge.  — The wall leans inward 4.5 degrees. Rotate it into position — approach from outside, rotate inward. Tabs engage BASE and the two adjacent walls simultaneously.

**Step 5.  **Repeat for WALL_LEG_RIGHT.

**Step 6.  **Inspect all joints. Go/no-go gate — see table below.

| Joint location | PASS | FAIL / action |
|---|---|---|
| BASE to WALL_LONG | Tabs fully seated, flush face | Gap at joint: kerf too tight, re-cut with higher compensation |
| BASE to WALL_SHORT | Tabs fully seated, flush face | Tabs shear: check grain direction on WALL_SHORT |
| BASE to WALL_LEG | Tabs seat on rotation, no force | Tabs miss slots: BASE-as-master rule not implemented — finger zones misaligned |
| WALL_LONG to WALL_SHORT corner | Flush, no gap | Corner gap: depth-edge finger count wrong |
| Overall squareness | Box stands square on flat surface | Diagonal measurement: both diagonals equal within 1mm |
| All four walls | No panel proud of adjacent panel face | Proud panel: one edge too long — check outer profile path |


> ✅ All joints seat by hand. Box stands square. No gaps &gt; 0.5mm. Proceed to glue-up.


> ❌ Any BASE-to-leg-wall joint misses slots entirely: stop. This is the finger alignment blocker. BASE-as-master rule is not correctly implemented. Wall panels are computing their own finger positions instead of inheriting from BASE.


### 4.3  Glue-up
**Step 1.  **Disassemble the dry-fit box. Keep panels in order.

**Step 2.  **Apply PVA wood glue to finger tabs with a small brush or toothpick.  — Thin coat — thick glue swells the tab and prevents seating.

**Step 3.  **Re-assemble in the same sequence as dry-fit (Steps 1–5 above).

**Step 4.  **Clamp all joints. Rubber bands work well for the angled leg joints.

**Step 5.  **Check squareness again with diagonal measurement. Adjust before glue sets.

**Step 6.  **Leave clamped for minimum 30 minutes. Full cure: 24 hours.

> ✅ Box is square, all joints tight, no squeeze-out gaps. The box is structurally complete.


## Phase 5 — Instrument Mode Additions
> ℹ️ Skip this phase if you are building a plain box. Instrument mode adds: soundboard with sound hole, kerfing strips, optional neck slot with kerfing plugs, and Helmholtz-tuned sound hole diameter.


### 5.1  Soundboard and Helmholtz sound hole
**Step 1.  **Add sound hole flag to your command:

```
python3 trapezoid_boxes.py --long 180 --short 120 --length 380 --depth 90 --thickness 3.0 --soundhole-type round --soundhole-hz 110 --output my_instrument.svg
```


The tool computes the sound hole diameter needed to tune the air cavity to 110Hz (default). Check stdout:

```
helmholtz_target=110.0 Hz   solved_diameter=22.94mm   achieved=110.00 Hz   error=0.00%
```


> ✅ achieved frequency within 5% of target. Diameter between 10mm and short_inner/2 (57mm). Proceed.


> ❌ error &gt; 5%: the solver did not converge or V_air is wrong. Re-run script 05 to verify Helmholtz independently.


> ⚠️ If --neck-slot-both-ends is active: the solver automatically uses corrected air volume (subtracts neck shaft displacement). Verify stdout shows: neck_correction_applied=yes  V_corrected=4,288,284 mm3.


### 5.2  Kerfing strips
Kerfing strips are thin triangular fillets glued into the interior corners between the BASE and each wall, giving the SOUNDBOARD a gluing surface. They are essential for an air-tight acoustic body.

**Step 1.  **Cut KERF_STRIP panels from the SVG. Typically 8 strips (two per corner, mirrored).

**Step 2.  **Glue-up the box walls to BASE as in Phase 4. Do not attach SOUNDBOARD yet.

**Step 3.  **Glue kerfing strips into all four BASE-to-wall interior corners. Clamp 20 minutes.

**Step 4.  **Fit SOUNDBOARD dry first — tabs should engage kerfing strip surfaces smoothly.

**Step 5.  **Glue SOUNDBOARD. Weight or clamp flat for 30 minutes.

> ✅ Soundboard lies flat, no gaps between soundboard face and kerfing strips. Body is air-tight (test by pressing gently on soundboard — no hiss from joints).


> ❌ Soundboard does not lie flat: kerfing strips not flush with wall top face. Plane or sand until flush before gluing soundboard.


### 5.3  Neck slot and kerfing plugs
> ℹ️ Neck slot (--neck-slot or --neck-slot-both-ends) cuts a rectangular notch at the top of WALL_SHORT (and WALL_LONG for through-body). The slot must be sealed with kerfing plugs to keep the body air-tight.


**Step 1.  **Cut NECK_SLOT_PLUG panels (42 × 15mm by default, generated on the final sheet).

**Step 2.  **Before fitting the neck, glue one plug into each slot opening from inside the body.  — Grain direction: across the 42mm width. Glue face: the 3mm cut edge.

**Step 3.  **Clamp or tape flush. Let cure 20 minutes.

**Step 4.  **Test air-tightness as above.

**Step 5.  **Fit neck through plug (plug has a matching hole sized to neck tenon width).

> ✅ Neck seats correctly. Body is air-tight with neck in place. No rattles.


> ❌ Plug cracks on neck insertion: plug hole is too small. Re-cut plug with +0.2mm kerf_compensation on the neck hole only.


D6 — Sliding lid groove cross-section (if lid=sliding). Green lid must be cut to short_inner - 2*(T+tol) = 107.8mm for dulcimer preset. Wrong formula (short_outer + 2*(T+tol) = 126.2mm) will not fit.

## Appendix — Error Codes and Troubleshooting
### A.1  Error code reference
| Error code | Cause | Fix |
|---|---|---|
| ERR_VALIDATION_LONG_NOT_GT_SHORT | long &lt;= short | long must be strictly greater than short |
| ERR_VALIDATION_RADIUS_TOO_LARGE | R &gt; short/4 or R &gt; depth/4 | **Reduce corner_radius. Default is 3*thickness; lower if depth or short is small** |
| ERR_VALIDATION_FINGER_WIDTH_TOO_SMALL | fw &lt; T | Increase finger_width. Must be at least wall thickness |
| ERR_VALIDATION_STRUCTURAL_TAB | W_struct &lt; T/2 at leg angle | Reduce leg angle (make long and short closer in size) or increase finger_width |
| ERR_VALIDATION_GROOVE_ANGLE_TOO_STEEP | Sliding lid + angle &gt; 14.6 deg | Use lift-off lid, or reduce leg angle below 14.6 degrees |
| ERR_VALIDATION_NECK_SLOT_TOO_WIDE | **Neck slot &gt;= short - 4*T | Reduce --neck-slot-width** |
| ERR_VALIDATION_NECK_SLOT_TOO_DEEP | Neck slot &gt;= depth/2 | Reduce --neck-slot-depth |
| ERR_VALIDATION_SLIDING_LID_NECK_SLOT_CONFLICT | --neck-slot-both-ends + sliding lid | Use lid=none or lid=lift_off with through-body neck |
| ERR_LID_NOT_IMPLEMENTED | lid=hinged or lid=flap | Use lid=none, lid=lift_off, or lid=sliding |


### A.2  Common physical failures and fixes
| Symptom | Most likely cause | Fix |
|---|---|---|
| Tabs too tight, joint will not seat | Kerf compensation too low | Increase kerf_compensation by 0.05mm per iteration |
| Tabs too loose, joint rattles | Kerf compensation too high | Decrease kerf_compensation by 0.05mm per iteration |
| Leg wall tabs miss BASE slots entirely | BASE-as-master rule not implemented | Wall finger zone must inherit from BASE, not recompute |
| Corner arcs have kink at edge junction | Arc tangent point wrong | Check bisector formula: normalise(-edge_a_dir + edge_b_dir) |
| Panels slightly proud after assembly | Burn on finger faces | Sand finger faces lightly before glue-up, or reduce laser power |
| Soundboard not flat | Kerfing strips not flush | Plane kerfing strip top faces flush before fitting soundboard |
| Body not air-tight | Neck slot not plugged | Glue NECK_SLOT_PLUG into each slot before fitting neck |
| Helmholtz frequency off by &gt;5% | Neck volume not corrected | Ensure --neck-slot-both-ends triggers V_correction in solver |
| Sliding lid too wide to insert | Wrong lid width formula | **Lid width = short_inner - 2*(T+tol), not short_outer + 2*(T+tol)** |


### A.3  Proof script quick reference
| Script | Checks | Key value confirmed |
|---|---|---|
| 01_trapezoid_geometry.py | 27 | leg_angle=4.514 deg, air_volume=4,523,904 mm3 |
| 02_corner_arcs.py | 30 | tang long-end=8.317mm, tang short-end=9.739mm |
| 03_finger_joints.py | 33 | n_long=17, n_short=11, n_leg=39, lid_w=107.8mm |
| 04_panel_alignment.py | 10 | All 4 mating pairs aligned, max_offset=0.000mm |
| 05_helmholtz.py | 23 | D=22.938mm for 110Hz, corrected D=21.883mm with neck |
| 06_svg_primitives.py | Visual | 4 SVG files: arcs, finger strip, BASE outline, lid diagram |
| 07_assembly_simulation.py | 48 | ALL PASS — geometry consistent and assembly-ready |


### A.4  Plywood sheet size guide
| Use case | Recommended sheet |
|---|---|
| Box mode (no soundboard), dulcimer preset | 1 × 600 × 400mm, 3mm ply |
| Instrument mode (with soundboard + kerfing) | 2 × 600 × 400mm, 3mm ply |
| Minimum laser bed size (dulcimer preset) | 400 × 400mm (largest panel: 180×380mm BASE) |
| If building multiple boxes from one sheet | 1200 × 600mm sheet fits 3–4 full box sets |
| Material choice | 3mm birch ply preferred. MDF is heavier but cheaper. Both work. |
| Grain direction | Long axis of BASE and SOUNDBOARD aligned with sheet grain for best strength |


End of Build Validation Manual

trapezoid_boxes.py v0.20 — spec believed correct, unproven by physical cut