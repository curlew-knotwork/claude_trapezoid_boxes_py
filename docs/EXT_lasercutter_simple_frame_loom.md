# External Lessons: lasercutter-simple-frame-loom

Source repo: https://github.com/curlew-knotwork/lasercutter-simple-frame-loom
Protocol: see `docs/ENGINEERING_PROCESS.md § External Lessons`

Entries are append-only. If the source project revises a lesson, add a REVISION note below the original entry — do not delete or overwrite.

---

## EXT-001 — Silent geometry degradation

Imported: 2026-03-19
Source: `lasercutter-simple-frame-loom / FAILURE_PATTERN_REGISTRY.md` (category G / pattern P-G, context: wall-to-wall joint generation)
Status: **UNVERIFIED-HERE** (source pattern is from code analysis, not a physical test — credible regardless of machine)

Summary: `make_finger_edge()` returned `count=0` (plain edge, no joints) with only `warnings.warn` when corner radius left insufficient room for joints. The box was geometrically valid SVG but structurally unassembleable. No hard error was raised; the soft failure was silent to the caller and to any proof checking the SVG for validity.

Lesson for this project: `verify_or_abort()` checks coordinates and path closure but does not check that functional geometry (joints, tabs, slots) is present and deep enough. A generator can produce a passing SVG where all joints are zero-depth or absent. This is a distinct failure mode from geometry being out of bounds.

Candidate pattern: **"Soft failure masking a hard assembly requirement"** — code degrades gracefully when it should fail hard.

Staleness: Re-check source repo if `FAILURE_PATTERN_REGISTRY.md` is updated or if loom physical test cuts are made. If source project retracts or requalifies this pattern, add REVISION note below.

---

## EXT-002 — Kerf prior: 0.15mm per side

Imported: 2026-03-19
Source: `lasercutter-simple-frame-loom / CLAUDE.md` (line: `kerf=0.15mm`)
Status: **SUSPECT-CIRCULAR — do not use as independent prior**

Summary: Loom project CLAUDE.md states `kerf=0.15mm`. If this came from an independent physical test on the same Oodi Epilog Fusion M2, it would be a strong prior: for a nominal-3mm joint, total gap = 4×0.15 = 0.60mm, so drawn slot ≈ 2.4mm for a snug fit.

Circularity flag: User confirmed (2026-03-19) that no physical test cuts have been made for the loom project. The 0.15mm figure likely originated from a discussion of THIS project's floppy joint result (FAILURE_REPORT entry: burn model wrong), was noted in loom's CLAUDE.md, and was then re-imported here as if it were independent loom data. It is not independent.

Actionable: Use `02_kerf_calibration.svg` results (today's Oodi test) as the first real measurement. Once we have actual kerf data from this project, update this entry's Status and optionally feed the confirmed value back to the loom project.

Staleness: When loom project makes its first physical test cut, its kerf value will become independent. At that point update Status to VERIFIED or REVISED-DIFFERS as appropriate.
