"""Tests for discipline-specific outlines and methods chapter helpers."""

from backend.domain.document.discipline_outline import (
    default_chapter_titles,
    draft_has_methods_chapter,
    ensure_methods_in_outline,
    outline_template_for_discipline,
    text_has_methods_chapter,
)
from backend.domain.document.coursework_draft import (
    coursework_draft_issues,
    outline_titles_from_structure,
)


def test_economics_default_chapters_not_it_shaped():
    titles = default_chapter_titles("economics")
    blob = " ".join(titles).lower()
    assert "метод" in blob
    assert "проектирован" not in blob
    assert "реализац" not in blob
    assert "расч" in blob or "экономич" in blob


def test_programming_defaults_include_methods():
    titles = default_chapter_titles("programming")
    assert any("МЕТОД" in t.upper() for t in titles)


def test_outline_fallback_uses_discipline():
    titles = outline_titles_from_structure("", discipline="economics")
    assert len(titles) >= 3
    assert any("метод" in t.lower() for t in titles)
    assert not any("проектирован" in t.lower() for t in titles)


def test_ensure_methods_injects_when_missing():
    outline = "Введение\n1 Теоретические основы\n3 Анализ данных\nЗаключение"
    fixed = ensure_methods_in_outline(outline, "economics")
    assert text_has_methods_chapter(fixed)
    assert "методик" in fixed.lower() or "метод" in fixed.lower()


def test_ensure_methods_noop_when_present():
    outline = "Введение\n1 Анализ\n2 Методы и средства\n3 Реализация"
    assert ensure_methods_in_outline(outline, "programming") == outline


def test_ensure_methods_empty_uses_template():
    fixed = ensure_methods_in_outline("", "management")
    assert "метод" in fixed.lower()
    assert fixed == outline_template_for_discipline("management")


def test_draft_methods_detection():
    assert draft_has_methods_chapter(
        {"sections": [{"title": "2 МЕТОДЫ ИССЛЕДОВАНИЯ", "paragraphs": ["x"]}]}
    )
    assert not draft_has_methods_chapter(
        {"sections": [{"title": "1 АНАЛИЗ", "paragraphs": ["x"]}]}
    )


def test_coursework_issues_without_methods_chapter():
    # Fat draft without methods title → only methods issue (and maybe citations ok).
    para = (
        "Связный академический абзац курсовой работы БГУИР достаточной длины для проверки. "
        * 2
    ).strip()
    draft = {
        "intro": [para + " [1]", para + " [2]", para + " [3]"],
        "sections": [
            {"title": "1 АНАЛИЗ", "paragraphs": [para, para, para, para]},
            {"title": "2 ПРОЕКТИРОВАНИЕ", "paragraphs": [para + " [4]", para, para, para]},
            {
                "title": "3 РЕАЛИЗАЦИЯ",
                "paragraphs": [para + " [5]", para + " [6]", para + " [7]", para + " [8]"],
            },
        ],
        "conclusion": [para, para],
        "sources": [
            f"[{n}] Автор {n}. Книга {n}. — Минск: БГУИР, 202{n % 10}." for n in range(1, 9)
        ],
    }
    issues = coursework_draft_issues(draft)
    assert any("метод" in issue.lower() for issue in issues)
