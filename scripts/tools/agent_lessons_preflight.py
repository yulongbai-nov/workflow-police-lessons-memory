#!/usr/bin/env python3
"""Select task-relevant lessons from structured metadata and write preflight artifact."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from lessons_lib import LEVEL_ORDER, collect_lessons


def tokenize(text: str) -> list[str]:
    return sorted({t for t in re.split(r"[\s\.,;:!\?\-_/\\]+", text.lower()) if len(t) >= 3})


def read_headings(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line[3:].strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.startswith("## ")]


def parse_iso_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw.strip())
    except Exception:
        return None


def recency_score(last_validated_at: str) -> int:
    d = parse_iso_date(last_validated_at or "")
    if not d:
        return 0
    age_days = (date.today() - d).days
    if age_days <= 30:
        return 3
    if age_days <= 90:
        return 2
    if age_days <= 180:
        return 1
    return 0


def score_entry(entry: dict, tokens: list[str]) -> tuple[int, dict]:
    level = entry.get("level", "case")
    level_weight = {"principle": 30, "pattern": 20, "case": 10}.get(level, 0)
    status = entry.get("status", "candidate")
    status_bonus = {"canonical": 4, "validated": 2, "candidate": 0, "retired": -999}.get(status, 0)
    confidence = int(entry.get("confidence", 3))
    transferability = int(entry.get("transferability", 3))

    tags = [str(t).lower() for t in entry.get("tags", [])]
    hay = " ".join(
        [
            str(entry.get("id", "")),
            str(entry.get("title", "")),
            str(entry.get("summary", "")),
            " ".join(tags),
        ]
    ).lower()
    token_hits = sum(1 for t in tokens if t in hay)
    tag_hits = sum(1 for t in tokens if t in tags)
    rscore = recency_score(str(entry.get("last_validated_at", "")))

    score = level_weight + (token_hits * 3) + (tag_hits * 2) + confidence + transferability + status_bonus + rscore
    detail = {
        "tokenHits": token_hits,
        "tagHits": tag_hits,
        "recencyScore": rscore,
        "levelWeight": level_weight,
        "statusBonus": status_bonus,
    }
    return score, detail


def to_selection(entry: dict, score: int, detail: dict, reason: str) -> dict:
    out = {
        "id": entry.get("id"),
        "level": entry.get("level"),
        "status": entry.get("status"),
        "title": entry.get("title"),
        "path": entry.get("path"),
        "score": score,
        "reason": reason,
    }
    out.update(detail)
    return out


def load_entries(repo_root: Path, lessons_root: Path, index_path: Path) -> tuple[list[dict], str]:
    if index_path.exists():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            entries = raw.get("lessons", [])
            if isinstance(entries, list):
                return entries, "index"
        except Exception:
            pass
    return collect_lessons(lessons_root), "scan"


def main() -> int:
    parser = argparse.ArgumentParser(description="Lessons preflight selection from metadata index.")
    parser.add_argument("--task", required=True, help="User request/task text")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--lessons-root", default="lessons", help="Structured lessons root")
    parser.add_argument("--index-path", default="", help="Lessons index path (defaults to <lessons-root>/index.json)")
    parser.add_argument("--fallback-headings-path", default="LESSONS.md", help="Legacy markdown headings fallback")
    parser.add_argument("--top", type=int, default=5, help="Top N headings")
    parser.add_argument("--principles-max", type=int, default=2, help="Max selected principles")
    parser.add_argument("--patterns-max", type=int, default=2, help="Max selected patterns")
    parser.add_argument("--cases-max", type=int, default=2, help="Max selected cases")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    lessons_root = repo_root / args.lessons_root
    index_path = Path(args.index_path) if args.index_path else lessons_root / "index.json"
    if not index_path.is_absolute():
        index_path = repo_root / index_path

    tokens = tokenize(args.task)
    entries, source = load_entries(repo_root, lessons_root, index_path)

    candidates = []
    for entry in entries:
        score, detail = score_entry(entry, tokens)
        if score <= 0:
            continue
        if entry.get("status") == "retired":
            continue
        candidates.append((score, entry, detail))
    candidates.sort(key=lambda x: (x[0], -LEVEL_ORDER.get(x[1].get("level", "case"), 99), x[1].get("id", "")), reverse=True)

    quotas = {"principle": args.principles_max, "pattern": args.patterns_max, "case": args.cases_max}
    used = {"principle": 0, "pattern": 0, "case": 0}
    selected: list[dict] = []
    seen_ids: set[str] = set()

    for score, entry, detail in candidates:
        if len(selected) >= args.top:
            break
        level = entry.get("level", "case")
        if level in quotas and used[level] >= quotas[level]:
            continue
        lesson_id = str(entry.get("id", "")).strip()
        if not lesson_id or lesson_id in seen_ids:
            continue
        selected.append(to_selection(entry, score, detail, reason="ranked"))
        used[level] = used.get(level, 0) + 1
        seen_ids.add(lesson_id)

    fallback_used = False
    if len(selected) < args.top:
        fallback_used = True
        validated = []
        for entry in entries:
            if entry.get("status") not in ("validated", "canonical"):
                continue
            if entry.get("status") == "retired":
                continue
            d = parse_iso_date(str(entry.get("last_validated_at", "")))
            validated.append((d or date.min, entry))
        validated.sort(key=lambda x: (x[0], -LEVEL_ORDER.get(x[1].get("level", "case"), 99), x[1].get("id", "")), reverse=True)
        for _, entry in validated:
            if len(selected) >= args.top:
                break
            lesson_id = str(entry.get("id", "")).strip()
            if not lesson_id or lesson_id in seen_ids:
                continue
            selected.append(
                to_selection(
                    entry,
                    score=0,
                    detail={"tokenHits": 0, "tagHits": 0, "recencyScore": recency_score(str(entry.get("last_validated_at", ""))), "levelWeight": 0, "statusBonus": 0},
                    reason="fallback_latest_validated",
                )
            )
            seen_ids.add(lesson_id)

    if len(selected) == 0:
        fallback_used = True
        headings = read_headings(repo_root / args.fallback_headings_path)
        for heading in headings[: args.top]:
            selected.append(
                {
                    "id": "legacy-" + re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-"),
                    "level": "legacy",
                    "status": "n/a",
                    "title": heading,
                    "path": str((repo_root / args.fallback_headings_path).relative_to(repo_root).as_posix()),
                    "score": 0,
                    "reason": "fallback_legacy_headings",
                    "tokenHits": 0,
                    "tagHits": 0,
                    "recencyScore": 0,
                    "levelWeight": 0,
                    "statusBonus": 0,
                }
            )

    out_dir = Path("logs/agent/preflight")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"preflight_{stamp}.json"
    result = {
        "task": args.task,
        "tokens": tokens,
        "source": source,
        "indexPath": str(index_path),
        "matchCount": len(selected),
        "matches": selected,
        "fallbackUsed": fallback_used,
        "selection": {
            "top": args.top,
            "principlesMax": args.principles_max,
            "patternsMax": args.patterns_max,
            "casesMax": args.cases_max,
        },
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Preflight artifact: {out_path.resolve()}")
    if selected:
        print("Selected lessons:")
        for m in selected:
            print(f"- {m['level']}: {m['id']} ({m['reason']})")
    else:
        print("No matching lessons.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
