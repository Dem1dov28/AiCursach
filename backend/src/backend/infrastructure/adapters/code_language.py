"""Определение языка/стека кода по тексту задания."""

from __future__ import annotations

import re

from backend.infrastructure.adapters.text_utils import as_text

_WEB = (
    r"\bhtml\b",
    r"\bcss\b",
    r"\bjavascript\b",
    r"\bjs\b",
    r"html\s*/\s*css",
    r"html/css/js",
    r"\bвеб\b",
    r"\bweb\b",
    r"\bбраузер",
    r"\bdom\b",
    r"экранн\w+\s+форм",
)
_PYTHON = (r"\bpython\b", r"\bпитон\b", r"\.py\b")
_JAVA = (r"\bjava\b", r"\.java\b", r"\bjdk\b")
_CPP = (r"\bc\+\+\b", r"\bcpp\b", r"\.cpp\b", r"\bg\+\+\b")
_C = (r"\bansi\s+c\b", r"\bязык\s+c\b", r"\bна\s+си\b", r"\bна\s+c\b", r"\.c\b", r"\bgcc\b(?!\s*\+)")

_SUPPORTED = ("javascript", "python", "java", "c", "cpp")


def normalize_code_language(lang: str) -> str:
    value = (lang or "").strip().lower()
    if value in ("html", "css", "js", "web", "javascript", "front-end", "frontend"):
        return "javascript"
    if value in ("py", "python3"):
        return "python"
    if value in ("c++",):
        return "cpp"
    return value


def score_languages_from_text(*texts: str) -> dict[str, int]:
    blob = "\n".join(as_text(t) for t in texts if t is not None).lower()
    scores = {lang: 0 for lang in _SUPPORTED}
    if not blob.strip():
        return scores

    for pat in _WEB:
        if re.search(pat, blob, re.I):
            scores["javascript"] += 1
    if re.search(r"\bhtml\b", blob, re.I) and re.search(r"\bcss\b", blob, re.I):
        scores["javascript"] += 2

    for pat in _CPP:
        if re.search(pat, blob, re.I):
            scores["cpp"] += 2

    for pat in _C:
        if re.search(pat, blob, re.I):
            scores["c"] += 1
    if re.search(r"\.c\b", blob, re.I) and not re.search(r"c\+\+|\.cpp", blob, re.I):
        scores["c"] += 2

    for pat in _PYTHON:
        if re.search(pat, blob, re.I):
            scores["python"] += 1
    for pat in _JAVA:
        if re.search(pat, blob, re.I):
            scores["java"] += 1

    return scores


def resolve_code_language(llm_lang: str | None, *texts: str) -> str:
    """Выбрать язык по заданию и ответу анализатора."""
    scores = score_languages_from_text(*texts)
    llm = normalize_code_language(llm_lang or "")
    if llm in scores:
        scores[llm] += 2

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return llm or "python"
