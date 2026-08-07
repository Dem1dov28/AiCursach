"""Тесты очистки исходников от текста отчёта."""

from backend.infrastructure.adapters.source_sanitize import (
    contains_lab_report_text,
    extract_app_only_html,
    apply_source_sanitize,
)


SAMPLE_REPORT_HTML = """<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Lab</title>
<link rel="stylesheet" href="../css/style.css"></head>
<body>
<h1>Лабораторная работа</h1>
<h2>Цель работы</h2>
<p>Изучить JavaScript и HTML-формы.</p>
<h2>Теоретические сведения</h2>
<p>JavaScript используется для клиентской логики.</p>
<h2>Форма регистрации</h2>
<form id="reg">
  <label>Имя <input name="name"></label>
  <button type="submit">Отправить</button>
</form>
<script src="../js/script.js"></script>
</body>
</html>
"""


def test_contains_lab_report_text():
    assert contains_lab_report_text(SAMPLE_REPORT_HTML)


def test_extract_app_only_html():
    cleaned = extract_app_only_html(SAMPLE_REPORT_HTML)
    assert "<form" in cleaned.lower()
    assert "теоретические сведения" not in cleaned.lower()
    assert "цель работы" not in cleaned.lower()


def test_sanitize_code_files_strips_report():
    files = apply_source_sanitize({"html/index.html": SAMPLE_REPORT_HTML})
    html = files["html/index.html"].lower()
    assert "<form" in html
    assert "теоретические сведения" not in html
