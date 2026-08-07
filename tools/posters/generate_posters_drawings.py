#!/usr/bin/env python3
"""Плакаты (A1) и чертежи (ГОСТ) для курсового проекта CharityLedger."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from flowchart_gost_sheet import draw_donation_sheet
from gost_frame import A1_LANDSCAPE, draw_gost_frame, paste_centered

CW = Path(__file__).resolve().parents[1]
PNG = CW / "Материалы" / "Диаграммы" / "png"
SHOTS = CW / "Материалы" / "Скриншоты"
PUML = CW / "Материалы" / "Диаграммы" / "puml"
OUT = CW / "Материалы" / "Плакаты_и_чертежи"
JAR = Path(__file__).resolve().parents[2] / "tools" / "jars" / "plantuml.jar"

# A1 альбомная в пунктах (как в образце)
A1_PT = (2384, 1684)

DOC_DRAWING = "ГУИР.473601.010"
GROUP = "473601"
DEVELOPER = "Демидов"
CHECKER = "Пономарева"

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size=size)


def _fit(img: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    x1, y1, x2, y2 = box
    tw, th = x2 - x1, y2 - y1
    iw, ih = img.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _paste_in_box(canvas: Image.Image, img: Image.Image, box: tuple[int, int, int, int]):
    x1, y1, x2, y2 = box
    fitted = _fit(img, box)
    px = x1 + (x2 - x1 - fitted.width) // 2
    py = y1 + (y2 - y1 - fitted.height) // 2
    canvas.paste(fitted, (px, py))


def _caption(draw, box, text, fig_num: int, *, sub: str = ""):
    x1, y1, x2, y2 = box
    title = sub if sub else text
    f = _font(42, True)
    fs = _font(36)
    bb = draw.textbbox((0, 0), title, font=f)
    tw = bb[2] - bb[0]
    draw.text(((x1 + x2 - tw) // 2, y2 - 120), title, fill="black", font=f)
    cap = f"Рисунок {fig_num}"
    bb2 = draw.textbbox((0, 0), cap, font=fs)
    tw2 = bb2[2] - bb2[0]
    draw.text(((x1 + x2 - tw2) // 2, y2 - 60), cap, fill="black", font=fs)


def _poster_title(draw, text: str, w: int):
    f = _font(64, True)
    bb = draw.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    draw.text(((w - tw) // 2, 80), text, fill="black", font=f)


def render_combined_class() -> Path:
    out = PNG / "poster_class_combined.png"
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


def poster_1_class() -> Image.Image:
    class_png = render_combined_class()
    w, h = A1_LANDSCAPE
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    _poster_title(draw, "UML Диаграмма классов", w)
    _paste_in_box(img, Image.open(class_png), (120, 200, w - 120, h - 100))
    _caption(draw, (120, 200, w - 120, h - 20), "UML Диаграмма классов", 1)
    return img


def poster_2_models() -> Image.Image:
    w, h = A1_LANDSCAPE
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    _poster_title(draw, "Модели представления программного средства", w)

    comp = Image.open(PNG / "03_component.png")
    seq = Image.open(PNG / "03_sequence_donation.png")
    dep = Image.open(PNG / "03_deployment.png")

    _paste_in_box(img, comp, (80, 200, int(w * 0.48), h - 80))
    _caption(
        draw,
        (80, 200, int(w * 0.48), h - 20),
        "Диаграмма компонентов программного средства",
        2,
    )

    _paste_in_box(img, seq, (int(w * 0.50), 200, w - 80, int(h * 0.52)))
    _caption(
        draw,
        (int(w * 0.50), 200, w - 80, int(h * 0.52)),
        'Диаграмма последовательности «Регистрация пожертвования»',
        3,
    )

    _paste_in_box(img, dep, (int(w * 0.50), int(h * 0.54), w - 80, h - 80))
    _caption(
        draw,
        (int(w * 0.50), int(h * 0.54), w - 80, h - 20),
        "Диаграмма развертывания программного средства",
        4,
    )
    return img


def poster_3_screenshots() -> Image.Image:
    w, h = A1_LANDSCAPE
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    _poster_title(draw, "Скриншоты рабочих окон программного средства", w)

    shots = [
        (SHOTS / "03_app_campaigns.png", "Окно кампаний", 5),
        (SHOTS / "03_app_donation.png", "Окно пожертвования", 6),
        (SHOTS / "03_app_transparency.png", "Окно прозрачности", 7),
        (SHOTS / "03_app_admin.png", "Окно администрирования", 8),
    ]
    boxes = [
        (100, 200, w // 2 - 40, h // 2 - 20),
        (w // 2 + 40, 200, w - 100, h // 2 - 20),
        (100, h // 2 + 20, w // 2 - 40, h - 100),
        (w // 2 + 40, h // 2 + 20, w - 100, h - 100),
    ]
    for (path, title, num), box in zip(shots, boxes):
        if not path.exists():
            path = PNG / path.name.replace("03_app_", "03_ui_")
        _paste_in_box(img, Image.open(path), box)
        _caption(draw, box, title, num, sub=title)
    return img


def drawing_idef0() -> Image.Image:
    inner = Image.open(PNG / "02_idef0_context.png")
    base, content = draw_gost_frame(
        *A1_LANDSCAPE,
        doc_code=f"{DOC_DRAWING} Д1",
        title="IDEF0-модель процесса\nучёта благотворительных\nпожертвований",
        developer=DEVELOPER,
        checker=CHECKER,
        group=GROUP,
    )
    paste_centered(base, content, inner)
    return base


def drawing_algorithm() -> Image.Image:
    tmp = PNG / "_sheet_algo_donation.png"
    draw_donation_sheet(tmp, width=5200, height=3600)
    inner = Image.open(tmp)
    base, content = draw_gost_frame(
        *A1_LANDSCAPE,
        doc_code=f"{DOC_DRAWING} Д2",
        title="Схема алгоритма\nрегистрации пожертвования",
        developer=DEVELOPER,
        checker=CHECKER,
        group=GROUP,
    )
    paste_centered(base, content, inner)
    return base


def save_pdf(images: list[tuple[str, Image.Image]]):
    import io

    try:
        import fitz
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf", "-q"], check=True)
        import fitz

    OUT.mkdir(parents=True, exist_ok=True)
    for name, img in images:
        pdf_path = OUT / f"{name}.pdf"
        png_path = OUT / f"{name}.png"
        img.save(png_path, "PNG", optimize=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        doc = fitz.open()
        page = doc.new_page(width=A1_PT[0], height=A1_PT[1])
        rect = fitz.Rect(0, 0, A1_PT[0], A1_PT[1])
        page.insert_image(rect, stream=buf.getvalue())
        doc.save(pdf_path)
        doc.close()
        print(f"  → {pdf_path.name}")


def main():
    """По умолчанию — шаблоны PDF из корня проекта + рисунки CharityLedger."""
    from compose_posters_from_templates import main as compose_main

    raise SystemExit(compose_main())


if __name__ == "__main__":
    main()
