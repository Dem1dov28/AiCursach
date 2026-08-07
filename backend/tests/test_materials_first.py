"""Tests for materials classification and work_brief volume targets."""

from backend.domain.document.coursework_draft import coursework_draft_issues
from backend.domain.document.materials_classify import classify_materials, pick_role
from backend.domain.document.work_brief import (
    brief_summary_for_hitl,
    infer_volume_targets_from_methodical,
    merge_volume_targets,
    parse_work_brief,
)


def test_classify_by_filename_roles():
    items = [
        ("задание_вариант5.pdf", "Вариант №5. Выполнить курсовую по теме ИС склада."),
        (
            "пример_курсовой.docx",
            "Введение\n1 Анализ\n2 Методы\n3 Реализация\nЗаключение\n"
            "Список использованных источников\n" + ("текст " * 400),
        ),
        (
            "ГОСТ_7.0.5.pdf",
            "Оформление по ГОСТ 7.0.5-2008. Шрифт Times New Roman 14 пт. "
            "Межстрочный интервал. Титульный лист. Библиографическое описание.",
        ),
    ]
    result = classify_materials(items)
    assert result.roles.get("задание_вариант5.pdf") == "assignment"
    assert result.roles.get("пример_курсовой.docx") == "example"
    assert result.roles.get("ГОСТ_7.0.5.pdf") == "gost_methodical"
    assert "Вариант" in result.assignment_text
    assert "Введение" in result.example_text
    assert "ГОСТ" in result.methodical_text


def test_pick_role_methodical_name():
    role, conf = pick_role("методичка_оформление.docx", "Требования к оформлению работы.")
    assert role == "gost_methodical"
    assert conf >= 0.35


def test_explicit_slots_override_heuristics():
    items = [
        ("file1.txt", "Вариант №1 выполнить задание"),
        ("file2.txt", "Введение Заключение Список использованных источников " + ("x" * 3000)),
    ]
    result = classify_materials(
        items,
        explicit_assignment="ЯВНОЕ ЗАДАНИЕ",
        explicit_methodical="ЯВНАЯ МЕТОДИЧКА ГОСТ",
    )
    assert result.assignment_text == "ЯВНОЕ ЗАДАНИЕ"
    assert result.methodical_text == "ЯВНАЯ МЕТОДИЧКА ГОСТ"


def test_infer_min_sources_from_methodical():
    text = "Список литературы должен содержать не менее 10 источников."
    targets = infer_volume_targets_from_methodical(text)
    assert targets["min_sources"] == 10


def test_coursework_issues_respect_brief_min_sources():
    para = (
        "Связный академический абзац курсовой работы БГУИР достаточной длины для проверки. "
        * 2
    ).strip()
    draft = {
        "intro": [para + " [1]", para + " [2]", para + " [3]"],
        "sections": [
            {"title": "1 АНАЛИЗ", "paragraphs": [para, para, para, para]},
            {"title": "2 МЕТОДЫ", "paragraphs": [para + " [4]", para, para, para]},
            {"title": "3 РЕАЛИЗ", "paragraphs": [para + " [5]", para + " [6]", para, para]},
        ],
        "conclusion": [para, para],
        "sources": [f"[{n}] Author {n}. Book. — 2020." for n in range(1, 9)],
    }
    # Default: 8 sources OK
    assert not any("источник" in i for i in coursework_draft_issues(draft))

    brief = {
        "volume_targets": {"min_sources": 10},
        "from_gost": {},
        "from_example": {},
        "from_assignment": [],
    }
    issues = coursework_draft_issues(draft, work_brief=brief)
    assert any("≥10" in i or "10" in i for i in issues if "источник" in i)


def test_methodical_text_raises_source_floor_without_brief_json():
    para = (
        "Связный академический абзац курсовой работы БГУИР достаточной длины для проверки. "
        * 2
    ).strip()
    draft = {
        "intro": [para + " [1]", para + " [2]", para + " [3]"],
        "sections": [
            {"title": "1 АНАЛИЗ", "paragraphs": [para, para, para, para]},
            {"title": "2 МЕТОДЫ", "paragraphs": [para + " [4]", para, para, para]},
            {
                "title": "3 РЕАЛИЗ",
                "paragraphs": [para + " [5]", para + " [6]", para + " [7]", para + " [8]"],
            },
        ],
        "conclusion": [para, para],
        "sources": [f"[{n}] Author {n}. Book. — 2020." for n in range(1, 9)],
    }
    issues = coursework_draft_issues(
        draft,
        methodical_text="Требуется не менее 12 источников в списке литературы.",
    )
    assert any("12" in i for i in issues)


def test_brief_summary_mentions_structure_source():
    brief = parse_work_brief(
        {
            "structure_source": "example",
            "from_gost": {"bibliography_standard": "ГОСТ 7.0.5-2008"},
            "volume_targets": {"min_sources": 10},
        }
    )
    summary = brief_summary_for_hitl(brief, "1 Анализ\n2 Методы")
    assert "пример" in summary.lower()
    assert "10" in summary


def test_merge_volume_prefers_brief_over_methodical():
    brief = {"volume_targets": {"min_sources": 15}}
    targets = merge_volume_targets(
        brief,
        methodical_text="не менее 10 источников",
    )
    assert targets["min_sources"] == 15
