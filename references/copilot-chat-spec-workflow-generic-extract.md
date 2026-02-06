# Generic Extract From `vscode-copilot-chat` AGENTS Spec

Source analyzed:
- https://github.com/yulongbai-nov/vscode-copilot-chat/blob/main/AGENTS.md

This file captures transferable, language-agnostic workflow patterns.

## Transferable patterns

## 1) Three-document spec core

- `design.md`: architecture and key decisions
- `requirements.md`: user stories and acceptance criteria
- `tasks.md`: implementation checklist and status

Transfer value:
- separates intent, behavior, and execution
- keeps change review traceable

## 2) Explicit phase model

- design phase: refine and agree scope/spec
- implementation phase: execute next unchecked task

Transfer value:
- prevents coding ahead of agreement
- gives a clear protocol for scope ambiguity

## 3) Scope drift protocol

- stop when unrelated scope appears
- isolate with new branch/worktree
- finish current scope before resuming new one

Transfer value:
- reduces mixed-diff complexity and review confusion

## 4) Checkpoint coach/guard

- run a policy reminder/coach at commit-push-PR checkpoints
- automate via hooks where practical

Transfer value:
- improves adherence without requiring manual memory

## 5) Verification stack before commit/push

- lint/static checks
- type/build checks
- targeted tests
- broader regression/simulation where available

Transfer value:
- provides layered confidence before integration

## 6) Spec-to-task traceability

- each task references requirements
- implementation and handoff map completed tasks back to requirements

Transfer value:
- makes "done" auditable and reviewable

## 7) Debug status handoff block

- branch state
- active phase
- spec location
- pending next tasks

Transfer value:
- reduces state loss across asynchronous collaboration

## Adaptation notes for generic use

- Keep required structure, but avoid language-specific commands in policy core.
- Store repo-specific build/test commands in a policy file, not in the universal workflow text.
- Keep deterministic checks blocking and semantic checks advisory by default.
