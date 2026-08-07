"""Researcher — академический поиск + Tavily + методичка."""

from __future__ import annotations

import json
import re

from backend.core.config import get_config
from backend.domain.workflow.prompt_override import apply_prompt_override
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import RESEARCHER_SUMMARY_PROMPT
from backend.domain.workflow.work_state import WorkState
from backend.domain.workflow.clarification import detect_researcher_clarification
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.academic_search import (
    format_hits_for_researcher,
    search_academic_literature,
    search_russian_web_sources,
)


def _tavily_search(query: str) -> str:
    api_key = get_config().tavily_api_key
    if not api_key:
        return ""

    try:
        from langchain_tavily import TavilySearch

        tool = TavilySearch(max_results=5, search_depth="basic")
        response = tool.invoke({"query": query})
    except Exception:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=5)
        except Exception as exc:
            return f"Поиск недоступен: {exc}"

    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            return response

    if isinstance(response, dict):
        results = response.get("results", [])
        chunks = []
        for item in results[:5]:
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")[:400]
            chunks.append(f"**{title}**\n{url}\n{content}")
        return "\n---\n".join(chunks)

    return str(response)


def _methodical_excerpt(state: WorkState) -> str:
    methodical = (state.get("methodical_text") or "").strip()
    if methodical:
        return methodical[:5000]
    requirements = (state.get("requirements") or "").strip()
    if requirements:
        return requirements[:3000]
    topic = state.get("topic", "")
    return f"Теоретическая база по теме «{topic}»: используйте методичку кафедры и учебники."


def _collect_raw_research(state: WorkState, topic: str) -> str:
    parts: list[str] = []

    discipline = (state.get("discipline") or "").strip()
    include_russian = bool(re.search(r"[а-яА-ЯёЁ]", topic)) or discipline.lower() in (
        "economics",
        "humanities",
        "law",
        "management",
        "экономика",
        "гуманитарные",
    )

    academic_hits = search_academic_literature(topic, limit=5, include_russian=include_russian)
    academic_block = format_hits_for_researcher(academic_hits)
    if academic_block:
        parts.append(academic_block)

    web_query = search_russian_web_sources(topic, discipline) if include_russian else f"{topic} {discipline} учебная работа теория"
    web_raw = _tavily_search(web_query)
    if web_raw.strip():
        label = "Веб-источники (RU)" if include_russian else "Веб-источники (Tavily)"
        parts.append(f"## {label}\n\n" + web_raw)

    if include_russian:
        en_query = f"{topic} {discipline} academic research"
        en_raw = _tavily_search(en_query)
        if en_raw.strip():
            parts.append("## Веб-источники (EN)\n\n" + en_raw)

    methodical = _methodical_excerpt(state)
    if methodical:
        parts.append("## Методичка / требования\n\n" + methodical[:4000])

    return "\n\n---\n\n".join(parts)


def researcher_node(state: WorkState) -> dict:
    llm_payload: dict = {}
    if not state.get("needs_research", True):
        base = {"research_findings": [_methodical_excerpt(state)]}
    else:
        topic = state.get("topic", "")
        work_type = state.get("work_type", "auto")
        raw = _collect_raw_research(state, topic)

        if not raw.strip():
            base = {"research_findings": [_methodical_excerpt(state)]}
        else:
            llm = get_llm()
            summary_prompt = RESEARCHER_SUMMARY_PROMPT.format(
                query=topic,
                work_type=work_type,
                raw_results=raw[:8000],
            )
            summary_prompt = apply_prompt_override(summary_prompt, state, "researcher")
            summary_raw = llm_text(llm, summary_prompt)
            llm_payload = parse_json_from_llm(summary_raw) or {}
            if isinstance(llm_payload, dict) and llm_payload.get("summary"):
                summary_text = str(llm_payload.get("summary") or "").strip()
                hints = llm_payload.get("source_hints") or []
                if isinstance(hints, list) and hints:
                    summary_text += "\n\nИсточники:\n" + "\n".join(str(h) for h in hints[:8])
            else:
                summary_text = summary_raw or raw[:3000]
            base = {"research_findings": [summary_text or raw[:3000]]}

    base.update(
        gate_after_llm(
            state,
            "researcher",
            llm_payload,
            heuristic=lambda s, _: detect_researcher_clarification(s),
        )
    )
    return base
