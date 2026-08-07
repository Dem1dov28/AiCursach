"""Pure DOI parsing and title comparison helpers."""

from __future__ import annotations

import re

_DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\]>\"',;]+)", re.IGNORECASE)


def normalize_title(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def title_overlap(claimed: str, canonical: str) -> float:
    claimed_tokens = set(normalize_title(claimed).split())
    canonical_tokens = set(normalize_title(canonical).split())
    if not claimed_tokens or not canonical_tokens:
        return 0.0
    return len(claimed_tokens & canonical_tokens) / len(claimed_tokens)


def extract_doi(entry: str) -> str | None:
    match = _DOI_RE.search(entry)
    if not match:
        return None
    return match.group(1).rstrip(".")
