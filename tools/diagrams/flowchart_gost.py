"""Блок-схемы по ГОСТ 19.701-90 (как в ПСП_Ивановская)."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
FONT_B = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_B if bold and FONT_B.exists() else FONT
    return ImageFont.truetype(str(path), size=size)


class GostFlowchart:
    def __init__(self, width: int = 900, height: int = 1500):
        self.W, self.H = width, height
        self.img = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.img)
        self.cx = width // 2
        self.f = _font(20)
        self.fs = _font(18)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path, "PNG", optimize=True)

    def _text_center(self, box, text: str, font=None):
        font = font or self.f
        x1, y1, x2, y2 = box
        lines = text.split("\n")
        lh = font.size + 5
        total = len(lines) * lh
        y = y1 + (y2 - y1 - total) // 2
        for line in lines:
            bb = self.draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            self.draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill="black", font=font)
            y += lh

    def _arrow(self, p1, p2):
        self.draw.line([p1, p2], fill="black", width=2)
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        sz = 10
        self.draw.polygon(
            [
                p2,
                (p2[0] + sz * math.cos(ang + 2.6), p2[1] + sz * math.sin(ang + 2.6)),
                (p2[0] + sz * math.cos(ang - 2.6), p2[1] + sz * math.sin(ang - 2.6)),
            ],
            fill="black",
        )

    def _connect(self, y_from: int, y_to: int, x: int | None = None):
        x = x or self.cx
        self._arrow((x, y_from), (x, y_to))

    def _polyline(self, points: list[tuple[int, int]], *, arrow: bool = True):
        for i in range(len(points) - 1):
            self.draw.line([points[i], points[i + 1]], fill="black", width=2)
        if arrow and len(points) >= 2:
            self._arrow(points[-2], points[-1])

    def _route_v_down(self, x: int, y_from: int, y_to: int):
        self._polyline([(x, y_from), (x, y_to)])

    def _merge_boxes(self, boxes: list[tuple], end_box: tuple):
        ex = (end_box[0] + end_box[2]) // 2
        merge_y = end_box[1] - 40
        for box in boxes:
            sx = (box[0] + box[2]) // 2
            self._polyline([(sx, box[3]), (sx, merge_y), (ex, merge_y)], arrow=False)
        self._arrow((ex, merge_y), (ex, end_box[1]))

    def terminal(self, y: int, text: str, *, cx: int | None = None) -> tuple[int, int, int, int]:
        cx = cx or self.cx
        w, h = 180, 50
        box = (cx - w // 2, y, cx + w // 2, y + h)
        self.draw.rounded_rectangle(box, radius=25, outline="black", width=2)
        self._text_center(box, text)
        return box

    def process(self, y: int, text: str, *, subprocess: bool = False, cx: int | None = None, width: int = 340) -> tuple:
        cx = cx or self.cx
        h = 58
        box = (cx - width // 2, y, cx + width // 2, y + h)
        self.draw.rectangle(box, outline="black", width=2)
        if subprocess:
            self.draw.line([(box[0] + 14, box[1]), (box[0] + 14, box[3])], fill="black", width=2)
            self.draw.line([(box[2] - 14, box[1]), (box[2] - 14, box[3])], fill="black", width=2)
        self._text_center(box, text)
        return box

    def io_at(self, cx: int, y: int, text: str, width: int = 300) -> tuple:
        h = 56
        pad = 20
        x1, x2 = cx - width // 2, cx + width // 2
        pts = [(x1 + pad, y), (x2, y), (x2 - pad, y + h), (x1, y + h)]
        self.draw.polygon(pts, outline="black", width=2)
        self._text_center((x1 + pad, y, x2 - pad, y + h), text, self.fs)
        return (x1, y, x2, y + h)

    def io(self, y: int, text: str) -> tuple:
        return self.io_at(self.cx, y, text)

    def decision(self, y: int, text: str, *, cx: int | None = None) -> tuple:
        cx = cx or self.cx
        w, h = 280, 96
        cy = y + h // 2
        pts = [(cx, y), (cx + w // 2, cy), (cx, y + h), (cx - w // 2, cy)]
        self.draw.polygon(pts, outline="black", width=2)
        self._text_center((cx - w // 2 + 16, y + 8, cx + w // 2 - 16, y + h - 8), text, self.fs)
        return (cx - w // 2, y, cx + w // 2, y + h)

    def loop(self, y: int, text: str) -> tuple:
        w, h = 320, 48
        x1, y1 = self.cx - w // 2, y
        x2, y2 = self.cx + w // 2, y + h
        notch = 18
        pts = [
            (x1 + notch, y1), (x2 - notch, y1), (x2, y1 + h // 2),
            (x2 - notch, y2), (x1 + notch, y2), (x1, y1 + h // 2),
        ]
        self.draw.polygon(pts, outline="black", width=2)
        self._text_center((x1 + notch, y1, x2 - notch, y2), text, self.fs)
        return (x1, y1, x2, y2)

    def label(self, xy, text: str):
        self.draw.text(xy, text, fill="black", font=self.fs)

    def branch_no_to_end(self, dec_box, msg: str, end_box, *, side: str = "right"):
        dy = (dec_box[1] + dec_box[3]) // 2
        if side == "left":
            io_cx = max(dec_box[0] - 200, 130)
            io_box = self.io_at(io_cx, dy - 28, msg, width=250)
            self._polyline([(dec_box[0], dy), (io_box[2], dy)])
            self.label((dec_box[0] - 42, dy - 20), "Нет")
            ix = (io_box[0] + io_box[2]) // 2
        else:
            dx = dec_box[2]
            io_cx = min(dx + 200, self.W - 150)
            io_box = self.io_at(io_cx, dy - 28, msg, width=250)
            self._polyline([(dx, dy), (io_box[0], dy)])
            self.label((dx + 8, dy - 20), "Нет")
            ix = (io_box[0] + io_box[2]) // 2
        ex = (end_box[0] + end_box[2]) // 2
        merge = end_box[1] - 40
        self._polyline([(ix, io_box[3]), (ix, merge), (ex, merge)], arrow=False)
        self._arrow((ex, merge), (ex, end_box[1]))

    def branch_yes_down(self, dec_box, next_y: int):
        self.label((self.cx + 6, dec_box[3] + 2), "Да")
        self._connect(dec_box[3], next_y)


def draw_algo_client_server(path: Path):
    g = GostFlowchart(920, 1280)
    g.cx = 460
    y = 40
    b0 = g.terminal(y, "Начало")
    y += 80
    g._connect(b0[3], y)
    b1 = g.process(y, "Создание ClientConnection", subprocess=True)
    y += 90
    g._connect(b1[3], y)
    b2 = g.process(y, "Подключение к серверу :9090", subprocess=True)
    y += 90
    g._connect(b2[3], y)
    d1 = g.decision(y, "Соединение\nустановлено?")
    y += 130
    end_b = g.terminal(1180, "Конец")
    g.branch_no_to_end(d1, "Вывод: сервер\nнедоступен", end_b)
    g.branch_yes_down(d1, y)
    b3 = g.process(y, "Формирование Request(action, payload)")
    y += 90
    g._connect(b3[3], y)
    b4 = g.process(y, "Отправка Request по TCP", subprocess=True)
    y += 90
    g._connect(b4[3], y)
    b5 = g.process(y, "ClientHandler → CharityService\n→ CharityDao → SQLite", subprocess=True)
    y += 100
    g._connect(b5[3], y)
    d2 = g.decision(y, "status == OK?")
    y += 130
    g.branch_no_to_end(d2, "Вывод: сообщение\nоб ошибке", end_b)
    g.branch_yes_down(d2, y)
    b6 = g.process(y, "Обновление интерфейса JavaFX", subprocess=True)
    g._connect(b6[3], end_b[1])
    g.save(path)


def draw_algo_donation(path: Path):
    g = GostFlowchart(960, 1340)
    g.cx = 480
    y = 40
    b0 = g.terminal(y, "Начало")
    y += 78
    g._connect(b0[3], y)
    b1 = g.io(y, "Ввод campaignId,\namount, donorName")
    y += 88
    g._connect(b1[3], y)
    d1 = g.decision(y, "amount > 0?")
    y += 125
    end_b = g.terminal(1250, "Конец")
    g.branch_no_to_end(d1, "Вывод: некорректная\nсумма", end_b)
    g.branch_yes_down(d1, y)
    d2 = g.decision(y, "anonymous\n== true?")
    y += 125
    dy2 = (d2[1] + d2[3]) // 2
    join_y = y - 12
    left_cx = 175
    g.label((left_cx - 18, dy2 - 22), "Да")
    g._polyline([(d2[0], dy2), (left_cx, dy2), (left_cx, join_y - 55)], arrow=False)
    left_box = g.process(join_y - 55, 'Имя = "Анонимный\nжертвователь"', cx=left_cx, width=250, subprocess=True)
    g.label((g.cx + 6, d2[3] + 4), "Нет")
    g._connect(d2[3], y)
    b3 = g.process(y, "INSERT INTO donors", subprocess=True, width=300)
    lx = left_cx
    g._polyline([(lx, left_box[3]), (lx, join_y), (g.cx, join_y), (g.cx, y)], arrow=False)
    y += 86
    g._connect(b3[3], y)
    b4 = g.process(y, "INSERT INTO donations", subprocess=True, width=300)
    y += 86
    g._connect(b4[3], y)
    b5 = g.process(y, "Пересчёт collected\nпо кампании", subprocess=True, width=300)
    y += 86
    g._connect(b5[3], y)
    b6 = g.io(y, "Вывод: пожертвование\nзарегистрировано")
    g._connect(b6[3], end_b[1])
    g.save(path)


def draw_algo_report(path: Path):
    g = GostFlowchart(920, 1100)
    g.cx = 460
    y = 40
    b0 = g.terminal(y, "Начало")
    y += 80
    g._connect(b0[3], y)
    b1 = g.process(y, "publishReport(campaignId)")
    y += 90
    g._connect(b1[3], y)
    b2 = g.process(y, "SUM(amount) FROM donations", subprocess=True)
    y += 90
    g._connect(b2[3], y)
    b3 = g.process(y, "SUM(amount) FROM expenses", subprocess=True)
    y += 90
    g._connect(b3[3], y)
    b4 = g.process(y, "balance = donations − expenses")
    y += 90
    g._connect(b4[3], y)
    b5 = g.process(y, "INSERT transparency_reports", subprocess=True)
    y += 90
    g._connect(b5[3], y)
    b6 = g.io(y, "Вывод отчёта во вкладке\n«Прозрачность»")
    y += 90
    g._connect(b6[3], y)
    g.terminal(y, "Конец")
    g.save(path)


def draw_activity_operator(path: Path):
    """Рис. 3.18 — три роли; ветка ошибки авторизации уходит влево, без наложения."""
    g = GostFlowchart(1080, 1240)
    g.cx = 540
    y = 35
    b0 = g.terminal(y, "Начало")
    y += 72
    g._connect(b0[3], y)
    b1 = g.process(y, "Считывание данных из БД", subprocess=True, width=310)
    y += 82
    g._connect(b1[3], y)
    b2 = g.process(y, "Открытие окна авторизации", subprocess=True, width=310)
    y += 82
    g._connect(b2[3], y)
    d1 = g.decision(y, "Вход\nвыполнен?")
    end_b = g.terminal(1140, "Конец")
    # ошибка — влево, чтобы не пересекать правую ветку «Жертвователь»
    g.branch_no_to_end(d1, "Вывод: ошибка\nавторизации", end_b, side="left")
    y += 118
    g.branch_yes_down(d1, y)
    b3 = g.process(y, "Вход в систему", subprocess=True, width=260)
    y += 82
    g._connect(b3[3], y)
    d2 = g.decision(y, "Роль\nпользователя?")

    role_y = d2[3] + 95
    dy = (d2[1] + d2[3]) // 2
    cx_l, cx_c, cx_r = 220, g.cx, 860
    lane_y = dy + 48

    g._polyline([(d2[0], dy), (cx_l, dy), (cx_l, lane_y)], arrow=False)
    g._polyline([(g.cx, d2[3]), (g.cx, lane_y)], arrow=False)
    g._polyline([(d2[2], dy), (cx_r, dy), (cx_r, lane_y)], arrow=False)

    g.label((cx_l - 52, dy - 24), "Администратор")
    g.label((g.cx - 38, d2[3] + 6), "Оператор")
    g.label((cx_r - 52, dy - 24), "Жертвователь")

    g._route_v_down(cx_l, lane_y, role_y)
    g._route_v_down(g.cx, lane_y, role_y)
    g._route_v_down(cx_r, lane_y, role_y)

    b_adm = g.process(role_y, "Вкладка\n«Администрирование»", subprocess=True, cx=cx_l, width=270)
    b_op = g.process(
        role_y,
        "Учёт расходов и\nпубликация отчётов",
        subprocess=True,
        cx=cx_c,
        width=270,
    )
    b_don = g.process(
        role_y,
        "Вкладки «Кампании»,\n«Пожертвование»",
        subprocess=True,
        cx=cx_r,
        width=270,
    )
    g._merge_boxes([b_adm, b_op, b_don], end_b)
    g.save(path)
