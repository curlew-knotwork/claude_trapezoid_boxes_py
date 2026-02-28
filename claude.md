# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:   docs/SPECIFICATION.md
- Proofs: proofs/  (run before claiming correctness)
- Style:  PEP8, strict typing, ruff + mypy clean

## USER
Senior engineer. Terse. No summaries after file links. No "great question".

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


- Units: track throughout. Physics/geometry requires dimensional sanity check.
- Unknowns: if any API/constant is uncertain, say so before using it.
- Trapezoid corner angles: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle). Wrong assignment produces invalid geometry silently.
- Corner radius: fixed mm, never a ratio. Ratio-based radius fails visually at steep leg angles.

## SVG OUTPUT RULES
- stroke-width="0.1" (unitless). Never "0.001mm". Never "0.3mm". Unitless is visible on screen AND hairline at laser DPI.
- Every SVG generator must run verify_or_abort() before writing the file:
  - All coordinates finite and within sheet bounds
  - All paths end with Z
  - No bounding box overlaps
  - Soundhole corner angles within 0.1° of expected
- If verification fails: print errors, do not write file, do not present output.
- Never present an SVG that has not passed verification.

## WHAT NOT TO DO
- Do not present output and wait for the user to find the bug.
- Do not re-derive known invariants from scratch — check the spec first.
- Do not use ratio-based corner radii.
- Do not use mm-suffixed stroke-width on cut lines.
