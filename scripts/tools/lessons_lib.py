#!/usr/bin/env python3
"""Shared helpers for structured lessons storage and indexing."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

LEVELS = ("case", "pattern", "principle")
LEVEL_ORDER = {level: idx for idx, level in enumerate(LEVELS)}
STATUS_VALUES = ("candidate", "validated", "canonical", "retired")
FOLDER_TO_LEVEL = {"cases": "case", "patterns": "pattern", "principles": "principle"}
LEVEL_TO_FOLDER = {v: k for k, v in FOLDER_TO_LEVEL.items()}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "lesson"


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip() for p in inner.split(",")]
        out: list[str] = []
        for p in parts:
            if len(p) >= 2 and p[0] == p[-1] and p[0] in ("'", '"'):
                out.append(p[1:-1])
            elif p:
                out.append(p)
        return out
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text

    meta: dict[str, Any] = {}
    for line in lines[1:end_idx]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = parse_scalar(v)
    body = "\n".join(lines[end_idx + 1 :]).strip()
    return meta, body


def clamp_score(value: Any, fallback: int = 3) -> int:
    try:
        ivalue = int(value)
    except Exception:
        ivalue = fallback
    if ivalue < 1:
        return 1
    if ivalue > 5:
        return 5
    return ivalue


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [x.strip() for x in raw.split(",")]
        return sorted({x.lower() for x in parts if x})
    if isinstance(raw, list):
        return sorted({str(x).strip().lower() for x in raw if str(x).strip()})
    return []


def normalize_case_ids(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [x.strip() for x in raw.split(",")]
        return sorted({x for x in parts if x})
    if isinstance(raw, list):
        return sorted({str(x).strip() for x in raw if str(x).strip()})
    return []


def valid_date_or_today(raw: Any) -> str:
    if isinstance(raw, str):
        txt = raw.strip()
        if txt:
            try:
                date.fromisoformat(txt)
                return txt
            except ValueError:
                pass
    return date.today().isoformat()


def detect_level(path: Path) -> str:
    parent = path.parent.name.lower()
    return FOLDER_TO_LEVEL.get(parent, "case")


def extract_title_summary(body: str, fallback_id: str) -> tuple[str, str]:
    title = ""
    summary = ""
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            title = s[2:].strip()
            continue
        if not summary and not s.startswith("#"):
            summary = s
            break
    if not title:
        title = fallback_id.replace("-", " ").strip().title()
    return title, summary


def normalize_lesson_entry(path: Path, metadata: dict[str, Any], body: str, lessons_root: Path) -> dict[str, Any]:
    inferred_level = detect_level(path)
    lesson_id = str(metadata.get("id") or path.stem).strip()
    if not lesson_id:
        lesson_id = path.stem

    level = str(metadata.get("level") or inferred_level).strip().lower()
    if level not in LEVELS:
        level = inferred_level

    status = str(metadata.get("status") or "candidate").strip().lower()
    if status not in STATUS_VALUES:
        status = "candidate"

    tags = normalize_tags(metadata.get("tags"))
    source_case_ids = normalize_case_ids(metadata.get("source_case_ids"))
    confidence = clamp_score(metadata.get("confidence"), fallback=3)
    transferability = clamp_score(metadata.get("transferability"), fallback=3)
    last_validated_at = valid_date_or_today(metadata.get("last_validated_at"))

    title, extracted_summary = extract_title_summary(body, lesson_id)
    title = str(metadata.get("title") or title).strip()
    summary = str(metadata.get("summary") or extracted_summary).strip()

    rel_path = path.relative_to(lessons_root.parent).as_posix()
    return {
        "id": lesson_id,
        "level": level,
        "status": status,
        "tags": tags,
        "confidence": confidence,
        "transferability": transferability,
        "source_case_ids": source_case_ids,
        "last_validated_at": last_validated_at,
        "title": title,
        "summary": summary,
        "path": rel_path,
    }


def collect_lessons(lessons_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not lessons_root.exists():
        return entries

    for folder in ("cases", "patterns", "principles"):
        base = lessons_root / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            metadata, body = parse_frontmatter(path)
            entries.append(normalize_lesson_entry(path, metadata, body, lessons_root))

    entries.sort(key=lambda e: (LEVEL_ORDER.get(e["level"], 99), e["id"]))
    return entries


def build_index(entries: list[dict[str, Any]]) -> dict[str, Any]:
    stats = {
        "total": len(entries),
        "byLevel": {level: 0 for level in LEVELS},
        "byStatus": {status: 0 for status in STATUS_VALUES},
    }
    for e in entries:
        stats["byLevel"][e["level"]] = stats["byLevel"].get(e["level"], 0) + 1
        stats["byStatus"][e["status"]] = stats["byStatus"].get(e["status"], 0) + 1

    return {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "stats": stats,
        "lessons": entries,
    }


def write_index(index: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def metadata_to_frontmatter(metadata: dict[str, Any]) -> str:
    keys = [
        "id",
        "level",
        "status",
        "tags",
        "confidence",
        "transferability",
        "source_case_ids",
        "last_validated_at",
        "title",
        "summary",
    ]
    lines = ["---"]
    for k in keys:
        if k not in metadata:
            continue
        v = metadata[k]
        if isinstance(v, list):
            inner = ", ".join(str(x) for x in v)
            lines.append(f"{k}: [{inner}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)

