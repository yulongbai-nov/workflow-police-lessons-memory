# Requirements Document

## Introduction

This feature standardizes how engineering lessons are captured and reused across tasks by integrating structured lessons memory with workflow policing.

Goals:

- reduce repeated incidents
- improve transfer of operational knowledge
- keep retrieval practical and low-noise

Non-goals (phase 1):

- full enterprise knowledge graph
- mandatory multi-repo federation
- custom vector search infrastructure

## Glossary

- Lesson Case: incident-specific lesson tied to one concrete event.
- Lesson Pattern: reusable lesson distilled from multiple cases.
- Lesson Principle: stable cross-domain guidance with high transferability.
- Preflight: task-start lesson retrieval step.
- Guard: policy check before final response and before commit/push.

## Requirements

### Requirement 1: Structured Lessons Model

**User Story:** As an engineer, I want lessons organized by abstraction level, so that I can quickly use the right depth of guidance.

#### Acceptance Criteria

1. THE SYSTEM SHALL support lesson levels `case`, `pattern`, and `principle`.
2. THE SYSTEM SHALL store each lesson with metadata fields: `id`, `level`, `status`, `tags`, `confidence`, `transferability`, and `last_validated_at`.
3. WHEN a lesson is linked to prior incidents, THE SYSTEM SHALL store `source_case_ids`.
4. THE SYSTEM SHALL keep an index that can be queried without loading all lesson bodies.

### Requirement 2: Task-Start Retrieval

**User Story:** As an engineer, I want the most relevant lessons surfaced at task start, so that I can avoid known mistakes.

#### Acceptance Criteria

1. WHEN a task begins, THE SYSTEM SHALL run a preflight lesson selection step.
2. THE SYSTEM SHALL rank results by level priority, metadata relevance, and recency.
3. THE SYSTEM SHALL prioritize principles and patterns before case-level items.
4. THE SYSTEM SHALL output a compact shortlist suitable for first status updates.

### Requirement 3: Workflow Guard Integration

**User Story:** As a maintainer, I want workflow gates tied to lesson retrieval, so that policy compliance is consistent.

#### Acceptance Criteria

1. BEFORE final response, THE SYSTEM SHALL support guard execution in `warn` mode.
2. BEFORE commit or push, THE SYSTEM SHALL support guard execution in `block` mode.
3. WHEN required preflight artifacts are missing, THE SYSTEM SHALL surface explicit guard findings.
4. THE SYSTEM SHALL write guard artifacts to a stable path for auditability.

### Requirement 4: Promotion Lifecycle

**User Story:** As a knowledge steward, I want clear promotion criteria, so that reusable guidance becomes canonical over time.

#### Acceptance Criteria

1. THE SYSTEM SHALL define explicit thresholds for `case -> pattern` promotion.
2. THE SYSTEM SHALL define explicit thresholds for `pattern -> principle` promotion.
3. WHEN a lesson is superseded or invalid, THE SYSTEM SHALL allow retirement with status tracking.
4. THE SYSTEM SHALL preserve provenance links across promotions.

### Requirement 5: Bootstrap for Missing Tooling

**User Story:** As a repo owner, I want missing workflow scripts scaffolded automatically, so that adoption cost is low.

#### Acceptance Criteria

1. WHEN required workflow scripts are absent, THE SYSTEM SHALL generate baseline script templates.
2. THE SYSTEM SHALL scaffold at least preflight, guard, PowerShell syntax validation, and doc-link validation scripts.
3. THE SYSTEM SHALL avoid overwriting existing files unless explicitly requested.
4. THE SYSTEM SHALL report created, updated, and skipped files.

### Requirement 6: Phase-1 Repository Boundary

**User Story:** As a rollout owner, I want an incremental adoption strategy, so that we can validate value before scaling.

#### Acceptance Criteria

1. DURING phase 1, THE SYSTEM SHALL use a single canonical lessons repository as source of truth.
2. THE SYSTEM SHALL document multi-repo and MCP retrieval as phase-2 options, not phase-1 dependencies.
3. THE SYSTEM SHALL remain functional without any external memory service.

### Requirement 7: Codex Sub-Instance Semantic Review

**User Story:** As a workflow owner, I want context-sensitive review findings from a Codex subprocess, so that non-deterministic risks are surfaced without destabilizing hard gates.

#### Acceptance Criteria

1. WHEN semantic review is enabled in policy, THE SYSTEM SHALL invoke `codex exec` as a subprocess reviewer.
2. THE SYSTEM SHALL constrain semantic output with a JSON schema before consuming findings.
3. THE SYSTEM SHALL treat semantic findings as advisory by default and SHALL NOT block unless configured severities match `blockOnSeverity`.
4. WHEN semantic execution fails, THE SYSTEM SHALL record explicit guard findings and continue deterministic evaluation.

### Requirement 8: Platform-Agnostic Automation

**User Story:** As a maintainer working across operating systems, I want workflow tools to run consistently, so that policy enforcement is not tied to one shell environment.

#### Acceptance Criteria

1. THE SYSTEM SHALL provide Python-first CLI scripts for preflight, semantic review, workflow guard, and spec initialization.
2. THE SYSTEM SHALL avoid mandatory dependence on PowerShell for core workflow behavior.
3. WHEN compatibility wrappers exist, THE SYSTEM SHALL treat Python scripts as canonical implementation paths.
