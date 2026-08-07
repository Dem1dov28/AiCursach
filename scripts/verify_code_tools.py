#!/usr/bin/env python3
"""Проверка компиляторов, Chromium и скриншотов на сервере / в Docker."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.core.bootstrap import ensure_repo_on_path

ensure_repo_on_path()

from backend.infrastructure.adapters.html_screenshots import _find_chrome
from backend.tests.test_code_tools_run import run_all_checks


def _toolchain_report() -> dict[str, str]:
    tools = {
        "python3": shutil.which("python3") or shutil.which("python") or "",
        "javac": shutil.which("javac") or "",
        "java": shutil.which("java") or "",
        "gcc": shutil.which("gcc") or "",
        "g++": shutil.which("g++") or "",
        "chromium": _find_chrome() or "",
    }
    return {name: (path or "NOT FOUND") for name, path in tools.items()}


def main() -> int:
    print("=== Toolchain ===")
    toolchain = _toolchain_report()
    print(json.dumps(toolchain, ensure_ascii=False, indent=2))

    missing = [k for k, v in toolchain.items() if v == "NOT FOUND" and k != "chromium"]
    if missing:
        print("WARN: отсутствуют:", ", ".join(missing))

    print("\n=== Code run + screenshots ===")
    results = run_all_checks()
    print(json.dumps(results, ensure_ascii=False, indent=2))

    failed = [
        lang
        for lang, row in results.items()
        if not row.get("run_ok") or not row.get("screenshot")
    ]
    if failed:
        print(f"\nFAILED languages: {', '.join(failed)}", file=sys.stderr)
        return 1

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
