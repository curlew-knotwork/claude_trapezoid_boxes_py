# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:   docs/SPECIFICATION.md  
- Proofs: proofs/  (run before claiming correctness)
- Style:  PEP8, strict typing, ruff + mypy clean

## INVARIANTS
- Units: track throughout. Physics/geometry requires dimensional sanity check.
- Unknowns: if any API/constant is uncertain, say so before using it.
- Trapezoid corner angles: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle). Wrong assignment produces invalid geometry silently.
- Corner radius: fixed mm, never a ratio. Ratio-based radius fails visually at steep leg angles.

## OUTPUT VERIFICATION
- SVG: parse generated coordinates back to mm and verify against expected geometry before presenting. Do not present unverified SVG output.
- Proofs: if changing geometry, run affected proof scripts and show pass/fail counts.

## WHAT NOT TO DO
- Do not present output and wait for the user to find the bug.
- Do not re-derive known invariants from scratch — check the spec first.

## USER
Senior engineer. Terse. Catch your own bugs before presenting. 
No summaries after file links. No "great question".