#!/usr/bin/env python3
"""Графики для пояснительной записки: академическое оформление, кириллица."""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from calc_bz import STRATEGY_NAMES, compute_bz_capital, compute_bz_strategies, compute_bz_warehouse_areas

BASE = Path(__file__).resolve().parent
OUT = BASE / "word_assets_final"
OUT.mkdir(exist_ok=True)

# Соотношение сторон близко к вставке 150 мм x 90 мм в Word
W, H = 3600, 2100
SCALE = 2  # supersampling

FONT_PATH = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
FONT_BOLD_PATH = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")

BLUE = "#2F5597"
BLUE_LIGHT = "#5B9BD5"
GREEN = "#548235"
RED = "#C00000"
GRAY = "#7F7F7F"
GRID = "#E6E6E6"
BORDER = "#000000"

ABC_GROUPS = ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]
ABC_COLORS = {
    "A": "#1F4E79",
    "B": "#2F75B5",
    "C": "#9DC3E6",
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD_PATH if bold and FONT_BOLD_PATH.exists() else FONT_PATH
    return ImageFont.truetype(str(path), size=size)


F_TICK = _font(52)
F_LABEL = _font(56)
F_AXIS = _font(58, bold=True)


def _save(img: Image.Image, name: str) -> Path:
    # downscale для сглаживания
    out = img.resize((W // SCALE, H // SCALE), Image.Resampling.LANCZOS)
    path = OUT / name
    out.save(path, "PNG", optimize=True)
    return path


def _new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), "white")
    return img, ImageDraw.Draw(img)


def _text_wh(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def _center_text(draw, cx: int, y: int, text: str, font, fill=BORDER) -> None:
    tw, _ = _text_wh(draw, text, font)
    draw.text((cx - tw // 2, y), text, fill=fill, font=font)


def _y_max(values: list[float], extra: float = 0.15) -> float:
    vmax = max(values) if values else 1.0
    return vmax * (1 + extra) if vmax > 0 else 1.0


def _y_ticks(ymax: float, steps: int = 5) -> list[float]:
    raw = ymax / steps
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    step = math.ceil(raw / mag) * mag
    ticks = [0.0]
    v = step
    while v <= ymax + step * 0.01:
        ticks.append(v)
        v += step
    if ticks[-1] < ymax:
        ticks.append(math.ceil(ymax / step) * step)
    return ticks


def _fmt(val: float) -> str:
    if abs(val - round(val)) < 1e-6:
        return str(int(round(val)))
    if val < 10:
        return f"{val:.2f}".rstrip("0").rstrip(".")
    return f"{val:.1f}".rstrip("0").rstrip(".")


def _draw_rotated_text(base: Image.Image, x: int, y: int, text: str, font) -> None:
    tmp = Image.new("RGBA", (800, 800), (255, 255, 255, 0))
    d = ImageDraw.Draw(tmp)
    d.text((0, 0), text, fill=BORDER, font=font)
    b = tmp.getbbox()
    if not b:
        return
    crop = tmp.crop(b)
    rot = crop.rotate(90, expand=True)
    base.paste(rot, (x, y), rot)


def _plot_frame(
    draw: ImageDraw.ImageDraw,
    *,
    bottom_extra: int = 0,
) -> tuple[int, int, int, int, int]:
    left, top, right, bottom = 420, 120, W - 120, H - 260 - bottom_extra
    draw.rectangle((left, top, right, bottom), outline=BORDER, width=4)
    return left, top, right, bottom


def _draw_y_axis(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
    ymax: float,
    ylabel: str,
) -> list[float]:
    ticks = _y_ticks(ymax)
    tmax = ticks[-1]
    for t in ticks:
        y = bottom - int((t / tmax) * (bottom - top))
        draw.line((left, y, right, y), fill=GRID, width=3)
        draw.line((left - 12, y, left, y), fill=BORDER, width=3)
        label = _fmt(t)
        tw, th = _text_wh(draw, label, F_TICK)
        draw.text((left - 35 - tw, y - th // 2), label, fill=BORDER, font=F_TICK)
    _draw_rotated_text(img, 70, (top + bottom) // 2 - 220, ylabel, F_AXIS)
    return ticks


def _draw_x_label(draw, left, right, bottom, text: str, offset: int = 95) -> None:
    _center_text(draw, (left + right) // 2, bottom + offset, text, F_AXIS)


def bar_chart(
    labels: list[str],
    values: list[float],
    ylabel: str,
    filename: str,
    *,
    colors: list[str] | None = None,
    highlight_min: bool = False,
    xlabel: str = "",
) -> Path:
    img, draw = _new_canvas()
    extra = 120 if xlabel else 0
    left, top, right, bottom = _plot_frame(draw, bottom_extra=extra)
    ymax = _y_max(values)
    ticks = _draw_y_axis(draw, img, left, top, right, bottom, ymax, ylabel)
    tmax = ticks[-1]

    n = len(values)
    gap = 55
    bar_w = (right - left - gap * (n + 1)) // max(n, 1)

    min_idx = values.index(min(values)) if highlight_min and values else -1
    default_colors = colors or [BLUE] * n

    for i, (label, val) in enumerate(zip(labels, values)):
        if highlight_min and i == min_idx:
            color = GREEN
        elif colors:
            color = colors[i]
        else:
            color = default_colors[i % len(default_colors)]

        x0 = left + gap + i * (bar_w + gap)
        x1 = x0 + bar_w
        h = int((val / tmax) * (bottom - top))
        y0, y1 = bottom - h, bottom
        draw.rectangle((x0, y0, x1, y1), fill=color, outline=BORDER, width=3)
        _center_text(draw, (x0 + x1) // 2, y0 - 58, _fmt(val), F_LABEL)

        lines = label.split("\n")
        ly = bottom + 28
        for line in lines:
            _center_text(draw, (x0 + x1) // 2, ly, line, F_TICK)
            ly += 58

    if xlabel:
        _draw_x_label(draw, left, right, bottom, xlabel, offset=175)

    return _save(img, filename)


def line_chart(
    xlabels: list[str],
    values: list[float],
    ylabel: str,
    filename: str,
    *,
    hline: float | None = None,
    xlabel: str = "Период, №",
) -> Path:
    img, draw = _new_canvas()
    left, top, right, bottom = _plot_frame(draw)
    ymax = _y_max([*values, hline or 0.0])
    ticks = _draw_y_axis(draw, img, left, top, right, bottom, ymax, ylabel)
    tmax = ticks[-1]

    n = len(values)
    pts: list[tuple[int, int]] = []
    xs: list[int] = []
    for i, val in enumerate(values):
        x = left + int(i * (right - left) / max(n - 1, 1))
        y = bottom - int((val / tmax) * (bottom - top))
        pts.append((x, y))
        xs.append(x)
        _center_text(draw, x, bottom + 28, xlabels[i], F_TICK)

    # заливка под линией
    if len(pts) > 1:
        poly = [(left, bottom), *pts, (right, bottom)]
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.polygon(poly, fill=(47, 117, 181, 35))
        img.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(img)
        draw.line(pts, fill=BLUE, width=8)
        for x, y in pts:
            draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=BLUE, outline=BORDER, width=3)

    if hline is not None:
        y = bottom - int((hline / tmax) * (bottom - top))
        draw.line((left, y, right, y), fill=GREEN, width=5)
        note = f"max = {_fmt(hline)} м2"
        tw, _ = _text_wh(draw, note, F_LABEL)
        draw.text((right - tw - 20, y - 70), note, fill=GREEN, font=F_LABEL)

    _draw_x_label(draw, left, right, bottom, xlabel)
    return _save(img, filename)


def pie_chart(labels: list[str], values: list[int], filename: str) -> Path:
    img, draw = _new_canvas()
    total = sum(values) or 1
    cx, cy, r = 1180, H // 2 + 40, 520

    palette = [BLUE, GREEN, RED, "#7030A0"]
    start = 0.0
    for i, val in enumerate(values):
        extent = 360 * val / total
        draw.pieslice(
            (cx - r, cy - r, cx + r, cy + r),
            start,
            start + extent,
            fill=palette[i % len(palette)],
            outline=BORDER,
            width=4,
        )
        if val / total >= 0.07:
            mid = math.radians(start + extent / 2)
            tx = cx + int(0.62 * r * math.cos(mid))
            ty = cy + int(0.62 * r * math.sin(mid))
            _center_text(draw, tx, ty - 20, f"{100 * val / total:.0f}%", F_LABEL)
        start += extent

    lx, ly = 2100, 620
    for i, (label, val) in enumerate(zip(labels, values)):
        pct = 100 * val / total
        draw.rectangle((lx, ly, lx + 44, ly + 44), fill=palette[i % len(palette)], outline=BORDER, width=3)
        draw.text((lx + 62, ly + 2), f"{label} - {val} шт. ({pct:.0f}%)", fill=BORDER, font=F_LABEL)
        ly += 72

    return _save(img, filename)


def read_abc_groups() -> dict[str, int]:
    with (BASE / "результаты_ABC_XYZ.tsv").open(encoding="utf-8") as f:
        counts = Counter(r["group"] for r in csv.DictReader(f, delimiter="\t"))
    return {g: counts.get(g, 0) for g in ABC_GROUPS}


def compute_group_daily_costs() -> tuple[list[str], list[float], list[str]]:
    """Суточные TC по группам для рис. 4.1 (логика гл. 4)."""
    import math

    with (BASE / "приложение_А_исходные_данные_50.tsv").open(encoding="utf-8") as f:
        src = {r["code"]: r for r in csv.DictReader(f, delimiter="\t")}
    with (BASE / "результаты_ABC_XYZ.tsv").open(encoding="utf-8") as f:
        abc = list(csv.DictReader(f, delimiter="\t"))

    groups: dict[str, list[dict[str, str]]] = {}
    for r in abc:
        groups.setdefault(r["group"], []).append(r)

    def fv(code: str, key: str) -> float:
        return float(src[code][key])

    tc: dict[str, float] = {g: 0.0 for g in ABC_GROUPS}

    bx = groups.get("BX", [])
    if bx:
        kavg = sum(fv(r["code"], "order_cost_K") for r in bx) / len(bx)
        tc["BX"] = sum(
            math.sqrt(2 * kavg * fv(r["code"], "holding_cost_h") * fv(r["code"], "demand_v"))
            for r in bx
        )

    for g in ("AY", "BY", "CY"):
        rows = groups.get(g, [])
        if not rows:
            continue
        ksum = sum(fv(r["code"], "order_cost_K") for r in rows)
        hv = sum(fv(r["code"], "demand_v") * fv(r["code"], "holding_cost_h") for r in rows)
        tstar = math.sqrt(2 * ksum / hv)
        tc[g] = sum(
            math.sqrt(
                2
                * (fv(r["code"], "order_cost_K") / tstar)
                * fv(r["code"], "holding_cost_h")
                * fv(r["code"], "demand_v")
            )
            for r in rows
        )

    for g in ("AZ", "BZ"):
        tc[g] = sum(
            math.sqrt(
                2
                * fv(r["code"], "order_cost_K")
                * fv(r["code"], "holding_cost_h")
                * fv(r["code"], "demand_v")
            )
            for r in groups.get(g, [])
        )

    labels, values, colors = [], [], []
    for g in ABC_GROUPS:
        if tc[g] <= 0:
            continue
        labels.append(g)
        values.append(round(tc[g], 2))
        colors.append(ABC_COLORS[g[0]])
    return labels, values, colors


def chart_group_costs() -> Path:
    labels, values, colors = compute_group_daily_costs()
    return bar_chart(
        labels,
        values,
        "Суточные издержки, ден. ед.",
        "fig_4_1_group_costs.png",
        colors=colors,
        xlabel="Группа ABC-XYZ",
    )


def main() -> None:
    abc = read_abc_groups()
    abc_colors = [ABC_COLORS[g[0]] for g in ABC_GROUPS]
    bar_chart(
        ABC_GROUPS,
        [float(abc[g]) for g in ABC_GROUPS],
        "Число номенклатур, шт.",
        "fig_1_1_abc_distribution.png",
        colors=abc_colors,
        xlabel="Группа ABC-XYZ",
    )

    with (BASE / "приложение_А_исходные_данные_50.tsv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    buckets = {
        "до 100 руб.": 0,
        "100-300 руб.": 0,
        "300-500 руб.": 0,
        "свыше 500 руб.": 0,
    }
    for r in rows:
        c = float(r["unit_price_c"])
        if c < 100:
            buckets["до 100 руб."] += 1
        elif c < 300:
            buckets["100-300 руб."] += 1
        elif c < 500:
            buckets["300-500 руб."] += 1
        else:
            buckets["свыше 500 руб."] += 1
    pie_chart(
        list(buckets.keys()),
        list(buckets.values()),
        "fig_1_2_price_structure.png",
    )

    strategies = compute_bz_strategies()
    bar_chart(
        ["Раздельная\nоптимизация", "Полное\nсовмещение", "Частичное\nсовмещение"],
        [strategies[n][0] for n in STRATEGY_NAMES],
        "Суточные издержки, ден. ед.",
        "fig_5_1_bz_costs.png",
        highlight_min=True,
        xlabel="Стратегия управления запасами",
    )

    areas, peak = compute_bz_warehouse_areas()
    line_chart(
        [str(i) for i in range(1, 13)],
        areas,
        "Занятая площадь, м2",
        "fig_5_2_warehouse_bz.png",
        hline=peak,
    )

    capital = compute_bz_capital()
    bar_chart(
        ["Раздельная\nоптимизация", "Полное\nсовмещение", "Частичное\nсовмещение"],
        [capital[n] for n in STRATEGY_NAMES],
        "Капиталовложения, руб.",
        "fig_5_3_capital_bz.png",
        highlight_min=True,
        xlabel="Стратегия управления запасами",
    )

    chart_group_costs()

    for name in [
        "fig_1_1_abc_distribution.png",
        "fig_1_2_price_structure.png",
        "fig_4_1_group_costs.png",
        "fig_5_1_bz_costs.png",
        "fig_5_2_warehouse_bz.png",
        "fig_5_3_capital_bz.png",
    ]:
        print(f"Created: {OUT / name}")


if __name__ == "__main__":
    main()
