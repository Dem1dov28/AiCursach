#!/usr/bin/env python3
"""
Подставляет реальные скриншоты приложения в существующую пояснительную записку.
Меняются только рисунки 3.3–3.8, текст и разбивка страниц не трогаются.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

CW_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = CW_ROOT / "Материалы" / "Скриншоты"
DOCX = CW_ROOT / "Отчет" / "Пояснительная_записка_CharityLedger.docx"

# подпись в документе -> файл скриншота
FIGURES = {
    "3.3": ("03_app_admin.png", "Рисунок 3.3 – Интерфейс авторизации (вкладка «Администрирование»)"),
    "3.4": ("03_app_campaigns.png", "Рисунок 3.4 – Вкладка «Кампании»"),
    "3.5": ("03_app_donation.png", "Рисунок 3.5 – Вкладка «Пожертвование»"),
    "3.6": ("03_app_transparency.png", "Рисунок 3.6 – Вкладка «Прозрачность»"),
    "3.7": ("03_app_admin.png", "Рисунок 3.7 – Вкладка «Администрирование»"),
    "3.8": ("03_app_report.png", "Рисунок 3.8 – Отображение отчёта прозрачности"),
}


def _has_image(paragraph) -> bool:
    return bool(paragraph._element.xpath(".//wp:inline"))


def _replace_image_paragraph(paragraph, image_path: Path, width=Cm(15)) -> None:
    paragraph.clear()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image_path), width=width)


def patch(doc_path: Path) -> int:
    if not doc_path.exists():
        print(f"Файл не найден: {doc_path}", file=sys.stderr)
        return 1

    needed = sorted({v[0] for v in FIGURES.values()})
    missing = [f for f in needed if not (SCREENSHOTS / f).exists()]
    if missing:
        print("Нет скриншотов:", ", ".join(missing), file=sys.stderr)
        print(f"Сначала: python3 {CW_ROOT / 'Скрипты' / 'capture_app_screenshots.py'} --interactive", file=sys.stderr)
        return 1

    doc = Document(str(doc_path))
    paras = doc.paragraphs
    replaced = 0

    for num, (filename, new_caption) in FIGURES.items():
        pattern = re.compile(rf"Рисунок\s+{re.escape(num)}\s*[–\-]")
        cap_idx = None
        for i, p in enumerate(paras):
            if p.text.strip() and pattern.search(p.text):
                cap_idx = i
                break
        if cap_idx is None:
            print(f"Подпись рисунка {num} не найдена", file=sys.stderr)
            continue

        img_idx = None
        for j in range(cap_idx - 1, max(cap_idx - 5, -1), -1):
            if _has_image(paras[j]):
                img_idx = j
                break
        if img_idx is None:
            print(f"Изображение для рисунка {num} не найдено", file=sys.stderr)
            continue

        image_path = SCREENSHOTS / filename
        _replace_image_paragraph(paras[img_idx], image_path)
        paras[cap_idx].text = new_caption
        replaced += 1
        print(f"Заменён рисунок {num}: {filename}")

    if replaced == 0:
        return 1

    doc.save(str(doc_path))
    print(f"Сохранено: {doc_path} ({replaced} рисунков)")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCX
    raise SystemExit(patch(target))
