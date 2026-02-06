# Generic Software Workflow Baseline

This baseline combines external best practices with a spec-first execution model.

## 1) Discover and Scope

- Define problem, stakeholders, success criteria, and non-goals before implementation.
- Record constraints early: performance, reliability, security, compatibility, platform limits.

Why:
- Early scope clarity reduces rework and uncontrolled scope growth.

## 2) Design Before Build

- Create explicit design and requirements artifacts.
- Use testable acceptance criteria and clear terminology.
- Keep rollout and rollback strategy in design, not as afterthoughts.

Why:
- Design-first reduces ambiguity and enables traceable implementation.

## 3) Plan as Small, Verifiable Tasks

- Keep tasks small enough for one focused session.
- Link tasks to requirements so review can verify intent coverage.
- Track status explicitly, including deviations and technical debt.

Why:
- Small batches improve review quality and throughput.

## 4) Branch and Change Isolation

- Use short-lived branches with clear naming.
- Isolate unrelated scope into separate branches/worktrees.
- Keep PRs focused on one change objective.

Why:
- Smaller diffs and isolated scope reduce merge risk and speed review.

## 5) Continuous Verification

- Run deterministic quality gates before commit/push:
  - static checks
  - targeted tests
  - build/compile validation
- Keep known failure lists explicit so regressions are distinguishable from pre-existing debt.

Why:
- Continuous checks lower integration risk and shorten feedback loops.

## 6) Security and Compliance by Default

- Integrate secure development controls as standard workflow steps.
- Treat security artifacts and policy checks as first-class gates, not optional review notes.

Why:
- Security left to the end creates avoidable release risk.

## 7) Semantic Review as Advisory Layer

- Add LLM/sub-instance semantic review for context-sensitive findings:
  - scope drift
  - spec mismatch
  - risky operational behavior
- Keep deterministic checks as block authority.

Why:
- Hybrid guard (deterministic + semantic) improves coverage without making release gates brittle.

## 8) Post-Change Learning Loop

- Convert incidents into lessons.
- Promote repeated lessons into reusable patterns and principles.
- Revalidate and retire stale lessons.

Why:
- Teams improve when operational learning is structured and retrievable.

## Source mapping

- GitHub flow and branch/PR practices:
  - https://docs.github.com/en/get-started/using-github/github-flow
- Trunk-based change isolation and short-lived branch guidance:
  - https://trunkbaseddevelopment.com/
- Review quality and small changes:
  - https://google.github.io/eng-practices/review/reviewer/
  - https://google.github.io/eng-practices/review/developer/
- Security development framework controls:
  - https://csrc.nist.gov/projects/secure-software-development-framework
  - https://owasp.org/www-project-samm/

