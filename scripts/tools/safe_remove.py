#!/usr/bin/env python3
"""Safe deletion wrapper for workflow automation."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def remove_path(path: Path, recursive: bool) -> str:
    if not path.exists():
        return f"missing: {path}"
    if path.is_dir():
        if not recursive:
            return f"skip-dir-requires-recursive: {path}"
        shutil.rmtree(path)
        return f"removed-dir: {path}"
    path.unlink()
    return f"removed-file: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete files/directories via explicit wrapper.")
    parser.add_argument("--path", dest="paths", action="append", required=True, help="Path to remove (repeatable)")
    parser.add_argument("--recursive", action="store_true", help="Allow deleting directories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    args = parser.parse_args()

    rc = 0
    for raw in args.paths:
        path = Path(raw).resolve()
        if args.dry_run:
            if not path.exists():
                print(f"missing: {path}")
            elif path.is_dir() and not args.recursive:
                print(f"skip-dir-requires-recursive: {path}")
                rc = 1
            elif path.is_dir():
                print(f"would-remove-dir: {path}")
            else:
                print(f"would-remove-file: {path}")
            continue
        result = remove_path(path, args.recursive)
        print(result)
        if result.startswith("skip-"):
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
