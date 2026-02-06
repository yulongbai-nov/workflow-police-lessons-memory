# Workflow Police Lessons Memory

Spec-first repository for a reusable lessons and memory model that integrates with `workflow-police`.

## Purpose

Build a generic way to capture, retrieve, and promote lessons at multiple abstraction levels:

- case-specific lessons
- reusable patterns
- cross-project principles

Phase 1 is intentionally lessons-repo bound (single source) to keep adoption simple.  
Phase 2 can add cross-repo retrieval through MCP or other memory backends.

## Documents

- Design: `.specs/lessons-memory-foundation/design.md`
- Requirements: `.specs/lessons-memory-foundation/requirements.md`
- Tasks: `.specs/lessons-memory-foundation/tasks.md`
- Workflow baseline: `references/generic-software-workflow.md`
- Generic extract from spec-oriented AGENTS prompt: `references/copilot-chat-spec-workflow-generic-extract.md`

## Prototype scripts

- Python-first (platform agnostic):
  - `scripts/tools/init_feature_spec.py`
  - `scripts/tools/bootstrap_lessons_repo.py`
  - `scripts/tools/update_lessons_index.py`
  - `scripts/tools/promote_lesson.py`
  - `scripts/tools/agent_lessons_preflight.py`
  - `scripts/tools/agent_semantic_guard.py` (Codex subprocess reviewer)
  - `scripts/tools/agent_workflow_guard.py` (deterministic + semantic aggregation)
  - `scripts/tools/safe_remove.py` (deletion wrapper)
- PowerShell compatibility wrappers/prototypes (optional):
  - `scripts/tools/init_feature_spec.ps1`
  - `scripts/tools/agent_lessons_preflight.ps1`
  - `scripts/tools/agent_semantic_guard.ps1`
  - `scripts/tools/agent_workflow_guard.ps1`
- Policy: `scripts/config/agent/agent_workflow_policy.json`

## Runbook and tests

- Runbook: `runbooks/sample_workflow_police_runbook.md`
- Smoke test:
  - `python tests/run_smoke.py`
- End-to-end runbook test:
  - `python tests/run_sample_runbook_e2e.py`

## Status

- Phase: design with implementation spike
- Initial draft: committed
