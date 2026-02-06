#!/usr/bin/env python3
"""Initialize spec-first docs for a feature."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "feature"


def write_if_missing(path: Path, content: str, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return f"skip: {path}"
    path.write_text(content, encoding="utf-8")
    return f"write: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize design/requirements/tasks docs.")
    parser.add_argument("--feature-name", required=True, help="Feature display name")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--spec-root", default=".specs", help="Spec root folder")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repo root not found: {repo_root}")

    slug = slugify(args.feature_name)
    spec_dir = repo_root / args.spec_root / slug

    design = spec_dir / "design.md"
    requirements = spec_dir / "requirements.md"
    tasks = spec_dir / "tasks.md"

    design_text = f"""# Design Document: {args.feature_name}

## Overview

## Current Architecture

## Proposed Architecture

## Components

## Data and Control Flow

## Integration Points

## Migration and Rollout Strategy

## Performance, Reliability, Security, UX Considerations

## Risks and Mitigations

## Future Enhancements
"""

    requirements_text = """# Requirements Document

## Introduction

## Glossary

## Requirements

### Requirement 1
**User Story:** As a <role>, I want <capability>, so that <value>.

#### Acceptance Criteria
1. THE SYSTEM SHALL ...
2. WHEN <condition>, THE SYSTEM SHALL ...
3. WHEN <event> OCCURS, THEN ...
"""

    tasks_text = """# Implementation Plan

- [ ] 1. Define implementation slices. _Requirements: 1_
- [ ] 2. Implement first slice. _Requirements: 1_
- [ ] 3. Validate and document outcomes. _Requirements: 1_

## Current Status Summary

- Active phase: design
- Next task: define implementation slices
"""

    for p, c in [(design, design_text), (requirements, requirements_text), (tasks, tasks_text)]:
        print(write_if_missing(p, c, args.force))

    print(f"Initialized spec at: {spec_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
