"""Writer — генерация контента лабораторной или курсовой."""

from __future__ import annotations

import json
from typing import Any

from backend.domain.document.coursework_draft import (
    MAX_MULTIPASS_SECTIONS,
    merge_coursework_parts,
    outline_titles_from_structure,
    parse_coursework_draft,
)
from backend.domain.workflow.prompt_override import apply_prompt_override
from backend.domain.workflow.work_profile import writer_uses_coursework_prompt
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.lab_code import is_code_listing
from backend.infrastructure.adapters.text_utils import join_texts
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import (
    WRITER_COURSEWORK_PROMPT,
    WRITER_CW_CLOSING_PROMPT,
    WRITER_CW_INTRO_PROMPT,
    WRITER_CW_SECTION_PROMPT,
    WRITER_LAB_PROMPT,
)


def writer_node(state: WorkState) -> dict:
    if writer_uses_coursework_prompt(state):
        data, logs = _write_coursework(state)
    else:
        data, logs = _write_lab(state)

    try:
        previous = json.loads(state.get("content_draft", "") or "{}")
    except json.JSONDecodeError:
        previous = {}
    if isinstance(previous, dict) and isinstance(data, dict):
        data = _preserve_generated_sections(previous, data)

    draft = json.dumps(data, ensure_ascii=False, indent=2)
    result = {
        "content_draft": draft,
        "critique_notes": "",
        "critique_rerun": "",
        "tool_log": logs,
    }
    result.update(gate_after_llm(state, "writer", data if isinstance(data, dict) else {}))
    return result


def _shared_coursework_context(state: WorkState) -> dict[str, str]:
    research = join_texts(state.get("research_findings", []), sep="\n\n")
    brief = (state.get("work_brief") or "").strip()
    return {
        "topic": state.get("topic", "") or "",
        "requirements": (state.get("requirements") or "")[:4000],
        "structure_outline": (state.get("structure_outline") or "")[:4000],
        "work_brief": brief[:4000] or "(brief не сформирован — опирайся на задание, пример и методичку)",
        "research_findings": research[:6000] or "(исследование не выполнялось)",
        "methodical_text": (state.get("methodical_text") or "")[:6000]
        or "(методичка не предоставлена)",
        "example_text": (state.get("example_text") or "")[:3000]
        or "(пример не предоставлен)",
        "general_requirements_text": (
            state.get("general_requirements_text") or state.get("assignment_text") or ""
        )[:4000]
        or "(не указаны)",
        "variant_task_text": (
            state.get("variant_task_text") or state.get("assignment_text") or ""
        )[:4000]
        or "(не указано)",
        "content_draft": (state.get("content_draft") or "")[:8000],
        "critique_notes": state.get("critique_notes") or "",
    }


def _write_lab(state: WorkState) -> tuple[dict[str, Any], list[str]]:
    llm = get_llm()
    research = join_texts(state.get("research_findings", []), sep="\n\n")
    prompt = WRITER_LAB_PROMPT.format(
        topic=state.get("topic", ""),
        requirements=state.get("requirements", ""),
        structure_outline=state.get("structure_outline", ""),
        research_findings=research,
        general_requirements_text=(
            state.get("general_requirements_text") or state.get("assignment_text") or ""
        )[:4000],
        variant_task_text=(
            state.get("variant_task_text") or state.get("assignment_text") or ""
        )[:4000],
        assignment_variant=state.get("assignment_variant") or "не указан",
        content_draft=state.get("content_draft", ""),
        critique_notes=state.get("critique_notes", ""),
    )
    prompt = apply_prompt_override(prompt, state, "writer")
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {"raw_text": raw}
    return data, ["Writer: lab single-pass"]


def _write_coursework(state: WorkState) -> tuple[dict[str, Any], list[str]]:
    """Multi-pass coursework: intro → chapters → closing; revision stays single-pass."""
    ctx = _shared_coursework_context(state)
    critique = (state.get("critique_notes") or "").strip()
    previous = parse_coursework_draft(state.get("content_draft"))

    # Revision / already-rich draft: one full rewrite with critique context.
    if critique or _draft_has_body(previous):
        llm = get_llm()
        prompt = WRITER_COURSEWORK_PROMPT.format(**ctx)
        prompt = apply_prompt_override(prompt, state, "writer")
        raw = llm_text(llm, prompt)
        data = parse_json_from_llm(raw) or {"raw_text": raw}
        mode = "revision" if critique else "single-pass-existing"
        return data, [f"Writer: coursework {mode}"]

    return _write_coursework_multipass(state, ctx)


