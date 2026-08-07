from pathlib import Path
import csv
import random
from statistics import mean

import pygal


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "иоуз4_данные.txt"
OUT_DIR = BASE_DIR / "stochastic_results"

# If needed, adjust these constants to your variant.
SIGMA_DEMAND = 1.5
TARGET_SERVICE_LEVEL = 0.90
SIM_DAYS = 300
REPLICATIONS = 300
SAFETY_STOCK_VALUES = list(range(0, 21))
RNG_SEED = 42


def to_float(value):
    value = (value or "").strip()
    if not value:
        return None
    return float(value.replace(",", "."))


def read_base_parameters():
    """
    Extract base scenario parameters from prepared TXT data:
    - v: average demand
    - Q: average receipt size
    - L: average lead time in days
    """
    rows = []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["scenario"] == "Сценарий 1":
                rows.append(row)

    if not rows:
        raise RuntimeError("В файле данных не найден 'Сценарий 1'.")

    demand_values = []
    order_days = []
    receipt_days = []
    receipt_values = []

    for row in rows:
        day = int(float(row["day"]))
        demand = to_float(row["demand"])
        order_flag = to_float(row["order_flag"]) or 0.0
        receipt = to_float(row["receipt"]) or 0.0

        if demand is not None:
            demand_values.append(demand)
        if order_flag > 0:
            order_days.append(day)
        if receipt > 0:
            receipt_days.append(day)
            receipt_values.append(receipt)

    if not demand_values or not receipt_values or not order_days or not receipt_days:
        raise RuntimeError("Недостаточно данных для расчета параметров модели.")

    # Pair orders with receipts in chronological order to estimate L.
    pairs = min(len(order_days), len(receipt_days))
    lead_times = [
        receipt_days[i] - order_days[i]
        for i in range(pairs)
        if receipt_days[i] >= order_days[i]
    ]
    if not lead_times:
        raise RuntimeError("Не удалось оценить время поставки L из данных.")

    v = mean(demand_values)
    q = mean(receipt_values)
    l = int(round(mean(lead_times)))

    return v, q, l


