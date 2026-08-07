#!/usr/bin/env python3
"""Титульник и реферат из ручной редакции Word."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document

BASE = Path(__file__).resolve().parent
MANUAL_BACKUP = BASE / "Курсовая_ИОУЗ_ручная_редакция_backup.docx"

TITLE_SLICE = slice(0, 24)      # body-элементы титульного листа
ABSTRACT_SLICE = slice(24, 37)  # реферат до «СОДЕРЖАНИЕ»

TITLE_THEME_OLD = "МАГАЗИНА БЫТОВОЙ ХИМИИ"
TITLE_THEME_NEW = "МАСТЕРСКОЙ ПО РЕМОНТУ КОМПЬЮТЕРНОЙ ТЕХНИКИ"


def _load_body_children() -> list:
    if not MANUAL_BACKUP.exists():
        raise FileNotFoundError(f"Не найден файл ручной редакции: {MANUAL_BACKUP}")
    src = Document(MANUAL_BACKUP)
    return list(src.element.body)


def _clear_body_keep_sectpr(doc: Document) -> None:
    body = doc.element.body
    for child in list(body):
        if not child.tag.endswith("sectPr"):
            body.remove(child)


def _element_plain_text(el) -> str:
    if el.tag.endswith("tbl"):
        rows = []
        for tr in el.xpath(".//w:tr"):
            cells = []
            for tc in tr.xpath("./w:tc"):
                texts = tc.xpath(".//w:t")
                cells.append("".join(t.text or "" for t in texts).strip())
            if any(cells):
                rows.append(" | ".join(c for c in cells if c))
        return "\n".join(rows)
    texts = el.xpath(".//w:t")
    return "".join(t.text or "" for t in texts)


def _strip_sectpr(el) -> None:
    for sectpr in el.xpath(".//w:sectPr"):
        parent = sectpr.getparent()
        if parent is not None:
            parent.remove(sectpr)


def _append_elements(doc: Document, elements: list, txt: list[str]) -> None:
    body = doc.element.body
    for el in elements:
        if el.tag.endswith("sectPr"):
            continue
        copied = deepcopy(el)
        _strip_sectpr(copied)
        body.append(copied)
        text = _element_plain_text(copied).strip()
        if text:
            txt.append(text)


def _fix_title_theme(doc: Document) -> None:
    """На титуле в backup была старая тема — выравниваем с рефератом."""
    for t in doc.element.body.xpath(".//w:t"):
        if t.text and TITLE_THEME_OLD in t.text:
            t.text = t.text.replace(TITLE_THEME_OLD, TITLE_THEME_NEW)


def append_manual_title(doc: Document, txt: list[str]) -> None:
    children = _load_body_children()[TITLE_SLICE]
    _clear_body_keep_sectpr(doc)
    _append_elements(doc, children, txt)
    _fix_title_theme(doc)


def append_manual_abstract(doc: Document, txt: list[str]) -> None:
    children = _load_body_children()[ABSTRACT_SLICE]
    _append_elements(doc, children, txt)
