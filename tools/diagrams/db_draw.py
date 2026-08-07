"""Физическая, логическая (таблицы) и концептуальная (Чен) модели БД — стиль ПСП_Ивановская."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
FONT_B = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")
W, H = 2800, 1600
W_ER, H_ER = 2600, 1800


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_B if bold and FONT_B.exists() else FONT
    return ImageFont.truetype(str(path), size=size)


def _new(w=W, h=H) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), "white")
    return img, ImageDraw.Draw(img)


def _text_center(draw, box, text: str, font, fill="black"):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    lh = font.size + 6
    total = len(lines) * lh
    y = y1 + (y2 - y1 - total) // 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill=fill, font=font)
        y += lh


def _dashed_line(draw, p1, p2, width=3, dash=14):
    x1, y1 = p1
    x2, y2 = p2
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line(
            [(x1 + dx * pos, y1 + dy * pos), (x1 + dx * end, y1 + dy * end)],
            fill="black",
            width=width,
        )
        pos += dash * 2


def _dot(draw, pos, r=9):
    x, y = pos
    draw.ellipse((x - r, y - r, x + r, y + r), fill="black", outline="black")


def _table(draw, x, y, name: str, fields: list[str], *, pk: str, f_title, f_body, types: dict[str, str] | None = None):
    line_h = f_body.size + 10
    pad = 18
    labels = []
    for field in fields:
        if types and field in types:
            labels.append(f"{field}: {types[field]}")
        elif field == pk:
            labels.append(f"{field}  (PK)" if not types else f"{field}: {types.get(field, 'INTEGER PK')}")
        else:
            labels.append(field)
    max_w = max(
        draw.textbbox((0, 0), name, font=f_title)[2],
        max(draw.textbbox((0, 0), label, font=f_body)[2] for label in labels),
    ) + pad * 2
    h = 56 + len(labels) * line_h + pad
    box = (x, y, x + max_w, y + h)
    draw.rectangle(box, outline="black", width=3)
    draw.line([(x, y + 52), (x + max_w, y + 52)], fill="black", width=2)
    _text_center(draw, (x, y, x + max_w, y + 52), name, f_title)
    cy = y + 58
    for field, label in zip(fields, labels):
        draw.text((x + pad, cy), label, fill="black", font=f_body)
        cy += line_h
    return box


def _rel_physical(draw, p_from, p_to, many_at_end=True):
    _dashed_line(draw, p_from, p_to, width=3)
    if many_at_end:
        _dot(draw, p_to, r=9)


def _route_rel(draw, p_from, p_to):
    """Ортогональная пунктирная связь FK (как в ПСП_Ивановская, рис. 3.9–3.10)."""
    fx, fy = p_from
    tx, ty = p_to
    if abs(fx - tx) < 12:
        _rel_physical(draw, p_from, p_to)
        return
    if abs(fy - ty) < 12:
        _rel_physical(draw, p_from, p_to)
        return
    mid_y = (fy + ty) // 2
    _dashed_line(draw, p_from, (fx, mid_y), width=3)
    _dashed_line(draw, (fx, mid_y), (tx, mid_y), width=3)
    _rel_physical(draw, (tx, mid_y), p_to)


def draw_physical_db(out: Path) -> None:
    img, draw = _new()
    ft = _font(34, True)
    fb = _font(26)
    types = {
        "id": "INTEGER NOT NULL",
        "login": "TEXT NOT NULL",
        "password_hash": "TEXT NOT NULL",
        "full_name": "TEXT NOT NULL",
        "role": "TEXT NOT NULL",
        "email": "TEXT",
        "phone": "TEXT",
        "is_anonymous": "INTEGER NOT NULL",
        "title": "TEXT NOT NULL",
        "description": "TEXT",
        "target_amount": "REAL NOT NULL",
        "status": "TEXT NOT NULL",
        "created_at": "TEXT NOT NULL",
        "campaign_id": "INTEGER NOT NULL (FK)",
        "donor_id": "INTEGER (FK)",
        "amount": "REAL NOT NULL",
        "payment_method": "TEXT NOT NULL",
        "donated_at": "TEXT NOT NULL",
        "comment": "TEXT",
        "spent_at": "TEXT NOT NULL",
        "document_ref": "TEXT",
        "period_start": "TEXT NOT NULL",
        "period_end": "TEXT NOT NULL",
        "total_donations": "REAL NOT NULL",
        "total_expenses": "REAL NOT NULL",
        "balance": "REAL NOT NULL",
        "published_at": "TEXT NOT NULL",
        "is_public": "INTEGER NOT NULL",
    }

    t_users = _table(
        draw, 120, 180, "users",
        ["id", "login", "password_hash", "full_name", "role"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )
    t_campaigns = _table(
        draw, 980, 140, "campaigns",
        ["id", "title", "description", "target_amount", "status", "created_at"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )
    t_donors = _table(
        draw, 1880, 180, "donors",
        ["id", "full_name", "email", "phone", "is_anonymous"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )
    t_donations = _table(
        draw, 1180, 720, "donations",
        ["id", "campaign_id", "donor_id", "amount", "payment_method", "donated_at", "comment"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )
    t_expenses = _table(
        draw, 620, 720, "expenses",
        ["id", "campaign_id", "title", "amount", "spent_at", "document_ref"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )
    t_reports = _table(
        draw, 1880, 700, "transparency_reports",
        ["id", "campaign_id", "period_start", "period_end", "total_donations",
         "total_expenses", "balance", "published_at", "is_public"],
        pk="id", f_title=ft, f_body=fb, types=types,
    )

    cx_c = (t_campaigns[0] + t_campaigns[2]) // 2
    cy_c = t_campaigns[3]
    _route_rel(draw, (cx_c, cy_c), ((t_donations[0] + t_donations[2]) // 2, t_donations[1]))
    _route_rel(draw, ((t_donors[0] + t_donors[2]) // 2, t_donors[3]),
               ((t_donations[0] + t_donations[2]) // 2 + 80, t_donations[1]))
    _route_rel(draw, (cx_c - 60, cy_c), ((t_expenses[0] + t_expenses[2]) // 2, t_expenses[1]))
    _route_rel(draw, (cx_c + 60, cy_c), ((t_reports[0] + t_reports[2]) // 2, t_reports[1]))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def draw_logical_db(out: Path) -> None:
    """Логическая модель — таблицы и связи FK (рис. 3.10 в ПСП_Ивановская)."""
    img, draw = _new()
    ft = _font(32, True)
    fb = _font(28)

    t_campaigns = _table(
        draw, 980, 120, "campaigns",
        ["id", "title", "description", "target_amount", "status", "created_at"],
        pk="id", f_title=ft, f_body=fb,
    )
    t_donations = _table(
        draw, 1180, 680, "donations",
        ["id", "campaign_id", "donor_id", "amount", "payment_method", "donated_at", "comment"],
        pk="id", f_title=ft, f_body=fb,
    )
    t_donors = _table(
        draw, 1880, 680, "donors",
        ["id", "full_name", "email", "phone", "is_anonymous"],
        pk="id", f_title=ft, f_body=fb,
    )
    t_expenses = _table(
        draw, 620, 680, "expenses",
        ["id", "campaign_id", "title", "amount", "spent_at", "document_ref"],
        pk="id", f_title=ft, f_body=fb,
    )
    t_reports = _table(
        draw, 1880, 120, "transparency_reports",
        ["id", "campaign_id", "period_start", "period_end", "total_donations",
         "total_expenses", "balance", "published_at", "is_public"],
        pk="id", f_title=ft, f_body=fb,
    )
    t_users = _table(
        draw, 120, 120, "users",
        ["id", "login", "password_hash", "full_name", "role"],
        pk="id", f_title=ft, f_body=fb,
    )

    cx_c = (t_campaigns[0] + t_campaigns[2]) // 2
    cy_c = t_campaigns[3]
    cx_d = (t_donations[0] + t_donations[2]) // 2
    _route_rel(draw, (cx_c, cy_c), (cx_d, t_donations[1]))
    _route_rel(draw, ((t_donors[0] + t_donors[2]) // 2, t_donors[1]), (t_donations[2], (t_donations[1] + t_donations[3]) // 2))
    _route_rel(draw, (cx_c - 50, cy_c), ((t_expenses[0] + t_expenses[2]) // 2, t_expenses[1]))
    _route_rel(draw, (t_campaigns[2], (t_campaigns[1] + t_campaigns[3]) // 2),
               (t_reports[0], (t_reports[1] + t_reports[3]) // 2))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


# --- Концептуальная модель (нотация Чена, рис. 3.11) ---


def _entity(draw, cx, cy, w, h, name, f):
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    draw.rectangle(box, outline="black", width=3)
    _text_center(draw, box, name, f)
    return {"cx": cx, "cy": cy, "box": box}


def _attr(draw, cx, cy, text, f):
    bb = draw.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0] + 32, bb[3] - bb[1] + 22
    box = (cx - tw // 2, cy - th // 2, cx + tw // 2, cy + th // 2)
    draw.ellipse(box, outline="black", width=2)
    draw.text((cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2 - 2), text, fill="black", font=f)
    return cx, cy, box


def _edge(box, side: str, frac: float = 0.5) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    if side == "left":
        return x1, int(y1 + (y2 - y1) * frac)
    if side == "right":
        return x2, int(y1 + (y2 - y1) * frac)
    if side == "top":
        return int(x1 + (x2 - x1) * frac), y1
    return int(x1 + (x2 - x1) * frac), y2


def _line_to_oval(entity_box, attr_box):
    ex1, ey1, ex2, ey2 = entity_box
    ax1, ay1, ax2, ay2 = attr_box
    ecx, ecy = (ex1 + ex2) // 2, (ey1 + ey2) // 2
    acx, acy = (ax1 + ax2) // 2, (ay1 + ay2) // 2
    dx, dy = acx - ecx, acy - ecy
    if abs(dx) >= abs(dy):
        if dx > 0:
            return (ex2, ecy), (ax1, acy)
        return (ex1, ecy), (ax2, acy)
    if dy > 0:
        return (ecx, ey2), (acx, ay1)
    return (ecx, ey1), (acx, ay2)


def _attrs_place(draw, entity, attrs: list[str], side: str, font, *, gap: int = 88, offset: int = 110):
    box = entity["box"]
    cx, cy = entity["cx"], entity["cy"]
    n = len(attrs)
    points = []
    if side == "left":
        ax = box[0] - offset
        y0 = cy - (n - 1) * gap // 2
        points = [(ax, y0 + i * gap) for i in range(n)]
    elif side == "right":
        ax = box[2] + offset
        y0 = cy - (n - 1) * gap // 2
        points = [(ax, y0 + i * gap) for i in range(n)]
    elif side == "top":
        ay = box[1] - offset
        span = max(gap, (n - 1) * gap)
        x0 = cx - span // 2
        points = [(x0 + i * (span // max(n - 1, 1)), ay) for i in range(n)]
    else:
        ay = box[3] + offset
        span = max(gap, (n - 1) * gap)
        x0 = cx - span // 2
        points = [(x0 + i * (span // max(n - 1, 1)), ay) for i in range(n)]

    for text, (ax, ay) in zip(attrs, points):
        _, _, abox = _attr(draw, ax, ay, text, font)
        p1, p2 = _line_to_oval(box, abox)
        draw.line([p1, p2], fill="black", width=2)


def _rel_diamond(draw, cx, cy, size, name, f):
    pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
    draw.polygon(pts, outline="black", fill="white", width=2)
    _text_center(draw, (cx - size + 8, cy - size + 8, cx + size - 8, cy + size - 8), name, f)
    return cx, cy


def _rel_h(draw, x1, x2, y, label, font, card_a="1", card_b="N"):
    size = 64
    mx = (x1 + x2) // 2
    _rel_diamond(draw, mx, y, size, label, font)
    fc = _font(22)
    draw.line([(x1, y), (mx - size, y)], fill="black", width=2)
    draw.line([(mx + size, y), (x2, y)], fill="black", width=2)
    draw.text((x1 + 16, y - 28), card_a, fill="black", font=fc)
    draw.text((x2 - 28, y - 28), card_b, fill="black", font=fc)


def _rel_v(draw, x, y1, y2, label, font, card_a="1", card_b="N"):
    size = 64
    my = (y1 + y2) // 2
    _rel_diamond(draw, x, my, size, label, font)
    fc = _font(22)
    draw.line([(x, y1), (x, my - size)], fill="black", width=2)
    draw.line([(x, my + size), (x, y2)], fill="black", width=2)
    draw.text((x + 12, y1 + 16), card_a, fill="black", font=fc)
    draw.text((x + 12, y2 - 36), card_b, fill="black", font=fc)


def _rel_elbow(draw, x1, y1, x2, y2, label, font, card_a="1", card_b="N"):
    """Г-образная связь с ромбом на вертикальном участке (как в ПСП_Ивановская)."""
    size = 64
    mid_x = x1 + 150 if x2 >= x1 else x1 - 150
    my = (y1 + y2) // 2
    _rel_diamond(draw, mid_x, my, size, label, font)
    fc = _font(22)
    draw.line([(x1, y1), (mid_x, y1)], fill="black", width=2)
    draw.line([(mid_x, y1), (mid_x, my - size)], fill="black", width=2)
    draw.line([(mid_x, my + size), (mid_x, y2)], fill="black", width=2)
    draw.line([(mid_x, y2), (x2, y2)], fill="black", width=2)
    draw.text((x1 + 16, y1 - 28), card_a, fill="black", font=fc)
    draw.text((x2 - 28, y2 - 28), card_b, fill="black", font=fc)


def _draw_chen_schema(
    out: Path,
    *,
    entities: dict,
    attrs_map: dict,
    relations: list,
    fe_size: int,
    fa_size: int,
    fr_size: int,
):
    img, draw = _new(W_ER, H_ER)
    fe, fa, fr = _font(fe_size, True), _font(fa_size), _font(fr_size)
    built = {}
    for key, (cx, cy, w, h, name) in entities.items():
        built[key] = _entity(draw, cx, cy, w, h, name, fe)

    for rel in relations:
        kind = rel[0]
        if kind == "h":
            _, x1, x2, y, label, card_a, card_b = rel
            _rel_h(draw, x1, x2, y, label, fr, card_a, card_b)
        elif kind == "v":
            _, x, y1, y2, label, card_a, card_b = rel
            _rel_v(draw, x, y1, y2, label, fr, card_a, card_b)
        else:
            _, x1, y1, x2, y2, label, card_a, card_b = rel
            _rel_elbow(draw, x1, y1, x2, y2, label, fr, card_a, card_b)

    for key, (cx, cy, w, h, name) in entities.items():
        built[key] = _entity(draw, cx, cy, w, h, name, fe)

    for key in entities:
        if key in attrs_map:
            side, items, gap = attrs_map[key]
            _attrs_place(draw, built[key], items, side, fa, gap=gap)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def draw_logical_chen(out: Path) -> None:
    """Совместимость: логическая модель — таблицы (не Чен)."""
    draw_logical_db(out)


def draw_conceptual_chen(out: Path) -> None:
    """Концептуальная модель в нотации Чена (как рис. 3.11 ПСП_Ивановская)."""
    y_top, y_bot = 520, 1320
    cx_user, cx_camp, cx_right = 520, 1320, 2120
    cx_donor, cx_don, cx_rep = 520, 1320, 2120

    entities = {
        "user": (cx_user, y_top, 250, 78, "Пользователь\nсистемы"),
        "camp": (cx_camp, y_top, 340, 86, "Благотворительная\nкампания"),
        "exp": (cx_right, y_top, 200, 78, "Расход"),
        "donor": (cx_donor, y_bot, 220, 78, "Жертвователь"),
        "don": (cx_don, y_bot, 230, 78, "Пожертвование"),
        "rep": (cx_rep, y_bot, 260, 78, "Отчёт\nпрозрачности"),
    }
    attrs_map = {
        "user": ("left", ["логин", "роль"], 92),
        "donor": ("left", ["ФИО", "анонимность"], 92),
        "camp": ("top", ["название", "статус"], 180),
        "don": ("bottom", ["сумма", "дата"], 180),
        "exp": ("right", ["сумма"], 0),
        "rep": ("right", ["период", "остаток"], 92),
    }

    hw = lambda cx, w, side: cx - w // 2 if side == "l" else cx + w // 2
    camp_b = y_top + 86 // 2
    don_t = y_bot - 78 // 2

    relations = [
        ("h", hw(cx_user, 250, "r"), hw(cx_camp, 340, "l"), y_top, "управляет", "1", "N"),
        ("h", hw(cx_camp, 340, "r"), hw(cx_right, 200, "l"), y_top, "финансирует", "1", "N"),
        ("h", hw(cx_donor, 220, "r"), hw(cx_don, 230, "l"), y_bot, "вносит", "1", "N"),
        ("v", cx_camp, camp_b, don_t, "принимает", "1", "N"),
        ("elbow", hw(cx_camp, 340, "r"), y_top, hw(cx_rep, 260, "l"), y_bot, "формирует", "1", "N"),
    ]
    _draw_chen_schema(
        out,
        entities=entities,
        attrs_map=attrs_map,
        relations=relations,
        fe_size=30,
        fa_size=24,
        fr_size=22,
    )
