"""Тесты выделения варианта и индивидуального задания."""

from backend.domain.workflow.variant_select import (
    build_assignment_context,
    extract_general_requirements,
    extract_individual_task,
    extract_variant_for_state,
)


SAMPLE_LAB = """
Цель работы
Изучить JavaScript и HTML-формы.

Теоретические сведения
JavaScript используется для клиентской логики.

Индивидуальное задание
Создайте веб-страницу с формой регистрации пользователя.
Поля: имя, фамилия, email, пароль, подтверждение пароля.
Проверка JavaScript: все поля заполнены, email корректен, пароли совпадают.
Сохраните данные в localStorage.
Кнопка открывает новое окно с приветствием.

Контрольные вопросы
1. Что такое DOM?
"""


def test_extract_individual_task():
    block = extract_individual_task(SAMPLE_LAB, "")
    assert "регистрации" in block.lower()
    assert "localstorage" in block.lower()
    assert "контрольные вопросы" not in block.lower()


def test_variant_for_state_falls_back_to_individual():
    block = extract_variant_for_state(SAMPLE_LAB, "7")
    assert "регистрации" in block.lower()


def test_general_requirements_exclude_individual():
    general = extract_general_requirements(SAMPLE_LAB, "7")
    assert "регистрации" not in general.lower()
    assert "цель работы" in general.lower()


def test_build_assignment_context_splits_sections():
    ctx = build_assignment_context(SAMPLE_LAB, variant="7")
    assert "регистрации" in ctx["variant_task_text"].lower()
    assert "регистрации" not in ctx["general_requirements_text"].lower()
    assert "регистрации" in ctx["assignment_text"].lower()
