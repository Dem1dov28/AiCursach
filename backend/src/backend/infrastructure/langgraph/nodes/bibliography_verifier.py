"""Bibliography Verifier — проверка и исправление списка источников."""

from __future__ import annotations

import json

from backend.core.config import get_config
from backend.domain.quality.analyze_draft import analyze_draft_quality
from backend.infrastructure.adapters.crossref_client import fetch_crossref_title
from backend.domain.workflow.clarification import detect_bibliography_clarification
from backend.domain.workflow.work_profile import writer_uses_coursework_prompt
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.text_utils import join_texts
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import BIBLIOGRAPHY_FIX_PROMPT


def _context_texts(state: WorkState) -> list[str]:
    texts = [
        state.get("methodical_text") or "",
        state.get("assignment_text") or "",
        state.get("general_requirements_text") or "",
    ]
    texts.extend(state.get("research_findings") or [])
    return [text for text in texts if text.strip()]


def _issues_summary(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "(проблем не найдено)"
    return "\n".join(f"- {item['citation']}: {item['reason']}" for item in issues)


def bibliography_verifier_node(state: WorkState) -> dict:
    if not state.get("enable_bibliography_verifier", True):
        result = {
            "bibliography_verified": True,
            "citation_issues": state.get("citation_issues") or [],
            "tool_log": ["Bibliography: проверка отключена в настройках — пропуск"],
        }
        result.update(gate_after_llm(state, "bibliography_verifier", {}))
        return result

    draft = state.get("content_draft", "") or ""
    work_type = state.get("work_type", "auto")
    context = _context_texts(state)
    coursework = writer_uses_coursework_prompt(dict(state))

    quality = analyze_draft_quality(
        draft,
        work_type=work_type,
        context_texts=context,
        resolve_doi_title=fetch_crossref_title,
        verify_doi=get_config().crossref_verify,
        require_in_text_citations=coursework,
    )
    issues = quality.get("citation_issues") or []

    if not draft.strip():
        result = {
            "bibliography_verified": True,
            "citation_issues": [],
            "tool_log": ["Bibliography: черновик пуст — пропуск"],
        }
        result.update(gate_after_llm(state, "bibliography_verifier", {}))
        return result

    if not issues:
        result = {
            "bibliography_verified": True,
            "citation_issues": [],
            "tool_log": ["Bibliography: источники проверены, замечаний нет"],
        }
        result.update(gate_after_llm(state, "bibliography_verifier", {}))
        return result

    research = join_texts(state.get("research_findings") or [], sep="\n\n")[:6000]
    llm = get_llm(temperature=0.2)
    prompt = BIBLIOGRAPHY_FIX_PROMPT.format(
        topic=state.get("topic", ""),
        requirements=(state.get("requirements") or "")[:3000],
        issues_text=_issues_summary(issues),
        research_findings=research or "(исследование не выполнялось)",
        content_draft=draft[:12000],
    )
    raw = llm_text(llm, prompt)
    fixed = parse_json_from_llm(raw)
    logs = [f"Bibliography: исправление по {len(issues)} замечаниям"]

    if isinstance(fixed, dict):
        new_draft = json.dumps(fixed, ensure_ascii=False, indent=2)
        recheck = analyze_draft_quality(
            new_draft,
            work_type=work_type,
            context_texts=context,
            resolve_doi_title=fetch_crossref_title,
            verify_doi=get_config().crossref_verify,
            require_in_text_citations=coursework,
        )
        remaining = recheck.get("citation_issues") or []
        verified = len(remaining) == 0
        attempts = int(state.get("bibliography_attempts") or 0)
        if not verified:
            attempts += 1
        result = {
            "content_draft": new_draft,
            "bibliography_verified": verified,
            "bibliography_attempts": attempts if not verified else 0,
            "citation_issues": remaining,
            "tool_log": logs + [f"Bibliography: осталось замечаний — {len(remaining)}"],
        }
        remaining_count = len(remaining)
        result.update(
            gate_after_llm(
                state,
                "bibliography_verifier",
                fixed,
                heuristic=lambda s, d, n=remaining_count: detect_bibliography_clarification(s, n),
            )
        )
        return result

    attempts = int(state.get("bibliography_attempts") or 0) + 1
    result = {
        "bibliography_verified": False,
        "bibliography_attempts": attempts,
        "citation_issues": issues,
        "tool_log": logs + ["Bibliography: LLM не вернул JSON — оставлен исходный черновик"],
    }
    issue_count = len(issues)
    result.update(
        gate_after_llm(
            state,
            "bibliography_verifier",
            {},
            heuristic=lambda s, d, n=issue_count: detect_bibliography_clarification(s, n),
        )
    )
    return result
