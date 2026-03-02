---
description: Run pattern scan #1–#10 before committing or presenting results
allowed-tools: Read, Bash(python3:*)
---

Log yes/no for each item. Surface any yes before proceeding.

1. Root cause named (not just symptom) before first code line?
2. Proof imports the changed production module (not a mock or reimplementation)?
3. Design question surfaced (not silently picked an implementation path)?
4. Changed module is what the proof actually calls (not a decoupled script)?
5. All files sharing this bug class checked (fix in X → verified Y, Z)?
6. Every assert maps to a named failure mode?
7. Thinking-doing steps stated before first code line?
8. This scan: running it now counts as yes.

Update counts in docs/FAILURE_PATTERNS.md for any yes.
