"""Листинг исходного кода для раздела «Код программы»."""

from __future__ import annotations

import json
import re
from pathlib import Path

from backend.core.paths import project_dir
from backend.infrastructure.adapters.source_sanitize import contains_lab_report_text

_CODE_EXTS = (".html", ".htm", ".css", ".js", ".py", ".java", ".cpp", ".cc", ".cs")

_CODE_HINTS = (
    "<!doctype",
    "<html",
    "<head",
    "<body",
    "<form",
    "<input",
    "<script",
    "<style",
    "function ",
    "const ",
    "let ",
    "var ",
    "=>",
    "document.",
    "addEventListener",
    "def ",
    "import ",
    "#include",
    "public class",
    "if __name__",
    "body {",
    ".header",
    "margin:",
    "padding:",
)

_PROSE_HINTS = (
    "проект состоит",
    "используется flexbox",
    "представляет собой",
    "включает в себя",
    "разработан",
    "реализован",
    "папка ",
    "папки ",
    "содержит файл",
    "семантические блоки",
    "блок layout",
    "валидация данных",
    "при успешной",
    "теоретические сведения",
    "цель работы",
    "лабораторная работа",
    "индивидуальное задание",
    "методические указания",
)


def _block_looks_like_source(body: str) -> bool:
    text = (body or "").strip()
    if len(text) < 40:
        return False
    lower = text.lower()
    code_hits = sum(1 for hint in _CODE_HINTS if hint in lower)
    prose_hits = sum(1 for hint in _PROSE_HINTS if hint in lower)
    if prose_hits >= 2 and code_hits == 0:
        return False
    if code_hits >= 2:
        return True
    if re.search(r"[{};<>]=?", text) and code_hits >= 1:
        return True
    return False


def is_code_listing(text: str) -> bool:
    value = (text or "").strip()
    if not value:
        return False

    if "// === " in value:
        blocks = re.split(r"(?=// === )", value)
        return any(
            block.strip().startswith("// === ") and _block_looks_like_source(
                block.split("\n", 1)[1] if "\n" in block else ""
            )
            for block in blocks
            if block.strip()
        )

    return _block_looks_like_source(value)


def _listing_score(text: str) -> int:
    value = (text or "").strip()
    if not value:
        return 0
    lower = value.lower()
    score = min(value.count("\n"), 40)
    score += 5 * sum(1 for hint in _CODE_HINTS if hint in lower)
    score -= 6 * sum(1 for hint in _PROSE_HINTS if hint in lower)
    if contains_lab_report_text(value):
        score -= 40
    if "// === " in value and is_code_listing(value):
        score += 10
    return score


def format_files_listing(files: dict[str, str]) -> str:
    parts: list[str] = []
    for name in sorted(files):
        content = files[name]
        if not isinstance(content, str):
            continue
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            continue
        parts.append(f"// === {name} ===\n{content.strip()}")
    return "\n\n".join(parts)


def load_code_listing_from_state(state: dict) -> str:
    raw = state.get("code_files", "")
    if not raw:
        return ""
    try:
        files = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if isinstance(files, dict):
        return format_files_listing(files)
    return ""


def load_code_listing_from_src(project_name: str) -> str:
    src = project_dir(project_name) / "src"
    if not src.is_dir():
        return ""
    files: dict[str, str] = {}
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _CODE_EXTS:
            continue
        rel = path.relative_to(src).as_posix()
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except OSError:
            continue
    return format_files_listing(files)


def resolve_program_code(content: dict, state: dict, project_name: str) -> str:
    """Источник истины — файлы в src/, не текстовое описание от Writer."""
    candidates = {
        "src": load_code_listing_from_src(project_name),
        "state": load_code_listing_from_state(state),
        "draft": str(content.get("program_code") or "").strip(),
    }
    best = ""
    best_score = 0
    for source, text in candidates.items():
        score = _listing_score(text)
        if source == "src" and score > 0:
            score += 5
        if score > best_score:
            best_score = score
            best = text
    if best_score > 0 and is_code_listing(best):
        return best
    return ""
