"""Critiquer — проверка качества и соответствия требованиям."""

from __future__ import annotations

from backend.domain.document.coursework_draft import coursework_draft_issues
from backend.domain.workflow.clarification import detect_critiquer_clarification
from backend.domain.workflow.revision_limit import effective_max_revisions
from backend.domain.workflow.work_profile import writer_uses_coursework_prompt
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.text_utils import join_texts
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import CRITIQUE_PROMPT

_MIN_LAB_DRAFT_CHARS = 80
_CITATION_ISSUE_MARKERS = (
    "ссыл",
    "источник",
    "год издания",
    "гост",
    "библиог",
    "[n]",
)


def _mostly_citation_issues(issues: list[str]) -> bool:
    if not issues:
        return False
    return all(any(m in issue.lower() for m in _CITATION_ISSUE_MARKERS) for issue in issues)


def _code_status(state: WorkState) -> str:
    if not state.get("needs_code"):
        return "не требуется"
    if state.get("code_run_success"):
        return "запущен успешно"
    if state.get("code_run_done"):
        return "запуск с ошибкой"
    if state.get("code_generated"):
        return "сгенерирован, не запускался"
    return "отсутствует"


def _build_status(state: WorkState) -> str:
    if state.get("output_docx_path"):
        return f"собран: {state['output_docx_path']}"
    return "не собран"


def _finalize_at_revision_limit(*, coursework: bool, draft: str, lab_short: bool, state: WorkState) -> dict:
    """Stop the loop without pretending a thin draft is cleanly APPROVED."""
    if coursework:
        leftover = coursework_draft_issues(
            draft,
            work_brief=state.get("work_brief"),
            methodical_text=str(state.get("methodical_text") or ""),
        )
        if leftover:
            return {
                "critique_notes": (
                    "FINALIZED — лимит ревизий; остались замечания по объёму/полноте: "
                    + "; ".join(leftover)
                ),
                "critique_rerun": "",
            }
    elif lab_short:
        return {
            "critique_notes": (
                "FINALIZED — лимит ревизий; черновик лабораторной всё ещё короткий."
            ),
            "critique_rerun": "",
        }
    return {
        "critique_notes": "APPROVED — лимит ревизий, работа финализирована.",
        "critique_rerun": "",
    }


def critiquer_node(state: WorkState) -> dict:
    draft = state.get("content_draft", "") or ""
    revision = int(state.get("revision_number") or 0)
    max_revisions = effective_max_revisions(state)
    coursework = writer_uses_coursework_prompt(dict(state))
    lab_short = (not coursework) and len(draft.strip()) < _MIN_LAB_DRAFT_CHARS

    # Short / incomplete drafts must not be rubber-stamped.
    if coursework:
        issues = coursework_draft_issues(
            draft,
            work_brief=state.get("work_brief"),
            methodical_text=str(state.get("methodical_text") or ""),
        )
        if issues and revision < max_revisions:
            notes = "Черновик курсовой неполный: " + "; ".join(issues)
            rerun = "bibliography_verifier" if _mostly_citation_issues(issues) else "writer"
            return {
                "critique_notes": notes,
                "critique_rerun": rerun,
            }
    elif lab_short and revision < max_revisions:
        return {
            "critique_notes": (
                f"Черновик слишком короткий ({len(draft.strip())} символов) — "
                "нужна доработка Writer."
            ),
            "critique_rerun": "writer",
        }

    if revision >= max_revisions:
        return _finalize_at_revision_limit(
            coursework=coursework,
            draft=draft,
            lab_short=lab_short,
            state=state,
        )

    tool_log = join_texts(state.get("tool_log") or [], sep="\n")[:2000]

    llm = get_llm(temperature=0.2)
    prompt = CRITIQUE_PROMPT.format(
        work_type=state.get("work_type", "lab"),
        requirements=state.get("requirements", ""),
        structure_outline=state.get("structure_outline", ""),
        work_brief=(state.get("work_brief") or "")[:3000] or "(нет)",
        variant_task_text=(
            state.get("variant_task_text") or state.get("assignment_variant") or "не указан"
        )[:2000],
        code_status=_code_status(state),
        build_status=_build_status(state),
        content_draft=draft[:12000],
        tool_log=tool_log or "(пусто)",
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}

    if data:
        approved = bool(data.get("approved"))
        notes = str(data.get("notes") or "").strip()
        rerun = str(data.get("rerun") or "none").strip().lower()
        if not approved and not state.get("code_run_success") and state.get("needs_code"):
            rerun = "coder_gen"
        # Domain guard: LLM must not approve incomplete coursework.
        if approved and coursework:
            issues = coursework_draft_issues(
                draft,
                work_brief=state.get("work_brief"),
                methodical_text=str(state.get("methodical_text") or ""),
            )
            if issues and revision < max_revisions:
                approved = False
                notes = (notes + " ").strip() + "Дополнительно: " + "; ".join(issues)
                rerun = "writer"
        if approved:
            result = {"critique_notes": notes or "APPROVED", "critique_rerun": ""}
        else:
            result = {
                "critique_notes": notes or raw[:2000] or "Требуются правки",
                "critique_rerun": rerun if rerun not in ("none", "") else "writer",
            }
        clar_notes = result.get("critique_notes", "")
        result.update(
            gate_after_llm(
                state,
                "critiquer",
                data,
                heuristic=lambda s, _: detect_critiquer_clarification(s, clar_notes),
            )
        )
        return result

    critique = raw or ""
    if critique and "APPROVED" in critique.upper():
        leftover = (
            coursework_draft_issues(
                draft,
                work_brief=state.get("work_brief"),
                methodical_text=str(state.get("methodical_text") or ""),
            )
            if coursework
            else []
        )
        if leftover and revision < max_revisions:
            result = {
                "critique_notes": "Требуется доработка объёма курсовой.",
                "critique_rerun": "writer",
            }
        else:
            result = {"critique_notes": critique, "critique_rerun": ""}
    else:
        result = {
            "critique_notes": critique or "Требуются правки",
            "critique_rerun": "writer",
        }
    clar_notes = result.get("critique_notes", "")
    result.update(
        gate_after_llm(
            state,
            "critiquer",
            {},
            heuristic=lambda s, _: detect_critiquer_clarification(s, clar_notes),
        )
    )
    return result
