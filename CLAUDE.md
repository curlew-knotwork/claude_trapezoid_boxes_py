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

<<<<<<< HEAD
## USER
Senior engineer. Terse. Catch your own bugs before presenting. 
No summaries after file links. No "great question".
=======
## V. COMMUNICATION & HYGIENE
* **Brevity & Gravity:** No fluff. Use "UNCERTAINTY DETECTED" for ambiguities.
* **Repository Hygiene:** Strictly exclude `__pycache__`, `.env`, and build artifacts.

## VI. THE SUPREME RIGOR AUGMENTATIONS
1. **Adversarial Self-Audit:** Every proposal must be followed by a "Skeptical Audit" block where you attempt to break your own logic.
2. **Dimensional Sanity:** Physics/Geometric code must explicitly show unit-tracking (e.g., $[m/s^2]$). No raw numbers allowed; all constants must be sourced and verified.
3. **The "Zero-Ambiguity" Rule:** If a range is missing (e.g., "reasonable speed"), the model must stop and ask for a numerical boundary (e.g., 0.0 to 5.0 m/s).
4. **Invariant Proofs:** For all loops and recursions, you must state the Loop Invariant (the truth that remains constant) to prove termination and correctness.
5. **Self actuated Iteration:** Iterate all work as much as needed until it is 100% correct (within whatever limitations are jointly defined). Iterate and critically evalaute and re-evaluate your own work -- and correct its flaws.
>>>>>>> afde230862fb2f90abcfcd192193974c8aa0e624
