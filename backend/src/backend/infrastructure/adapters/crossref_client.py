"""CrossRef HTTP client (infrastructure I/O)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def fetch_crossref_title(doi: str) -> str | None:
    url = f"https://api.crossref.org/works/{doi}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AiCursach/1.0 (mailto:aicursach@local)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    message = payload.get("message") or {}
    if isinstance(message, dict):
        titles = message.get("title") or []
        if titles:
            return str(titles[0])
    return None
