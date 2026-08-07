"""Autonomy levels for Human-in-the-Loop clarification."""

from __future__ import annotations

from typing import Literal

AutonomyLevel = Literal["full_auto", "interactive"]

AUTONOMY_LEVELS: tuple[AutonomyLevel, ...] = ("full_auto", "interactive")

DEFAULT_AUTONOMY_LEVEL: AutonomyLevel = "interactive"
DEFAULT_CONFIDENCE_THRESHOLD = 0.8

_LEGACY_INTERACTIVE = frozenset({"smart_assist", "step_by_step", "interactive"})


def normalize_autonomy_level(value: str | None) -> AutonomyLevel:
    normalized = (value or DEFAULT_AUTONOMY_LEVEL).strip().lower()
    if normalized == "full_auto":
        return "full_auto"
    if normalized in _LEGACY_INTERACTIVE:
        return "interactive"
    return DEFAULT_AUTONOMY_LEVEL


def is_interactive_mode(value: str | None) -> bool:
    return normalize_autonomy_level(value) == "interactive"
