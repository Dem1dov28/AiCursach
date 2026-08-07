"""Проверка компиляции, запуска и скриншотов для всех языковых инструментов."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from backend.core.paths import reset_projects_root, set_projects_root
from backend.infrastructure.adapters.code_runner import write_code_files
from backend.infrastructure.adapters.code_tools import get_code_toolkit, supported_languages
from backend.infrastructure.adapters.code_tools.runners import project_src


SAMPLES: dict[str, dict[str, str]] = {
    "python": {
        "main.py": (
            "# -*- coding: utf-8 -*-\n"
            "if __name__ == '__main__':\n"
            "    print('BSUIR Python OK')\n"
        ),
    },
    "java": {
        "Main.java": (
            "public class Main {\n"
            "  public static void main(String[] args) {\n"
            "    System.out.println(\"BSUIR Java OK\");\n"
            "  }\n"
            "}\n"
        ),
    },
    "c": {
        "main.c": (
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "  printf(\"BSUIR C OK\\n\");\n"
            "  return 0;\n"
            "}\n"
        ),
    },
    "cpp": {
        "main.cpp": (
            "#include <iostream>\n"
            "int main() {\n"
            "  std::cout << \"BSUIR C++ OK\" << std::endl;\n"
            "  return 0;\n"
            "}\n"
        ),
    },
    "javascript": {
        "html/index.html": (
            "<!DOCTYPE html>\n<html lang=\"ru\"><head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <title>Test</title>\n"
            "  <link rel=\"stylesheet\" href=\"../css/style.css\">\n"
            "</head><body>\n"
            "  <h1 id=\"title\">BSUIR Web OK</h1>\n"
            "  <script src=\"../js/script.js\"></script>\n"
            "</body></html>\n"
        ),
        "css/style.css": "body { font-family: serif; padding: 24px; color: #004080; }\n",
        "js/script.js": "document.getElementById('title').style.fontSize = '28px';\n",
    },
}


def _has_screenshot(project_name: str, lang: str) -> bool:
    shots_dir = project_src(project_name).parent / "Материалы" / "Скриншоты"
    if not shots_dir.is_dir():
        return False
    pngs = list(shots_dir.glob("*.png"))
    if not pngs:
        return False
  # Web: browser shots; console langs: 02_console.png
    if lang == "javascript":
        return any(p.stat().st_size > 500 for p in pngs)
    return any(p.name == "02_console.png" and p.stat().st_size > 500 for p in pngs)


def run_all_checks() -> dict[str, dict]:
    results: dict[str, dict] = {}
    tmp = Path(tempfile.mkdtemp(prefix="bsuir_code_test_"))
    token = set_projects_root(tmp)

    try:
        for lang in supported_languages():
            project = f"Test_{lang}"
            toolkit = get_code_toolkit(lang)
            files = SAMPLES[lang]
            write_code_files(project, files)
            entry = toolkit.default_listing_file()
            ok, output = toolkit.run(project, files, entry_file=entry)
            shot = _has_screenshot(project, lang)
            results[lang] = {
                "run_ok": ok,
                "output": (output or "")[:200],
                "screenshot": shot,
                "toolkit": toolkit.display_name,
            }
    finally:
        reset_projects_root(token)
        shutil.rmtree(tmp, ignore_errors=True)

    return results


if __name__ == "__main__":
    out = run_all_checks()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    failed = [
        lang
        for lang, r in out.items()
        if not r["run_ok"] or not r["screenshot"]
    ]
    if failed:
        raise SystemExit(f"FAILED: {', '.join(failed)}")
    print("ALL OK")
