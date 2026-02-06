#!/usr/bin/env python3
"""Bootstrap structured lessons hierarchy and starter templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from lessons_lib import build_index, collect_lessons, write_index


def write_if_missing(path: Path, content: str, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return f"skip: {path}"
    action = "update" if path.exists() else "create"
    path.write_text(content, encoding="utf-8")
    return f"{action}: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap lessons hierarchy, templates, and index.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--lessons-root", default="lessons", help="Lessons root folder")
    parser.add_argument("--force", action="store_true", help="Overwrite existing templates")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    lessons_root = repo_root / args.lessons_root
    today = date.today().isoformat()

    templates: dict[Path, str] = {
        lessons_root / "README.md": """# Lessons Hierarchy

This folder stores structured lessons by abstraction level:

- `cases/` for incident-specific lessons
- `patterns/` for reusable operational patterns
- `principles/` for stable cross-domain guidance

Use `scripts/tools/update_lessons_index.py` to regenerate `lessons/index.json`.
""",
        lessons_root / "cases" / "case-template.md": f"""---
id: case-template
level: case
status: candidate
tags: [example]
confidence: 3
transferability: 2
source_case_ids: []
last_validated_at: {today}
title: Example Case Lesson
summary: Replace this with incident summary.
---

# Example Case Lesson

## Symptom

Describe what failed and where.

## Root Cause

Describe the actual failure mechanism.

## Fix

Describe what changed to resolve it.

## Prevention

Describe checks or workflow changes that avoid recurrence.
""",
        lessons_root / "patterns" / "pattern-template.md": f"""---
id: pattern-template
level: pattern
status: candidate
tags: [example]
confidence: 3
transferability: 4
source_case_ids: [case-template]
last_validated_at: {today}
title: Example Pattern Lesson
summary: Replace this with reusable pattern summary.
---

# Example Pattern Lesson

## When To Apply

Describe the triggering context.

## Guidance

Describe reusable guidance distilled from multiple cases.

## Evidence

List source case IDs and why they support this pattern.
""",
        lessons_root / "principles" / "principle-template.md": f"""---
id: principle-template
level: principle
status: candidate
tags: [example]
confidence: 4
transferability: 5
source_case_ids: [case-template]
last_validated_at: {today}
title: Example Principle
summary: Replace this with stable cross-domain guidance.
---

# Example Principle

## Principle

Describe the durable rule.

## Rationale

Explain why this should hold across contexts.

## Boundaries

Describe when this principle does not apply.
""",
    }

    results = []
    for path, content in templates.items():
        results.append(write_if_missing(path, content, args.force))

    entries = collect_lessons(lessons_root)
    index = build_index(entries)
    index_path = lessons_root / "index.json"
    write_index(index, index_path)
    results.append(f"write: {index_path}")

    print("Lessons bootstrap complete.")
    for line in results:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
