"""Автовставка PNG-рисунков в docx (СТП БГУИР)."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document

from backend.core.paths import REPO_ROOT as ROOT, project_dir

IMAGE_DIRS = (
    "Материалы/Скриншоты",
    "Материалы/Диаграммы/png",
    "Материалы/Графики",
    "Материалы/Excel/charts",
    "src",
)

# Буквы приложений по СТП (без Ё/Й/Ъ/Ь).
_APPENDIX_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"


def _import_stp():
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.common.docx_stp import add_figure, appendix_continuation, appendix_start

    return add_figure, appendix_start, appendix_continuation


def _is_valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 64:
        return False
    try:
        head = path.read_bytes()[:12]
    except OSError:
        return False
    return head.startswith(b"\x89PNG\r\n\x1a\n") or head[:3] == b"\xff\xd8\xff"


def collect_project_pngs(project_name: str) -> list[Path]:
    proj = project_dir(project_name)
    found: list[Path] = []
    seen: set[str] = set()
    for rel in IMAGE_DIRS:
        folder = proj / rel
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.png")):
            if not _is_valid_image(path):
                continue
            key = path.name.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(path)
    return found


def classify_pngs(images: list[Path]) -> list[tuple[str, list[Path]]]:
    """Группы (title, paths) для приложений: диаграммы → графики → прочее."""
    diagrams: list[Path] = []
    charts: list[Path] = []
    other: list[Path] = []
    for path in images:
        parts = {p.lower() for p in path.parts}
        joined = "/".join(path.parts).lower()
        if "диаграммы" in parts or "/diagrams/" in joined:
            diagrams.append(path)
        elif "графики" in parts or "charts" in parts:
            charts.append(path)
        else:
            other.append(path)

    groups: list[tuple[str, list[Path]]] = []
    if diagrams:
        groups.append(("Диаграммы", diagrams))
    if charts:
        groups.append(("Графики результатов", charts))
    if other:
        title = "Иллюстрации" if groups else "Диаграммы и иллюстрации"
        groups.append((title, other))
    return groups


def _human_stem(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ")
    stem = re.sub(r"\s+", " ", stem).strip()
    if stem.lower().startswith("idef0"):
        stem = stem.replace("idef0", "IDEF0", 1)
    if stem.lower().startswith("fig"):
        stem = re.sub(r"^fig\s*", "", stem, flags=re.I).strip()
    if not stem:
        stem = path.stem
    return stem[:1].upper() + stem[1:] if stem else path.stem


def _human_caption(path: Path, index: int) -> str:
    return f"Рисунок {index} – {_human_stem(path)}"


def _appendix_caption(path: Path, letter: str, index: int) -> str:
    return f"Рисунок {letter}.{index} – {_human_stem(path)}"


def _find_anchor_paragraph(doc: Document, keywords: tuple[str, ...]):
    for p in doc.paragraphs:
        text = p.text.strip().upper()
        if not text:
            continue
        for kw in keywords:
            if kw.upper() in text:
                return p
    return None


def _move_paragraphs_before(ref_paragraph, new_paragraphs) -> None:
    ref_el = ref_paragraph._element
    for p in reversed(new_paragraphs):
        ref_el.addprevious(p._element)


def used_appendix_letters(doc: Document) -> set[str]:
    used: set[str] = set()
    for p in doc.paragraphs:
        match = re.search(r"Приложение\s*([А-ЯA-ZЁ])", p.text or "", re.I)
        if match:
            letter = match.group(1).upper().replace("Ё", "Е")
            used.add(letter)
    return used


def allocate_appendix_letters(used: set[str], count: int) -> list[str]:
    letters: list[str] = []
    for letter in _APPENDIX_LETTERS:
        if letter in used:
            continue
        letters.append(letter)
        if len(letters) >= count:
            break
    return letters


def insert_figures(
    docx_path: Path | str,
    images: list[Path] | None = None,
    *,
    project_name: str = "",
    anchor_keywords: tuple[str, ...] = ("ЗАКЛЮЧЕНИЕ", "ВЫВОДЫ"),
) -> tuple[int, str]:
    """Вставить PNG перед заключением/выводами или в конец документа."""
    docx_path = Path(docx_path)
    if not docx_path.exists():
        return 0, f"docx не найден: {docx_path}"

    if images is None and project_name:
        images = collect_project_pngs(project_name)
    images = [p for p in (images or []) if p.exists()]
    if not images:
        return 0, "Нет PNG для вставки"

    add_figure, _, _ = _import_stp()
    doc = Document(str(docx_path))
    anchor = _find_anchor_paragraph(doc, anchor_keywords)
    start_len = len(doc.paragraphs)

    for i, img in enumerate(images, 1):
        add_figure(doc, img, _human_caption(img, i))

    new_paras = doc.paragraphs[start_len:]
    if anchor and new_paras:
        _move_paragraphs_before(anchor, new_paras)

    doc.save(str(docx_path))
    return len(images), f"Вставлено рисунков: {len(images)} → {docx_path.name}"


def insert_figures_as_appendices(
    docx_path: Path | str,
    images: list[Path] | None = None,
    *,
    project_name: str = "",
    figures_per_page: int = 2,
    annex_plan: dict | None = None,
) -> tuple[int, str]:
    """Добавить PNG в конец DOCX как приложения А/Б… (СТП).

    Если передан ``annex_plan`` с figures — используем буквы/заголовки/подписи из плана.
    Иначе — авто-группировка по папкам (этап 2).
    """
    docx_path = Path(docx_path)
    if not docx_path.exists():
        return 0, f"docx не найден: {docx_path}"

    plan = annex_plan if isinstance(annex_plan, dict) else None
    if plan and plan.get("appendices"):
        return _insert_from_annex_plan(
            docx_path,
            plan,
            project_name=project_name,
            figures_per_page=figures_per_page,
        )

    if images is None and project_name:
        images = collect_project_pngs(project_name)
    images = [p for p in (images or []) if _is_valid_image(p)]
    if not images:
        return 0, "Нет PNG для приложений"

    groups = classify_pngs(images)
    if not groups:
        return 0, "Нет PNG для приложений"

    add_figure, appendix_start, appendix_continuation = _import_stp()
    doc = Document(str(docx_path))
    used = used_appendix_letters(doc)
    letters = allocate_appendix_letters(used, len(groups))
    if len(letters) < len(groups):
        return 0, "Недостаточно свободных букв приложений"

    total = 0
    summary: list[str] = []
    for letter, (title, paths) in zip(letters, groups):
        appendix_start(doc, letter, title, status="обязательное")
        for i, img in enumerate(paths, 1):
            if i > 1 and figures_per_page > 0 and (i - 1) % figures_per_page == 0:
                appendix_continuation(doc, letter)
            add_figure(doc, img, _appendix_caption(img, letter, i))
            total += 1
        summary.append(f"{letter}({len(paths)})")

    doc.save(str(docx_path))
    return total, f"Приложения {', '.join(summary)}: {total} рис. → {docx_path.name}"


def build_heuristic_annex_plan(
    images: list[Path],
    *,
    project_root: Path | None = None,
    reserved_letters: set[str] | None = None,
) -> dict:
    """Детерминированный план приложений по папкам PNG."""
    groups = classify_pngs(images)
    used = {str(x).upper().replace("Ё", "Е") for x in (reserved_letters or set())}
    letters = allocate_appendix_letters(used, len(groups))
    appendices: list[dict] = []
    for letter, (title, paths) in zip(letters, groups):
        figures: list[dict[str, str]] = []
        for i, path in enumerate(paths, 1):
            rel = str(path)
            if project_root is not None:
                try:
                    rel = str(path.resolve().relative_to(project_root.resolve()))
                except ValueError:
                    rel = path.name
            figures.append(
                {
                    "path": rel,
                    "caption": f"Рисунок {letter}.{i} – {_human_stem(path)}",
                }
            )
        appendices.append(
            {
                "letter": letter,
                "title": title,
                "status": "обязательное",
                "kind": "figures",
                "figures": figures,
            }
        )
    return {"appendices": appendices}


def _resolve_image_path(raw: str, *, project_name: str) -> Path | None:
    text = (raw or "").strip()
    if not text:
        return None
    candidate = Path(text)
    if _is_valid_image(candidate):
        return candidate
    if project_name:
        under_proj = project_dir(project_name) / text
        if _is_valid_image(under_proj):
            return under_proj
    under_root = ROOT / text
    if _is_valid_image(under_root):
        return under_root
    return None


def _insert_from_annex_plan(
    docx_path: Path,
    plan: dict,
    *,
    project_name: str,
    figures_per_page: int,
) -> tuple[int, str]:
    add_figure, appendix_start, appendix_continuation = _import_stp()
    doc = Document(str(docx_path))
    used = used_appendix_letters(doc)

    total = 0
    summary: list[str] = []
    for item in plan.get("appendices") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("kind") or "figures") != "figures":
            continue
        figures = item.get("figures") or []
        if not isinstance(figures, list) or not figures:
            continue

        letter = str(item.get("letter") or "").strip().upper().replace("Ё", "Е")
        if not letter or letter in used:
            free = allocate_appendix_letters(used, 1)
            if not free:
                continue
            letter = free[0]
        used.add(letter)

        title = str(item.get("title") or "Иллюстрации")
        status = str(item.get("status") or "обязательное")
        appendix_start(doc, letter, title, status=status)

        fig_index = 0
        for fig in figures:
            if not isinstance(fig, dict):
                continue
            img = _resolve_image_path(str(fig.get("path") or ""), project_name=project_name)
            if not img:
                continue
            fig_index += 1
            if fig_index > 1 and figures_per_page > 0 and (fig_index - 1) % figures_per_page == 0:
                appendix_continuation(doc, letter)
            caption = str(fig.get("caption") or "").strip() or _appendix_caption(img, letter, fig_index)
            add_figure(doc, img, caption)
            total += 1

        if fig_index:
            summary.append(f"{letter}({fig_index})")

    if not total:
        return 0, "План приложений не дал валидных PNG"

    doc.save(str(docx_path))
    return total, f"Приложения по плану {', '.join(summary)}: {total} рис. → {docx_path.name}"
