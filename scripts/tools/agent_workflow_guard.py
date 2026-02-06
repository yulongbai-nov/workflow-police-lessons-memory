#!/usr/bin/env python3
"""Run deterministic workflow checks and optional semantic review."""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid workflow guard.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["warn", "block"], default="warn")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy-path", default="scripts/config/agent/agent_workflow_policy.json")
    parser.add_argument("--changed-paths", nargs="*", default=None)
    parser.add_argument("--skip-semantic", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    policy = load_json(repo_root / args.policy_path)
    findings: list[dict] = []

    def add_finding(severity: str, code: str, message: str) -> None:
        findings.append({"severity": severity, "code": code, "message": message})

    for doc in policy.get("requiredDocs", []):
        if not (repo_root / doc).exists():
            add_finding("high", "missing-required-doc", f"Missing required doc/path: {doc}")

    checks = policy.get("deterministicChecks", {})
    if checks.get("requireSpecDocs", False):
        spec_root = repo_root / policy.get("specRoot", ".specs")
        if not spec_root.exists():
            add_finding("medium", "missing-spec-root", f"Spec root missing: {spec_root}")
        elif not list(spec_root.rglob("*.md")):
            add_finding("medium", "empty-spec-root", f"No spec markdown files found under {spec_root}")

    preflight_cfg = policy.get("preflight", {})
    if preflight_cfg.get("required", False) and checks.get("requirePreflightArtifact", False):
        pattern = str((repo_root / preflight_cfg.get("artifactGlob", "logs/agent/preflight/*.json")).as_posix())
        files = [Path(p) for p in glob.glob(pattern)]
        if not files:
            add_finding("medium", "missing-preflight-artifact", f"No preflight artifact found matching: {pattern}")
        else:
            max_age = preflight_cfg.get("maxAgeHours")
            if max_age is not None:
                latest = max(files, key=lambda p: p.stat().st_mtime)
                age_h = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
                if age_h > float(max_age):
                    add_finding("medium", "stale-preflight-artifact", f"Latest preflight artifact is stale ({age_h:.1f}h old).")

    semantic_result = {"status": "SKIPPED", "artifactPath": None, "findings": []}
    semantic_cfg = policy.get("semanticReview", {})
    if not args.skip_semantic and semantic_cfg.get("enabled", False):
        semantic_script = repo_root / "scripts/tools/agent_semantic_guard.py"
        if semantic_script.exists():
            sem_out = repo_root / "logs" / "agent" / "guard" / f"semantic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            sem_out.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                sys.executable,
                str(semantic_script),
                "--task",
                args.task,
                "--repo-root",
                str(repo_root),
                "--policy-path",
                args.policy_path,
                "--output-path",
                str(sem_out),
            ]
            if args.changed_paths:
                cmd.extend(["--changed-paths", *args.changed_paths])
            proc = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
            if proc.returncode != 0:
                add_finding("medium", "semantic-run-failed", f"Semantic guard failed: {(proc.stderr or proc.stdout).strip()}")
            elif sem_out.exists():
                sem = load_json(sem_out)
                semantic_result = {
                    "status": sem.get("status", "WARN"),
                    "artifactPath": str(sem_out),
                    "findings": sem.get("findings", []),
                }
        else:
            add_finding("medium", "missing-semantic-script", "Semantic script missing: scripts/tools/agent_semantic_guard.py")

    block_sev = {str(x).lower() for x in semantic_cfg.get("blockOnSeverity", [])}
    semantic_block = any(str(f.get("severity", "")).lower() in block_sev for f in semantic_result.get("findings", []))

    det_high = sum(1 for f in findings if f["severity"] == "high")
    status = "PASS"
    if findings or semantic_result.get("findings"):
        status = "WARN"
    if args.mode == "block" and (det_high > 0 or semantic_block):
        status = "BLOCK"

    out_dir = repo_root / "logs" / "agent" / "guard"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"guard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result = {
        "status": status,
        "mode": args.mode,
        "task": args.task,
        "deterministicFindings": findings,
        "deterministicSummary": {
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium"),
            "total": len(findings),
        },
        "semantic": semantic_result,
        "generatedAt": datetime.now().isoformat(),
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Guard artifact: {out_path.resolve()}")
    print(f"Guard status: {status} (det={len(findings)}, semantic={len(semantic_result.get('findings', []))})")
    return 2 if status == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
