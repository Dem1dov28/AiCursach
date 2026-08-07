"""HTTP helpers for file downloads."""

from __future__ import annotations

from urllib.parse import quote


def attachment_headers(filename: str) -> dict[str, str]:
    ascii_name = "".join(
        c for c in filename if ord(c) < 128 and (c.isalnum() or c in "._-")
    )
    if not ascii_name or ascii_name == ".zip":
        ascii_name = "work.zip"
    elif not ascii_name.endswith(".zip"):
        ascii_name = f"{ascii_name}.zip"
    encoded = quote(filename)
    return {
        "Content-Disposition": (
            f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
        ),
    }
