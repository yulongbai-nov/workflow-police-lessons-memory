# Implementation Plan

- [x] 1. Create initial spec set for lessons memory foundation (`design.md`, `requirements.md`, `tasks.md`). _Requirements: 1, 2, 6_
- [x] 2. Extract generic workflow elements from `vscode-copilot-chat` AGENTS spec and document transferable patterns. _Requirements: 2, 6_
- [x] 3. Research external best practices and map them to a generic workflow baseline. _Requirements: 2, 3, 6_
- [x] 4. Implement policy scaffolding for workflow police integration.
  - [x] 4.1 Add default policy config with deterministic and semantic lanes.
  - [x] 4.2 Add semantic review JSON schema for sub-instance output validation.
  - [x] 4.3 Add a generic feature spec initializer script (Python-first).
  - [x] 4.4 Add semantic guard script using `codex exec` (Python-first).
  - [x] 4.5 Add aggregate workflow guard script with warn/block modes (Python-first).
  - [x] 4.6 Add safe deletion wrapper script for non-ad-hoc removals.
  _Requirements: 3, 5, 6, 7, 8_
- [ ] 5. Add lessons hierarchy bootstrap and index tooling.
  - [ ] 5.1 Define lesson file templates for `case`, `pattern`, and `principle`.
  - [ ] 5.2 Add index updater script for metadata normalization.
  - [ ] 5.3 Add promotion helper script (`case -> pattern -> principle`).
  _Requirements: 1, 2, 4_
- [ ] 6. Add preflight retriever with ranked selection from metadata index.
  - [ ] 6.1 Implement token extraction and ranking.
  - [ ] 6.2 Add deterministic fallback to latest validated lessons.
  - [ ] 6.3 Emit stable preflight artifact and summary output.
  _Requirements: 2, 3, 6_
- [ ] 7. Integration and validation.
  - [ ] 7.1 Wire guard scripts into a sample repo runbook.
  - [ ] 7.2 Add smoke tests for script syntax and minimal execution paths.
  - [ ] 7.3 Document rollout and phase-2 MCP expansion path.
  _Requirements: 3, 5, 6_

## Implementation Notes

- Phase 1 keeps a single canonical lessons repository as source.
- Semantic review is advisory by default; deterministic checks own block authority.
- Use JSON schema constrained outputs for sub-instance reliability.

## Dependencies

- `codex` CLI available and authenticated for semantic guard subprocess mode.
- Git repository context available for `codex exec` unless `--skip-git-repo-check` is explicitly used.

## Testing Priority

1. Guard scripts syntax + happy path.
2. Semantic guard output schema validation.
3. Deterministic + semantic aggregation behavior in both `warn` and `block` modes.

## Backward Compatibility

- Scripts are additive and standalone.
- Existing repos can adopt incrementally through explicit invocation.

## Current Status Summary

- Active phase: design with implementation spike for guard scripts.
- Completed next steps: draft architecture, external-best-practice mapping, and semantic sub-instance guard prototype.
- Next concrete tasks:
  1. Implement lessons hierarchy templates and index updater.
  2. Implement ranked preflight retrieval.
  3. Add end-to-end sample runbook.
