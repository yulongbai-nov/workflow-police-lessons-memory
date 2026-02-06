#!/usr/bin/env python3
"""Quick smoke checks for Python tool scripts."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    scripts = sorted((root / "scripts" / "tools").glob("*.py"))
    if not scripts:
        raise SystemExit("No Python scripts found under scripts/tools.")
    for script in scripts:
        py_compile.compile(str(script), doraise=True)
        print(f"OK: {script.relative_to(root)}")
    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
