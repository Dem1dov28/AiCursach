"""Detect overused AI/academic clichés in draft text."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from backend.domain.document.draft_text import draft_to_plain_text

_CLICHE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("в современном мире", re.compile(r"\bв\s+современном\s+мире\b", re.I)),
    ("важно отметить", re.compile(r"\bважно\s+отметить\b", re.I)),
    ("следует отметить", re.compile(r"\bследует\s+отметить\b", re.I)),
    ("не секрет, что", re.compile(r"\bне\s+секрет,?\s+что\b", re.I)),
    ("на сегодняшний день", re.compile(r"\bна\s+сегодняш\w*\s+день\b", re.I)),
    ("играет важную роль", re.compile(r"\bигра\w*\s+важн\w*\s+роль\b", re.I)),
    ("в заключение хотелось бы", re.compile(r"\bв\s+заключени\w*\s+хотел\w*\s+бы\b", re.I)),
    ("является одним из", re.compile(r"\bявля\w+\s+одним\s+из\b", re.I)),
    ("в данной работе", re.compile(r"\bв\s+данн\w+\s+работ\w+\b", re.I)),
    ("актуальность темы", re.compile(r"\bактуальност\w+\s+тем\w+\b", re.I)),
)


@dataclass(frozen=True)
class StyleIssue:
    phrase: str
    reason: str
    count: int = 1

    def to_dict(self) -> dict[str, str | int]:
        return {"phrase": self.phrase, "reason": self.reason, "count": self.count}


def find_cliches(text: str) -> list[StyleIssue]:
    if not text.strip():
        return []

    issues: list[StyleIssue] = []
    for label, pattern in _CLICHE_PATTERNS:
        count = len(pattern.findall(text))
        if count:
            issues.append(
                StyleIssue(
                    phrase=label,
                    reason="Шаблонная фраза нейросети — замените на академический стиль",
                    count=count,
                )
            )
    return issues


def validate_style(content_draft: str, *, work_type: str = "lab") -> list[StyleIssue]:
    plain = draft_to_plain_text(content_draft, work_type=work_type)
    if plain:
        return find_cliches(plain)

    try:
        data = json.loads(content_draft or "{}")
        if isinstance(data, dict) and data.get("raw_text"):
            return find_cliches(str(data["raw_text"]))
    except json.JSONDecodeError:
        return find_cliches(content_draft)
    return []
