"""Запуск сгенерированного кода в projects/*/src."""

from __future__ import annotations

from pathlib import Path

from backend.core.paths import REPO_ROOT as ROOT, project_dir
from backend.infrastructure.adapters.code_language import normalize_code_language
from backend.infrastructure.adapters.code_tools import get_code_toolkit
from backend.infrastructure.adapters.code_tools.runners import project_src


def write_code_files(project_name: str, files: dict[str, str]) -> list[str]:
    src = project_src(project_name)
    written: list[str] = []
    for rel, content in files.items():
        rel = rel.replace("\\", "/").lstrip("/")
        if ".." in Path(rel).parts:
            continue
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        try:
            written.append(str(path.relative_to(ROOT)))
        except ValueError:
            written.append(str(path))
    return written


def detect_language(files: dict[str, str], hint: str = "") -> str:
    normalized = normalize_code_language(hint)
    if normalized in ("javascript", "java", "python", "cpp", "c"):
        return normalized
    exts = {Path(n).suffix.lower() for n in files}
    if ".html" in exts or ".js" in exts or ".css" in exts:
        return "javascript"
    if ".java" in exts:
        return "java"
    if ".py" in exts:
        return "python"
    if ".cpp" in exts or ".cc" in exts:
        return "cpp"
    if ".c" in exts:
        return "c"
    return "python"


def run_code(
    project_name: str,
    files: dict[str, str],
    *,
    language: str = "",
    entry_file: str = "",
) -> tuple[bool, str]:
    lang = normalize_code_language(language) or detect_language(files, language)
    toolkit = get_code_toolkit(lang)
    return toolkit.run(project_name, files, entry_file=entry_file)


def files_to_listing(files: dict[str, str]) -> str:
    parts = []
    for name, content in files.items():
        parts.append(f"// === {name} ===\n{content}")
    return "\n\n".join(parts)
