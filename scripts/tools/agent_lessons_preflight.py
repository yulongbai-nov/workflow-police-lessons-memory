#!/usr/bin/env python3
"""Select task-relevant lessons and write preflight artifact."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def tokenize(text: str) -> list[str]:
    return sorted({t for t in re.split(r"[\s\.,;:!\?\-_/\\]+", text.lower()) if len(t) >= 4})


def read_headings(path: Path) -> list[str]:
    if not path.exists():
        return []
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def main() -> int:
    parser = argparse.ArgumentParser(description="Lessons preflight selection.")
    parser.add_argument("--task", required=True, help="User request/task text")
    parser.add_argument("--lessons-path", default="LESSONS.md", help="Lessons markdown file")
    parser.add_argument("--top", type=int, default=5, help="Top N headings")
    args = parser.parse_args()

    tokens = tokenize(args.task)
    lessons_path = Path(args.lessons_path)
    scored = []
    for h in read_headings(lessons_path):
        score = sum(1 for t in tokens if t in h.lower())
        if score > 0:
            scored.append({"heading": h, "score": score})

    scored.sort(key=lambda x: (x["score"], x["heading"]), reverse=True)
    matches = scored[: args.top]

    out_dir = Path("logs/agent/preflight")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"preflight_{stamp}.json"
    result = {
        "task": args.task,
        "lessonsPath": str(lessons_path),
        "matchCount": len(matches),
        "matches": matches,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Preflight artifact: {out_path.resolve()}")
    if matches:
        print("Matched lesson headings:")
        for m in matches:
            print(f"- {m['heading']}")
    else:
        print("No matching lesson headings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
