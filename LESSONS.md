# LESSONS (Root-Cause Analysis)

## How to add a lesson

Add a dated entry with:
- Symptom
- Root cause
- Fix
- Prevention

## 2026-02-06 - Keep deterministic checks as block authority

- Symptom: Purely semantic review can produce uncertain findings, making hard block behavior unstable.
- Root cause: LLM review is context-sensitive and non-deterministic by nature.
- Fix: Use deterministic checks for block decisions and keep semantic review advisory by default.
- Prevention: Explicitly configure block severities for semantic findings and default them to empty.
