"""Clarification requests when agents need user input."""

from __future__ import annotations

from typing import Any, Literal

from backend.domain.workflow.autonomy import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    AutonomyLevel,
    normalize_autonomy_level,
)

ClarificationScenario = Literal[
    "structure_fork",
    "missing_data",
    "source_conflict",
    "formatting",
    "ambiguous_task",
    "step_confirm",
    "other",
]


def parse_llm_clarification(data: dict[str, Any]) -> tuple[dict[str, Any] | None, float, bool]:
    """Extract confidence and optional user question from agent LLM JSON."""
    try:
        confidence = float(data.get("confidence", 0.85))
    except (TypeError, ValueError):
        confidence = 0.85
    confidence = max(0.0, min(1.0, confidence))

    explicit = bool(data.get("needs_clarification"))
    raw = data.get("clarification")
    clarification: dict[str, Any] | None = None

    if isinstance(raw, dict):
        question = str(raw.get("question") or "").strip()
        if question:
            options = [
                str(item).strip()
                for item in (raw.get("options") or [])
                if str(item).strip()
            ]
            if not options:
                options = ["Продолжить с выбором агента", "Уточню в свободном поле"]
            clarification = {
                "scenario": raw.get("scenario") or "other",
                "question": question,
                "options": options[:5],
            }
    elif explicit:
        clarification = {
            "scenario": "other",
            "question": "Агент не уверен в деталях. Как поступить?",
            "options": ["Доверяю выбору агента", "Уточню в свободном поле"],
        }

    return clarification, confidence, explicit


def resolve_clarification(
    state: dict[str, Any],
    llm_data: dict[str, Any] | None,
    heuristic: Any | None = None,
) -> tuple[dict[str, Any] | None, float, bool]:
    """Merge LLM-reported doubt with optional rule-based detectors."""
    clarification, confidence, explicit = parse_llm_clarification(llm_data or {})

    if explicit and clarification:
        return clarification, confidence, True

    if heuristic is not None:
        h_clar, h_conf = heuristic(state, llm_data or {})
        if h_clar:
            return h_clar, min(confidence, float(h_conf)), True

    if clarification and confidence < DEFAULT_CONFIDENCE_THRESHOLD:
        return clarification, confidence, False

    return None, confidence, False


def _methodical_text(state: dict[str, Any]) -> str:
    return (state.get("methodical_text") or state.get("general_requirements_text") or "").lower()


def detect_analyzer_clarification(
    state: dict[str, Any], data: dict[str, Any]
) -> tuple[dict[str, Any] | None, float]:
    methodical = _methodical_text(state)
    work_type = state.get("work_type", "lab")
    confidence = float(data.get("confidence", 0.88))

    if work_type == "coursework" and "глава 3" not in methodical and "трет" not in methodical:
        return (
            {
                "scenario": "structure_fork",
                "question": (
                    "В методичке не указан обязательный объём 3-й главы. "
                    "Какой формат практической части выбрать?"
                ),
                "options": [
                    "Стандартные 10 страниц без расширенного кейса",
                    "Расширить до 15 страниц с практическим кейсом",
                ],
            },
            min(confidence, 0.72),
        )
    return None, confidence


def detect_researcher_clarification(state: dict[str, Any]) -> tuple[dict[str, Any] | None, float]:
    topic = (state.get("topic") or "").lower()
    assignment = (state.get("assignment_text") or state.get("variant_task_text") or "").lower()
    blob = f"{topic} {assignment}"
    if any(word in blob for word in ("практич", "кейс", "предприят", "компан", "организац")):
        return (
            {
                "scenario": "missing_data",
                "question": (
                    "Для практической части нужен пример компании. "
                    "Какой источник кейса использовать?"
                ),
                "options": [
                    "Реальный кейс (например, Сбер / Яндекс)",
                    "Вымышленное предприятие «ООО Вектор»",
                ],
            },
            0.68,
        )
    return None, 0.92


def detect_critiquer_clarification(
    state: dict[str, Any], notes: str
) -> tuple[dict[str, Any] | None, float]:
    lowered = notes.lower()
    if any(token in lowered for token in ("автор а", "автор б", "противореч", "conflict")):
        return (
            {
                "scenario": "source_conflict",
                "question": (
                    "Обнаружено противоречие в источниках. "
                    "Какую позицию закрепить в аргументации?"
                ),
                "options": [
                    "Опираться на более новые исследования (позиция A)",
                    "Сохранить нейтральное сравнение обеих позиций",
                ],
            },
            0.74,
        )
    return None, 0.9


def detect_bibliography_clarification(
    _state: dict[str, Any], issue_count: int
) -> tuple[dict[str, Any] | None, float]:
    if issue_count >= 3:
        return (
            {
                "scenario": "source_conflict",
                "question": (
                    f"Осталось {issue_count} проблем с источниками. "
                    "Как поступить со спорными ссылками?"
                ),
                "options": [
                    "Оставить как есть и продолжить",
                    "Удалить сомнительные источники",
                    "Заменить на источники из загруженных материалов",
                ],
            },
            0.66,
        )
    return None, 0.9


def detect_style_clarification(
    _state: dict[str, Any], cliche_count: int
) -> tuple[dict[str, Any] | None, float]:
    if cliche_count >= 4:
        return (
            {
                "scenario": "ambiguous_task",
                "question": (
                    f"Обнаружено {cliche_count} AI-клише. "
                    "Насколько агрессивно полировать стиль?"
                ),
                "options": [
                    "Максимально академично (убрать все клише)",
                    "Умеренно (оставить часть формулировок)",
                    "Минимально (только явные шаблоны)",
                ],
            },
            0.7,
        )
    return None, 0.88


