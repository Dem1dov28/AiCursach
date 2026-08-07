"""Extract readable plain text from content_draft JSON."""

from __future__ import annotations

import json
from typing import Any


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n\n".join(str(item) for item in value if item)
    return ""


def draft_to_plain_text(content_draft: str, *, work_type: str = "lab") -> str:
    if not content_draft.strip():
        return ""

    try:
        data = json.loads(content_draft)
    except json.JSONDecodeError:
        return content_draft.strip()

    if not isinstance(data, dict):
        return str(data)

    blocks: list[str] = []

    if work_type == "coursework":
        for part in data.get("intro") or []:
            text = _as_text(part)
            if text.strip():
                blocks.append(text.strip())
        for section in data.get("sections") or []:
            if not isinstance(section, dict):
                continue
            title = _as_text(section.get("title"))
            if title.strip():
                blocks.append(title.strip())
            for part in section.get("paragraphs") or []:
                text = _as_text(part)
                if text.strip():
                    blocks.append(text.strip())
        for part in data.get("conclusion") or []:
            text = _as_text(part)
            if text.strip():
                blocks.append(text.strip())
        for part in data.get("sources") or []:
            text = _as_text(part)
            if text.strip():
                blocks.append(text.strip())
    else:
        for key in ("purpose", "theory", "variant_task", "program_code", "program_work", "conclusions"):
            text = _as_text(data.get(key))
            if text.strip():
                blocks.append(text.strip())

    if not blocks and data.get("raw_text"):
        return str(data["raw_text"]).strip()
    return "\n\n".join(blocks)
