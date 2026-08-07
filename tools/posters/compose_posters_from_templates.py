#!/usr/bin/env python3
"""Плакаты и чертежи: шаблон PDF из корня проекта + рисунки CharityLedger."""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CW = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
PNG = CW / "Материалы" / "Диаграммы" / "png"
SHOTS = CW / "Материалы" / "Скриншоты"
OUT = CW / "Материалы" / "Плакаты_и_чертежи"
PUML = CW / "Материалы" / "Диаграммы" / "puml"
JAR = REPO_ROOT / "tools" / "jars" / "plantuml.jar"

TEMPLATES = {
    "poster1": REPO_ROOT / "Плакат 1 - UML диаграмма классов.pdf",
    "poster2": REPO_ROOT / "Плакат_2_результаты_проектирования_ПС.pdf",
    "poster3": REPO_ROOT / "Плакат 3 - скриншоты ПО.pdf",
    "drawing_idef0": REPO_ROOT / "Чертеж - IDEF0 A3.pdf",
    "drawing_algo": REPO_ROOT / "Чертеж - схема алгоритма.pdf",
}

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
DPI = 150


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size=size)


def _pdf_page_image(pdf_path: Path, page: int = 0) -> Image.Image:
    try:
        import fitz
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf", "-q"], check=True)
        import fitz

    doc = fitz.open(pdf_path)
    pg = doc[page]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = pg.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    doc.close()
    return img


def _fill_white(img: Image.Image, box: tuple[int, int, int, int]):
    draw = ImageDraw.Draw(img)
    draw.rectangle(box, fill="white")


