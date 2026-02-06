# Design Document: Lessons Memory Foundation

## Overview

This feature defines a reusable lessons memory system for engineering workflows, integrated with `workflow-police`.

The problem: important lessons are often stored as flat notes, hard to retrieve, and mixed across abstraction levels. This leads to repeated mistakes and poor transferability.

The design introduces a structured lessons hierarchy, retrieval pipeline, and promotion lifecycle:

- Level 1: case lessons (incident-specific)
- Level 2: pattern lessons (reusable operational pattern)
- Level 3: principle lessons (stable cross-domain guidance)

Phase 1 scope is intentionally narrow: one canonical lessons repository as source of truth.

## Current Architecture

Current state across repos:

- lessons often live in a single `LESSONS.md`
- retrieval is mostly keyword matching in preflight scripts
- no consistent metadata for confidence, transferability, or validation age
- no formal promotion process from case to pattern/principle

## Proposed Architecture

### Repository layout

Use a structured lessons store:

```
lessons/
  cases/
  patterns/
  principles/
  index.json
```

Each lesson file uses lightweight metadata frontmatter:

- `id`
- `level` (`case`, `pattern`, `principle`)
- `status` (`candidate`, `validated`, `canonical`, `retired`)
- `tags`
- `confidence` (1-5)
- `transferability` (1-5)
- `source_case_ids`
- `last_validated_at`

### Retrieval pipeline

At task start:

1. Parse task text and extract weighted tokens.
2. Query `index.json` and lesson metadata.
3. Rank lessons by:
   - level priority (`principle` > `pattern` > `case`)
   - tag overlap
   - confidence
   - transferability
   - recency
4. Return a compact selected set:
   - top principles
   - top patterns
   - up to two supporting cases

### Workflow integration

`workflow-police` should:

- ensure preflight runs before changes
- report selected lessons in the first status update
- run guard checks before final response and before commit/push
- require lesson updates when novel incidents are resolved
- use hybrid guard lanes:
  - deterministic lane (block authority)
  - semantic lane via Codex subprocess reviewer (advisory by default)

### Promotion lifecycle

- Case -> Pattern: requires >=2 independent case references.
- Pattern -> Principle: requires >=3 validated pattern applications across distinct contexts.
- Any -> Retired: superseded or invalid after review.

## Components

- `init_feature_spec.py`: initializes spec docs for new features.
- `agent_lessons_preflight.py`: selects relevant lessons by ranking.
- `agent_semantic_guard.py`: runs Codex subprocess review with schema-constrained JSON output.
- `agent_workflow_guard.py`: enforces evidence and policy gates.
- `agent_workflow_policy.json`: repo-level gate configuration.
- `semantic_review_schema.json`: output contract for semantic findings.
- `lessons/index.json`: searchable metadata index.

## Data and Control Flow

```
User request
  -> preflight selector
    -> lessons index + metadata
      -> ranked lesson shortlist
        -> execution + guard
          -> optional lesson creation/promotion
            -> index update
```

## Integration Points

- Existing workflow-police skill (`SKILL.md`, bootstrap scripts)
- Repo `AGENTS.md` and checklist documents
- Existing validation scripts (`validate_ps_syntax`, `validate_doc_links`)
- Codex CLI (`codex exec`) for sub-instance semantic review

## Migration and Rollout Strategy

### Phase 1 (this project)

- Create lessons hierarchy schema and governance rules.
- Keep memory source bound to one lessons repository.
- Integrate retrieval and guard behavior with workflow-police.

### Phase 2 (later)

- Add optional multi-repo lessons federation.
- Add MCP-backed retrieval when required by scale.

## Performance, Reliability, Security, UX

- Performance: metadata-first lookup avoids loading full lesson corpus.
- Reliability: deterministic ranking plus explicit fallback to latest lessons.
- Security: keep sensitive case details redacted or access-controlled.
- UX: selected lessons must be concise and visible at task start.

## Risks and Mitigations

- Risk: over-complex taxonomy reduces adoption.
  - Mitigation: keep level model to three levels only.
- Risk: stale lessons degrade quality.
  - Mitigation: require `last_validated_at` and periodic review.
- Risk: false-positive retrieval noise.
  - Mitigation: cap shortlist and prioritize higher-confidence entries.
- Risk: semantic reviewer instability causes inconsistent gating.
  - Mitigation: keep deterministic checks as block authority; semantic findings warn unless policy explicitly elevates severities.

## Future Enhancements

- Semantic clustering for duplicate lesson detection.
- Promotion recommendations based on repeated incidents.
- Dashboard for lesson aging, usage, and drift.

## External best-practice inputs

The generic workflow baseline integrates these source streams:

- Spec-first phase model and task traceability (from user-preferred AGENTS workflow template).
- Branch and review flow guidance from GitHub flow and trunk-based development.
- Review throughput guidance from Google engineering practices.
- Security lifecycle controls from NIST SSDF and OWASP SAMM.

See `references/generic-software-workflow.md` and `references/copilot-chat-spec-workflow-generic-extract.md`.
