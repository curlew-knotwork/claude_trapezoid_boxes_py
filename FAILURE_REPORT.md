# trapezoid_box — Failure Report

| Timestamp (UTC) | Δ prev | Iterations to fix | Failure | Detail |
|---|---|---|---|---|
| 2026-02-26T18:21:39Z | — | 2 sessions, ~11h | SVG visual inspection skipped — hanging tab | 06c_full_base.svg contained a hanging tab (finger overshot arc tangent point by 14.6mm) present since session 12; survived 9 declarations of spec correctness, 2 days, 15 sessions, and external Gemini audit; found only when user opened the file — arithmetic proof passing was treated as equivalent to output correctness, which it is not |
| 2026-02-27T01:28:21Z | +7h 6m | 6 SVG generations, ~25m | SVG visual inspection skipped — trapezoid corner angles inverted | Soundhole rounded-trapezoid corners had obtuse/acute assignment exactly backwards; narrow-end = obtuse (90+leg_angle), wide-end = acute (90−leg_angle) — same rule as body panel, never verified from geometry. Produced blobs/bumps, caught only by user each time. Same root cause as hanging tab: output presented without verifying geometry. Fix: invariant in spec §8, proofs 05+06, claude.md. |
