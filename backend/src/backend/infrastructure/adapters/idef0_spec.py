"""IDEF0 из JSON-спецификации (стиль БГУИР через Idef0Canvas)."""

from __future__ import annotations

import sys
from pathlib import Path

from backend.core.bootstrap import ensure_repo_on_path

ensure_repo_on_path()

from tools.diagrams.idef0_draw import Idef0Canvas, _font  # noqa: E402


def _wrap_title(title: str, max_len: int = 22) -> str:
    words = title.replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines[:3]) if lines else title


def draw_context(spec: dict, path: Path) -> None:
    c = Idef0Canvas()
    c.f_title = _font(24)
    c.f_label = _font(18)
    c.f_small = _font(16)
    box = (700, 455, 1528, 655)
    title = _wrap_title(spec.get("title", "Процесс A-0"))
    c.draw_box(box, title, 0)
    c.external_inputs(box, spec.get("inputs") or ["Входные данные"], arrow_len=175)
    c.external_outputs(box, spec.get("outputs") or ["Результат"], arrow_len=175)
    controls = spec.get("controls") or ["Нормативные документы"]
    c.top_controls_single(box, [_wrap_title(x, 28) for x in controls])
    mechanisms = spec.get("mechanisms") or ["ИС", "Персонал"]
    c.bottom_mechanisms_single(box, [_wrap_title(x, 20) for x in mechanisms])
    c.save(path)


def draw_decomposition(spec: dict, path: Path) -> None:
    c = Idef0Canvas()
    c.f_title = _font(20)
    c.f_label = _font(17)
    c.f_small = _font(14)

    box_titles = spec.get("boxes") or ["Блок 1", "Блок 2", "Блок 3"]
    n = min(max(len(box_titles), 2), 6)
    box_titles = box_titles[:n]
    step = (380, 110) if n <= 4 else (300, 90)
    size = (340, 155) if n <= 4 else (280, 140)
    boxes = c.cascade(n, start=(140, 310), step=step, size=size)

    for i, (rect, title) in enumerate(zip(boxes, box_titles), 1):
        c.draw_box(rect, _wrap_title(title), i)

    flows = spec.get("flows") or []
    while len(flows) < max(0, n - 1):
        flows.append(f"Поток {len(flows) + 1}")
    c.chain(boxes, [_wrap_title(f, 26) for f in flows[: n - 1]])

    if spec.get("inputs"):
        c.external_inputs(boxes[0], spec["inputs"], arrow_len=120)
    if spec.get("outputs"):
        c.external_outputs(boxes[-1], spec["outputs"], arrow_len=120)

    controls = spec.get("controls") or ["Методические указания"]
    if isinstance(controls, list) and controls and isinstance(controls[0], str):
        c.top_controls_forked(
            boxes,
            [( _wrap_title(controls[0], 30), list(range(n)))],
        )
    elif isinstance(controls, list):
        pairs = []
        for item in controls:
            if isinstance(item, dict):
                pairs.append(
                    (_wrap_title(item.get("text", ""), 30), item.get("boxes", list(range(n))))
                )
        if pairs:
            c.top_controls_forked(boxes, pairs)

    mechanisms = spec.get("mechanisms") or ["Программное обеспечение"]
    if isinstance(mechanisms, list) and mechanisms and isinstance(mechanisms[0], str):
        c.bottom_mechanisms_forked(
            boxes,
            [(_wrap_title(mechanisms[0], 24), list(range(n)))],
        )
    elif isinstance(mechanisms, list):
        pairs = []
        for item in mechanisms:
            if isinstance(item, dict):
                pairs.append(
                    (_wrap_title(item.get("text", ""), 24), item.get("boxes", [0]))
                )
        if pairs:
            c.bottom_mechanisms_forked(boxes, pairs)

    c.save(path)


def render_idef0(spec: dict, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    context = spec.get("context")
    if context:
        p = out_dir / "idef0_context.png"
        draw_context(context, p)
        saved.append(str(p))
    decomp = spec.get("decomposition")
    if decomp:
        p = out_dir / "idef0_decomposition.png"
        draw_decomposition(decomp, p)
        saved.append(str(p))
    return saved
