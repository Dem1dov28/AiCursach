"""Academic literature search via OpenAlex (and optional Semantic Scholar)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from backend.core.config import get_config


@dataclass(frozen=True)
class AcademicHit:
    title: str
    authors: str
    year: str
    doi: str
    url: str
    cited_by: int
    source: str
    snippet: str

    def to_gost_line(self, index: int) -> str:
        authors = self.authors or "Б. а."
        year = self.year or "б. г."
        title = self.title.strip().rstrip(".")
        doi_part = f" DOI: {self.doi}" if self.doi else ""
        return f"[{index}] {authors} {title} — {year}.{doi_part} URL: {self.url}"


def _fetch_json(url: str, *, timeout: float = 12.0) -> dict | list | None:
    mail = get_config().openalex_mailto
    headers = {
        "User-Agent": "AiCursach/1.0",
        "Accept": "application/json",
    }
    if "openalex.org" in url and mail:
        headers["User-Agent"] += f" (mailto:{mail})"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _author_list(raw: list[dict] | None) -> str:
    if not raw:
        return ""
    names: list[str] = []
    for item in raw[:3]:
        display = str(item.get("author", {}).get("display_name") or item.get("display_name") or "")
        if display:
            names.append(display)
    if len(raw) > 3:
        names.append("и др.")
    return ", ".join(names)


def search_openalex(query: str, *, limit: int = 5, language: str | None = None) -> list[AcademicHit]:
    params: dict[str, str | int] = {"search": query, "per_page": max(1, min(limit, 10))}
    if language:
        params["filter"] = f"language:{language}"
    payload = _fetch_json(f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}")
    if not isinstance(payload, dict):
        return []

    hits: list[AcademicHit] = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("display_name") or item.get("title") or "").strip()
        if not title:
            continue
        year = str(item.get("publication_year") or "")
        doi_raw = str(item.get("doi") or "")
        doi = doi_raw.replace("https://doi.org/", "").strip()
        url = str(item.get("id") or doi_raw or "")
        abstract = str(item.get("abstract_inverted_index") or "")
        if isinstance(item.get("abstract_inverted_index"), dict):
            abstract = " ".join(item["abstract_inverted_index"].keys())[:400]
        hits.append(
            AcademicHit(
                title=title,
                authors=_author_list(item.get("authorships")),
                year=year,
                doi=doi,
                url=url,
                cited_by=int(item.get("cited_by_count") or 0),
                source="openalex",
                snippet=abstract[:400],
            )
        )
    return hits


def search_semantic_scholar(query: str, *, limit: int = 5) -> list[AcademicHit]:
    cfg = get_config()
    api_key = cfg.semantic_scholar_api_key
    params = urllib.parse.urlencode({"query": query, "limit": max(1, min(limit, 10))})
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}&fields=title,authors,year,externalIds,url,citationCount,abstract"
    headers_extra = {"x-api-key": api_key} if api_key else {}
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"AiCursach/1.0 (mailto:{cfg.openalex_mailto})",
            "Accept": "application/json",
            **headers_extra,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []

    if not isinstance(payload, dict):
        return []

    hits: list[AcademicHit] = []
    for item in payload.get("data") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        authors_raw = item.get("authors") or []
        authors = ", ".join(
            str(a.get("name") or "") for a in authors_raw[:3] if isinstance(a, dict)
        )
        ext = item.get("externalIds") or {}
        doi = str(ext.get("DOI") or "") if isinstance(ext, dict) else ""
        hits.append(
            AcademicHit(
                title=title,
                authors=authors,
                year=str(item.get("year") or ""),
                doi=doi,
                url=str(item.get("url") or ""),
                cited_by=int(item.get("citationCount") or 0),
                source="semantic_scholar",
                snippet=str(item.get("abstract") or "")[:400],
            )
        )
    return hits


def _normalize_title(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def _dedupe_hits(hits: list[AcademicHit]) -> list[AcademicHit]:
    seen: set[str] = set()
    unique: list[AcademicHit] = []
    for hit in hits:
        key = _normalize_title(hit.title)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def search_academic_literature(
    query: str,
    *,
    limit: int = 5,
    include_russian: bool = False,
) -> list[AcademicHit]:
    """Search OpenAlex + Semantic Scholar; optional Russian-language boost."""
    query = query.strip()
    if not query:
        return []

    combined = search_openalex(query, limit=limit)
    if include_russian:
        combined.extend(search_openalex(query, limit=max(2, limit // 2), language="ru"))

    combined.extend(search_semantic_scholar(query, limit=limit))

    combined.sort(key=lambda item: item.cited_by, reverse=True)
    return _dedupe_hits(combined)[:limit]


def search_russian_web_sources(query: str, discipline: str = "") -> str:
    """Heuristic hints for Russian academic portals (used in Tavily query)."""
    parts = [query.strip()]
    if discipline.strip():
        parts.append(discipline.strip())
    parts.append("site:cyberleninka.ru OR site:rsl.ru OR elibrary.ru учебник монография")
    return " ".join(parts)


def format_hits_for_researcher(hits: list[AcademicHit]) -> str:
    if not hits:
        return ""
    lines = ["## Академические источники (OpenAlex / Semantic Scholar)", ""]
    for index, hit in enumerate(hits, start=1):
        lines.append(hit.to_gost_line(index))
        if hit.snippet:
            lines.append(f"   Кратко: {hit.snippet[:280]}")
        lines.append("")
    return "\n".join(lines).strip()
