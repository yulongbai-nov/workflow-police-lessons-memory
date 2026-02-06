# Sample Workflow Police Runbook (Python-First)

This runbook demonstrates the end-to-end flow in a platform-agnostic way.

## 1) Bootstrap structured lessons

```bash
python scripts/tools/bootstrap_lessons_repo.py --repo-root .
```

## 2) Initialize spec docs for a feature

```bash
python scripts/tools/init_feature_spec.py --feature-name "ssh-hardening" --repo-root .
```

## 3) Refresh lessons index

```bash
python scripts/tools/update_lessons_index.py --repo-root .
```

## 4) Promote lessons as evidence grows

Example case -> pattern:

```bash
python scripts/tools/promote_lesson.py \
  --repo-root . \
  --source-id case-template \
  --target-level pattern \
  --source-case-id case-template-2 \
  --title "SSH key and host alias stability"
```

Example pattern -> principle:

```bash
python scripts/tools/promote_lesson.py \
  --repo-root . \
  --source-id pattern-ssh-key-and-host-alias-stability \
  --target-level principle \
  --source-case-id case-template-3 \
  --title "Prefer deterministic identity and endpoint mapping"
```

## 5) Run task-start preflight

```bash
python scripts/tools/agent_lessons_preflight.py \
  --repo-root . \
  --task "fix ssh alias and key ACL mismatch"
```

## 6) Run workflow guard

Before final response:

```bash
python scripts/tools/agent_workflow_guard.py \
  --repo-root . \
  --task "fix ssh alias and key ACL mismatch" \
  --mode warn
```

Before commit/push:

```bash
python scripts/tools/agent_workflow_guard.py \
  --repo-root . \
  --task "fix ssh alias and key ACL mismatch" \
  --mode block
```

To avoid semantic subprocess during local dry-runs:

```bash
python scripts/tools/agent_workflow_guard.py \
  --repo-root . \
  --task "fix ssh alias and key ACL mismatch" \
  --mode warn \
  --skip-semantic
```
