"""Очистка исходников от текста отчёта и данных студента (без зависимостей от code_tools)."""

from __future__ import annotations

import re

_HTML_FOOTER = re.compile(
    r"<footer\b[^>]*>.*?(?:выполнил|проверил|студент\s+гр\.?).*?</footer>",
    re.I | re.S,
)
_HTML_CREDIT_LINE = re.compile(
    r"<p\b[^>]*>\s*(?:Выполнил|Проверила?|Проверил)\s*:.+?</p>",
    re.I | re.S,
)
_PLAIN_CREDIT = re.compile(
    r"^\s*(?:Выполнил|Проверила?|Проверил)\s*:.+$",
    re.I | re.M,
)

_LAB_REPORT_MARKERS = (
    "теоретические сведения",
    "цель работы",
    "индивидуальное задание",
    "лабораторная работа",
    "методические указания",
    "министерство образования",
    "бгуир",
    "выводы",
    "заключение",
)

_REPORT_HEADING = re.compile(
    r"<h[1-6][^>]*>\s*[^<]*(?:"
    r"теоретические\s+сведения|цель\s+работы|лабораторная\s+работа|"
    r"индивидуальное\s+задание|выводы|заключение"
    r")[^<]*</h[1-6]>[\s\S]*?(?=<h[1-6]\b|</body>|$)",
    re.I,
)


def _html_visible_text(content: str) -> str:
    text = re.sub(r"<!--[\s\S]*?-->", " ", content)
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def contains_lab_report_text(content: str) -> bool:
    """Текст отчёта (теория, цель, задание) — не должен быть в исходниках."""
    sample = _html_visible_text(content) if "<" in (content or "") else (content or "").lower()
    if not sample:
        return False
    hits = sum(1 for marker in _LAB_REPORT_MARKERS if marker in sample)
    if hits >= 2:
        return True
    return "теоретические сведения" in sample and "цель работы" in sample


def extract_app_only_html(content: str) -> str:
    """Оставить только интерфейс приложения, если HTML по ошибке содержит текст отчёта."""
    if not content or not contains_lab_report_text(content):
        return content

    forms = re.findall(r"<form\b[\s\S]*?</form>", content, flags=re.I)
    head_match = re.search(r"<head\b[\s\S]*?</head>", content, flags=re.I)
    head = head_match.group(0) if head_match else (
        '<head>\n  <meta charset="UTF-8">\n  <title>Приложение</title>\n</head>'
    )
    if forms:
        body = "\n".join(forms)
        scripts = re.findall(r"<script\b[\s\S]*?</script>", content, flags=re.I)
        body += "\n" + "\n".join(scripts) if scripts else ""
        return (
            "<!DOCTYPE html>\n<html lang=\"ru\">\n"
            f"{head}\n<body>\n{body}\n</body>\n</html>"
        )

    text = _REPORT_HEADING.sub("", content)
    for marker in _LAB_REPORT_MARKERS:
        text = re.sub(
            rf"<(?:p|div|section|article)\b[^>]*>[\s\S]*?{re.escape(marker)}[\s\S]*?</(?:p|div|section|article)>",
            "",
            text,
            flags=re.I,
        )
    return text


def sanitize_html_source(content: str) -> str:
    text = _HTML_FOOTER.sub("", content)
    text = _HTML_CREDIT_LINE.sub("", text)
    text = re.sub(r"<footer\b[^>]*>\s*</footer>", "", text, flags=re.I)
    return extract_app_only_html(text)


def sanitize_plain_source(content: str) -> str:
    """Убрать абзацы отчёта из исходников не-HTML."""
    if not content or not contains_lab_report_text(content):
        return _PLAIN_CREDIT.sub("", content)
    lines: list[str] = []
    skip = False
    for line in content.splitlines():
        lower = line.strip().lower()
        if any(marker in lower for marker in _LAB_REPORT_MARKERS[:4]):
            skip = True
            continue
        if skip and not line.strip():
            skip = False
            continue
        if skip:
            continue
        lines.append(line)
    return _PLAIN_CREDIT.sub("", "\n".join(lines))


def apply_source_sanitize(files: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for name, raw in files.items():
        if not isinstance(raw, str):
            cleaned[name] = raw
            continue
        lower_name = name.lower()
        if lower_name.endswith((".html", ".htm")):
            cleaned[name] = sanitize_html_source(raw)
        elif lower_name.endswith((".js", ".css", ".py", ".java", ".cpp", ".cc", ".c", ".cs")):
            cleaned[name] = sanitize_plain_source(_PLAIN_CREDIT.sub("", raw))
        else:
            cleaned[name] = raw
    return cleaned
