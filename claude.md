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

## SELF-REVIEW PROTOCOL — MANDATORY BEFORE ANY "DONE" CLAIM

The recurring failure mode: make a change, declare victory, user finds the bug in seconds, repeat.
This is not acceptable. Before saying anything is fixed, correct, or complete, execute this checklist:

1. **Read every file you touched, in full.** Not just the changed lines. The whole file, top to bottom.
2. **Trace the full code path with concrete numbers.** Use real inputs (e.g., fw=5.0, burn=0.05, tol=0.0).
   Compute the expected output from the spec by hand. Then follow the code and verify it matches — to the digit.
3. **Audit every file that shares the same pattern.** Fix in joints.py? Immediately check gen_test_cut.py, proofs/, and any other file that touches burn/tab/slot. Same class of bug may exist in multiple places.
4. **Re-read the relevant spec section.** Do not trust memory notes — they have been wrong before. The spec is authoritative.
5. **Run verification scripts and inspect the output values**, not just "did it exit 0?"
   Check nominal_fit, panel dimensions, finger counts — not just absence of crash.
6. **Actively look for what you missed.** Assume something is wrong. Find it yourself before the user does.
7. **Check consistency across mating parts.** If panel A changed, verify panel B still fits panel A.

If any step cannot be completed, say so explicitly and state what remains unverified.
Never say "all fixed" or "tests pass" without completing this protocol.
"It ran without error" is not verification. "I traced the math and it matches spec §X.Y" is verification.

## WHAT NOT TO DO
- Do not present output and wait for the user to find the bug.
- Do not re-derive known invariants from scratch — check the spec first.
- Do not use ratio-based corner radii.
- Do not use mm-suffixed stroke-width on cut lines.
- Do not treat "STATUS: fixed" in memory notes as ground truth — verify against actual code.
