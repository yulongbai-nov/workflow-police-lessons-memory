# Rollout Plan and Phase-2 MCP Expansion

## Phase 1 (current)

Scope:
- One canonical lessons repository.
- Python-first scripts for bootstrap, index update, promotion, preflight, and guard.
- Hybrid guard with deterministic block authority and semantic advisory findings.

Adoption sequence:
1. Bootstrap lessons hierarchy in target repo.
2. Initialize feature specs.
3. Run preflight at task start.
4. Run guard in `warn` before final response and `block` before commit/push.
5. Convert recurring incidents into case lessons and promote when thresholds are met.

## Phase 2 (optional)

Goal:
- Federate lessons across repos with queryable retrieval while preserving phase-1 local reliability.

Recommended approach:
1. Keep local deterministic fallback (`lessons/index.json`) as mandatory.
2. Add MCP-backed retrieval as additive context source.
3. Merge remote lessons with local lessons using confidence and recency scoring.
4. Preserve provenance and de-duplicate via lesson IDs.

Operational guardrails:
- If MCP is unavailable, preflight must still complete from local index.
- Never make external memory service availability a hard blocker for deterministic guard checks.
