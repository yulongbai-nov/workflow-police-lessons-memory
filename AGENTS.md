# Agent Notes

This repo follows a spec-first workflow.

## Source of truth

For this feature, treat these files as authoritative:

- `.specs/lessons-memory-foundation/design.md`
- `.specs/lessons-memory-foundation/requirements.md`
- `.specs/lessons-memory-foundation/tasks.md`
- `references/generic-software-workflow.md`
- `references/copilot-chat-spec-workflow-generic-extract.md`

## Phase model

- Default phase: design
- Implementation starts only after design and requirements are accepted

## Working rules

- Update spec docs before code when scope changes.
- Keep tasks granular and traceable to requirements.
- Preserve phase-1 boundary: single lessons-repo source first.
- Keep deterministic checks as block authority; keep semantic review advisory unless policy explicitly elevates severities.
- For automation scripts, prefer Python first (`scripts/tools/*.py`) for platform-agnostic execution.
- Use `scripts/tools/safe_remove.py` for delete operations instead of ad-hoc shell deletions.
