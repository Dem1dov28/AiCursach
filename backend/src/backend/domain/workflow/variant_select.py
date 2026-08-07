"""Выбор варианта задания из текста с несколькими вариантами."""

from __future__ import annotations

import re


def _variant_number(variant: str) -> str | None:
    m = re.search(r"\d+", (variant or "").strip())
    return m.group(0) if m else None


def _collect_matches(text: str, num: str) -> list[tuple[int, int, str, str]]:
    """(приоритет, длина, блок, имя_шаблона)"""
    escaped = re.escape(num)
    n = int(num)
    next_num = str(n + 1)
    flags = re.IGNORECASE | re.DOTALL
    patterns: list[tuple[int, str, str]] = [
        # 7. Текст ... до 8. (типичный список заданий БГУИР)
        (
            100,
            "numbered_dot",
            rf"(?is)(?:^|\n)\s*{escaped}\.\s+.+?(?=(?:^|\n)\s*{re.escape(next_num)}\.\s+|\Z)",
        ),
        # 7. до следующего пункта с любым номером
        (
            95,
            "numbered_any",
            rf"(?is)(?:^|\n)\s*{escaped}\.\s+.+?(?=(?:^|\n)\s*\d+\.\s+|\Z)",
        ),
        # Вариант 7: / Вариант 7.
        (
            85,
            "variant_label",
            rf"(?is)(?:^|\n)\s*вариант\s*№?\s*{escaped}\s*[.:]?\s*.+?(?=(?:^|\n)\s*вариант\s*№?\s*\d+\b|\Z)",
        ),
        # Задание 7 / Задание №7
        (
            80,
            "task_label",
            rf"(?is)(?:^|\n)\s*задание\s*№?\s*{escaped}\b[^\n]*\n.+?(?=(?:^|\n)\s*(?:задание|вариант)\s*№?\s*\d+\b|\Z)",
        ),
        # 7 вариант
        (
            75,
            "num_first",
            rf"(?is)(?:^|\n)\s*{escaped}\s*[-–—]?\s*вариант\b.+?(?=(?:^|\n)\s*\d+\s*[-–—]?\s*вариант\b|\Z)",
        ),
        # Строка «7.» без следующего номера (конец документа)
        (
            70,
            "numbered_tail",
            rf"(?is)(?:^|\n)\s*{escaped}\.\s+.+$",
        ),
    ]

    found: list[tuple[int, int, str, str]] = []
    for priority, name, pattern in patterns:
        match = re.search(pattern, text, flags)
        if not match:
            continue
        block = match.group(0).strip()
        if len(block) >= 15:
            found.append((priority, len(block), block, name))
    return found


def _section_end_pattern() -> str:
    return (
        r"(?=(?:^|\n)\s*(?:"
        r"контрольные\s+вопросы|"
        r"список\s+(?:рекомендуемой\s+)?литературы|"
        r"литература|"
        r"приложение|"
        r"заключение|"
        r"требования\s+к\s+(?:оформлению\s+)?отч|"
        r"ход\s+выполнения"
        r")\b|\Z)"
    )


def extract_individual_task(assignment_text: str, variant: str = "") -> str:
    """Блок «Индивидуальное задание» — частый формат лабораторных БГУИР без нумерации 1..N."""
    text = (assignment_text or "").strip()
    if not text:
        return ""

    num = _variant_number(variant) if variant else None
    flags = re.IGNORECASE | re.DOTALL
    end = _section_end_pattern()

    if num:
        labeled = re.search(
            rf"(?is)(?:^|\n)\s*индивидуальное\s+задание\s*"
            rf"\(\s*вариант\s*№?\s*{re.escape(num)}\s*\)\s*[.:]?\s*.+?{end}",
            text,
            flags,
        )
        if labeled:
            return labeled.group(0).strip()

    generic = re.search(
        rf"(?is)(?:^|\n)\s*индивидуальное\s+задание\s*[.:]?\s*.+?{end}",
        text,
        flags,
    )
    if not generic:
        return ""

    block = generic.group(0).strip()
    if num:
        inner = extract_variant_exact(block, variant)
        if inner and inner != block:
            return f"Индивидуальное задание (вариант {variant})\n\n{inner.strip()}"
    return block


