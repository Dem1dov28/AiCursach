"""Post-process docx with GOST 7.32-2017 formatting via gostdoc (optional dependency)."""

from __future__ import annotations

import shutil
from pathlib import Path


def apply_gost_formatting(
    input_path: str | Path,
    *,
    detect_structure: bool = True,
) -> tuple[bool, str, Path]:
    """Format docx per GOST 7.32-2017. Returns (ok, message, output_path)."""
    source = Path(input_path)
    if not source.exists() or source.suffix.lower() != ".docx":
        return False, "GOST: файл docx не найден", source

    try:
        from gostdoc.formatter import GostDocError, format_document
    except ImportError:
        return False, "GOST: пакет gostdoc не установлен (pip install git+https://github.com/samikofficial/gostdoc.git)", source

    temp_out = source.with_name(f"{source.stem}.gost.tmp.docx")
    try:
        messages = format_document(
            str(source),
            str(temp_out),
            detect_structure=detect_structure,
        )
        shutil.move(str(temp_out), str(source))
        note = "; ".join(messages[:2]) if messages else "оформление применено"
        return True, f"GOST 7.32: {note}", source
    except GostDocError as exc:
        if temp_out.exists():
            temp_out.unlink(missing_ok=True)
        return False, f"GOST: {exc}", source
    except Exception as exc:  # noqa: BLE001
        if temp_out.exists():
            temp_out.unlink(missing_ok=True)
        return False, f"GOST: ошибка форматирования — {exc}", source
