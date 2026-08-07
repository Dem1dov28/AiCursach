"""Parse uploaded file bytes into text."""

from __future__ import annotations

from backend.application.container import file_text_extractor


def parse_upload_bytes(data: bytes, filename: str) -> tuple[str, str, str | None]:
    if not data:
        return "", filename, f"Файл «{filename}» пустой"
    try:
        text, hint = file_text_extractor().extract(data, filename)
        if hint:
            return "", filename, hint
        return text, filename, None
    except Exception as exc:
        return "", filename, str(exc)
