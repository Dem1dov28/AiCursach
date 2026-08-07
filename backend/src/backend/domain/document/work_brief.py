"""Work brief extracted from assignment + example + GOST/methodical."""

from __future__ import annotations

import json
import re
from typing import Any


def empty_work_brief() -> dict[str, Any]:
    return {
        "from_assignment": [],
        "from_example": {"structure_notes": "", "style_notes": "", "structure_source": ""},
        "from_gost": {
            "volume": "",
            "bibliography_standard": "",
            "title_fields": [],
            "required_sections": [],
        },
        "volume_targets": {
            "min_pages": None,
            "min_sources": None,
            "min_intro_paras": None,
            "min_section_paras": None,
            "min_body_chars": None,
        },
        "structure_source": "",  # example | methodical | discipline_fallback
    }


def parse_work_brief(raw: Any) -> dict[str, Any]:
    base = empty_work_brief()
    if raw is None:
        return base
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return base
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return base
    if not isinstance(raw, dict):
        return base

    out = empty_work_brief()
    fa = raw.get("from_assignment")
    if isinstance(fa, list):
        out["from_assignment"] = [str(x).strip() for x in fa if str(x).strip()][:20]
    elif isinstance(fa, str) and fa.strip():
        out["from_assignment"] = [fa.strip()]

    fe = raw.get("from_example")
    if isinstance(fe, dict):
        out["from_example"]["structure_notes"] = str(fe.get("structure_notes") or "")[:2000]
        out["from_example"]["style_notes"] = str(fe.get("style_notes") or "")[:2000]
        out["from_example"]["structure_source"] = str(fe.get("structure_source") or "")[:40]
    elif isinstance(fe, str):
        out["from_example"]["structure_notes"] = fe[:2000]

    fg = raw.get("from_gost")
    if isinstance(fg, dict):
        out["from_gost"]["volume"] = str(fg.get("volume") or "")[:1000]
        out["from_gost"]["bibliography_standard"] = str(fg.get("bibliography_standard") or "")[:500]
        titles = fg.get("title_fields") or []
        if isinstance(titles, list):
            out["from_gost"]["title_fields"] = [str(x) for x in titles if str(x).strip()][:20]
        req = fg.get("required_sections") or []
        if isinstance(req, list):
            out["from_gost"]["required_sections"] = [str(x) for x in req if str(x).strip()][:30]

    vt = raw.get("volume_targets")
    if isinstance(vt, dict):
        for key in (
            "min_pages",
            "min_sources",
            "min_intro_paras",
            "min_section_paras",
            "min_body_chars",
        ):
            val = vt.get(key)
            if val is None or val == "":
                out["volume_targets"][key] = None
            else:
                try:
                    out["volume_targets"][key] = int(val)
                except (TypeError, ValueError):
                    out["volume_targets"][key] = None

    src = str(raw.get("structure_source") or "").strip().lower()
    if src in ("example", "methodical", "discipline_fallback", "assignment"):
        out["structure_source"] = src
    elif out["from_example"].get("structure_notes"):
        out["structure_source"] = "example"
    elif out["from_gost"].get("required_sections"):
        out["structure_source"] = "methodical"
    return out


def work_brief_to_json(brief: dict[str, Any] | None) -> str:
    return json.dumps(parse_work_brief(brief), ensure_ascii=False)


def volume_targets_from_brief(brief: dict[str, Any] | str | None) -> dict[str, int | None]:
    parsed = parse_work_brief(brief)
    return dict(parsed.get("volume_targets") or {})


def infer_volume_targets_from_methodical(methodical_text: str) -> dict[str, int | None]:
    """Heuristic extraction when Analyzer omits numeric targets."""
    text = methodical_text or ""
    targets: dict[str, int | None] = {
        "min_pages": None,
        "min_sources": None,
        "min_intro_paras": None,
        "min_section_paras": None,
        "min_body_chars": None,
    }
    # «не менее 10 источников», «≥ 8 источников», «источников: 10–15»
    m = re.search(
        r"(?:не\s+менее|минимум|≥|>=)\s*(\d{1,2})\s*источник",
        text,
        re.I,
    )
    if not m:
        m = re.search(r"источник\w*\s*[:\—\-]?\s*(\d{1,2})\s*[–\-]\s*\d{1,2}", text, re.I)
    if m:
        targets["min_sources"] = int(m.group(1))

    m = re.search(
        r"(?:не\s+менее|минимум|≥|>=|объ[её]м)\s*(\d{1,2})\s*(?:страниц|стр\b)",
        text,
        re.I,
    )
    if not m:
        m = re.search(r"(\d{2})\s*[–\-]\s*\d{2}\s*страниц", text, re.I)
    if m:
        targets["min_pages"] = int(m.group(1))
        # Rough: ~1800 chars/page of body prose
        targets["min_body_chars"] = targets["min_pages"] * 1500

    return targets


def merge_volume_targets(
    brief: dict[str, Any] | None,
    *,
    methodical_text: str = "",
) -> dict[str, int | None]:
    targets = volume_targets_from_brief(brief)
    inferred = infer_volume_targets_from_methodical(methodical_text)
    for key, val in inferred.items():
        if targets.get(key) is None and val is not None:
            targets[key] = val
    return targets


def brief_summary_for_hitl(brief: dict[str, Any] | None, structure_outline: str = "") -> str:
    """Short human-readable blurb for team/plan HITL."""
    b = parse_work_brief(brief)
    parts: list[str] = []
    src = b.get("structure_source") or ""
    src_label = {
        "example": "структура из примера",
        "methodical": "структура из методички/ГОСТ",
        "discipline_fallback": "структура по шаблону дисциплины",
        "assignment": "структура из задания",
    }.get(src, "")
    if src_label:
        parts.append(src_label)
    gost = b.get("from_gost") or {}
    if gost.get("bibliography_standard"):
        parts.append(f"библиография: {gost['bibliography_standard']}")
    if gost.get("volume"):
        parts.append(f"объём: {gost['volume']}")
    vt = b.get("volume_targets") or {}
    if vt.get("min_sources"):
        parts.append(f"источников ≥{vt['min_sources']}")
    if vt.get("min_pages"):
        parts.append(f"стр. ≥{vt['min_pages']}")
    if structure_outline.strip():
        first_lines = [ln.strip() for ln in structure_outline.splitlines() if ln.strip()][:4]
        if first_lines:
            parts.append("план: " + " → ".join(first_lines))
    return "; ".join(parts)


def required_sections_from_brief(brief: dict[str, Any] | None) -> list[str]:
    b = parse_work_brief(brief)
    gost = b.get("from_gost") or {}
    req = gost.get("required_sections") or []
    return [str(x) for x in req if str(x).strip()]
