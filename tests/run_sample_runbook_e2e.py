#!/usr/bin/env python3
"""End-to-end smoke test for sample workflow-police runbook."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc


def write_case(path: Path, lesson_id: str, title: str, tags: list[str]) -> None:
    content = f"""---
id: {lesson_id}
level: case
status: validated
tags: [{", ".join(tags)}]
confidence: 4
transferability: 3
source_case_ids: []
last_validated_at: 2026-02-06
title: {title}
summary: {title} summary.
---

# {title}

## Symptom

Example symptom.

## Root Cause

Example root cause.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def latest_json(path: Path, glob_pattern: str) -> Path:
    files = sorted(path.glob(glob_pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise RuntimeError(f"No files found for pattern: {glob_pattern}")
    return files[0]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="workflow-police-e2e-") as tmp:
        root = Path(tmp)
        (root / "AGENTS.md").write_text("# Agent Notes\n", encoding="utf-8")
        (root / "scripts" / "config" / "agent").mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "scripts/config/agent/agent_workflow_policy.json", root / "scripts/config/agent/agent_workflow_policy.json")
        shutil.copy2(REPO_ROOT / "scripts/config/agent/semantic_review_schema.json", root / "scripts/config/agent/semantic_review_schema.json")

        run([PY, str(REPO_ROOT / "scripts/tools/bootstrap_lessons_repo.py"), "--repo-root", str(root)], cwd=root)
        run([PY, str(REPO_ROOT / "scripts/tools/init_feature_spec.py"), "--feature-name", "ssh-hardening", "--repo-root", str(root)], cwd=root)

        write_case(root / "lessons/cases/case-ssh-key-acl.md", "case-ssh-key-acl", "SSH key ACL mismatch", ["ssh", "acl"])
        write_case(root / "lessons/cases/case-ssh-host-alias.md", "case-ssh-host-alias", "SSH host alias mismatch", ["ssh", "alias"])
        write_case(root / "lessons/cases/case-known-host-drift.md", "case-known-host-drift", "Known_hosts endpoint drift", ["ssh", "known_hosts"])

        run([PY, str(REPO_ROOT / "scripts/tools/update_lessons_index.py"), "--repo-root", str(root)], cwd=root)

        run(
            [
                PY,
                str(REPO_ROOT / "scripts/tools/promote_lesson.py"),
                "--repo-root",
                str(root),
                "--source-id",
                "case-ssh-key-acl",
                "--target-level",
                "pattern",
                "--source-case-id",
                "case-ssh-host-alias",
                "--title",
                "SSH identity and alias stability",
            ],
            cwd=root,
        )

        run(
            [
                PY,
                str(REPO_ROOT / "scripts/tools/promote_lesson.py"),
                "--repo-root",
                str(root),
                "--source-id",
                "pattern-ssh-identity-and-alias-stability",
                "--target-level",
                "principle",
                "--source-case-id",
                "case-known-host-drift",
                "--title",
                "Prefer deterministic endpoint and identity mapping",
            ],
            cwd=root,
        )

        run(
            [
                PY,
                str(REPO_ROOT / "scripts/tools/agent_lessons_preflight.py"),
                "--repo-root",
                str(root),
                "--task",
                "fix ssh alias and key acl mismatch from endpoint drift",
            ],
            cwd=root,
        )

        preflight_artifact = latest_json(root / "logs/agent/preflight", "*.json")
        preflight = json.loads(preflight_artifact.read_text(encoding="utf-8"))
        if preflight.get("matchCount", 0) <= 0:
            raise RuntimeError("Preflight returned no matches.")
        levels = {m.get("level") for m in preflight.get("matches", [])}
        if "principle" not in levels and "pattern" not in levels:
            raise RuntimeError(f"Expected principle or pattern in preflight matches, got: {levels}")

        run(
            [
                PY,
                str(REPO_ROOT / "scripts/tools/agent_workflow_guard.py"),
                "--repo-root",
                str(root),
                "--task",
                "fix ssh alias and key acl mismatch from endpoint drift",
                "--mode",
                "warn",
                "--skip-semantic",
            ],
            cwd=root,
        )
        guard_artifact = latest_json(root / "logs/agent/guard", "guard_*.json")
        guard = json.loads(guard_artifact.read_text(encoding="utf-8"))
        if guard.get("status") not in ("PASS", "WARN"):
            raise RuntimeError(f"Unexpected guard status: {guard.get('status')}")

        print("E2E_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