def run_simulation(v, q, l, sz, days, rng):
    tz = v * l + sz
    mzz = tz + q
    stock = mzz

    delivery_day = None
    active_order = False
    deficit_days = 0

    trace = []

    for day in range(days):
        order_event = 0
        receipt_event = 0.0

        if active_order and day == delivery_day:
            stock += q
            receipt_event = q
            active_order = False
            delivery_day = None

        demand = max(0.0, rng.gauss(v, SIGMA_DEMAND))
        stock -= demand

        if stock <= 0:
            deficit_days += 1

        if (stock <= tz) and (not active_order):
            active_order = True
            delivery_day = day + l
            order_event = 1

        trace.append(
            {
                "day": day,
                "stock": stock,
                "demand": demand,
                "order_event": order_event,
                "receipt_event": receipt_event,
                "tz": tz,
                "sz": sz,
                "mzz": mzz,
            }
        )

    service_level = 1.0 - deficit_days / days
    deficit_probability = deficit_days / days

    return service_level, deficit_probability, trace


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Не найден файл данных: {DATA_FILE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RNG_SEED)

    v, q, l = read_base_parameters()

    results = []
    for sz in SAFETY_STOCK_VALUES:
        sl_values = []
        def_values = []

        for _ in range(REPLICATIONS):
            sl, deficit_p, _ = run_simulation(v, q, l, sz, SIM_DAYS, rng)
            sl_values.append(sl)
            def_values.append(deficit_p)

        results.append(
            {
                "sz": sz,
                "service_level": mean(sl_values),
                "deficit_probability": mean(def_values),
            }
        )

    acceptable = [r for r in results if r["service_level"] >= TARGET_SERVICE_LEVEL]
    if acceptable:
        best = min(acceptable, key=lambda r: r["sz"])
    else:
        best = max(results, key=lambda r: r["service_level"])

    _, _, trace = run_simulation(
        v, q, l, best["sz"], SIM_DAYS, random.Random(RNG_SEED + 1)
    )

    # Chart 1: service level vs safety stock
    c1 = pygal.Line(show_dots=True, x_label_rotation=20, legend_at_bottom=True)
    c1.title = "Зависимость уровня обслуживания от страхового запаса"
    c1.x_labels = [str(r["sz"]) for r in results]
    c1.add("Уровень обслуживания", [r["service_level"] for r in results])
    c1.add("Вероятность дефицита", [r["deficit_probability"] for r in results])
    c1.render_to_file(str(OUT_DIR / "service_level_vs_sz.svg"))

    # Chart 2: stock movement for selected SZ (required chart style)
    days = [row["day"] for row in trace]
    stock = [row["stock"] for row in trace]
    tz_line = [trace[0]["tz"]] * len(trace)
    sz_line = [trace[0]["sz"]] * len(trace)
    mzz_line = [trace[0]["mzz"]] * len(trace)
    order_points = [stock[i] if trace[i]["order_event"] > 0 else None for i in range(len(trace))]
    receipt_points = [stock[i] if trace[i]["receipt_event"] > 0 else None for i in range(len(trace))]
    step = max(1, len(days) // 20)
    xlabels = [str(d) if i % step == 0 else "" for i, d in enumerate(days)]

    c2 = pygal.Line(
        show_dots=False,
        x_label_rotation=20,
        legend_at_bottom=True,
        show_minor_x_labels=False,
    )
    c2.title = f"Стохастический сценарий: движение запаса (СЗ={best['sz']})"
    c2.x_labels = xlabels
    c2.add("Текущий запас", stock)
    c2.add("ТЗ", tz_line)
    c2.add("СЗ", sz_line)
    c2.add("МЖЗ", mzz_line)
    c2.add("Момент заказа", order_points, dots_size=4, stroke=False)
    c2.add("Момент поступления", receipt_points, dots_size=4, stroke=False)
    c2.render_to_file(str(OUT_DIR / "stochastic_stock_movement.svg"))

    # Text report
    report_lines = [
        "СТОХАСТИЧЕСКОЕ МОДЕЛИРОВАНИЕ (Q-модель)",
        "",
        f"Исходные параметры (оценены из Сценария 1):",
        f"v (средний спрос) = {v:.4f}",
        f"Q (размер заказа) = {q:.4f}",
        f"L (время поставки) = {l}",
        f"sigma (СКО спроса) = {SIGMA_DEMAND:.4f}",
        "",
        f"Целевой уровень обслуживания = {TARGET_SERVICE_LEVEL:.2%}",
        f"Длина имитации = {SIM_DAYS} дней, повторов = {REPLICATIONS}",
        "",
        "Таблица результатов (СЗ, уровень обслуживания, вероятность дефицита):",
    ]
    for r in results:
        report_lines.append(
            f"СЗ={r['sz']:>2d} | SL={r['service_level']:.4f} | P(дефицит)={r['deficit_probability']:.4f}"
        )
    report_lines.extend(
        [
            "",
            f"Рекомендуемый СЗ для целевого SL: {best['sz']}",
            f"Полученный SL: {best['service_level']:.4f}",
            f"Полученная P(дефицит): {best['deficit_probability']:.4f}",
            "",
            "Сформированы файлы:",
            f"- {OUT_DIR / 'service_level_vs_sz.svg'}",
            f"- {OUT_DIR / 'stochastic_stock_movement.svg'}",
        ]
    )
    (OUT_DIR / "stochastic_report.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("Done.")
    print(f"Report: {OUT_DIR / 'stochastic_report.txt'}")
    print(f"Charts: {OUT_DIR / 'service_level_vs_sz.svg'}")
    print(f"Charts: {OUT_DIR / 'stochastic_stock_movement.svg'}")


if __name__ == "__main__":
    main()