def _draft_has_body(draft: dict[str, Any]) -> bool:
    sections = draft.get("sections") or []
    if isinstance(sections, list) and len(sections) >= 2:
        return True
    intro = draft.get("intro") or []
    return isinstance(intro, list) and len(intro) >= 2


def _write_coursework_multipass(
    state: WorkState,
    ctx: dict[str, str],
) -> tuple[dict[str, Any], list[str]]:
    llm = get_llm()
    logs: list[str] = ["Writer: coursework multi-pass"]
    titles = outline_titles_from_structure(
        ctx["structure_outline"],
        discipline=state.get("discipline"),
    )
    titles = titles[:MAX_MULTIPASS_SECTIONS]
    logs.append(f"Writer: глав в плане — {len(titles)}")

    # 1) Intro
    intro_prompt = WRITER_CW_INTRO_PROMPT.format(**ctx)
    intro_prompt = apply_prompt_override(intro_prompt, state, "writer")
    intro_raw = llm_text(llm, intro_prompt)
    intro_data = parse_json_from_llm(intro_raw) or {}
    intro = intro_data.get("intro") if isinstance(intro_data.get("intro"), list) else []
    if not intro and intro_raw.strip():
        intro = [intro_raw.strip()[:2000]]
    intro_summary = " ".join(str(p) for p in intro)[:800]
    logs.append(f"Writer: введение — {len(intro)} абз.")

    # 2) Sections
    sections: list[dict[str, Any]] = []
    for index, title in enumerate(titles, start=1):
        section_prompt = WRITER_CW_SECTION_PROMPT.format(
            **ctx,
            section_title=title.replace('"', "'"),
            section_index=index,
            section_count=len(titles),
            intro_summary=intro_summary or "(пусто)",
        )
        section_prompt = apply_prompt_override(section_prompt, state, "writer")
        section_raw = llm_text(llm, section_prompt)
        section_data = parse_json_from_llm(section_raw) or {}
        paragraphs = section_data.get("paragraphs")
        if not isinstance(paragraphs, list) or not paragraphs:
            paragraphs = [section_raw.strip()[:3000]] if section_raw.strip() else ["(глава без текста)"]
        sec_title = str(section_data.get("title") or title).strip() or title
        sections.append(
            {
                "title": sec_title,
                "paragraphs": [str(p).strip() for p in paragraphs if str(p).strip()],
            }
        )
        logs.append(f"Writer: глава «{sec_title[:40]}» — {len(paragraphs)} абз.")

    sections_summary = "; ".join(
        f"{s['title']}: {' '.join(s['paragraphs'][:1])[:160]}" for s in sections
    )[:2000]

    # 3) Closing
    closing_prompt = WRITER_CW_CLOSING_PROMPT.format(
        **ctx,
        sections_summary=sections_summary or "(главы пусты)",
    )
    closing_prompt = apply_prompt_override(closing_prompt, state, "writer")
    closing_raw = llm_text(llm, closing_prompt)
    closing = parse_json_from_llm(closing_raw) or {}
    conclusion = closing.get("conclusion") if isinstance(closing.get("conclusion"), list) else []
    sources = closing.get("sources") if isinstance(closing.get("sources"), list) else []
    referat = closing.get("referat") if isinstance(closing.get("referat"), dict) else {}
    logs.append(
        f"Writer: заключение — {len(conclusion)} абз., источников — {len(sources)}"
    )

    draft = merge_coursework_parts(
        intro=intro,
        sections=sections,
        conclusion=conclusion,
        sources=sources,
        referat=referat,
    )
    return draft, logs


def _preserve_generated_sections(previous: dict, new: dict) -> dict:
    """Не затирать листинг кода и описание работы программы после Coder."""
    merged = dict(new)
    old_code = str(previous.get("program_code") or "").strip()
    new_code = str(merged.get("program_code") or "").strip()
    if is_code_listing(old_code) and not is_code_listing(new_code):
        merged["program_code"] = old_code
    elif not is_code_listing(new_code):
        merged["program_code"] = ""

    old_work = str(previous.get("program_work") or "").strip()
    new_work = str(merged.get("program_work") or "").strip()
    if old_work and (
        not new_work
        or ("скриншот" in old_work.lower() and "скриншот" not in new_work.lower())
    ):
        merged["program_work"] = old_work
    return merged
