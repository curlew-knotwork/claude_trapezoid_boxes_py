# Engineering Process

## Mantras

- **Thinking is the job.** Proposing a spec update, writing a failing test, naming a design question — these are deliverables. Code and output generation are the smallest part. 4 units of thinking for every 1 unit of code/runs.
- **Half baked is worse than not baked.** A broken test cut, a decoupled verification script, a workaround validation — each gives false confidence and costs more than nothing.
- **Think twice, cut once.** Done well, upfront thinking pays back many times. Done poorly, it doesn't. The investment is only worthwhile if the thinking is genuinely rigorous.
- **Target: ZERO FAILURES.** Not "low failure rate." Zero. Every failure is a process failure.
- **Name things for what they are.** Ask: "what is it? what is its true purpose?" The answer makes the name obvious. Never name for implementation detail. Example: `FINGER_ZONE_BOUNDARY`, not "etch" or "score line."
- **Treat Claude as an adult.** Checklists produce compliance theater, not judgment. Principles are internalized and applied with genuine thought — proactive, self-correcting, raising design questions before being asked.

---

## Session Start (project-specific)

Before reading any code or answering any question:
1. Read `docs/FAILURE_PATTERNS.md`. Which patterns are most active? Commit to catching them proactively.
2. Read spec references listed in CLAUDE.md. Do not rely on memory.
3. Ask: what is the user actually asking? Is there a thinking question before a doing question?

---

## Process

**0. Understand first.**
Read the spec. Identify all affected components. Check `FAILURE_PATTERNS.md` — is this a recurring pattern? Ask: am I solving the right problem?

**1. Design before code.**
State the approach. Identify design questions. If a design question exists: spar first, update spec before touching code. If the fix requires rejecting valid user inputs: the implementation is wrong, not the inputs.

**2. Failing tests first.**
Write tests that express correct behaviour and currently fail. Tests must call the production module — not a copy of its logic. Failing tests define "done" before any production code is written.

**3. Implement minimally.**
Minimum change to make failing tests pass. No opportunistic additions. After changing X: grep for all other files sharing the same pattern. Fix all of them.

**4. Verify.**
Confirm the verification tool calls the changed module. Inspect actual output values — not just exit code. Trace the code path with concrete numbers against the spec. State what was verified and what was not.

**5. Done means done.**
"It ran" is not done. "I traced the math against spec §X.Y and confirmed values at all boundary conditions" is done.

---

## Sparring

Initiate (do not wait to be asked) when:
- A fix requires rejecting valid user inputs
- A workaround is being added instead of fixing root cause
- The same problem class has appeared more than once
- A standalone script is being treated as verification of production code

How: state the design question → present analysis → reach agreement → update spec and CLAUDE.md → then touch code.

---

## Anti-patterns

- Jumping to code before spec, test, and design are settled
- Adding validation that rejects valid inputs to work around a flawed implementation
- Running verification that doesn't call the changed production module
- Fixing X without checking Y and Z for the same bug class
- Declaring done without tracing actual values against spec at boundary conditions
- Standalone scripts that duplicate production logic used as verification
- Implementing around a design question instead of surfacing it
