"""Classify uploaded materials into assignment / example / GOST-methodical roles."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

MaterialRole = Literal["assignment", "example", "gost_methodical", "other"]

_ASSIGNMENT_NAME = re.compile(
    r"(задани|variant|assignment|лаб[\s_-]?|курсов[\w]*[\s_-]?зада|tz\b|тз\b)",
    re.I,
)
_EXAMPLE_NAME = re.compile(
    r"(пример|sample|example|образец|demo|эталон)",
    re.I,
)
_GOST_NAME = re.compile(
    r"(гост|gost|методич|methodic|stp|стп|оформлен|требован|standard|стандарт)",
    re.I,
)

_ASSIGNMENT_BODY = re.compile(
    r"(вариант\s*№|выполнить|цель\s+работы|задани[ея]\s+на\s|по\s+варианту)",
    re.I,
)
_EXAMPLE_BODY = re.compile(
    r"(введение|заключени[ея]|список\s+использованных\s+источников|реферат)",
    re.I,
)
_GOST_BODY = re.compile(
    r"(гост\s*7|шрифт\s*times|межстрочн|титульн|библиографи|объ[её]м\s+работы|"
    r"поля\s*страницы|14\s*пт|одинарн)",
    re.I,
)


@dataclass(frozen=True)
class ClassifiedMaterial:
    name: str
    text: str
    role: MaterialRole
    confidence: float


@dataclass
class MaterialsClassification:
    assignment_text: str = ""
    example_text: str = ""
    methodical_text: str = ""
    materials_bundle_text: str = ""
    roles: dict[str, str] = field(default_factory=dict)
    items: list[ClassifiedMaterial] = field(default_factory=list)


def score_material_role(name: str, text: str) -> dict[MaterialRole, float]:
    """Return confidence scores per role (0..1)."""
    scores: dict[MaterialRole, float] = {
        "assignment": 0.0,
        "example": 0.0,
        "gost_methodical": 0.0,
        "other": 0.05,
    }
    n = name or ""
    body = (text or "")[:8000]

    if _ASSIGNMENT_NAME.search(n):
        scores["assignment"] += 0.55
    if _EXAMPLE_NAME.search(n):
        scores["example"] += 0.55
    if _GOST_NAME.search(n):
        scores["gost_methodical"] += 0.55

    if _ASSIGNMENT_BODY.search(body):
        scores["assignment"] += 0.35
    if _EXAMPLE_BODY.search(body):
        scores["example"] += 0.3
    # Long coursework-like body with chapters → example
    if len(re.findall(r"(?m)^\s*\d+[\.\)]\s+\S+", body)) >= 3 and len(body) > 2500:
        scores["example"] += 0.25
    if _GOST_BODY.search(body):
        scores["gost_methodical"] += 0.4
    if re.search(r"гост", body, re.I) and len(body) < 15000:
        scores["gost_methodical"] += 0.15

    # Cap
    for key in list(scores):
        scores[key] = min(1.0, scores[key])
    return scores


def pick_role(name: str, text: str) -> tuple[MaterialRole, float]:
    scores = score_material_role(name, text)
    role, conf = max(scores.items(), key=lambda kv: kv[1])
    if conf < 0.35:
        return "other", conf
    return role, conf


def classify_materials(
    materials: list[tuple[str, str]],
    *,
    explicit_assignment: str = "",
    explicit_example: str = "",
    explicit_methodical: str = "",
) -> MaterialsClassification:
    """
    Classify a dump of (filename, text) into roles.

    Explicit API slots win over heuristic assignment for that role's text,
    but heuristics still fill empty slots from the dump.
    """
    classified: list[ClassifiedMaterial] = []
    for name, text in materials:
        if not (text or "").strip():
            continue
        role, conf = pick_role(name, text)
        classified.append(
            ClassifiedMaterial(name=name, text=text.strip(), role=role, confidence=conf)
        )

    # Resolve unique winners per primary role (highest confidence).
    buckets: dict[MaterialRole, list[ClassifiedMaterial]] = {
        "assignment": [],
        "example": [],
        "gost_methodical": [],
        "other": [],
    }
    for item in classified:
        buckets[item.role].append(item)
    for role in ("assignment", "example", "gost_methodical"):
        buckets[role].sort(key=lambda m: m.confidence, reverse=True)

    roles_map: dict[str, str] = {m.name: m.role for m in classified}

    def _join(items: list[ClassifiedMaterial]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0].text
        return "\n\n".join(f"=== {m.name} ===\n{m.text}" for m in items)

    assignment = explicit_assignment.strip() or _join(buckets["assignment"][:2])
    example = explicit_example.strip() or _join(buckets["example"][:2])
    methodical = explicit_methodical.strip() or _join(buckets["gost_methodical"][:2])

    # Leftovers (other + unused extras) stay in bundle for Analyzer context.
    leftover_parts: list[str] = []
    used_names = set()
    if not explicit_assignment.strip():
        for m in buckets["assignment"][:2]:
            used_names.add(m.name)
    if not explicit_example.strip():
        for m in buckets["example"][:2]:
            used_names.add(m.name)
    if not explicit_methodical.strip():
        for m in buckets["gost_methodical"][:2]:
            used_names.add(m.name)

    for m in classified:
        leftover_parts.append(f"=== {m.name} [{roles_map.get(m.name, 'other')}] ===\n{m.text}")

    bundle = "\n\n".join(leftover_parts)

    # If assignment still empty, use whole bundle / first material.
    if not assignment and classified:
        # Prefer non-example, non-gost
        candidates = [m for m in classified if m.role == "other"] or classified
        assignment = candidates[0].text
        roles_map[candidates[0].name] = "assignment"

    return MaterialsClassification(
        assignment_text=assignment,
        example_text=example,
        methodical_text=methodical,
        materials_bundle_text=bundle,
        roles=roles_map,
        items=classified,
    )
