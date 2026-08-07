#!/usr/bin/env python3
"""Проверка расчётов курсовой: ABC-XYZ, EOQ, согласованность TSV/Excel/текста."""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from openpyxl import load_workbook

from calc_bz import STRATEGY_NAMES, best_strategy, compute_bz_strategies, compute_bz_warehouse_areas

BASE = Path(__file__).resolve().parent
DAYS = 365
XYZ_X_MAX = 0.15
XYZ_Y_MAX = 0.25


def read_tsv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def abc_class(cum_share: float) -> str:
    if cum_share <= 0.80:
        return "A"
    if cum_share <= 0.95:
        return "B"
    return "C"


def xyz_class(cv: float) -> str:
    if cv <= XYZ_X_MAX:
        return "X"
    if cv <= XYZ_Y_MAX:
        return "Y"
    return "Z"


def eoq_daily(v: float, k: float, h: float) -> float:
    return math.sqrt(2 * k * h * v)


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    source = read_tsv("приложение_А_исходные_данные_50.tsv")
    saved = read_tsv("результаты_ABC_XYZ.tsv")
    matrix = read_tsv("матрица_ABC_XYZ.tsv")

    if len(source) != 50:
        errors.append(f"Исходных позиций: {len(source)}, ожидалось 50")

    # --- ABC-XYZ пересчёт ---
    rows = []
    for r in source:
        v = float(r["demand_v"])
        c = float(r["unit_price_c"])
        cv = float(r["coef_variation_cv"])
        annual = v * c * DAYS
        rows.append(
            {
                "code": r["code"],
                "annual_value": round(annual, 2),
                "cv": cv,
                "xyz": xyz_class(cv),
            }
        )
    rows.sort(key=lambda x: -x["annual_value"])
    total = sum(x["annual_value"] for x in rows)
    cum = 0.0
    recomputed = {}
    for row in rows:
        share = row["annual_value"] / total
        cum += share
        abc = abc_class(cum)
        group = abc + row["xyz"]
        recomputed[row["code"]] = {
            "abc": abc,
            "xyz": row["xyz"],
            "group": group,
            "annual_value": row["annual_value"],
        }

    saved_map = {r["code"]: r for r in saved}
    for code, calc in recomputed.items():
        s = saved_map[code]
        for key in ("abc", "xyz", "group"):
            if calc[key] != s[key]:
                errors.append(f"{code}: {key} расчёт={calc[key]}, файл={s[key]}")
        if abs(calc["annual_value"] - float(s["annual_value"])) > 0.05:
            errors.append(
                f"{code}: annual_value расчёт={calc['annual_value']}, файл={s['annual_value']}"
            )

    # --- матрица ---
    matrix_counts = {r["group"]: int(r["count"]) for r in matrix}
    from collections import Counter

    cnt = Counter(recomputed[c]["group"] for c in recomputed)
    for group in ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]:
        if matrix_counts.get(group, 0) != cnt.get(group, 0):
            errors.append(
                f"Матрица {group}: файл={matrix_counts.get(group, 0)}, расчёт={cnt.get(group, 0)}"
            )

    # --- Excel vs TSV ---
    xlsx = BASE / "таблицы_для_курсовой.xlsx"
    bz_strategies = compute_bz_strategies()
    max_area = compute_bz_warehouse_areas()[1]
    if not xlsx.exists():
        errors.append("Не найден таблицы_для_курсовой.xlsx")
    else:
        wb = load_workbook(xlsx, data_only=False)
        ws_src = wb["Source50"]
        for i, r in enumerate(source, start=2):
            if ws_src.cell(i, 1).value != r["code"]:
                errors.append(f"Excel исходные: строка {i}, код не совпадает")
                break

        formula_count = sum(
            1
            for sname in wb.sheetnames
            for row in wb[sname].iter_rows()
            for cell in row
            if isinstance(cell.value, str) and cell.value.startswith("=")
        )
        if formula_count < 500:
            errors.append(f"Excel: мало формул ({formula_count}), ожидались расчётные листы")

        ws_bz = wb["BZ_Compare"]
        for row in range(2, 5):
            name = ws_bz.cell(row, 1).value
            if name not in STRATEGY_NAMES:
                errors.append(f"BZ: неизвестная стратегия «{name}»")
            elif not (
                isinstance(ws_bz.cell(row, 2).value, str)
                and ws_bz.cell(row, 2).value.startswith("=")
            ):
                errors.append(f"BZ «{name}»: ожидалась формула в ячейке суточных затрат")

        expected = {
            STRATEGY_NAMES[0]: (49.34, 18008.16),
            STRATEGY_NAMES[1]: (32.47, 11852.01),
            STRATEGY_NAMES[2]: (50.21, 18326.80),
        }
        for name, vals in expected.items():
            d, y = bz_strategies[name]
            if abs(d - vals[0]) > 0.02 or abs(y - vals[1]) > 1.0:
                errors.append(f"BZ «{name}»: расчёт=({d:.2f}, {y:.2f}), ожидание={vals}")

        if abs(max_area - 0.9892) > 0.01:
            errors.append(f"BZ max площадь: {max_area:.4f}, ожидалось 0.9892")

    # --- раздельная оптимизация BZ (EOQ) ---
    bz_row = next(r for r in matrix if r["group"] == "BZ")
    bz_codes = [c.strip() for c in bz_row["codes"].split(",")]
    source_map = {r["code"]: r for r in source}
    sep = sum(
        eoq_daily(
            float(source_map[code]["demand_v"]),
            float(source_map[code]["order_cost_K"]),
            float(source_map[code]["holding_cost_h"]),
        )
        for code in bz_codes
    )
    if abs(sep - 49.34) > 0.02:
        errors.append(f"BZ раздельная EOQ: {sep:.2f}, ожидалось 49.34")
    else:
        notes.append(f"BZ раздельная оптимизация (EOQ): {sep:.2f} ✓")

    best = best_strategy(bz_strategies)
    if best != STRATEGY_NAMES[1]:
        errors.append(f"Лучшая стратегия BZ: {best}")

    # --- итог ---
    print("=== Проверка расчётов курсовой ===\n")
    print(f"Номенклатур: {len(source)}")
    print("Матрица ABC-XYZ:", dict(sorted(cnt.items())))
    if xlsx.exists():
        print(f"BZ стратегии: {bz_strategies}")
        print(f"Макс. площадь BZ: {max_area} м²")
    print()
    for n in notes:
        print(n)
    if errors:
        print("\nОШИБКИ:")
        for e in errors:
            print(" -", e)
        return 1
    print("\nВсе проверки пройдены.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