def _paste_fit(canvas: Image.Image, inner: Image.Image, box: tuple[int, int, int, int], *, margin: int = 8):
    x1, y1, x2, y2 = box
    area_w, area_h = x2 - x1 - 2 * margin, y2 - y1 - 2 * margin
    iw, ih = inner.size
    scale = min(area_w / iw, area_h / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = inner.resize((nw, nh), Image.Resampling.LANCZOS)
    px = x1 + margin + (area_w - nw) // 2
    py = y1 + margin + (area_h - nh) // 2
    canvas.paste(resized, (px, py))


def _center_text(draw, y: int, text: str, font, w: int, *, x1: int = 0, x2: int | None = None):
    x2 = x2 or w
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    cx = x1 + (x2 - x1 - tw) // 2
    draw.text((cx, y), text, fill="black", font=font)


def _ensure_class_poster() -> Path:
    out = PNG / "poster_class_combined.png"
    if out.exists():
        return out
    if not JAR.exists():
        from render_diagrams import ensure_plantuml

        ensure_plantuml()
    puml = PUML / "poster_class_combined.puml"
    subprocess.run(
        ["java", "-jar", str(JAR), "-tpng", "-o", str(PNG), str(puml)],
        check=True,
        capture_output=True,
    )
    return out


def _ensure_algo_sheet() -> Path:
    from flowchart_gost_sheet import draw_donation_sheet

    out = PNG / "_sheet_algo_donation.png"
    if not out.exists():
        draw_donation_sheet(out, width=5200, height=3600)
    return out


def compose_poster1() -> Image.Image:
    img = _pdf_page_image(TEMPLATES["poster1"])
    w, h = img.size
    _fill_white(img, (int(w * 0.03), int(h * 0.11), int(w * 0.97), int(h * 0.87)))
    _paste_fit(img, Image.open(_ensure_class_poster()), (int(w * 0.03), int(h * 0.11), int(w * 0.97), int(h * 0.87)))
    return img


def compose_poster2() -> Image.Image:
    img = _pdf_page_image(TEMPLATES["poster2"])
    w, h = img.size
    boxes = [
        (int(w * 0.02), int(h * 0.14), int(w * 0.48), int(h * 0.84), PNG / "03_component.png"),
        (int(w * 0.50), int(h * 0.14), int(w * 0.98), int(h * 0.48), PNG / "03_sequence_donation.png"),
        (int(w * 0.50), int(h * 0.50), int(w * 0.98), int(h * 0.84), PNG / "03_deployment.png"),
    ]
    for x1, y1, x2, y2, path in boxes:
        _fill_white(img, (x1, y1, x2, y2))
        _paste_fit(img, Image.open(path), (x1, y1, x2, y2))

    draw = ImageDraw.Draw(img)
    f = _font(int(h * 0.021), bold=True)
    # только заголовок диаграммы последовательности (вместо «Обновление дашборда»)
    _fill_white(img, (int(w * 0.50), int(h * 0.075), int(w * 0.98), int(h * 0.125)))
    _center_text(
        draw,
        int(h * 0.082),
        "Диаграмма последовательности «Регистрация пожертвования»",
        f,
        w,
        x1=int(w * 0.50),
        x2=int(w * 0.98),
    )
    return img


def compose_poster3() -> Image.Image:
    img = _pdf_page_image(TEMPLATES["poster3"])
    w, h = img.size
    shots = [
        (SHOTS / "03_app_campaigns.png", "Окно кампаний", 5),
        (SHOTS / "03_app_donation.png", "Окно пожертвования", 6),
        (SHOTS / "03_app_transparency.png", "Окно прозрачности", 7),
        (SHOTS / "03_app_admin.png", "Окно администрирования", 8),
    ]
    quads = [
        (int(w * 0.03), int(h * 0.17), int(w * 0.49), int(h * 0.49)),
        (int(w * 0.51), int(h * 0.17), int(w * 0.97), int(h * 0.49)),
        (int(w * 0.03), int(h * 0.53), int(w * 0.49), int(h * 0.85)),
        (int(w * 0.51), int(h * 0.53), int(w * 0.97), int(h * 0.85)),
    ]
    # убрать все старые подписи окон и «Рисунок N» образца
    _fill_white(img, (0, int(h * 0.095), w, int(h * 0.172)))
    _fill_white(img, (0, int(h * 0.848), w, h))

    draw = ImageDraw.Draw(img)
    f_title = _font(int(h * 0.022), bold=True)
    f_cap = _font(int(h * 0.019), bold=True)
    title_y = int(h * 0.122)
    cap_y = int(h * 0.872)

    for (path, title, num), (x1, y1, x2, y2) in zip(shots, quads):
        _fill_white(img, (x1, y1, x2, y2))
        _paste_fit(img, Image.open(path), (x1, y1, x2, y2))
        _fill_white(img, (x1, title_y - 10, x2, title_y + int(h * 0.032)))
        _fill_white(img, (x1, cap_y - 6, x2, cap_y + int(h * 0.028)))
        _center_text(draw, title_y, title, f_title, w, x1=x1, x2=x2)
        _center_text(draw, cap_y, f"Рисунок {num}", f_cap, w, x1=x1, x2=x2)

    return img


def compose_drawing_idef0() -> Image.Image:
    img = _pdf_page_image(TEMPLATES["drawing_idef0"])
    w, h = img.size
    # область сетки без основной надписи (справа внизу)
    box = (int(w * 0.055), int(h * 0.09), int(w * 0.88), int(h * 0.82))
    _fill_white(img, box)
    _paste_fit(img, Image.open(PNG / "02_idef0_context.png"), box, margin=4)
    return img


def compose_drawing_algo() -> Image.Image:
    img = _pdf_page_image(TEMPLATES["drawing_algo"])
    w, h = img.size
    box = (int(w * 0.055), int(h * 0.09), int(w * 0.92), int(h * 0.82))
    _fill_white(img, box)
    _paste_fit(img, Image.open(_ensure_algo_sheet()), box, margin=12)
    return img


def save_outputs(items: list[tuple[str, Image.Image]]):
    import fitz

    OUT.mkdir(parents=True, exist_ok=True)
    for name, image in items:
        png_path = OUT / f"{name}.png"
        pdf_path = OUT / f"{name}.pdf"
        image.save(png_path, "PNG", optimize=True)
        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        pw, ph = image.size
        doc = fitz.open()
        page = doc.new_page(width=pw * 72 / DPI, height=ph * 72 / DPI)
        page.insert_image(page.rect, stream=buf.getvalue())
        doc.save(pdf_path)
        doc.close()
        print(f"  → {pdf_path.name}")


def main():
    missing = [k for k, p in TEMPLATES.items() if not p.exists()]
    if missing:
        print("Не найдены шаблоны в корне проекта:", ", ".join(missing), file=sys.stderr)
        return 1

    print("Сборка плакатов и чертежей из шаблонов...")
    items = [
        ("Плакат_1_UML_диаграмма_классов", compose_poster1()),
        ("Плакат_2_результаты_проектирования_ПС", compose_poster2()),
        ("Плакат_3_скриншоты_ПО", compose_poster3()),
        ("Чертеж_IDEF0_A3", compose_drawing_idef0()),
        ("Чертеж_схема_алгоритма", compose_drawing_algo()),
    ]
    save_outputs(items)
    print(f"Готово: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
