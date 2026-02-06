#!/usr/bin/env python3
"""Run semantic workflow review through a Codex subprocess."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_changed_paths(repo_root: Path) -> list[str]:
    git = shutil.which("git")
    if not git:
        return []
    for cmd in (
        [git, "-C", str(repo_root), "diff", "--name-only", "--cached"],
        [git, "-C", str(repo_root), "diff", "--name-only"],
    ):
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if p.returncode == 0 and p.stdout.strip():
            return [x.strip() for x in p.stdout.splitlines() if x.strip()]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantic workflow guard (Codex subprocess).")
    parser.add_argument("--task", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy-path", default="scripts/config/agent/agent_workflow_policy.json")
    parser.add_argument("--changed-paths", nargs="*", default=None)
    parser.add_argument("--output-path", default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    policy_path = repo_root / args.policy_path
    policy = load_json(policy_path)
    semantic = policy.get("semanticReview", {})

    out_dir = repo_root / "logs" / "agent" / "guard"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.output_path:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = out_dir / f"semantic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    if not semantic.get("enabled", False):
        result = {
            "status": "SKIPPED",
            "engine": "disabled",
            "summary": "Semantic review disabled by policy.",
            "findings": [],
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Semantic artifact: {output_path.resolve()}")
        return 0

    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex CLI not found on PATH.")

    changed_paths = list(args.changed_paths or [])
    if not changed_paths:
        changed_paths = detect_changed_paths(repo_root)
    changed_text = "\n".join(changed_paths) if changed_paths else "<none>"

    schema_path = repo_root / semantic.get("schemaPath", "scripts/config/agent/semantic_review_schema.json")
    if not schema_path.exists():
        raise SystemExit(f"Semantic schema not found: {schema_path}")

    timeout_sec = int(semantic.get("timeoutSec", 180))
    model = semantic.get("model", "")
    max_findings = int(semantic.get("maxFindings", 6))

    prompt = f"""You are a workflow compliance reviewer.

Goal:
- Review workflow/process risk for this task.
- Focus on scope drift, missing spec updates, missing verification evidence, and unsafe operational behavior.
- Do not invent repository facts; if uncertain, report uncertainty.

Task:
{args.task}

Changed paths:
{changed_text}

Instructions:
- Return strictly valid JSON per the provided schema.
- Keep findings concise and actionable.
- At most {max_findings} findings.
"""

    with tempfile.NamedTemporaryFile(delete=False) as tmp_out:
        tmp_out_path = Path(tmp_out.name)

    cmd = [
        codex,
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-C",
        str(repo_root),
    ]
    if model:
        cmd.extend(["-m", str(model)])
    cmd.extend(["--output-schema", str(schema_path), "-o", str(tmp_out_path), "-"])

    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        raise SystemExit(f"codex exec failed (exit {proc.returncode}). {err}")

    semantic_json = json.loads(tmp_out_path.read_text(encoding="utf-8"))
    findings = semantic_json.get("findings", [])
    result = {
        "status": "WARN" if findings else "PASS",
        "engine": "codex_subprocess",
        "model": model or None,
        "summary": semantic_json.get("summary", ""),
        "findings": findings,
        "changedPaths": changed_paths,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    try:
        tmp_out_path.unlink(missing_ok=True)
    except Exception:
        pass
    print(f"Semantic artifact: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