def detect_docx_clarification(state: dict[str, Any]) -> tuple[dict[str, Any] | None, float]:
    methodical = _methodical_text(state)
    has_2008 = "2008" in methodical or "7.05-2008" in methodical
    has_2018 = "2018" in methodical or "7.0.5-2018" in methodical
    if has_2008 and has_2018:
        return (
            {
                "scenario": "formatting",
                "question": "В методичке упомянуты разные редакции ГОСТ. Как оформить список литературы?",
                "options": ["ГОСТ 7.0.5-2008", "ГОСТ 7.0.5-2018"],
            },
            0.7,
        )
    if "гост" in methodical and not has_2008 and not has_2018:
        return (
            {
                "scenario": "formatting",
                "question": "Год стандарта для списка литературы не указан явно. Какой ГОСТ применить?",
                "options": ["ГОСТ 7.0.5-2008", "ГОСТ 7.0.5-2018"],
            },
            0.75,
        )
    return None, 0.95


def default_step_confirmation(agent: str, state: dict[str, Any]) -> dict[str, Any]:
    labels = {
        "analyzer": "Planner",
        "project_init": "ProjectInit",
        "researcher": "Researcher",
        "writer": "Writer",
        "bibliography_verifier": "Bibliography",
        "style_polisher": "StylePolisher",
        "coder_gen": "CoderGen",
        "code_runner": "CodeRunner",
        "diagrammer": "Diagrammer",
        "assets_builder": "Assets",
        "antiplagiat": "Antiplagiat",
        "annex_builder": "Annex",
        "docx_builder": "Formatter",
        "critiquer": "Reviewer",
    }
    name = labels.get(agent, agent)
    topic = state.get("topic") or "работа"
    return {
        "scenario": "step_confirm",
        "question": f"Узел «{name}» завершил этап по теме «{topic}». Продолжить выполнение графа?",
        "options": ["Продолжить без правок", "Нужна корректировка (опишу в поле ниже)"],
    }


def should_request_clarification(
    state: dict[str, Any],
    *,
    agent: str,
    confidence: float,
    clarification: dict[str, Any] | None,
    explicit_request: bool = False,
) -> bool:
    level: AutonomyLevel = normalize_autonomy_level(state.get("autonomy_level"))
    threshold = float(state.get("confidence_threshold") or DEFAULT_CONFIDENCE_THRESHOLD)

    if level == "full_auto":
        return False
    # interactive: pause when agent explicitly doubts or confidence is low
    if explicit_request and clarification is not None:
        return True
    if clarification is None:
        return False
    return confidence < threshold


def build_interrupt_payload(
    *,
    agent: str,
    clarification: dict[str, Any],
    confidence: float,
) -> dict[str, Any]:
    return {
        "type": "clarification",
        "agent": agent,
        "scenario": clarification.get("scenario", "step_confirm"),
        "question": clarification.get("question", ""),
        "options": list(clarification.get("options") or []),
        "confidence": confidence,
    }


def apply_clarification_answer(
    state: dict[str, Any],
    *,
    agent: str,
    clarification: dict[str, Any],
    answer: Any,
) -> dict[str, Any]:
    if isinstance(answer, dict):
        selected = str(answer.get("selected_option") or answer.get("selected") or "")
        custom = str(answer.get("custom_text") or answer.get("custom") or "").strip()
    else:
        selected = str(answer or "")
        custom = ""

    choice = custom or selected
    scenario = clarification.get("scenario", "")
    updates: dict[str, Any] = {
        "awaiting_clarification": False,
        "pending_clarification": {},
        "clarification_log": [
            {
                "agent": agent,
                "scenario": scenario,
                "question": clarification.get("question", ""),
                "answer": choice,
            }
        ],
    }

    if agent == "analyzer" and scenario == "structure_fork":
        suffix = f"\n\n[Уточнение пользователя — структура]: {choice}"
        updates["structure_outline"] = (state.get("structure_outline") or "") + suffix
    elif agent == "researcher" and scenario == "missing_data":
        updates["research_findings"] = [f"[Директива пользователя по кейсу]: {choice}"]
    elif agent == "critiquer" and scenario == "source_conflict":
        updates["critique_notes"] = (
            (state.get("critique_notes") or "") + f"\n[Позиция пользователя]: {choice}"
        )
    elif agent == "docx_builder" and scenario == "formatting":
        updates["requirements"] = (
            (state.get("requirements") or "") + f"\n[ГОСТ по выбору пользователя]: {choice}"
        )
    elif agent == "antiplagiat" and scenario == "missing_data":
        # clarification_log already stores answer; node re-reads skip/recheck
        pass
    elif custom or scenario in ("other", "ambiguous_task"):
        overrides = dict(state.get("prompt_overrides") or {})
        overrides[f"user_directive_{agent}"] = custom or selected or choice
        updates["prompt_overrides"] = overrides
        if agent == "researcher" and choice:
            updates["research_findings"] = [
                *((state.get("research_findings") or [])),
                f"[Уточнение пользователя]: {choice}",
            ]

    return updates


def parse_interrupt_value(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if hasattr(raw, "value"):
        value = raw.value
        return value if isinstance(value, dict) else {"value": value}
    return {}
