"""IDEF0-диаграммы в стиле ПСП_Ивановская: ICOM, 0 Br, тень, каскад."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
FONT_B = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_B if bold and FONT_B.exists() else FONT
    return ImageFont.truetype(str(path), size=size)


BG = "#FFF9F0"  # фон как в ПСП_Ивановская


class Idef0Canvas:
    def __init__(self, width: int = 2228, height: int = 1234):
        self.W, self.H = width, height
        self.img = Image.new("RGB", (width, height), BG)
        self.draw = ImageDraw.Draw(self.img)
        self.f_title = _font(26)
        self.f_label = _font(22)
        self.f_small = _font(18)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path, "PNG", optimize=True)

    def _center(self, box, text: str, font):
        x1, y1, x2, y2 = box
        lines = text.split("\n")
        lh = font.size + 6
        total_h = len(lines) * lh
        y = y1 + (y2 - y1 - total_h) // 2
        for line in lines:
            bb = self.draw.textbbox((0, 0), line, font=font)
            tw = bb[2] - bb[0]
            self.draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill="black", font=font)
            y += lh

    def draw_box(self, rect: tuple[int, int, int, int], title: str, number: int):
        x1, y1, x2, y2 = rect
        for d in range(10, 0, -2):
            self.draw.rectangle((x1 + d, y1 + d, x2 + d, y2 + d), outline="#B0B0B0", width=1)
        self.draw.rectangle(rect, outline="black", width=3, fill=BG)
        self.draw.rectangle((x1 + 10, y1 + 10, x1 + 28, y1 + 28), fill="black")
        self.draw.text((x1 + 12, y2 - 34), "0 Br", fill="black", font=self.f_small)
        self.draw.text((x2 - 28, y2 - 34), str(number), fill="black", font=self.f_label)
        self._center((x1 + 8, y1 + 32, x2 - 8, y2 - 36), title, self.f_title)

    def _arrow_head(self, p1, p2, size=11):
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        a1, a2 = ang + math.pi * 0.85, ang - math.pi * 0.85
        self.draw.polygon(
            [
                p2,
                (p2[0] + size * math.cos(a1), p2[1] + size * math.sin(a1)),
                (p2[0] + size * math.cos(a2), p2[1] + size * math.sin(a2)),
            ],
            fill="black",
        )

    def _snap(self, x: int, y: int) -> tuple[int, int]:
        return int(x), int(y)

    def polyline(self, points: list[tuple[int, int]], arrow: bool = True):
        pts = [self._snap(x, y) for x, y in points]
        for i in range(len(pts) - 1):
            self.draw.line([pts[i], pts[i + 1]], fill="black", width=2)
        if arrow and len(pts) >= 2:
            self._arrow_head(pts[-2], pts[-1])

    def line(self, p1, p2, *, arrow: bool = False):
        a, b = self._snap(*p1), self._snap(*p2)
        self.draw.line([a, b], fill="black", width=2)
        if arrow:
            self._arrow_head(a, b)

    def label(self, xy: tuple[int, int], text: str):
        x, y = xy
        lh = self.f_label.size + 3
        for i, line in enumerate(text.split("\n")):
            self.draw.text((x, y + i * lh), line, fill="black", font=self.f_label)

    def cascade(self, n: int, start=(120, 340), step=(210, 95), size=(430, 165)):
        return [
            (
                start[0] + i * step[0],
                start[1] + i * step[1],
                start[0] + i * step[0] + size[0],
                start[1] + i * step[1] + size[1],
            )
            for i in range(n)
        ]

    def mid_left(self, rect):
        return rect[0], (rect[1] + rect[3]) // 2

    def mid_right(self, rect):
        return rect[2], (rect[1] + rect[3]) // 2

    def mid_top(self, rect):
        return (rect[0] + rect[2]) // 2, rect[1]

    def mid_bottom(self, rect):
        return (rect[0] + rect[2]) // 2, rect[3]

    def _edge_ys(self, box: tuple, n: int) -> list[int]:
        if n <= 1:
            return [(box[1] + box[3]) // 2]
        h = box[3] - box[1]
        return [int(box[1] + h * (i + 1) / (n + 1)) for i in range(n)]

    def _label_width(self, text: str) -> int:
        return max(self.draw.textbbox((0, 0), ln, font=self.f_label)[2] for ln in text.split("\n"))

    def _label_height(self, text: str) -> int:
        lh = self.f_label.size + 3
        return len(text.split("\n")) * lh

    def _label_above(self, x: int, y_line: int, text: str, *, offset: int = 24):
        lh = self.f_label.size + 3
        self.label((x, y_line - offset - self._label_height(text) + lh), text)

    def chain(self, boxes: list[tuple], labels: list[str]):
        """Межблочные связи: горизонталь — вертикаль в зазоре — горизонталь (без лишних шин)."""
        lh = self.f_label.size + 3
        for i in range(len(boxes) - 1):
            bi, bj = boxes[i], boxes[i + 1]
            x_out = self.mid_right(bi)
            x_in = self.mid_left(bj)
            y0, y1 = x_out[1], x_in[1]
            gap = bj[0] - bi[2]
            mid_x = (bi[2] + bj[0]) // 2

            if abs(y0 - y1) <= 8:
                # Блоки на одной высоте — прямая горизонтальная стрелка
                self.polyline([x_out, x_in])
                label_y = y0 - lh - 8
                lx = mid_x - self._label_width(labels[i]) // 2 if i < len(labels) else mid_x
            else:
                # Один излом по центру зазора между блоками
                ox = bi[2] + max(14, min(gap // 3, 32))
                ix = bj[0] - max(14, min(gap // 3, 32))
                if gap < 70:
                    route_x = mid_x
                    self.polyline([x_out, (route_x, y0), (route_x, y1), x_in])
                else:
                    self.polyline([x_out, (ox, y0), (ox, y1), (ix, y1), x_in])
                    route_x = (ox + ix) // 2
                label_y = min(y0, y1) - lh - 8
                lx = route_x - (self._label_width(labels[i]) // 2 if i < len(labels) else 0)

            if i < len(labels):
                tw = self._label_width(labels[i])
                lx = max(bi[2] + 4, min(lx, bj[0] - tw - 4))
                self.label((lx, label_y), labels[i])

    def external_inputs(
        self, box, items: list[str], margin_left: int = 28, *, arrow_len: int | None = None
    ):
        x_in = box[0]
        x0 = x_in - (arrow_len or 130)
        x0 = max(42, x0)
        for text, ey in zip(items, self._edge_ys(box, len(items))):
            tw = self._label_width(text)
            lx = margin_left if arrow_len is None else max(margin_left, x0 - tw - 8)
            self._label_above(lx, ey, text)
            self.polyline([(x0, ey), (x_in, ey)])

    def external_outputs(
        self, box, items: list[str], margin_right: int = 28, *, arrow_len: int | None = None
    ):
        x_out = box[2]
        x1 = x_out + (arrow_len or 130) if arrow_len else self.W - 46
        if arrow_len:
            x1 = min(self.W - 50, x1)
        for text, ey in zip(items, self._edge_ys(box, len(items))):
            self.polyline([(x_out, ey), (x1, ey)])
            tw = self._label_width(text)
            if arrow_len is None:
                lx = self.W - margin_right - tw
            else:
                lx = min(x1 + 6, self.W - margin_right - tw)
                lx = max(x_out + 8, lx)
            self._label_above(lx, ey, text)

    def top_controls_forked(self, boxes: list[tuple], groups: list[tuple[str, list[int]]]):
        """Управление: шина над блоками, подпись справа, вертикаль в каждый блок."""
        xs = [self.mid_top(b)[0] for b in boxes]
        top_y = min(b[1] for b in boxes)

        for gi, (ctrl, indices) in enumerate(groups):
            targets = sorted({xs[i] for i in indices})
            t_left, t_right = targets[0], targets[-1]
            bus_y = top_y - 38 - gi * 58
            th = self._label_height(ctrl)

            stem_x = t_right + 32 + gi * 12
            lx = stem_x + 12
            ly = bus_y - th - 10
            self.label((lx, ly), ctrl)
            stem_bottom = ly + th + 6

            if len(targets) == 1:
                bx, by = targets[0], boxes[indices[0]][1]
                self.polyline([(bx, stem_bottom), (bx, by)])
            else:
                self.line((t_left, bus_y), (stem_x, bus_y))
                self.line((stem_x, stem_bottom), (stem_x, bus_y))
                for idx in indices:
                    bx, by = xs[idx], boxes[idx][1]
                    self.polyline([(bx, bus_y), (bx, by)])

    def top_controls(self, boxes: list[tuple], controls: list[str]):
        groups = [(c, list(range(len(boxes)))) for c in controls]
        self.top_controls_forked(boxes, groups)

    def bottom_mechanisms_forked(self, boxes: list[tuple], groups: list[tuple[str, list[int]]]):
        """Механизмы: шина под блоками, подпись ниже, стрелка вверх в каждый блок."""
        xs = [self.mid_bottom(b)[0] for b in boxes]
        bottom_y = max(b[3] for b in boxes)

        for gi, (mech, indices) in enumerate(groups):
            targets = sorted({xs[i] for i in indices})
            t_left, t_right = targets[0], targets[-1]
            bus_y = bottom_y + 30 + gi * 54
            tw = self._label_width(mech)
            th = self._label_height(mech)
            label_y = bus_y + 40

            if len(targets) == 1:
                join_x = targets[0]
                lx = max(24, join_x - tw // 2)
            else:
                join_x = t_left
                lx = max(24, t_left - tw // 2)

            self.label((lx, label_y), mech)
            line_from = label_y + th + 8

            if len(targets) == 1:
                self.polyline([(join_x, line_from), (join_x, boxes[indices[0]][3])])
            else:
                self.line((join_x, line_from), (join_x, bus_y))
                self.line((t_left, bus_y), (t_right, bus_y))
                for idx in indices:
                    bx, by = xs[idx], boxes[idx][3]
                    self.polyline([(bx, bus_y), (bx, by)])

    def bottom_mechanisms(self, boxes: list[tuple], mechanisms: list[str]):
        groups = [(m, [i]) for i, m in enumerate(mechanisms)]
        self.bottom_mechanisms_forked(boxes, groups)

    def top_controls_single(self, box: tuple, controls: list[str]):
        """A-0: отдельные вертикальные стрелки управления, подписи на двух ярусах."""
        x1, y1, x2, y2 = box
        n = len(controls)
        pts = [int(x1 + (x2 - x1) * (i + 1) / (n + 1)) for i in range(n)]
        tiers = [0, 1, 0, 1] if n >= 4 else [i % 2 for i in range(n)]
        tier_heights = [0, 0]
        for i, (ctrl, cx) in enumerate(zip(controls, pts)):
            tw = self._label_width(ctrl)
            th = self._label_height(ctrl)
            tier = tiers[i]
            label_y = y1 - 58 - th - tier * 34 - tier_heights[tier]
            tier_heights[tier] += th + 12
            lx = cx - tw // 2
            lx = max(24, min(lx, self.W - tw - 24))
            self.label((lx, label_y), ctrl)
            self.polyline([(cx, label_y + th + 8), (cx, y1)])

    def bottom_mechanisms_single(self, box: tuple, mechanisms: list[str]):
        """A-0: отдельные стрелки механизмов вверх в блок."""
        x1, y1, x2, y2 = box
        n = len(mechanisms)
        pts = [int(x1 + (x2 - x1) * (i + 1) / (n + 1)) for i in range(n)]
        tiers = [0, 1, 0, 1] if n >= 4 else [i % 2 for i in range(n)]
        tier_offset = [0, 0]
        for i, (mech, cx) in enumerate(zip(mechanisms, pts)):
            tw = self._label_width(mech)
            tier = tiers[i]
            label_y = y2 + 54 + tier * 30 + tier_offset[tier]
            tier_offset[tier] += 22
            lx = max(24, min(cx - tw // 2, self.W - tw - 24))
            self.label((lx, label_y), mech)
            self.polyline([(cx, label_y + self._label_height(mech) + 4), (cx, y2)])


def draw_a0_single(path: Path):
    """Рисунок 2.2 — IDEF0 A-0: один блок (как «Управлять складскими запасами» в ПСП)."""
    c = Idef0Canvas()
    c.f_title = _font(26)
    c.f_label = _font(19)
    c.f_small = _font(17)
    box = (700, 455, 1528, 655)
    c.draw_box(box, "Управлять учётом\nблаготворительных\nпожертвований", 0)
    c.external_inputs(
        box,
        ["Отчёты за прошлый период", "Пожертвования доноров", "Заявки на помощь"],
        arrow_len=175,
    )
    c.external_outputs(
        box,
        [
            "Отчёт о расходах",
            "Публичные отчёты",
            "Баланс кампаний",
            "Финансовые отчёты",
            "Сводка по кампаниям",
        ],
        arrow_len=175,
    )
    c.top_controls_single(
        box,
        [
            "Закон о благотворительной\nдеятельности",
            "Политика фонда",
            "Положение о фонде",
            "Требования к отчётности",
        ],
    )
    c.bottom_mechanisms_single(
        box,
        ["CharityLedger", "Оператор фонда", "Администратор", "Жертвователь"],
    )
    c.save(path)


def draw_context_a0(path: Path):
    """Рисунок 2.3 — декомпозиция A-0 (5 блоков, как в примере склада)."""
    c = Idef0Canvas()
    c.f_title = _font(21)
    c.f_label = _font(18)
    c.f_small = _font(15)
    boxes = c.cascade(5, start=(140, 300), step=(378, 118), size=(348, 158))
    titles = [
        "Регистрировать\nпожертвования",
        "Учитывать\nрасходы",
        "Рассчитывать\nбаланс",
        "Публиковать\nотчёты",
        "Управлять\nкампаниями",
    ]
    for i, (rect, title) in enumerate(zip(boxes, titles), 1):
        c.draw_box(rect, title, i)
    c.chain(
        boxes,
        [
            "Зарегистрированные\nпожертвования",
            "Данные о расходах",
            "Рассчитанный баланс",
            "Опубликованные отчёты",
        ],
    )
    c.external_inputs(boxes[0], ["Пожертвования доноров", "Заявки на помощь"], arrow_len=120)
    c.external_outputs(boxes[-1], ["Публичные отчёты", "Баланс кампаний"], arrow_len=120)
    c.top_controls_forked(
        boxes,
        [
            ("Политика фонда", [0, 1, 2, 3, 4]),
            ("Закон о благотворительной деятельности", [0, 1, 2, 3, 4]),
        ],
    )
    c.bottom_mechanisms_forked(
        boxes,
        [
            ("CharityLedger", [0, 1]),
            ("Оператор фонда", [2]),
            ("Администратор", [3, 4]),
        ],
    )
    c.save(path)


def draw_decompose_a0(path: Path):
    """Рисунок 2.4 — декомпозиция контекстной диаграммы."""
    c = Idef0Canvas()
    c.f_title = _font(20)
    c.f_label = _font(17)
    c.f_small = _font(14)
    boxes = c.cascade(4, start=(250, 360), step=(420, 95), size=(288, 148))
    titles = [
        "Проанализировать\nпотребности кампании",
        "Определить источники\nфинансирования",
        "Зарегистрировать\nпоступления",
        "Согласовать\nрасходы",
    ]
    for i, (rect, title) in enumerate(zip(boxes, titles), 1):
        c.draw_box(rect, title, i)
    c.chain(boxes, ["Выявленные потребности", "Источники финансирования", "Зарегистрированные поступления"])
    c.external_inputs(boxes[0], ["Отчёты за период", "Прогноз сбора средств"], arrow_len=115)
    c.external_outputs(boxes[-1], ["Подтверждённые расходы"], arrow_len=115)
    c.top_controls_forked(
        boxes,
        [
            ("Положение о фонде", [0, 1, 2, 3]),
            ("Закон о благотворительной деятельности", [0, 1, 2, 3]),
        ],
    )
    c.bottom_mechanisms_forked(
        boxes,
        [("CharityLedger", [0, 1, 2]), ("Оператор фонда", [3])],
    )
    c.save(path)


def draw_decompose_donations(path: Path):
    """Рисунок 2.5 — декомпозиция «Регистрировать пожертвования»."""
    c = Idef0Canvas()
    c.f_title = _font(20)
    c.f_label = _font(17)
    c.f_small = _font(14)
    boxes = c.cascade(4, start=(220, 368), step=(445, 98), size=(292, 148))
    titles = [
        "Выбрать\nкампанию",
        "Ввести данные\nдонора и сумму",
        "Сохранить\nпожертвование",
        "Обновить баланс\nкампании",
    ]
    for i, (rect, title) in enumerate(zip(boxes, titles), 1):
        c.draw_box(rect, title, i)
    c.chain(boxes, ["Выбранная кампания", "Данные пожертвования", "Запись в БД"])
    c.external_inputs(boxes[0], ["Заявка донора", "Список кампаний"], arrow_len=115)
    c.external_outputs(boxes[-1], ["Обновлённый баланс"], arrow_len=115)
    c.top_controls_forked(boxes, [("Положение о фонде", [0, 1, 2, 3])])
    c.bottom_mechanisms_forked(
        boxes,
        [("CharityLedger", [0, 2, 3]), ("Жертвователь", [1])],
    )
    c.save(path)


def draw_decompose_expenses(path: Path):
    """Рисунок 2.6 — декомпозиция «Учитывать расходы»."""
    c = Idef0Canvas()
    c.f_title = _font(20)
    c.f_label = _font(17)
    c.f_small = _font(14)
    boxes = c.cascade(3, start=(310, 358), step=(505, 128), size=(348, 162))
    titles = [
        "Проверить полномочия\nоператора",
        "Сравнить расход\nс балансом",
        "Зафиксировать\nрасход",
    ]
    for i, (rect, title) in enumerate(zip(boxes, titles), 1):
        c.draw_box(rect, title, i)
    c.chain(boxes, ["Подтверждённые полномочия", "Проверенный расход"])
    c.external_inputs(boxes[0], ["Данные расхода", "Подтверждающий документ"], arrow_len=115)
    c.external_outputs(boxes[-1], ["Запись в таблице expenses"], arrow_len=115)
    c.top_controls_forked(
        boxes,
        [
            ("Положение о фонде", [0, 1, 2]),
            ("Закон о благотворительной деятельности", [0, 1, 2]),
        ],
    )
    c.bottom_mechanisms_forked(
        boxes,
        [("CharityLedger", [0, 2]), ("Оператор фонда", [1])],
    )
    c.save(path)


def draw_decompose_reports(path: Path):
    """Рисунок 2.7 — декомпозиция «Публиковать отчёты»."""
    c = Idef0Canvas()
    c.f_title = _font(20)
    c.f_label = _font(17)
    c.f_small = _font(14)
    boxes = c.cascade(3, start=(310, 358), step=(505, 128), size=(348, 162))
    titles = [
        "Суммировать\nпожертвования",
        "Суммировать\nрасходы",
        "Подготовить\nпубличный отчёт",
    ]
    for i, (rect, title) in enumerate(zip(boxes, titles), 1):
        c.draw_box(rect, title, i)
    c.chain(boxes, ["Сумма поступлений", "Сумма расходов"])
    c.external_inputs(boxes[0], ["Данные кампании"], arrow_len=115)
    c.external_outputs(boxes[-1], ["Отчёт прозрачности"], arrow_len=115)
    c.top_controls_forked(boxes, [("Требования к отчётности фонда", [0, 1, 2])])
    c.bottom_mechanisms_forked(
        boxes,
        [("CharityLedger", [0, 1, 2]), ("Оператор фонда", [1, 2])],
    )
    c.save(path)


def run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_a0_single(out_dir / "02_idef0_a0.png")
    print("  DRAW→02_idef0_a0.png")
    draw_context_a0(out_dir / "02_idef0_context.png")
    print("  DRAW→02_idef0_context.png")
    draw_decompose_a0(out_dir / "02_idef0_decompose.png")
    print("  DRAW→02_idef0_decompose.png")
    draw_decompose_donations(out_dir / "02_idef0_donations.png")
    print("  DRAW→02_idef0_donations.png")
    draw_decompose_expenses(out_dir / "02_idef0_expenses.png")
    print("  DRAW→02_idef0_expenses.png")
    draw_decompose_reports(out_dir / "02_idef0_reports.png")
    print("  DRAW→02_idef0_reports.png")


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1] / "Материалы" / "Диаграммы" / "png")
