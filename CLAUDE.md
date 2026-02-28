# PROJECT: TRAPEZOID_BOX

## REFERENCES
- Spec:   docs/SPECIFICATION.md
- Proofs: proofs/  (run before claiming correctness)
- Style:  PEP8, strict typing, ruff + mypy clean

## USER
Senior engineer. Terse. No summaries after file links. No "great question".

## INVARIANTS
- Track units throughout; verify dimensional sanity.
- Unknowns: if any API/constant is uncertain, say so before using it.

## SVG OUTPUT RULES
- Cut line style: fill="none" stroke="red" stroke-width="0.1" (all three required).
  stroke-width must be unitless 0.1. Never "0.001mm". Never "0.3mm".
- Every SVG generator must run verify_or_abort() before writing the file:
  - All coordinates finite and within sheet bounds
  - All paths end with Z
  - No bounding box overlaps
  - Soundhole corner angles within 0.1° of expected
- If verification fails: print errors, do not write file, do not present output.
- Never present an SVG that has not passed verification.

## SELF-VERIFICATION PROTOCOL (mandatory, all non-trivial logic)
Before implementing:
- Every variable feeding a formula: look up its definition and value. Never reason from names.
- Every formula: substitute one concrete input, trace to expected output. Fix before coding if wrong.
- Name all coordinate/sign-convention assumptions; challenge each with a concrete test case.

After implementing:
- Run it. Read all output including numbers.
- Identify the most plausible mistake; check for it in output.
- Verify against known constraints (bounds, symmetry, mating-part complementarity).

On failure: fix and restart from top. No partial reports. No asking user to check.

## GEOMETRY-SPECIFIC INVARIANTS
- Trapezoid corners: narrow-end = obtuse (90+leg_angle), wide-end = acute (90-leg_angle).
- Corner radius: fixed mm, never a ratio.
- SVG is y-down. Left-of-travel perpendicular = (d[1], -d[0]). Check: d=(1,0) → (0,-1)=up ✓

## WHAT NOT TO DO
- Do not re-derive known invariants from scratch — check the spec first.
- Do not use mm-suffixed stroke-width on cut lines.
