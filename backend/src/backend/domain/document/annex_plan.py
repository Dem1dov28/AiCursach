"""Normalize / validate annex plan JSON for coursework appendices."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_APPENDIX_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
_LETTER_RE = re.compile(r"^[А-ЯA-ZЁ]$")


def parse_annex_plan(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(raw, dict):
        return normalize_annex_plan(raw)
    text = (raw or "").strip()
    if not text:
        return {"appendices": []}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"appendices": []}
    return normalize_annex_plan(data if isinstance(data, dict) else {})


def normalize_annex_plan(raw: dict[str, Any] | None) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    items = data.get("appendices") or data.get("annexes") or []
    if not isinstance(items, list):
        return {"appendices": []}

    appendices: list[dict[str, Any]] = []
    used_letters: set[str] = set()
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        letter = str(item.get("letter") or "").strip().upper().replace("Ё", "Е")
        if not _LETTER_RE.match(letter) or letter not in _APPENDIX_LETTERS or letter in used_letters:
            letter = next_appendix_letter(used_letters)
        if not letter:
            break
        used_letters.add(letter)

        title = str(item.get("title") or "Иллюстрации").strip()[:120] or "Иллюстрации"
        status = str(item.get("status") or "обязательное").strip()[:40] or "обязательное"
        kind = str(item.get("kind") or "figures").strip().lower()
        if kind not in ("figures", "listing", "other"):
            kind = "figures"

        figures_in = item.get("figures") or []
        figures: list[dict[str, str]] = []
        if isinstance(figures_in, list):
            for fig in figures_in[:20]:
                if not isinstance(fig, dict):
                    continue
                path = str(fig.get("path") or fig.get("file") or "").strip()
                if not path:
                    continue
                caption = str(fig.get("caption") or "").strip()[:200]
                if not caption:
                    stem = Path(path).stem.replace("_", " ")
                    caption = f"Рисунок {letter}.{len(figures) + 1} – {stem}"
                figures.append({"path": path, "caption": caption})

        if kind == "figures" and not figures:
            continue
        appendices.append(
            {
                "letter": letter,
                "title": title,
                "status": status,
                "kind": kind,
                "figures": figures,
            }
        )

    return {"appendices": appendices}


def annex_plan_issues(plan: dict[str, Any] | str | None) -> list[str]:
    data = parse_annex_plan(plan)
    apps = data.get("appendices") or []
    if not apps:
        return ["нет приложений в плане"]
    figure_apps = [a for a in apps if a.get("kind") == "figures" and a.get("figures")]
    if not figure_apps:
        return ["нет приложений с рисунками"]
    return []


def inventory_png_entries(paths: list[Path], *, project_root: Path | None = None) -> list[dict[str, str]]:
    """Relative path + stem for LLM prompt."""
    entries: list[dict[str, str]] = []
    for path in paths:
        rel = str(path)
        if project_root is not None:
            try:
                rel = str(path.resolve().relative_to(project_root.resolve()))
            except ValueError:
                rel = path.name
        entries.append({"path": rel, "stem": path.stem})
    return entries


def next_appendix_letter(used: set[str]) -> str:
    for letter in _APPENDIX_LETTERS:
        if letter not in used:
            return letter
    return ""


def reassign_letters_avoiding(
    plan: dict[str, Any],
    reserved: set[str] | list[str] | None,
) -> dict[str, Any]:
    """Ensure appendix letters do not collide with reserved ones (e.g. А = Антиплагиат)."""
    data = normalize_annex_plan(plan)
    blocked = {
        str(x).strip().upper().replace("Ё", "Е")
        for x in (reserved or [])
        if str(x).strip()
    }
    if not blocked:
        return data

    used = set(blocked)
    for app in data.get("appendices") or []:
        letter = str(app.get("letter") or "")
        if letter in blocked or letter in used - blocked:
            letter = next_appendix_letter(used)
        if not letter:
            break
        app["letter"] = letter
        used.add(letter)
        for i, fig in enumerate(app.get("figures") or [], 1):
            cap = str(fig.get("caption") or "")
            if not cap or re.match(rf"^Рисунок\s+[А-ЯA-ZЁ]\.\d+", cap):
                stem = Path(str(fig.get("path") or "рис")).stem.replace("_", " ")
                fig["caption"] = f"Рисунок {letter}.{i} – {stem}"
    return data
