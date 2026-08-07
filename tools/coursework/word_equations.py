#!/usr/bin/env python3
"""Вставка формул Word (OMML / редактор формул) в python-docx."""
from __future__ import annotations

import re
from xml.sax.saxutils import escape

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
FONT = "Times New Roman"
FONT_SIZE = Pt(14)


def _t(text: str) -> str:
    return escape(text, entities={"'": "&apos;", '"': "&quot;"})


def _r(text: str) -> str:
    return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t xml:space="preserve">{_t(text)}</m:t></m:r>'


def _sub(base: str, sub: str) -> str:
    return f"<m:sSub><m:e>{_r(base)}</m:e><m:sub>{_r(sub)}</m:sub></m:sSub>"


def _sup(base: str, sup: str) -> str:
    return f"<m:sSup><m:e>{_r(base)}</m:e><m:sup>{_r(sup)}</m:sup></m:sSup>"


def _frac(num: str, den: str) -> str:
    return f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>"


def _rad(body: str) -> str:
    return (
        f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{body}</m:e></m:rad>'
    )


def _sum_i(body: str) -> str:
    return (
        "<m:nary>"
        '<m:naryPr><m:chr m:val="∑"/><m:subHide m:val="off"/><m:supHide m:val="on"/></m:naryPr>'
        f"<m:sub>{_r('i')}</m:sub><m:sup>{_r('')}</m:sup><m:e>{body}</m:e>"
        "</m:nary>"
    )


def _omath(*parts: str) -> str:
    inner = "".join(parts)
    return (
        f'<m:oMathPara xmlns:m="{M_NS}">'
        f"<m:oMath>{inner}</m:oMath>"
        "</m:oMathPara>"
    )


def _norm_key(text: str) -> str:
    text = text.strip().strip("*")
    text = text.rstrip(",.;")
    text = re.sub(r"\s+", " ", text)
    return text


# --- Составные элементы ---
_QI = _sub("Q", "i")
_KI = _sub("K", "i")
_VI = _sub("v", "i")
_HI = _sub("h", "i")
_CI = _sub("c", "i")
_FI = _sub("f", "i")
_GI = _sub("G", "i")
_ST = _sub("S", "t")
_SSI = _sub("SS", "i")
_SIGI = _sub("σ", "i")
_KAVG = _sub("K", "avg")
_CHOLD = _sub("C", "hold")
_CORDER = _sub("C", "order")
_II = _sub("I", "i")
_DOLYA = _sub("Доля", "i")

_SQRT_2_KAVG_VI_HI = _rad(f"{_r('2')}{_KAVG}{_VI}{_frac(_r('1'), _HI)}")
_SQRT_2_KAVG_VI_HI_PROD = _rad(f"{_r('2')}{_KAVG}{_VI}{_HI}")
_SQRT_2_KI_T_VI_HI = _rad(
    f"{_r('2')}{_frac(_KI, _r('T'))}{_VI}{_frac(_r('1'), _HI)}"
)
_SQRT_2_KI_T_VI_HI_PROD = _rad(f"{_r('2')}{_frac(_KI, _r('T'))}{_VI}{_HI}")
_SQRT_2_KI_VI_HI = _rad(f"{_r('2')}{_KI}{_VI}{_frac(_r('1'), _HI)}")
_SQRT_2_KI_VI_HI_PROD = _rad(f"{_r('2')}{_KI}{_VI}{_HI}")
_SQRT_L = _rad(_r("L"))
_QI_HALF = _frac(_QI, _r("2"))
_TSTAR = _sup("T", "*")
_TSTAR_SQRT = _rad(_r("2") + _frac(_r("SUM(K)"), _r("SUM(h·v)")))


def _build_registry() -> dict[str, str]:
    return {
        _norm_key("G_i = v_i * c_i * 365"): _omath(
            _GI, _r(" = "), _VI, _r("·"), _sub("c", "i"), _r("·365")
        ),
        _norm_key("Доля_i = G_i / sum(G_i)"): _omath(
            _DOLYA,
            _r(" = "),
            _frac(_GI, _sum_i(_GI)),
        ),
        _norm_key("Q_i = sqrt(2 * K_avg * v_i / h_i)"): _omath(
            _QI, _r(" = "), _SQRT_2_KAVG_VI_HI
        ),
        _norm_key("TC = sum_i sqrt(2 * K_avg * v_i * h_i)"): _omath(
            _r("TC = "), _sum_i(_SQRT_2_KAVG_VI_HI_PROD)
        ),
        _norm_key("SS_i = z * sigma_i * sqrt(L)"): _omath(
            _SSI, _r(" = "), _r("z·"), _SIGI, _r("·"), _SQRT_L
        ),
        _norm_key("Q_i = sqrt(2 * (K_i / T) * v_i / h_i)"): _omath(
            _QI, _r(" = "), _SQRT_2_KI_T_VI_HI
        ),
        _norm_key("TC_full = sum_i sqrt(2 * (K_i / T) * v_i * h_i)"): _omath(
            _sub("TC", "full"), _r(" = "), _sum_i(_SQRT_2_KI_T_VI_HI_PROD)
        ),
        _norm_key("Q_i = sqrt(2 * K_i * v_i / h_i)"): _omath(
            _QI, _r(" = "), _SQRT_2_KI_VI_HI
        ),
        _norm_key("TC_sep = sum_i sqrt(2 * K_i * v_i * h_i)"): _omath(
            _sub("TC", "sep"), _r(" = "), _sum_i(_SQRT_2_KI_VI_HI_PROD)
        ),
        _norm_key("TC = C_hold + C_order"): _omath(
            _r("TC = "), _CHOLD, _r(" + "), _CORDER
        ),
        _norm_key("S_t = sum_i f_i * max(0, Q_i - v_i * t)"): _omath(
            _ST,
            _r(" = "),
            _sum_i(_FI + _r("·max(0,") + _QI + _r(" − ") + _VI + _r("·t)")),
        ),
        _norm_key("I_i = (Q_i / 2) * c_i"): _omath(
            _II, _r(" = "), _QI_HALF, _r("·"), _CI
        ),
        _norm_key("T* = sqrt(2 * SUM(K) / SUM(h * v))"): _omath(
            _TSTAR, _r(" = "), _TSTAR_SQRT
        ),
    }


FORMULA_REGISTRY = _build_registry()


def get_omml(text: str) -> str | None:
    return FORMULA_REGISTRY.get(_norm_key(text))


def setup_formula_paragraph(p) -> None:
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.line_spacing = 1.0
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_formula_paragraph(doc, text: str, txt: list[str]) -> bool:
    """Вставляет формулу через OMML. Возвращает True при успехе."""
    key = _norm_key(text)
    omml = FORMULA_REGISTRY.get(key)
    if not omml:
        return False

    p = doc.add_paragraph()
    setup_formula_paragraph(p)
    p._element.append(parse_xml(omml))
    txt.append(key)
    return True
