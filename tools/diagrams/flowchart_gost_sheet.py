"""Схема алгоритма на листе чертежа — три колонки, как в образце ПСП."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
FONT_B = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_B if bold and FONT_B.exists() else FONT), size=size)


class SheetFlowchart:
    def __init__(self, width: int, height: int):
        self.img = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.img)
        self.W, self.H = width, height
        self.f = _font(max(22, width // 90))
        self.fs = _font(max(18, width // 110))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path, "PNG", optimize=True)

    def _text_center(self, box, text, font=None):
        font = font or self.f
        x1, y1, x2, y2 = box
        lines = text.split("\n")
        lh = font.size + 8
        total = len(lines) * lh
        y = y1 + (y2 - y1 - total) // 2
        for line in lines:
            bb = self.draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            self.draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill="black", font=font)
            y += lh

    def _arrow(self, p1, p2):
        self.draw.line([p1, p2], fill="black", width=3)
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        sz = max(12, self.W // 250)
        self.draw.polygon(
            [
                p2,
                (p2[0] + sz * math.cos(ang + 2.6), p2[1] + sz * math.sin(ang + 2.6)),
                (p2[0] + sz * math.cos(ang - 2.6), p2[1] + sz * math.sin(ang - 2.6)),
            ],
            fill="black",
        )

    def _connect(self, y_from, y_to, x):
        self._arrow((x, y_from), (x, y_to))

    def _polyline(self, pts, arrow=True):
        for i in range(len(pts) - 1):
            self.draw.line([pts[i], pts[i + 1]], fill="black", width=3)
        if arrow and len(pts) >= 2:
            self._arrow(pts[-2], pts[-1])

    def terminal(self, cx, y, text, w=None):
        w = w or int(self.W * 0.11)
        h = int(self.H * 0.045)
        box = (cx - w // 2, y, cx + w // 2, y + h)
        self.draw.rounded_rectangle(box, radius=h // 2, outline="black", width=3)
        self._text_center(box, text)
        return box

    def process(self, cx, y, text, *, subprocess=False, w=None):
        w = w or int(self.W * 0.14)
        h = int(self.H * 0.055)
        box = (cx - w // 2, y, cx + w // 2, y + h)
        self.draw.rectangle(box, outline="black", width=3)
        if subprocess:
            pad = max(10, w // 22)
            self.draw.line([(box[0] + pad, box[1]), (box[0] + pad, box[3])], fill="black", width=3)
            self.draw.line([(box[2] - pad, box[1]), (box[2] - pad, box[3])], fill="black", width=3)
        self._text_center(box, text, self.fs)
        return box

    def io(self, cx, y, text, w=None):
        w = w or int(self.W * 0.13)
        h = int(self.H * 0.055)
        pad = int(w * 0.07)
        x1, x2 = cx - w // 2, cx + w // 2
        pts = [(x1 + pad, y), (x2, y), (x2 - pad, y + h), (x1, y + h)]
        self.draw.polygon(pts, outline="black", width=3)
        self._text_center((x1 + pad, y, x2 - pad, y + h), text, self.fs)
        return (x1, y, x2, y + h)

    def decision(self, cx, y, text, w=None):
        w = w or int(self.W * 0.12)
        h = int(self.H * 0.08)
        cy = y + h // 2
        pts = [(cx, y), (cx + w // 2, cy), (cx, y + h), (cx - w // 2, cy)]
        self.draw.polygon(pts, outline="black", width=3)
        self._text_center((cx - w // 2 + 12, y + 8, cx + w // 2 - 12, y + h - 8), text, self.fs)
        return (cx - w // 2, y, cx + w // 2, y + h)

    def connector(self, cx, y, num: str):
        r = int(self.H * 0.022)
        self.draw.ellipse((cx - r, y - r, cx + r, y + r), outline="black", width=3)
        bb = self.draw.textbbox((0, 0), num, font=self.f)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        self.draw.text((cx - tw // 2, y - th // 2 - 2), num, fill="black", font=self.f)
        return (cx - r, y - r, cx + r, y + r)

    def label(self, xy, text):
        self.draw.text(xy, text, fill="black", font=self.fs)


def draw_donation_sheet(path: Path, width: int = 5200, height: int = 3600):
    g = SheetFlowchart(width, height)
    c1 = int(width * 0.17)
    c2 = int(width * 0.50)
    c3 = int(width * 0.83)
    y = int(height * 0.04)
    step = int(height * 0.085)

    b0 = g.terminal(c1, y, "Начало")
    y += step
    g._connect(b0[3], y, c1)
    b1 = g.io(c1, y, "Ввод campaignId,\namount, donorName")
    y += step
    g._connect(b1[3], y, c1)
    d1 = g.decision(c1, y, "amount > 0?")
    end_y = int(height * 0.88)
    end_b = g.terminal(c3, end_y, "Конец")

    dy = (d1[1] + d1[3]) // 2
    err = g.process(c1 + int(width * 0.14), dy - 40, "Вывод: некорректная\nсумма", subprocess=True, w=int(width * 0.12))
    g._polyline([(d1[2], dy), (err[0], dy)])
    g.label((d1[2] + 6, dy - 28), "Нет")
    ex = (end_b[0] + end_b[2]) // 2
    merge = end_b[1] - int(height * 0.04)
    ix = (err[0] + err[2]) // 2
    g._polyline([(ix, err[3]), (ix, merge), (ex, merge)], arrow=False)
    g._arrow((ex, merge), (ex, end_b[1]))

    y += int(height * 0.11)
    g.label((c1 + 6, d1[3] + 4), "Да")
    g._connect(d1[3], y, c1)
    d2 = g.decision(c1, y, "anonymous\n== true?")
    y += int(height * 0.11)
    g.label((c1 + 6, d2[3] + 4), "Нет")
    g._connect(d2[3], y, c1)
    b3 = g.process(c1, y, "INSERT INTO donors", subprocess=True)

    dy2 = (d2[1] + d2[3]) // 2
    g.label((c1 - 50, dy2 - 24), "Да")
    anon = g.process(c1 - int(width * 0.12), dy2 - 30, 'Имя = "Анонимный\nжертвователь"', subprocess=True, w=int(width * 0.12))
    g._polyline([(d2[0], dy2), (anon[2], dy2)])
    join_y = y + int(height * 0.02)
    g._polyline([(anon[0] + (anon[2] - anon[0]) // 2, anon[3]), (anon[0] + (anon[2] - anon[0]) // 2, join_y), (c1, join_y)], arrow=False)

    conn1 = g.connector(c1, int(height * 0.52), "1")
    g._connect(b3[3], conn1[1], c1)

    y2 = int(height * 0.08)
    g.connector(c2, y2, "1")
    b4 = g.process(c2, y2 + int(height * 0.04), "INSERT INTO donations", subprocess=True)
    y2 = b4[3] + int(height * 0.04)
    g._connect(b4[3], y2, c2)
    b5 = g.process(c2, y2, "Пересчёт collected\nпо кампании", subprocess=True)
    conn2 = g.connector(c2, b5[3] + int(height * 0.05), "2")

    y3 = int(height * 0.12)
    g.connector(c3, y3, "2")
    b6 = g.process(c3, y3 + int(height * 0.04), "Вернуть результат\nна клиент")
    y3 = b6[3] + int(height * 0.04)
    g._connect(b6[3], y3, c3)
    b7 = g.io(c3, y3, "Отобразить сообщение\nв интерфейсе JavaFX")
    g._connect(b7[3], end_b[1], c3)

    g.save(path)
