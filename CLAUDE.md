# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:     docs/SPECIFICATION.md
- Process:  docs/ENGINEERING_PROCESS.md  ← mantras, sparring protocol, anti-patterns
- Proofs:   proofs/  (run before claiming correctness)
- Patterns: docs/FAILURE_PATTERNS.md     ← check before starting any task
- Style:    PEP8, strict typing, ruff + mypy clean

## BURN MODEL
SVG paths are laser centerlines. Laser removes burn mm from each side of every cut.
- drawn_tab  = fw + 2*burn   → physical_tab  = fw  (kerf removes 2*burn total)
- drawn_slot = fw - 2*burn + 2*tol   → physical_slot = fw + 2*tol
- depth      = T + burn
- nominal_fit = drawn_slot - drawn_tab = -4*burn + 2*tol
- DEFAULT: burn=0.05, tol=0.0 → fit=-0.2mm (rubber mallet, matches boxes.py)
- burn=0.05, tol=0.1 → fit=0.0mm (hand press)
- Larger burn = tighter. Larger tol = looser. Tune in 0.01mm steps.
- WRONG (floppy): tab=fw, gap=fw, only depth adjusted. Laser widens gap and narrows tab → +4*burn clearance.
- WRONG (also floppy): burn=0.1, tol=0.1 looks like fit=-0.2mm but physical fit=0.0mm — double-counts kerf.
- WRONG (clearance not interference): tab=fw-tol, gap=fw+tol.

## GEOMETRY RULES
- Trapezoid corner angles: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle). Wrong assignment produces invalid geometry silently.
- Corner radius: fixed mm, NEVER ratio. Ratio-based radius fails visually at steep leg angles.

## CORNER ARC MODEL (supersedes any prior arc-as-cut approach)
Three distinct concepts — never conflate them:

1. BASE cut outline: true trapezoid, four straight edges. Optional tiny safety chamfer at each
   corner (cut, ≤2mm) to prevent sharp points/splintering. NOT the finger-zone arc.

2. Finger zone boundary: tangent distance = R / tan(angle/2) from each corner vertex.
   This is a pure calculation — it controls where finger tabs start and stop.
   R is still a meaningful parameter (default 3×T, fixed mm, not ratio).

3. Corner arc etch: the arc at each BASE corner, drawn as a non-cut score/etch line.
   Purpose: makes the finger zone boundary visible for SVG inspection and human discussion.
   Exists on BASE only. Not on wall panels. Not on lids.

Wall panels: plain rectangles, no corner arcs (cut or etch). Full depth_outer available
for wall-to-wall finger zone.

Lid panels: plain trapezoid/rectangle. Optional tiny safety chamfer matching BASE. No etch arcs.

WRONG: using corner arc radius to limit wall-to-wall finger zone (that logic is deleted).
WRONG: cutting corner arcs into BASE or wall panel outlines.

## SVG OUTPUT RULES
- stroke-width="0.1" (unitless). Never "0.001mm". Never "0.3mm". Unitless is visible on screen AND hairline at laser DPI.
- Every SVG generator must run verify_or_abort() before writing the file:
  - All coordinates finite and within sheet bounds
  - All paths end with Z
  - No bounding box overlaps
  - Soundhole corner angles within 0.1° of expected
- If verification fails: print errors, do not write file, do not present output.
- Never present an SVG that has not passed verification.

## WHAT NOT TO DO (project-specific)
- Do not use ratio-based corner radii.
- Do not use mm-suffixed stroke-width on cut lines.
