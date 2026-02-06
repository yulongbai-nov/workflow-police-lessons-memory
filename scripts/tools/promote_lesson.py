#!/usr/bin/env python3
"""Promote lessons across abstraction levels with provenance checks."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from lessons_lib import (
    LEVEL_TO_FOLDER,
    build_index,
    collect_lessons,
    metadata_to_frontmatter,
    slugify,
    write_index,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote lessons (case->pattern, pattern->principle).")
    parser.add_argument("--source-id", required=True, help="Source lesson ID")
    parser.add_argument("--target-level", required=True, choices=["pattern", "principle"])
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--lessons-root", default="lessons", help="Lessons root folder")
    parser.add_argument("--new-id", default="", help="Target lesson ID")
    parser.add_argument("--title", default="", help="Target lesson title")
    parser.add_argument("--source-case-id", dest="source_case_ids", action="append", default=[], help="Additional source case ID (repeatable)")
    parser.add_argument("--force", action="store_true", help="Overwrite target if exists")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    lessons_root = repo_root / args.lessons_root
    entries = collect_lessons(lessons_root)
    by_id = {e["id"]: e for e in entries}
    source = by_id.get(args.source_id)
    if not source:
        raise SystemExit(f"Source lesson not found: {args.source_id}")

    if source["level"] == "case" and args.target_level != "pattern":
        raise SystemExit("Invalid transition: case can only be promoted to pattern.")
    if source["level"] == "pattern" and args.target_level != "principle":
        raise SystemExit("Invalid transition: pattern can only be promoted to principle.")
    if source["level"] == "principle":
        raise SystemExit("Principles cannot be promoted further.")

    provenance = set(args.source_case_ids)
    provenance.update(source.get("source_case_ids", []))
    if source["level"] == "case":
        provenance.add(source["id"])

    if args.target_level == "pattern" and len(provenance) < 2:
        raise SystemExit("Promotion blocked: case->pattern requires at least 2 source case IDs.")
    if args.target_level == "principle" and len(provenance) < 3:
        raise SystemExit("Promotion blocked: pattern->principle requires at least 3 source case IDs.")

    source_tags = set(source.get("tags", []))
    source_tags.add("promoted")
    title = args.title.strip() or f"{args.target_level.title()} from {source['id']}"
    new_id = args.new_id.strip() or f"{args.target_level}-{slugify(title)}"

    target_folder = lessons_root / LEVEL_TO_FOLDER[args.target_level]
    target_path = target_folder / f"{new_id}.md"
    if target_path.exists() and not args.force:
        raise SystemExit(f"Target lesson already exists: {target_path}")

    today = date.today().isoformat()
    metadata = {
        "id": new_id,
        "level": args.target_level,
        "status": "validated" if args.target_level == "pattern" else "canonical",
        "tags": sorted(source_tags),
        "confidence": max(int(source.get("confidence", 3)), 3),
        "transferability": max(int(source.get("transferability", 3)), 3),
        "source_case_ids": sorted(x for x in provenance if x),
        "last_validated_at": today,
        "title": title,
        "summary": f"Promoted from {source['id']} with structured provenance.",
    }

    content = f"""# {title}

## Context

Promoted from `{source['id']}`.

## Guidance

Replace this section with reusable guidance.

## Evidence

Source case IDs: {", ".join(metadata['source_case_ids'])}
"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(metadata_to_frontmatter(metadata) + "\n\n" + content, encoding="utf-8")
    print(f"Created: {target_path.resolve()}")

    updated_entries = collect_lessons(lessons_root)
    index = build_index(updated_entries)
    index_path = lessons_root / "index.json"
    write_index(index, index_path)
    print(f"Index updated: {index_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
