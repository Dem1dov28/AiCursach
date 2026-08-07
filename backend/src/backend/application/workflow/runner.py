"""Application service: run / resume LangGraph workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from backend.application.jobs.job_hitl import hitl
from backend.application.workflow.graph_config import graph_config
from backend.domain.workflow.clarification import parse_interrupt_value
from backend.application.container import app_settings, workflow_engine

RunStatus = Literal["completed", "paused"]


def _recursion_limit(explicit: int | None) -> int:
    return explicit if explicit is not None else app_settings().graph_recursion_limit


__all__ = ["stream_workflow", "resume_workflow", "rerun_workflow", "run_workflow"]


def _graph_config(thread_id: str, *, recursion_limit: int) -> dict[str, Any]:
    return graph_config(thread_id, recursion_limit=recursion_limit)


def _workflow():
    return workflow_engine()


def _sync_state_from_graph(config: dict[str, Any], final_state: dict[str, Any]) -> dict[str, Any]:
    try:
        snap = _workflow().get_state(config)
        if snap and snap.values:
            return {**final_state, **dict(snap.values)}
    except Exception:
        pass
    return final_state


def _handle_interrupt(
    event: dict[str, Any],
    config: dict[str, Any],
    final_state: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    """Returns updated state and breakpoint reason (plan_approval | clarification)."""
    final_state = _sync_state_from_graph(config, final_state)
    raw_interrupts = event.get("__interrupt__") or []
    payload: dict[str, Any] = {}
    if raw_interrupts:
        payload = parse_interrupt_value(raw_interrupts[0])

    if payload.get("type") == "clarification":
        final_state["awaiting_clarification"] = True
        final_state["pending_clarification"] = payload
        final_state["awaiting_plan_approval"] = False
        final_state["awaiting_team_approval"] = False
        return final_state, "clarification"

    if payload.get("type") == "team_approval":
        final_state["awaiting_team_approval"] = True
        final_state["pending_team"] = payload
        final_state["custom_pipeline"] = payload.get("pipeline") or final_state.get("custom_pipeline") or []
        final_state["team_rationale"] = payload.get("rationale") or final_state.get("team_rationale") or ""
        final_state["task_breakdown"] = payload.get("task_breakdown") or final_state.get("task_breakdown") or []
        final_state["awaiting_plan_approval"] = False
        final_state["awaiting_clarification"] = False
        return final_state, "team_approval"

    final_state["awaiting_plan_approval"] = True
    final_state["awaiting_clarification"] = False
    final_state["awaiting_team_approval"] = False
    return final_state, "plan_approval"


def stream_workflow(
    input_state: Any,
    *,
    thread_id: str,
    recursion_limit: int | None = None,
    on_step: Callable[[int, str, dict, dict], None] | None = None,
) -> tuple[dict[str, Any], RunStatus]:
    """Stream workflow until completion or HITL breakpoint."""
    limit = _recursion_limit(recursion_limit)
    config = _graph_config(thread_id, recursion_limit=limit)
    if isinstance(input_state, dict):
        final_state: dict[str, Any] = dict(input_state)
    else:
        # None, Command(resume=…), etc. — state lives in the checkpointer
        final_state = _sync_state_from_graph(config, {})
    step = 0
    paused = False
    breakpoint_reason = "plan_approval"

    stream_input = input_state
    engine = _workflow()
    for event in engine.stream(stream_input, config=config):
        if "__interrupt__" in event:
            paused = True
            final_state, breakpoint_reason = _handle_interrupt(event, config, final_state)
            if on_step:
                pending = final_state.get("pending_clarification") or {}
                if breakpoint_reason == "clarification":
                    on_step(
                        step + 1,
                        pending.get("agent") or "breakpoint",
                        {
                            "current_sub_task": "Ожидание ответа пользователя",
                            "next_step": pending.get("agent") or "",
                        },
                        final_state,
                    )
                elif breakpoint_reason == "team_approval":
                    on_step(
                        step + 1,
                        "breakpoint",
                        {
                            "current_sub_task": "Утвердите команду агентов",
                            "next_step": "supervisor",
                            "awaiting_team_approval": True,
                        },
                        final_state,
                    )
                else:
                    on_step(
                        step + 1,
                        "breakpoint",
                        {
                            "current_sub_task": "Ожидание утверждения плана",
                            "next_step": "writer",
                        },
                        final_state,
                    )
                if hitl.consume_stream_stop(thread_id):
                    return final_state, "paused"
            continue

        step += 1
        node = next(iter(event.keys()))
        output = event[node]
        final_state = {**final_state, **output}
        if on_step:
            on_step(step, node, output, final_state)
        if hitl.consume_stream_stop(thread_id):
            return final_state, "paused"

    if paused:
        return final_state, "paused"
    final_state["awaiting_plan_approval"] = False
    final_state["awaiting_clarification"] = False
    return final_state, "completed"


def resume_workflow(
    *,
    thread_id: str,
    state_updates: dict[str, Any] | None = None,
    resume_value: Any = None,
    recursion_limit: int | None = None,
    on_step: Callable[[int, str, dict, dict], None] | None = None,
) -> tuple[dict[str, Any], RunStatus]:
    """Resume after HITL breakpoint or clarification interrupt."""
    from langgraph.types import Command

    limit = _recursion_limit(recursion_limit)
    config = _graph_config(thread_id, recursion_limit=limit)
    updates = dict(state_updates or {})
    updates["awaiting_plan_approval"] = False
    updates["awaiting_clarification"] = False
    updates["pending_clarification"] = {}
    if isinstance(resume_value, dict) and resume_value.get("approved"):
        updates["awaiting_team_approval"] = False
        updates["pending_team"] = {}
    if updates:
        _workflow().update_state(config, updates)

    stream_input: dict[str, Any] | Command | None
    if resume_value is not None:
        stream_input = Command(resume=resume_value)
    else:
        stream_input = None
    return stream_workflow(stream_input, thread_id=thread_id, recursion_limit=limit, on_step=on_step)


def rerun_workflow(
    *,
    thread_id: str,
    from_node: str,
    state_updates: dict[str, Any] | None = None,
    recursion_limit: int | None = None,
    on_step: Callable[[int, str, dict, dict], None] | None = None,
) -> tuple[dict[str, Any], RunStatus]:
    """Restart workflow from a specific agent node."""
    from backend.domain.workflow.rerun import build_rerun_patches

    limit = _recursion_limit(recursion_limit)
    config = _graph_config(thread_id, recursion_limit=limit)
    updates = build_rerun_patches(from_node)
    if state_updates:
        updates.update(state_updates)
    _workflow().update_state(config, updates)
    return stream_workflow(None, thread_id=thread_id, recursion_limit=limit, on_step=on_step)


def run_workflow(
    initial_state: dict[str, Any],
    *,
    thread_id: str | None = None,
    recursion_limit: int | None = None,
    on_step: Callable[[int, str, dict, dict], None] | None = None,
) -> dict[str, Any]:
    """Run to completion (no pause). Used by tests / legacy callers."""
    tid = thread_id or "default"
    limit = _recursion_limit(recursion_limit)
    final_state, _status = stream_workflow(
        initial_state,
        thread_id=tid,
        recursion_limit=limit,
        on_step=on_step,
    )
    if _status == "paused":
        raise RuntimeError(
            "run_workflow(): workflow paused at HITL — use resume_workflow() with user input"
        )
    return final_state