def extract_variant_exact(assignment_text: str, variant: str) -> str:
    """Вернуть только найденный блок варианта или пустую строку."""
    text = (assignment_text or "").strip()
    variant = (variant or "").strip()
    if not text or not variant:
        return ""

    num = _variant_number(variant)
    if not num:
        return ""

    matches = _collect_matches(text, num)
    if not matches:
        return ""

    # При одинаковом приоритете берём более короткий блок — меньше риск
    # захватить соседние варианты из OCR/шумного текста.
    matches.sort(key=lambda item: (-item[0], item[1]))
    return matches[0][2]


def apply_variant_selection(full_text: str, variant: str) -> str:
    """Оставить в тексте только выбранный вариант."""
    text = (full_text or "").strip()
    variant = (variant or "").strip()
    if not text or not variant:
        return text

    num = _variant_number(variant)
    if not num:
        return text

    block = extract_variant_exact(text, variant)
    if block:
        return f"[Выбран вариант {variant}]\n\n{block}"

    return (
        f"=== ВАЖНО: выполнять ТОЛЬКО вариант {variant} ===\n"
        f"Игнорируй все остальные варианты и примеры с другими номерами.\n\n"
        f"{text}"
    )


def extract_variant_for_state(assignment_text: str, variant: str) -> str:
    """Текст конкретного варианта."""
    text = (assignment_text or "").strip()
    variant = (variant or "").strip()
    if not text:
        return ""

    if variant:
        block = extract_variant_exact(text, variant)
        if block:
            return block

    individual = extract_individual_task(text, variant)
    if individual:
        return individual

    if not variant:
        return extract_individual_task(text, "")

    return ""


def _strip_other_variants(text: str, keep_num: str | None) -> str:
    """Убрать из текста блоки чужих вариантов, оставить общую часть."""
    result = text
    for i in range(1, 31):
        num = str(i)
        if keep_num and num == keep_num:
            continue
        block = extract_variant_exact(result, num)
        if block:
            result = result.replace(block, "\n")
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def extract_general_requirements(assignment_text: str, variant: str = "") -> str:
    """Общие требования: всё задание без блоков других вариантов."""
    text = (assignment_text or "").strip()
    if not text:
        return ""

    keep = _variant_number(variant) if variant else None
    general = _strip_other_variants(text, keep)

    # Если после удаления вариантов остался только наш вариант — убрать и его
    if keep:
        own = extract_variant_exact(text, keep)
        if own and general == own:
            general = _strip_other_variants(text, None)
            if own:
                general = general.replace(own, "").strip()

    if keep:
        own = extract_variant_exact(text, keep)
        if own and own in general:
            general = general.replace(own, "").strip()

    individual = extract_individual_task(text, variant) or extract_individual_task(text, "")
    if individual and individual in general:
        general = general.replace(individual, "").strip()

    return re.sub(r"\n{3,}", "\n\n", general).strip()


def build_assignment_context(
    assignment_text: str,
    *,
    variant: str = "",
    methodical_text: str = "",
) -> dict[str, str]:
    """Разделить задание на общие требования и конкретный вариант для агентов."""
    full = (assignment_text or "").strip()
    variant = (variant or "").strip()
    methodical = (methodical_text or "").strip()

    variant_task = extract_variant_for_state(full, variant) if variant else ""
    general = extract_general_requirements(full, variant) if variant else full

    sections: list[str] = []
    if methodical:
        sections.append(f"=== Методичка ===\n{methodical}")
    if general:
        sections.append(f"=== Общие требования к работе ===\n{general}")
    if variant_task:
        sections.append(f"=== Вариант {variant} (выполнять именно это) ===\n{variant_task}")
    elif variant:
        sections.append(
            f"=== Вариант {variant} ===\n"
            "Текст варианта не выделен автоматически — найди его в полном задании."
        )

    combined = "\n\n".join(sections) if sections else full

    return {
        "assignment_full_text": full,
        "general_requirements_text": general,
        "variant_task_text": variant_task,
        "assignment_text": combined,
    }
