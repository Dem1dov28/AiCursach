#!/usr/bin/env python3
"""IDEF0: PNG из ПСП_Ивановская + замена всех подписей под CharityLedger."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "Материалы" / "эталон_пример"
OUT = ROOT / "Материалы" / "Диаграммы" / "png"
FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size=size)


def _bg(img: Image.Image) -> str:
    r, g, b = img.getpixel((12, 12))[:3]
    return f"#{r:02x}{g:02x}{b:02x}"


def _box_white(img: Image.Image) -> str:
    # внутри IDEF-блока фон белый
    w, h = img.size
    r, g, b = img.getpixel((int(w * 0.18), int(h * 0.38)))[:3]
    return f"#{r:02x}{g:02x}{b:02x}"


def _patch(img: Image.Image, draw: ImageDraw.ImageDraw, box, text: str, size: int, bg: str):
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=bg, outline=bg)
    if not text:
        return
    font = _font(size)
    lines = text.split("\n")
    lh = size + 4
    total = len(lines) * lh
    y = y1 + max(4, (y2 - y1 - total) // 2)
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill="black", font=font)
        y += lh


def _expand_box(box: tuple, pad: float = 0.012) -> tuple:
    x1, y1, x2, y2 = box
    return (max(0, x1 - pad), max(0, y1 - pad), min(1, x2 + pad), min(1, y2 + pad))


def _text_wipes_from_borders(src: Path, borders: list[tuple], pad: float = 0.01) -> list[tuple]:
    """Зачистка только текста внутри рамок блоков (стрелки не затрагиваются)."""
    img = Image.open(src).convert("RGB")
    w, h = img.size
    bg = img.getpixel((int(w * 0.15), int(h * 0.32)))[:3]
    wipes: list[tuple] = []
    inset = 0.006
    for xl, yt, xr, yb in borders:
        dark: list[tuple[int, int]] = []
        for y in range(int((yt + inset) * h), int((yb - inset) * h)):
            for x in range(int((xl + inset) * w), int((xr - inset) * w)):
                p = img.getpixel((x, y))
                if sum(p) < 500 and abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 35:
                    dark.append((x, y))
        if dark:
            xs = [d[0] for d in dark]
            ys = [d[1] for d in dark]
            wipes.append(_expand_box((min(xs) / w, min(ys) / h, max(xs) / w, max(ys) / h), pad))
    return wipes


def _wipe_bands(img: Image.Image, draw: ImageDraw.ImageDraw, bg: str, *, top=0.14, bottom=0.14, left=0.16):
    w, h = img.size
    if top:
        draw.rectangle((0, 0, w, int(h * top)), fill=bg)
    if bottom:
        draw.rectangle((0, int(h * (1 - bottom)), w, h), fill=bg)
    if left:
        draw.rectangle((0, int(h * 0.28), int(w * left), int(h * 0.58)), fill=bg)


def _inside_boxes(rx1: float, ry1: float, rx2: float, ry2: float, box_wipes: list[tuple] | None) -> bool:
    cx, cy = (rx1 + rx2) / 2, (ry1 + ry2) / 2
    for bx1, by1, bx2, by2 in box_wipes or []:
        if bx1 <= cx <= bx2 and by1 <= cy <= by2:
            return True
    return False


def _adapt(
    src: Path,
    dst: Path,
    patches: list[tuple],
    *,
    scale: float = 2.0,
    wipe: bool = True,
    box_wipes: list[tuple] | None = None,
):
    img = Image.open(src).convert("RGB")
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    bg = _bg(img)
    white = _box_white(img)
    w, h = img.size
    if wipe:
        _wipe_bands(img, draw, bg)
    if box_wipes:
        for rx1, ry1, rx2, ry2 in box_wipes:
            draw.rectangle(
                (int(rx1 * w), int(ry1 * h), int(rx2 * w), int(ry2 * h)),
                fill=white,
                outline=white,
            )
    for rx1, ry1, rx2, ry2, text, size in patches:
        box = (int(rx1 * w), int(ry1 * h), int(rx2 * w), int(ry2 * h))
        fill = white if _inside_boxes(rx1, ry1, rx2, ry2, box_wipes) else bg
        _patch(img, draw, box, text, size, fill)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG", optimize=True)
    print(f"  SAMPLE→{dst.name}")


def run():
    ctx_src = SAMPLE / "03_Рисунок_2_2_Контекстная_диаграмма_верхнего_уровня.png"
    ctx_boxes = _text_wipes_from_borders(
        ctx_src,
        [
            (0.098, 0.254, 0.269, 0.42),
            (0.262, 0.354, 0.433, 0.55),
            (0.426, 0.454, 0.597, 0.66),
            (0.550, 0.554, 0.721, 0.76),
            (0.724, 0.654, 0.895, 0.86),
        ],
    )
    ctx_titles = [
        (b[0], b[1], b[2], b[3], t, 19)
        for b, t in zip(
            ctx_boxes,
            [
                "Регистрировать\nпожертвования",
                "Учитывать\nрасходы",
                "Рассчитывать\nбаланс",
                "Публиковать\nотчёты",
                "Управлять\nкампаниями",
            ],
        )
    ]
    # --- Рис. 2.2 (5 блоков) ---
    _adapt(
        ctx_src,
        OUT / "02_idef0_context.png",
        [
            (0.00, 0.26, 0.16, 0.36, "", 10),
            (0.00, 0.36, 0.16, 0.46, "", 10),
            (0.00, 0.30, 0.14, 0.40, "Пожертвования\nдоноров", 14),
            (0.00, 0.42, 0.14, 0.52, "Заявки на помощь", 14),
            (0.88, 0.48, 0.98, 0.56, "", 10),
            (0.88, 0.58, 0.98, 0.66, "", 10),
            (0.88, 0.68, 0.98, 0.78, "", 10),
            (0.88, 0.78, 0.98, 0.88, "", 10),
            (0.18, 0.04, 0.40, 0.13, "Политика фонда", 14),
            (0.40, 0.04, 0.78, 0.13, "Закон о благотворительной\nдеятельности", 13),
            (0.16, 0.90, 0.36, 0.99, "CharityLedger", 15),
            (0.36, 0.90, 0.56, 0.99, "Оператор фонда", 15),
            (0.56, 0.90, 0.76, 0.99, "Администратор", 15),
            (0.28, 0.48, 0.44, 0.54, "Зарегистрированные\nпожертвования", 11),
            (0.38, 0.58, 0.54, 0.64, "Данные о расходах", 11),
            (0.48, 0.68, 0.64, 0.74, "Рассчитанный баланс", 11),
            (0.58, 0.78, 0.76, 0.84, "Публичные отчёты", 11),
            (0.58, 0.52, 0.78, 0.58, "Баланс кампаний", 11),
            # затереть старые подписи между блоками
            (0.14, 0.48, 0.30, 0.56, "", 10),
            (0.24, 0.58, 0.40, 0.66, "", 10),
            (0.34, 0.68, 0.50, 0.76, "", 10),
            (0.44, 0.78, 0.60, 0.86, "", 10),
            (0.88, 0.56, 0.98, 0.64, "", 10),
            (0.88, 0.66, 0.98, 0.74, "", 10),
            *ctx_titles,
        ],
        wipe=True,
        box_wipes=ctx_boxes,
    )

    decomp_src = SAMPLE / "04_Рисунок_2_3_Декомпозиция_контекстной_диаграммы_верхнего_ур.png"
    decomp_boxes = _text_wipes_from_borders(
        decomp_src,
        [
            (0.135, 0.305, 0.272, 0.440),
            (0.326, 0.385, 0.464, 0.520),
            (0.517, 0.465, 0.655, 0.600),
            (0.708, 0.545, 0.846, 0.680),
        ],
    )
    decomp_titles = [
        (b[0], b[1], b[2], b[3], t, 18)
        for b, t in zip(
            decomp_boxes,
            [
                "Проанализировать\nпотребности кампании",
                "Определить источники\nфинансирования",
                "Зарегистрировать\nпоступления",
                "Согласовать\nрасходы",
            ],
        )
    ]
    # --- Рис. 2.3 (4 блока) ---
    _adapt(
        decomp_src,
        OUT / "02_idef0_decompose.png",
        [
            (0.00, 0.32, 0.12, 0.40, "Отчёты за период", 14),
            (0.00, 0.42, 0.12, 0.50, "Прогноз сбора средств", 13),
            (0.10, 0.02, 0.45, 0.12, "Закон о благотворительной\nдеятельности", 13),
            (0.45, 0.02, 0.72, 0.12, "Положение о фонде", 14),
            (0.10, 0.88, 0.35, 0.98, "CharityLedger", 15),
            (0.35, 0.88, 0.60, 0.98, "Оператор фонда", 15),
            (0.00, 0.88, 0.10, 0.98, "", 12),
            (0.60, 0.88, 1.00, 0.98, "", 12),
            (0.32, 0.50, 0.52, 0.56, "Выявленные потребности", 12),
            (0.52, 0.60, 0.72, 0.66, "Источники финансирования", 11),
            (0.72, 0.70, 0.92, 0.76, "Зарегистрированные\nпоступления", 12),
            (0.84, 0.74, 1.00, 0.82, "Подтверждённые расходы", 12),
            *decomp_titles,
        ],
        box_wipes=decomp_boxes,
    )

    don_src = SAMPLE / "05_Рисунок_2_4_Декомпозиция_блока_Планировать_поступления_.png"
    don_boxes = _text_wipes_from_borders(
        don_src,
        [
            (0.117, 0.315, 0.255, 0.450),
            (0.321, 0.395, 0.459, 0.530),
            (0.525, 0.475, 0.663, 0.610),
            (0.729, 0.555, 0.867, 0.690),
        ],
    )
    don_titles = [
        (b[0], b[1], b[2], b[3], t, 18 if i < 1 else 17)
        for i, (b, t) in enumerate(
            zip(
                don_boxes,
                [
                    "Выбрать\nкампанию",
                    "Ввести данные\nдонора и сумму",
                    "Сохранить\nпожертвование",
                    "Обновить баланс\nкампании",
                ],
            )
        )
    ]
    # --- Рис. 2.4 ---
    _adapt(
        don_src,
        OUT / "02_idef0_donations.png",
        [
            (0.00, 0.34, 0.12, 0.42, "Заявка донора", 14),
            (0.00, 0.44, 0.12, 0.52, "Список кампаний", 13),
            (0.10, 0.02, 0.45, 0.12, "Закон о благотворительной\nдеятельности", 13),
            (0.45, 0.02, 0.72, 0.12, "Положение о фонде", 14),
            (0.10, 0.88, 0.35, 0.98, "CharityLedger", 15),
            (0.35, 0.88, 0.60, 0.98, "Жертвователь", 15),
            (0.00, 0.88, 0.10, 0.98, "", 12),
            (0.60, 0.88, 1.00, 0.98, "", 12),
            (0.32, 0.52, 0.52, 0.58, "Выбранная кампания", 12),
            (0.52, 0.62, 0.72, 0.68, "Данные пожертвования", 12),
            (0.72, 0.72, 0.92, 0.78, "Запись в БД", 12),
            (0.84, 0.76, 1.00, 0.84, "Обновлённый баланс", 12),
            *don_titles,
        ],
        box_wipes=don_boxes,
    )

    exp_src = SAMPLE / "06_Рисунок_2_5_Декомпозиция_блока_Обновлять_запасы_.png"
    exp_boxes = _text_wipes_from_borders(
        exp_src,
        [
            (0.166, 0.315, 0.340, 0.470),
            (0.405, 0.435, 0.579, 0.590),
            (0.645, 0.555, 0.819, 0.710),
        ],
    )
    exp_titles = [
        (b[0], b[1], b[2], b[3], t, 20)
        for b, t in zip(
            exp_boxes,
            [
                "Проверить полномочия\nоператора",
                "Сравнить расход\nс балансом",
                "Зафиксировать\nрасход",
            ],
        )
    ]
    # --- Рис. 2.5 (3 блока) ---
    _adapt(
        exp_src,
        OUT / "02_idef0_expenses.png",
        [
            (0.00, 0.36, 0.14, 0.44, "Данные расхода", 15),
            (0.00, 0.46, 0.16, 0.56, "Подтверждающий\nдокумент", 14),
            (0.06, 0.04, 0.46, 0.13, "Закон о благотворительной\nдеятельности", 14),
            (0.46, 0.04, 0.74, 0.13, "Положение о фонде", 15),
            (0.10, 0.90, 0.36, 0.99, "CharityLedger", 16),
            (0.36, 0.90, 0.62, 0.99, "Оператор фонда", 16),
            (0.34, 0.48, 0.58, 0.56, "Подтверждённые\nполномочия", 13),
            (0.56, 0.62, 0.80, 0.70, "Проверенный расход", 13),
            (0.78, 0.64, 1.00, 0.76, "Запись в таблице\nexpenses", 14),
            *exp_titles,
        ],
        box_wipes=exp_boxes,
    )

    rep_titles = [
        (b[0], b[1], b[2], b[3], t, 18 if i < 2 else 17)
        for i, (b, t) in enumerate(
            zip(
                exp_boxes,
                [
                    "Суммировать\nпожертвования",
                    "Суммировать\nрасходы",
                    "Подготовить\nпубличный отчёт",
                ],
            )
        )
    ]
    # --- Рис. 2.6 (тот же шаблон, другие подписи) ---
    _adapt(
        exp_src,
        OUT / "02_idef0_reports.png",
        [
            (0.00, 0.36, 0.12, 0.44, "Данные кампании", 14),
            (0.06, 0.02, 0.55, 0.12, "Требования к отчётности фонда", 13),
            (0.08, 0.88, 0.34, 0.98, "CharityLedger", 15),
            (0.34, 0.88, 0.60, 0.98, "Оператор фонда", 15),
            (0.00, 0.88, 0.08, 0.98, "", 12),
            (0.60, 0.88, 1.00, 0.98, "", 12),
            (0.34, 0.50, 0.56, 0.56, "Сумма поступлений", 12),
            (0.56, 0.64, 0.78, 0.70, "Сумма расходов", 12),
            (0.78, 0.66, 1.00, 0.76, "Отчёт прозрачности", 13),
            *rep_titles,
        ],
        box_wipes=exp_boxes,
    )


if __name__ == "__main__":
    run()
