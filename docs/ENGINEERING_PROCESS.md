# Engineering Process

## Mantras

- **Half baked is worse than not baked at all.** A broken test cut, a decoupled verification
  script, a workaround validation — each gives false confidence and costs more than nothing.
- **Think twice, cut once.** Thinking is expensive — but far more valuable than making errors
  and iterating. Done well, upfront thinking pays back many times over. Done poorly, it doesn't.
  The investment is only worthwhile if the thinking is genuinely rigorous.
- **Target: ZERO FAILURES.** Not "low failure rate." Zero. Every failure is a process failure.
- **Treat Claude as an adult.** Checklists and gates produce compliance theater, not judgment.
  Principles are internalized and applied with genuine thought — proactive, self-correcting,
  raising design questions before being asked.

---

## Process

**0. Understand first.**
Read the spec. Identify all affected components. Ask: am I solving the right problem?
Check `FAILURE_PATTERNS.md` — is this a recurring pattern?

**1. Design before code.**
State the approach. Identify design questions. If a design question exists: spar first.
If the fix requires rejecting valid user inputs: the implementation is wrong, not the inputs.

**2. Failing tests first.**
Write tests that express correct behaviour precisely and currently fail.
Tests must import and call the production module — not a copy of its logic.
Failing tests define "done" before a line of production code is written.

**3. Implement minimally.**
Minimum change to make failing tests pass. No opportunistic additions.
After changing X: grep for all other files sharing the same pattern. Fix all of them.

**4. Verify.**
Confirm the verification tool calls the changed module.
Inspect actual output values — not just exit code.
Trace the code path with concrete numbers against the spec.
State what was verified and what was not.

**5. Done means done.**
"It ran" is not done. "I traced the math against spec §X.Y" is done.

---

## Sparring

When to initiate (raise it — do not wait to be asked):
- A fix requires rejecting valid user inputs
- A workaround is being added instead of fixing the root cause
- The same problem class has appeared more than once
- A standalone script is being treated as verification of production code

How: state the design question, present analysis, reach agreement on correct design,
then update spec and CLAUDE.md before touching code.

---

## Anti-patterns

- Adding validation that rejects valid inputs to work around a flawed implementation
- Running verification that doesn't call the changed production module
- Fixing X without checking Y and Z for the same bug class
- Declaring done without tracing actual values against spec
- Standalone scripts that duplicate production logic
- Implementing around a design question instead of surfacing it
