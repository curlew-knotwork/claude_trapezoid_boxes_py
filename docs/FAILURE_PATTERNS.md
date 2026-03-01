# Recurring Failure Pattern Registry

Persistent record of recurring problem classes across all sessions.
Update counts and session log when a pattern recurs or is surfaced.

## Registry

| # | Pattern class | Total occurrences | Surfaced by Claude | Surfaced by user | Led to sparring | Led to arch/spec fix |
|---|---|---|---|---|---|---|
| 1 | Fix symptom not root cause | 4 | 0 | 4 | 1 | 1 |
| 2 | Verification chain decoupled (standalone script duplicates production logic) | 2 | 0 | 2 | 0 | 1 |
| 3 | Declared done without tracing math / visual inspection | 5 | 0 | 5 | 0 | 2 |
| 4 | Design question deferred — implemented workaround instead | 3 | 0 | 3 | 1 | 1 |
| 5 | Output presented without confirming it exercises changed code path | 3 | 0 | 3 | 0 | 1 |
| 6 | Same bug class in multiple files (fixed in X, not propagated to Y) | 3 | 0 | 3 | 0 | 0 |
| 7 | Requires Socratic prompting — user asks smell questions Claude should self-ask | 5 | 0 | 5 | 0 | 0 |

**Running totals (as of 2026-03-01):**
- Total occurrences tracked: 25
- Surfaced proactively by Claude: 0
- Surfaced by user (Claude missed): 25
- Led to sparring/design discussion: 2
- Led to architecture or spec correction: 6

## Pattern Descriptions

**1. Fix symptom not root cause**
Adding validation that rejects valid user inputs; patching around a flawed design rather than
questioning the design. Example: adding VALIDATION_FINGER_TOO_THIN to reject small boxes
when the real problem was corner arcs on wall panels.

**2. Verification chain decoupled**
Standalone scripts (gen_test_cut.py, proof scripts) duplicate production logic and are used
as verification — but they verify only their own copy, not the changed production path.
"It passed" means nothing if the tool doesn't call the fixed code.

**3. Declared done without tracing math**
Presenting SVG output or claiming correctness without tracing computed values against the spec.
"It ran without error" is not verification. Examples: hanging tab survived 9 declarations of
correctness; corner angle inversion caught only by user visual inspection.

**4. Design question deferred**
When a fix requires architectural judgment, defaulting to a point fix and moving on.
The cost: entropy accumulates, later fixes are more expensive, the user must initiate sparring.
Example: corner arcs on wall panels caused wall-to-wall joint failures across many small boxes;
the design question (why do walls have arcs at all?) was never raised proactively.

**5. Output presented without verifying code path**
Regenerating output after a fix without confirming the regeneration calls the fixed module.
Classic form: fix core/joints.py, run gen_test_cut.py (which doesn't import joints.py),
report "verification passed."

**6. Same bug class not propagated**
Fix applied to X but not audited in Y, Z which share the same pattern. Examples: burn model
fixed in gen_test_cut.py but not core/joints.py; slotted edge condition fixed in joints.py
but not checked in instrument panels.

**7. Requires Socratic prompting**
User asks broad smell/indicative questions ("does this feel right?", "what could go wrong?",
"why are you doing it this way?", "are you sure about this?") because Claude hasn't
self-reviewed. The user is supplying the prompts for reflection that Claude should generate
internally. Related to #3 (declared done without tracing) but the failure mode is
communication: Claude forces the user to act as a thinking scaffold rather than thinking first.
Target behaviour: Claude self-asks these questions before presenting output.

## How to Use This File

After each session:
1. Review which patterns recurred and increment counts.
2. If Claude surfaced a pattern proactively (before user raised it), increment that column.
3. Append a row to the Session Log below.

Target: surfaced-by-Claude column should grow. Surfaced-by-user column should shrink.
Pattern #7 rate = 0 when Claude asks smell questions before the user has to.

## Session Log

| Date | Work done | Patterns recurred | Notes |
|------|-----------|-------------------|-------|
| 2026-02-xx | Initial implementation sessions | 1,2,3,4,5,6 identified | All counts established retroactively |
| 2026-03-01 | Corner arc redesign sparring + implementation | 1 (VALIDATION workaround), 3, 4, 6 | Sparring initiated by user; redesign required arch change |
| 2026-03-01 | Context continuation: complete redesign + gen_test_cut rewrite | 6 (hardware/kerfing Panel missing field), 7 | Pattern 7 surfaced by user asking indicative questions about doc location and temporal tracking |
