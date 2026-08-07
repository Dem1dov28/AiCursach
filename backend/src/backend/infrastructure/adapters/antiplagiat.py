"""Антиплагиат: поиск скриншота и вставка приложения в DOCX."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document

from backend.core.paths import REPO_ROOT as ROOT, project_dir

_SHOT_NAME_RE = re.compile(r"(antiplag|антиплаг|originalit|оригинал)", re.I)


def find_antiplagiat_screenshot(project_name: str) -> Path | None:
    """Ищет PNG отчёта Антиплагиат в материалах проекта."""
    proj = project_dir(project_name)
    folders = (
        proj / "Материалы" / "Скриншоты",
        proj / "Материалы" / "Антиплагиат",
        proj / "Материалы",
    )
    candidates: list[Path] = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.png")):
            if _SHOT_NAME_RE.search(path.stem):
                candidates.append(path)
        exact = folder / "antiplagiat.png"
        if exact.is_file() and exact not in candidates:
            candidates.insert(0, exact)

    for path in candidates:
        if path.is_file() and path.stat().st_size >= 64:
            return path
    return None


def insert_antiplagiat_appendix(
    docx_path: Path | str,
    screenshot: Path | str,
    *,
    letter: str = "А",
    originality_pct: int = 95,
) -> tuple[bool, str]:
    """Добавить приложение со скриншотом Антиплагиат в конец DOCX."""
    docx_path = Path(docx_path)
    screenshot = Path(screenshot)
    if not docx_path.exists():
        return False, f"docx не найден: {docx_path}"
    if not screenshot.is_file():
        return False, f"скриншот не найден: {screenshot}"

    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.common.docx_stp import add_figure, appendix_start

    doc = Document(str(docx_path))
    title = "Отчет о проверке на заимствования в системе «Антиплагиат»"
    caption = (
        f"Рисунок {letter}.1 – Отчет о проверке на заимствования "
        f"в системе «Антиплагиат» (оригинальность {int(originality_pct)}%)"
    )
    appendix_start(doc, letter, title, status="обязательное")
    add_figure(doc, screenshot, caption)
    doc.save(str(docx_path))
    rel = str(screenshot)
    try:
        rel = str(screenshot.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        pass
    return True, f"Антиплагиат → Приложение {letter} ({rel})"


def clamp_originality_pct(value: object, default: int = 92) -> int:
    try:
        pct = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return max(50, min(99, pct))
