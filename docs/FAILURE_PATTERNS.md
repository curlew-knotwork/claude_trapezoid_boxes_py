# Recurring Failure Pattern Registry

## Registry

| # | Pattern class | Total | By Claude | By user | Sparked sparring | Sparked arch fix |
|---|---|---|---|---|---|---|
| 1 | Fix symptom not root cause | 4 | 0 | 4 | 1 | 1 |
| 2 | Verification chain decoupled (standalone script duplicates production logic) | 2 | 0 | 2 | 0 | 1 |
| 3 | Declared done without tracing math / visual inspection | 6 | 0 | 6 | 0 | 3 |
| 4 | Design question deferred — implemented workaround instead | 4 | 0 | 4 | 1 | 2 |
| 5 | Output presented without confirming it exercises changed code path | 3 | 0 | 3 | 0 | 1 |
| 6 | Same bug class in multiple files (fixed in X, not propagated to Y) | 3 | 0 | 3 | 0 | 0 |
| 7 | Requires Socratic prompting — user asks smell questions Claude should self-ask | 6 | 0 | 6 | 0 | 0 |
| 8 | Verification gap — test passes but does not cover the thing that is wrong | 1 | 0 | 1 | 0 | 1 |

**Totals (2026-03-01):** 29 occurrences. Surfaced by Claude: 0. By user: 29. Sparring: 2. Arch fixes: 8.

Target: surfaced-by-Claude grows. Surfaced-by-user shrinks. #7 rate=0 when Claude self-asks first. #8 rate=0 when defect found → test written before fix.

## Pattern Notes

1. **Symptom fix** — validation that rejects valid inputs; patch around bad design. Ex: VALIDATION_FINGER_TOO_THIN instead of removing wall arcs.
2. **Decoupled verification** — test calls its own copy of logic, not the changed module. "It passed" proves nothing.
3. **Done without tracing** — "it ran" ≠ correct. Ex: radius=0 on walls set without tracing burn overrun at boundary.
4. **Deferred design question** — point fix instead of surfacing architectural judgment. Ex: radius=0 chosen without asking what burn model does at zone boundary.
5. **Unverified code path** — fix X, run script that doesn't import X, report "verified."
6. **Bug not propagated** — fix in X, same class unfixed in Y, Z.
7. **Socratic prompting** — user asks "does this feel right?" because Claude didn't self-review. Claude should generate these questions internally.
8. **Verification gap** — tests coupled to production code but assert the wrong things. Ex: proofs 01-07 pass; no proof checks path coords stay within panel bounds.

## Session Log

| Date | Work done | Patterns | Notes |
|------|-----------|----------|-------|
| 2026-02-xx | Initial implementation | 1,2,3,4,5,6 | Counts established retroactively |
| 2026-03-01 | Corner arc redesign sparring + impl | 1,3,4,6 | Sparring initiated by user |
| 2026-03-01 | Complete redesign + gen_test_cut rewrite | 6,7 | Pattern 7 surfaced by user |
| 2026-03-01 | Burn model boundary overrun found post-commit | 3,4,7,8 | radius=0 on walls; proofs passed; user caught visually after ~1 day |
