# Recurring Failure Pattern Registry

## Registry

| # | Pattern class | Total | By Claude | By user | Sparked sparring | Sparked arch fix |
|---|---|---|---|---|---|---|
| 1 | Fix symptom not root cause | 4 | 0 | 4 | 1 | 1 |
| 2 | Verification chain decoupled (standalone script duplicates production logic) | 2 | 0 | 2 | 0 | 1 |
| 3 | Declared done without tracing math / visual inspection | 6 | 0 | 6 | 0 | 3 |
| 4 | Design question deferred — implemented workaround instead | 4 | 0 | 4 | 1 | 2 |
| 5 | Output presented without confirming it exercises changed code path | 3 | 0 | 3 | 0 | 1 |
| 6 | Same bug class in multiple files (fixed in X, not propagated to Y) | 4 | 1 | 3 | 0 | 1 |
| 7 | Requires Socratic prompting — user asks smell questions Claude should self-ask | 8 | 0 | 8 | 0 | 0 |
| 8 | Verification gap — test passes but does not cover the thing that is wrong | 2 | 0 | 2 | 0 | 2 |
| 9 | Skipped thinking-doing phase — doing-doing started without thinking-doing logged | 1 | 0 | 1 | 1 | 0 |
| 10 | Pattern scan skipped — work unit presented/committed without running scan | 0 | 0 | 0 | 0 | 0 |

**Totals (2026-03-01):** 33 occurrences. Surfaced by Claude: 1. By user: 32. Sparring: 3. Arch fixes: 10.

Target: surfaced-by-Claude grows. Surfaced-by-user shrinks. #7 rate=0 when Claude self-asks first. #8 rate=0 when defect found → test written before fix. #9 rate=0 when thinking-doing steps logged before any code. #10 is the enforcement mechanism for all others.

## Pattern Notes

1. **Symptom fix** — validation that rejects valid inputs; patch around bad design. Ex: VALIDATION_FINGER_TOO_THIN instead of removing wall arcs.
2. **Decoupled verification** — test calls its own copy of logic, not the changed module. "It passed" proves nothing.
3. **Done without tracing** — "it ran" ≠ correct. Ex: radius=0 on walls set without tracing burn overrun at boundary.
4. **Deferred design question** — point fix instead of surfacing architectural judgment. Ex: radius=0 chosen without asking what burn model does at zone boundary.
5. **Unverified code path** — fix X, run script that doesn't import X, report "verified."
6. **Bug not propagated** — fix in X, same class unfixed in Y, Z.
7. **Socratic prompting** — user asks "does this feel right?" because Claude didn't self-review. Claude should generate these questions internally.
8. **Verification gap** — tests coupled to production code but assert the wrong things. Ex: proofs 01-07 pass; no proof checks path coords stay within panel bounds.
9. **Skipped thinking-doing phase** — task received → code written; no root cause named, no design question surfaced, no thinking-doing steps stated first.
10. **Pattern scan skipped** — work unit presented or committed without running #1–#9 scan. Meta-pattern: enforcement mechanism for all others.

## Agency Protocols

Gate types: **entry** (before writing any code), **exit** (before presenting/committing), **daily** (once/day ≥ 06:00 EET at session start).

**#1 — Symptom fix** [entry]
- Gate: "Can I name the root cause, not just the symptom? If no: stop."
- Trigger: "I'm about to write a fix and can only describe the symptom. Raising before proceeding."
- Evidence: root cause named in transcript before first line of code.

**#2 — Decoupled verification** [exit]
- Gate: "Does this verification script import the changed module? Trace the chain."
- Trigger: "I'm about to report verification. Import chain not confirmed. Raising."
- Evidence: import chain stated before "verified" claim.

**#3 — Done without tracing** [exit]
- Gate: "I traced [formula] at [min/max/boundary] → [values] matching spec §X.Y. State this."
- Trigger: "I'm about to claim done. Math not traced with concrete values. Raising."
- Evidence: explicit numeric trace before done claim.

**#4 — Deferred design question** [entry]
- Gate: "Is there an architectural question I am choosing not to raise? If yes: raise it now."
- Trigger: "I see implementation paths and am about to pick one silently. Raising."
- Evidence: design question surfaced before implementation path chosen.

**#5 — Unverified code path** [exit]
- Gate: "Which file changed? Does the verification script import it? Confirm before reporting."
- Trigger: "I'm about to report verification. Code path not confirmed. Raising."
- Evidence: changed file + import chain stated before result.

**#6 — Bug not propagated** [exit]
- Gate: "What other files share this pattern class? List them. Check each one."
- Trigger: "I fixed X. I have not checked Y, Z for the same bug class. Raising."
- Evidence: list of files audited stated alongside fix.

**#7 — Socratic prompting** [exit]
- Gate: Log answers to: "Does this feel right? What could go wrong? Why this approach? What would I miss?"
- Trigger: "I'm about to present. Smell-test not yet logged internally. Doing it now."
- Evidence: smell-test answers in transcript before presentation.

**#8 — Verification gap** [exit]
- Gate: "What specific failure mode does this assertion cover? Map explicitly."
- Trigger: "I'm writing a test. I have not mapped assertion → failure mode. Raising."
- Evidence: assertion → failure mode mapping stated when test is written.

**#9 — Skipped thinking-doing phase** [entry]
- Gate: Before any code: state (a) root cause vs symptom, (b) thinking-doing steps needed, (c) any design question worth surfacing.
- Trigger: "I received a task and am about to start doing-doing without logging a thinking-doing step. Raising."
- Evidence: thinking-doing steps stated in transcript before first code written.

**#10 — Pattern scan skipped** [exit + daily]
- Gate (exit): Before presenting/committing: run scan #1–#9, log each yes/no. Surface any yes before proceeding.
- Gate (daily): ≥ 06:00 EET, once/day: scan + review counts for trends + raise sparring topic if any count increased.
- Trigger: "I'm about to present/commit. Pattern scan not run. Running now."
- Evidence: scan log in transcript before every result/commit; daily scan logged at session start.

## Session Log

CLAUDE.md ver = date of global CLAUDE.md at session start. Needed to slice Asymmetric Contribution ratio before/after rule changes. Record per session.

| Date | CLAUDE.md ver | Work done | Patterns | Notes |
|------|--------------|-----------|----------|-------|
| 2026-02-xx | pre-2026-03-01 | Initial implementation | 1,2,3,4,5,6 | Counts established retroactively; ver unknown |
| 2026-03-01 | pre-2026-03-01 | Corner arc redesign sparring + impl | 1,3,4,6 | Sparring initiated by user |
| 2026-03-01 | pre-2026-03-01 | Complete redesign + gen_test_cut rewrite | 6,7 | Pattern 7 surfaced by user |
| 2026-03-01 | pre-2026-03-01 | Burn model boundary overrun found post-commit | 3,4,7,8 | radius=0 on walls; proofs passed; user caught visually after ~1 day |
| 2026-03-01 | pre-2026-03-01 | Agency protocol sparring + redesign | 9 | Sparring initiated by user; patterns #9, #10 added; agency protocols added |
| 2026-03-01 | pre-2026-03-01 | Wall joint complementarity + arc_BL propagation + proof 09 | 6,7,8 | #6 first surfaced by Claude (arc_BL not in instrument from prior fix); #7 user asked "do joints mate?"; #8 filled by proof 09 (35/35 pass) |
| 2026-03-02 | 2026-03-02 | CLAUDE.md audit vs external template; accuracy fixes | 7 | User prompted metrics design → version tagging insight (pattern #7: Socratic prompting) |
