# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:     docs/SPECIFICATION.md
- Process:  docs/ENGINEERING_PROCESS.md  ← mantras, sparring protocol, anti-patterns
- Proofs:   proofs/  (run before claiming correctness)
- Patterns: docs/FAILURE_PATTERNS.md     ← read at session start
- Style:    PEP8, strict typing, ruff + mypy clean

## BURN MODEL
SVG paths are laser centerlines. Laser removes `burn` mm from each side of every cut.
- drawn_tab  = fw + 2*burn   → physical_tab  = fw
- drawn_slot = fw - 2*burn + 2*tol  → physical_slot ≈ fw + 2*tol
- depth      = T + burn
- nominal_fit = drawn_slot - drawn_tab = -4*burn + 2*tol
- DEFAULT: burn=0.05, tol=0.0 → fit=-0.2mm (rubber mallet)
- WRONG: tab=fw-tol, gap=fw+tol (clearance not interference)
- WRONG: tab=fw, gap=fw (laser widens gap, narrows tab → +4*burn floppy)
- WRONG: burn=0.1, tol=0.1 (double-counts kerf, looks right but isn't)

## BURN MODEL BOUNDARY RULE
tab_width = fw + 2*burn > fw. For n tabs in a zone of length n*fw: drawn overrun = 2*burn.
Without a buffer ≥ 2*burn at zone end, the last tab exits the panel boundary.

**Minimum corner radius for any finger edge: `corner_radius ≥ 2*burn`.**
For 90° corners, tangent_dist = corner_radius. For non-90°: tangent_dist = r / tan(angle/2).
- `radius=0` is forbidden on any panel with finger edges.
- verify_or_abort must check: no outline coordinate exceeds nominal panel bounding box by > burn.

## GEOMETRY RULES
- Trapezoid corners: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle). Wrong assignment is silent.
- Corner radius: fixed mm, NEVER ratio. Ratio fails at steep leg angles.

## CORNER ARC MODEL
Three distinct concepts:
1. **BASE cut outline**: true trapezoid, four straight edges. Tiny safety chamfer (≤2mm, cut) optional.
2. **Finger zone boundary**: tangent_dist = R / tan(angle/2). Controls where tabs start/stop.
3. **Corner arc etch**: non-cut mark on BASE only — makes zone boundary visible. Not on walls, not on lids.

Wall panels: plain rectangles, no arcs. Lid panels: plain shape, no arcs.
WRONG: using arc radius to limit wall-to-wall finger zone. WRONG: cutting arcs into wall outlines.

## SVG OUTPUT RULES
- stroke-width="0.1" (unitless). Never "0.001mm", never "0.3mm".
- Every generator runs verify_or_abort() before writing:
  - All coordinates finite and within sheet bounds
  - No outline coordinate exceeds nominal panel bounding box by > burn
  - All paths end with Z
  - No bounding box overlaps
  - Soundhole corner angles within 0.1° of expected
- Fail → print errors, do not write, do not present.

## WHAT NOT TO DO
- Use ratio-based corner radii.
- Use mm-suffixed stroke-width on cut lines.
- Set `corner_radius < 2*burn` on any panel with finger edges.
- Present an SVG that has not passed verification.
