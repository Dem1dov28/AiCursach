"""Рамка и основная надпись чертежа (ГОСТ 2.104 / форма 1)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"

# A1 альбомная, 150 dpi
A1_LANDSCAPE = (7016, 4961)  # 841×594 mm


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size=size)


def _text(draw, xy, text, font, anchor="la"):
    draw.text(xy, text, fill="black", font=font, anchor=anchor)


def _text_center(draw, box, text, font):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    lh = font.size + 6
    total = len(lines) * lh
    y = y1 + (y2 - y1 - total) // 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill="black", font=font)
        y += lh


def draw_gost_frame(
    width: int,
    height: int,
    *,
    doc_code: str,
    title: str,
    sheet: int = 1,
    sheets: int = 1,
    developer: str,
    checker: str,
    group: str,
    rows: str = "ABCDEFGHIJKLMNOPQR",
    cols: int = 17,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Возвращает изображение и прямоугольник области чертежа (внутри рамки)."""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    f = _font(28)
    fs = _font(22)
    fxs = _font(18)

    margin = int(width * 0.018)
    stamp_h = int(height * 0.085)
    stamp_w = int(width * 0.38)
    left = margin
    top = margin
    right = width - margin
    bottom = height - margin
    draw.rectangle((left, top, right, bottom), outline="black", width=4)

    # координатная сетка
    usable_w = right - left - stamp_w
    usable_h = bottom - top - stamp_h
    col_w = usable_w / cols
    row_h = usable_h / len(rows)

    for i in range(cols + 1):
        x = int(left + i * col_w)
        draw.line([(x, top), (x, bottom - stamp_h)], fill="black", width=1)
    for j in range(len(rows) + 1):
        y = int(top + j * row_h)
        draw.line([(left, y), (right - stamp_w, y)], fill="black", width=1)

    # подписи координат
    for i in range(cols):
        num = f"{i + 1:02d}"
        x = left + (i + 0.35) * col_w
        _text(draw, (x, top - 2), num, fxs, anchor="ls")
        _text(draw, (x, bottom - stamp_h + 4), num, fxs, anchor="ls")
    for j, letter in enumerate(rows):
        y = top + (j + 0.25) * row_h
        _text(draw, (left - 6, y), letter, fxs, anchor="rs")
        _text(draw, (right - stamp_w + 8, y), letter, fxs, anchor="ls")

    # основная надпись
    sx = right - stamp_w
    sy = bottom - stamp_h
    draw.rectangle((sx, sy, right, bottom), outline="black", width=2)
    # верхняя полоса
    h1 = int(stamp_h * 0.22)
    draw.line([(sx, sy + h1), (right, sy + h1)], fill="black", width=2)
    draw.line([(sx + int(stamp_w * 0.52), sy), (sx + int(stamp_w * 0.52), sy + h1)], fill="black", width=2)
    _text_center(draw, (sx, sy, sx + int(stamp_w * 0.52), sy + h1), doc_code.replace(".", "\n"), fs)
    _text_center(draw, (sx + int(stamp_w * 0.52), sy, right, sy + h1), title, f)

    # строки подписей
    row_h2 = int((stamp_h - h1) / 6)
    y0 = sy + h1
    labels = ["Изм", "Лист", "№ докум.", "Подп.", "Дата", "Лит.", "Масса", "Масштаб"]
    x_cols = [sx, sx + int(stamp_w * 0.06), sx + int(stamp_w * 0.14), sx + int(stamp_w * 0.22),
              sx + int(stamp_w * 0.30), sx + int(stamp_w * 0.38), sx + int(stamp_w * 0.46), sx + int(stamp_w * 0.54)]
    for i, lab in enumerate(labels[:5]):
        draw.line([(x_cols[i], y0), (x_cols[i], bottom)], fill="black", width=1)
        _text(draw, (x_cols[i] + 4, y0 + 2), lab, fxs)
    draw.line([(sx + int(stamp_w * 0.62), y0), (sx + int(stamp_w * 0.62), bottom)], fill="black", width=2)
    _text(draw, (sx + int(stamp_w * 0.64), y0 + 4), f"Лист {sheet}", fs)
    _text(draw, (sx + int(stamp_w * 0.64), y0 + row_h2 + 4), f"Листов {sheets}", fs)

    roles = [
        ("Разраб.", developer),
        ("Пров.", checker),
        ("Т.контр.", checker),
        ("Н.контр.", checker),
        ("Утв.", checker),
    ]
    for i, (role, name) in enumerate(roles):
        yy = y0 + i * row_h2
        draw.line([(sx, yy), (right, yy)], fill="black", width=1)
        _text(draw, (sx + 6, yy + 4), role, fxs)
        _text(draw, (sx + int(stamp_w * 0.18), yy + 4), name, fs)

    _text(draw, (sx + int(stamp_w * 0.64), y0 + 2 * row_h2 + 4), "Кафедра ЭИ,", fs)
    _text(draw, (sx + int(stamp_w * 0.64), y0 + 3 * row_h2 + 4), f"группа {group}", fs)

    content = (
        int(left + col_w * 0.4),
        int(top + row_h * 0.4),
        int(right - stamp_w - col_w * 0.3),
        int(bottom - stamp_h - row_h * 0.3),
    )
    return img, content


def paste_centered(base: Image.Image, content_box: tuple, inner: Image.Image, *, margin: int = 20):
    x1, y1, x2, y2 = content_box
    area_w, area_h = x2 - x1 - 2 * margin, y2 - y1 - 2 * margin
    iw, ih = inner.size
    scale = min(area_w / iw, area_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = inner.resize((nw, nh), Image.Resampling.LANCZOS)
    px = x1 + margin + (area_w - nw) // 2
    py = y1 + margin + (area_h - nh) // 2
    base.paste(resized, (px, py))
