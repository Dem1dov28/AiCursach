"""Apply user prompt overrides to agent prompts."""

from __future__ import annotations

from typing import Any


def apply_prompt_override(base_prompt: str, state: dict, agent: str) -> str:
    overrides = state.get("prompt_overrides") or {}
    extra = overrides.get(agent, "")
    if not str(extra).strip():
        return base_prompt
    return f"{base_prompt}\n\n---\nДополнительные инструкции пользователя ({agent}):\n{extra.strip()}"


def merge_prompt_override(
    updates: dict[str, Any] | None,
    *,
    current_overrides: dict[str, str] | None,
    agent: str,
    override_text: str,
) -> dict[str, Any]:
    """Merge a single agent override into state updates."""
    merged = dict(updates or {})
    text = str(override_text or "").strip()
    if not text:
        return merged
    overrides = dict(current_overrides or {})
    overrides[agent] = text
    merged["prompt_overrides"] = overrides
    return merged
