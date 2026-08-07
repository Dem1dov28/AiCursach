"""Tests for coursework draft domain helpers."""

from backend.domain.document.coursework_draft import (
    MIN_BODY_CHARS,
    MIN_SOURCES,
    coursework_draft_issues,
    draft_body_char_count,
    outline_titles_from_structure,
    parse_coursework_draft,
)


def _para(seed: str = "текст", *, citations: str = "") -> str:
    # ≥80 chars for substantial paragraph quota
    base = (
        f"{seed} курсовой работы БГУИР с достаточным объёмом связного академического текста. "
        * 2
    )
    return (base + " " + citations).strip()


def _ok_draft() -> dict:
    return {
        "intro": [
            _para("Актуальность", citations="[1]"),
            _para("Цель работы", citations="[2]"),
            _para("Задачи и методы", citations="[3]"),
        ],
        "sections": [
            {
                "title": "1 АНАЛИЗ",
                "paragraphs": [
                    _para("Анализ", citations="[1]"),
                    _para("Сравнение", citations="[2]"),
                    _para("Вывод по анализу"),
                    _para("Итог главы 1"),
                ],
            },
            {
                "title": "2 МЕТОДЫ И СРЕДСТВА",
                "paragraphs": [
                    _para("Методика", citations="[3]"),
                    _para("Инструменты", citations="[4]"),
                    _para("Этапы", citations="[5]"),
                    _para("Критерии", citations="[6]"),
                ],
            },
            {
                "title": "3 РЕАЛИЗ",
                "paragraphs": [
                    _para("Реализация", citations="[1]"),
                    _para("Тесты", citations="[2]"),
                    _para("Результаты", citations="[7]"),
                    _para("Обсуждение", citations="[8]"),
                ],
            },
        ],
        "conclusion": [
            _para("Заключение по задачам"),
            _para("Практическая значимость"),
        ],
        "sources": [
            f"[{n}] Автор {n}. Название работы {n}. — Минск: БГУИР, 202{n % 10}."
            for n in range(1, MIN_SOURCES + 1)
        ],
    }


def test_outline_titles_from_numbered_structure():
    outline = """
1. Анализ предметной области
2. Проектирование системы
3. Реализация и тестирование
"""
    titles = outline_titles_from_structure(outline)
    assert len(titles) == 3
    assert "Анализ" in titles[0]


def test_outline_fallback_when_empty():
    titles = outline_titles_from_structure("")
    assert len(titles) >= 3
    assert any("метод" in t.lower() for t in titles)


def test_coursework_draft_issues_on_thin_draft():
    draft = {
        "intro": ["одно предложение"],
        "sections": [{"title": "1", "paragraphs": ["a"]}],
        "conclusion": ["итог"],
        "sources": ["[1] x"],
    }
    issues = coursework_draft_issues(draft)
    assert issues
    assert any("глав" in issue for issue in issues)
    assert any("источник" in issue for issue in issues)


def test_coursework_draft_ok_enough():
    draft = _ok_draft()
    assert draft_body_char_count(draft) >= MIN_BODY_CHARS
    assert coursework_draft_issues(draft) == []


def test_volume_floors_reject_short_paragraphs():
    draft = _ok_draft()
    draft["sections"][0]["paragraphs"] = ["коротко", "ещё", "и ещё", "и ещё"]
    issues = coursework_draft_issues(draft)
    assert any("абзац" in issue for issue in issues)


def test_parse_invalid_json():
    data = parse_coursework_draft("not-json")
    assert data.get("raw_text") == "not-json"
