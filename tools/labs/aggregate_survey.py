#!/usr/bin/env python3
"""Агрегация опроса из data/survey_responses.csv (UTF-8)."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "survey_responses.csv"


def main() -> None:
    rows: list[dict[str, str]] = []
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    metrics = ["ease_of_use", "clarity", "visual_appeal", "learn_speed"]
    by_site: dict[str, list[list[float]]] = defaultdict(list)

    for r in rows:
        site = r["site"]
        vals = [float(r[m]) for m in metrics]
        by_site[site].append(vals)

    print("Средние по сайтам (по вопросам и общее среднее 4 вопросов):\n")
    for site in sorted(by_site.keys()):
        matrix = by_site[site]
        per_metric = []
        for i, m in enumerate(metrics):
            col = [row[i] for row in matrix]
            per_metric.append(statistics.mean(col))
        overall = statistics.mean(per_metric)
        print(f"{site}:")
        for m, v in zip(metrics, per_metric):
            print(f"  {m}: {v:.3f}")
        print(f"  overall_4q: {overall:.3f}\n")


if __name__ == "__main__":
    main()
