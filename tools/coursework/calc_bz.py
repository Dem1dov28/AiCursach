#!/usr/bin/env python3
"""Расчёт стратегий BZ и площади склада (дублирует формулы Excel)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
DAYS = 365
T_FULL_BZ = 2.309

STRATEGY_NAMES = (
    "Раздельная оптимизация",
    "Полное совмещение заказов",
    "Частичное совмещение (кратные периоды)",
)


def read_source() -> list[dict[str, str]]:
    with (BASE / "приложение_А_исходные_данные_50.tsv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def bz_codes() -> list[str]:
    with (BASE / "матрица_ABC_XYZ.tsv").open(encoding="utf-8") as f:
        matrix = list(csv.DictReader(f, delimiter="\t"))
    row = next(r for r in matrix if r["group"] == "BZ")
    return [c.strip() for c in row["codes"].split(",")]


def bz_items() -> list[dict[str, str]]:
    codes = set(bz_codes())
    return [r for r in read_source() if r["code"] in codes]


def compute_bz_strategies() -> dict[str, tuple[float, float]]:
    items = bz_items()
    n = len(items)
    ksum = sum(float(i["order_cost_K"]) for i in items)
    sep = sum(
        math.sqrt(
            2
            * float(i["order_cost_K"])
            * float(i["holding_cost_h"])
            * float(i["demand_v"])
        )
        for i in items
    )
    partial = sum(
        math.sqrt(2 * (ksum / n) * float(i["holding_cost_h"]) * float(i["demand_v"]))
        for i in items
    )
    full = sum(
        math.sqrt(
            2
            * (float(i["order_cost_K"]) / T_FULL_BZ)
            * float(i["holding_cost_h"])
            * float(i["demand_v"])
        )
        for i in items
    )
    daily = {
        STRATEGY_NAMES[0]: sep,
        STRATEGY_NAMES[1]: full,
        STRATEGY_NAMES[2]: partial,
    }
    return {name: (d, d * DAYS) for name, d in daily.items()}


def compute_bz_warehouse_areas() -> tuple[list[float], float]:
    """Площадь склада по 12 периодам при полном совмещении заказов (лист BZ_график_12п)."""
    areas: list[float] = []
    items = bz_items()
    params = []
    for i in items:
        v = float(i["demand_v"])
        k = float(i["order_cost_K"])
        h = float(i["holding_cost_h"])
        f = float(i["storage_area_f"])
        q = math.sqrt(2 * (k / T_FULL_BZ) * v / h)
        params.append((q, v, f))

    for period in range(1, 13):
        area = 0.0
        day = (period - 1) * T_FULL_BZ / 12
        for q, v, f in params:
            stock = max(0.0, q - v * day)
            area += stock * f
        areas.append(round(area, 4))
    return areas, max(areas)


def best_strategy(strategies: dict[str, tuple[float, float]]) -> str:
    return min(strategies.items(), key=lambda x: x[1][0])[0]


def _order_qty(k: float, v: float, h: float, t: float = 1.0) -> float:
    return math.sqrt(2 * (k / t) * v / h)


def compute_bz_capital() -> dict[str, float]:
    """Средний объём капиталовложений в запасы (Q/2 * c) по стратегиям для группы BZ."""
    items = bz_items()
    n = len(items)
    ksum = sum(float(i["order_cost_K"]) for i in items)
    out: dict[str, float] = {}
    configs = (
        (STRATEGY_NAMES[0], lambda i: float(i["order_cost_K"]), 1.0),
        (STRATEGY_NAMES[1], lambda i: float(i["order_cost_K"]), T_FULL_BZ),
        (STRATEGY_NAMES[2], lambda _i: ksum / n, 1.0),
    )
    for name, k_fn, t in configs:
        total = 0.0
        for i in items:
            v = float(i["demand_v"])
            h = float(i["holding_cost_h"])
            c = float(i["unit_price_c"])
            q = _order_qty(k_fn(i), v, h, t)
            total += (q / 2) * c
        out[name] = round(total, 2)
    return out
