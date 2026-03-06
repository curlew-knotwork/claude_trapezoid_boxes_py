# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:   docs/SPECIFICATION.md
- Proofs: proofs/  (run before claiming correctness)
- Style:  PEP8, strict typing, ruff + mypy clean

## USER
Senior engineer. Terse. No summaries after file links. No "great question".

## INVARIANTS
- Units: track throughout. Physics/geometry requires dimensional sanity check.
- Unknowns: if any API/constant is uncertain, say so before using it.
- Trapezoid corner angles: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle). Wrong assignment produces invalid geometry silently.
- Corner radius: fixed mm, never a ratio. Ratio-based radius fails visually at steep leg angles.

## SVG OUTPUT RULES
- Cut lines: stroke-width="0.1" (unitless). Score/etch lines: stroke-width="0.3" (unitless).
- Routing is by stroke-width only (Epilog Fusion M2): ≤0.1 → vector cut; ≥0.3 → raster etch. Color is human convention, not machine routing.
- Never use mm-suffixed stroke-width. Never use 0.001 (invisible on screen).
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