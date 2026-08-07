"""Normalize / validate LLM packages for coursework charts & tables."""

from __future__ import annotations

import re
from typing import Any

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}\.png$")
_ALLOWED_TYPES = frozenset({"bar", "pie", "line"})
_MIN_POINTS = 2
_MAX_POINTS = 12
_MAX_CHARTS = 4


def normalize_asset_package(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Return ``{table: {...}|None, charts: [...]}``; drop invalid parts."""
    data = raw if isinstance(raw, dict) else {}
    charts_in = data.get("charts")
    if not isinstance(charts_in, list):
        charts_in = []

    charts: list[dict[str, Any]] = []
    for item in charts_in[:_MAX_CHARTS]:
        normalized = _normalize_chart(item)
        if normalized:
            charts.append(normalized)

    table = _normalize_table(data.get("table") or data.get("rows"))
    return {"table": table, "charts": charts}


def asset_package_issues(package: dict[str, Any] | None) -> list[str]:
    data = normalize_asset_package(package if isinstance(package, dict) else {})
    issues: list[str] = []
    if not data["charts"]:
        issues.append("нет валидных графиков (нужен 1–4 chart bar/pie/line)")
    return issues


def _normalize_chart(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    chart_type = str(item.get("type") or "").strip().lower()
    if chart_type not in _ALLOWED_TYPES:
        return None

    labels_raw = item.get("labels") or item.get("xlabels") or []
    values_raw = item.get("values") or []
    if not isinstance(labels_raw, list) or not isinstance(values_raw, list):
        return None
    if not (_MIN_POINTS <= len(labels_raw) <= _MAX_POINTS):
        return None
    if len(labels_raw) != len(values_raw):
        return None

    labels = [str(x).strip()[:40] for x in labels_raw]
    if any(not lab for lab in labels):
        return None

    values: list[float] = []
    for v in values_raw:
        try:
            values.append(float(v))
        except (TypeError, ValueError):
            return None
    if any(x < 0 for x in values):
        return None
    if sum(values) <= 0:
        return None

    filename = str(item.get("filename") or "").strip()
    if not _SAFE_NAME.match(filename):
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", chart_type)[:40] or "chart"
        filename = f"fig_{stem}_{len(labels)}.png"

    ylabel = str(item.get("ylabel") or item.get("title") or "Показатель").strip()[:80]
    xlabel = str(item.get("xlabel") or "").strip()[:80]

    return {
        "type": chart_type,
        "filename": filename,
        "labels": labels,
        "values": values,
        "ylabel": ylabel or "Показатель",
        "xlabel": xlabel,
    }


def _normalize_table(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, list) and raw and all(isinstance(r, dict) for r in raw):
        rows = [{str(k): str(v) for k, v in row.items()} for row in raw[:80]]
        columns = list(rows[0].keys())
        return {"columns": columns, "rows": rows}

    if not isinstance(raw, dict):
        return None
    rows = raw.get("rows")
    columns = raw.get("columns")
    if not isinstance(rows, list) or not rows:
        return None
    if isinstance(columns, list) and columns:
        cols = [str(c) for c in columns]
        norm_rows = []
        for row in rows[:80]:
            if not isinstance(row, dict):
                continue
            norm_rows.append({c: str(row.get(c, "")) for c in cols})
        if not norm_rows:
            return None
        return {"columns": cols, "rows": norm_rows}
    if all(isinstance(r, dict) for r in rows):
        cols = list(rows[0].keys())
        return {
            "columns": cols,
            "rows": [{str(k): str(v) for k, v in r.items()} for r in rows[:80]],
        }
    return None
