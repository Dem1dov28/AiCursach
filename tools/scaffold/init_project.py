#!/usr/bin/env python3
"""Создать каркас новой курсовой/лабораторной в projects/<имя>."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS = REPO_ROOT / "data" / "projects"

BUILD_REPORT = '''#!/usr/bin/env python3
"""Сборка пояснительной записки. Заполните content.py и config.yaml."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _parent in Path(__file__).resolve().parents:
    if (_parent / "tools" / "diagrams" / "idef0_draw.py").is_file():
        ROOT = _parent
        break
sys.path.insert(0, str(ROOT))

from docx import Document

from tools.common.docx_stp import (
    add_page_number,
    appendix_start,
    body,
    h1,
    h1_center,
    setup_margins,
)
from tools.common.referat import ReferatConfig, append_referat_body, insert_antiplagiat_before_section1
from tools.common.report_title import build_title_page, build_toc
import content  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "Отчет" / "Пояснительная_записка.docx"
CFG = content.REFERAT


def main():
    doc = Document()
    setup_margins(doc.sections[0])
    build_title_page(
        doc,
        content.TOPIC,
        doc_code=content.DOC_CODE,
        discipline=content.DISCIPLINE,
        variant=content.VARIANT,
        student_group=content.GROUP,
        student_name=content.STUDENT,
        teacher_name=content.TEACHER,
        kind="psp",
    )
    doc.add_page_break()
    h1_center(doc, "РЕФЕРАТ")
    append_referat_body(doc.paragraphs[-1], CFG)
    doc.add_page_break()
    h1_center(doc, "СОДЕРЖАНИЕ")
    build_toc(doc, content.TOC_ENTRIES)
    doc.add_page_break()
    h1_center(doc, "ВВЕДЕНИЕ")
    for p in content.INTRO:
        body(doc, p)
    insert_antiplagiat_before_section1(doc, CFG)
    for section_title, paragraphs in content.SECTIONS:
        doc.add_page_break()
        h1(doc, section_title)
        for p in paragraphs:
            body(doc, p)
    doc.add_page_break()
    h1_center(doc, "ЗАКЛЮЧЕНИЕ")
    for p in content.CONCLUSION:
        body(doc, p)
    doc.add_page_break()
    h1_center(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
    for i, src in enumerate(content.SOURCES, 1):
        body(doc, f"[{i}] {src}", indent=False)
    add_page_number(doc.sections[0])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Сохранено: {OUT}")
    print("Далее: python3 tools/diagrams/render_diagrams.py --puml ...")
    print("       python3 tools/common/update_toc.py", OUT)
    print("       python3 tools/common/patch_antiplagiat.py", OUT, "-s скриншот.png")


if __name__ == "__main__":
    main()
'''

CONTENT_PY = '''"""Тексты пояснительной записки — редактируйте под новую тему."""
from tools.common.referat import ReferatConfig

TOPIC = "«Название темы курсового проекта»"
DOC_CODE = "БГУИР КП 6-05-0611-01 010 ПЗ"
DISCIPLINE = "Программирование сетевых приложений"
VARIANT = 10
GROUP = "473601"
STUDENT = "И. С. Демидов"
TEACHER = "Е.И. Пономарева"

REFERAT = ReferatConfig(
    topic_title="Название темы без кавычек",
    keywords_caps="КЛЮЧЕВОЕ, СЛОВО, JAVA, КЛИЕНТ-СЕРВЕР",
    goal="автоматизация …",
    methodology="системный подход, UML, IDEF0, тестирование",
    results="разработана ИС …",
    tech_stack="Программный продукт разработан на языке Java …",
    application="внедрение в …",
)

TOC_ENTRIES = [
    ("Введение", 0, 5),
    ("1 Анализ предметной области", 0, 7),
    ("2 Проектирование", 0, 12),
    ("Заключение", 0, 20),
    ("Список использованных источников", 0, 21),
    ("Приложение А (обязательное) Листинг программы", 0, 22),
    ("Приложение Б (обязательное) SQL-скрипт", 0, 30),
]

INTRO = [
    "Актуальность темы …",
    "Цель работы — …",
    "Задачи: …",
]

SECTIONS = [
    ("1 АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ", ["Текст раздела 1 …"]),
    ("2 ПРОЕКТИРОВАНИЕ И РАЗРАБОТКА", ["Текст раздела 2 …"]),
]

CONCLUSION = ["В ходе работы …"]

SOURCES = [
    "ГОСТ …",
    "Документация …",
]
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="Имя папки в data/projects/, например MyShop")
    args = ap.parse_args()
    proj = PROJECTS / args.name
    if proj.exists():
        raise SystemExit(f"Уже существует: {proj}")

    dirs = [
        proj / "Отчет",
        proj / "Материалы" / "Диаграммы" / "puml",
        proj / "Материалы" / "Диаграммы" / "png",
        proj / "Материалы" / "Скриншоты",
        proj / "Скрипты",
        proj / "src",
    ]
    for d in dirs:
        d.mkdir(parents=True)

    (proj / "README.md").write_text(
        textwrap.dedent(
            f"""\
            # {args.name}

            1. Заполните `Скрипты/content.py`
            2. `python3 Скрипты/build_report.py`
            3. Диаграммы: `python3 ../../../tools/diagrams/render_diagrams.py --puml Материалы/Диаграммы/puml --out Материалы/Диаграммы/png`
            4. Оглавление: `python3 ../../../tools/common/update_toc.py Отчет/Пояснительная_записка.docx`
            """
        ),
        encoding="utf-8",
    )
    (proj / "Скрипты" / "content.py").write_text(CONTENT_PY, encoding="utf-8")
    (proj / "Скрипты" / "build_report.py").write_text(BUILD_REPORT, encoding="utf-8")
    print(f"Создано: {proj}")


if __name__ == "__main__":
    main()
