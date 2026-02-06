#!/usr/bin/env python3
"""Rebuild lessons/index.json from structured lessons markdown files."""

from __future__ import annotations

import argparse
from pathlib import Path

from lessons_lib import build_index, collect_lessons, write_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Update lessons metadata index.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--lessons-root", default="lessons", help="Lessons root folder")
    parser.add_argument("--output-path", default="", help="Index output path (defaults to <lessons-root>/index.json)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    lessons_root = repo_root / args.lessons_root
    output_path = Path(args.output_path) if args.output_path else lessons_root / "index.json"
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    entries = collect_lessons(lessons_root)
    index = build_index(entries)
    write_index(index, output_path)

    print(f"Index updated: {output_path.resolve()}")
    print(f"Lessons indexed: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
