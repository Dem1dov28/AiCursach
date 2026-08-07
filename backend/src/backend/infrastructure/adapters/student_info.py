"""Разбор поля «Данные студента» из формы."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class StudentFields:
    group: str = ""
    student_name: str = ""
    teacher_name: str = ""
    variant: str = ""
    faculty: str = ""
    department: str = ""
    lab_number: str = ""
    checker_label: str = ""


_FIO = re.compile(
    r"(?:"
    r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\."
    r"|[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+"
    r")"
)
_GROUP = re.compile(r"групп[аы]?\s*[:\-]?\s*([0-9]{3,6}[а-яА-Яa-zA-Z]?)", re.I)
_VARIANT = re.compile(r"вариант\s*[:\-]?\s*(\d+)", re.I)
_TEACHER = re.compile(
    r"(?:преподавател[ьяюе]?\s*[:\-]?\s*|"
    r"руководител[ьяюе]?\s*[:\-]?\s*|"
    r"проверил[аи]?\s*[:\-]?\s*)"
    r"([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\."
    r"|[А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё]+)",
    re.I,
)
_FACULTY = re.compile(r"факультет\s*[:\-]?\s*(.+)", re.I)
_KAFEDRA = re.compile(r"кафедра\s*[:\-]?\s*(.+)", re.I)
_LAB_NUM = re.compile(r"лабораторн(?:ой|ая)\s+работ(?:e|ы)\s*№?\s*(\d+)", re.I)


def parse_student_info(text: str, *, variant: str = "") -> StudentFields:
    raw = (text or "").strip()
    fields = StudentFields(variant=(variant or "").strip())

    if not raw:
        return fields

    gm = _GROUP.search(raw)
    if gm:
        fields.group = gm.group(1).strip()

    vm = _VARIANT.search(raw)
    if vm:
        fields.variant = vm.group(1).strip()

    fm = _FACULTY.search(raw)
    if fm:
        fields.faculty = fm.group(1).strip()

    km = _KAFEDRA.search(raw)
    if km:
        fields.department = km.group(1).strip()

    lm = _LAB_NUM.search(raw)
    if lm:
        fields.lab_number = lm.group(1).strip()

    tm = _TEACHER.search(raw)
    fios = _FIO.findall(raw)
    if tm:
        fields.teacher_name = tm.group(1).strip()
        fios = [n for n in fios if n != fields.teacher_name]

    for name in fios:
        if not fields.student_name:
            fields.student_name = name
            break

    return fields


def fields_from_parts(
    *,
    group: str = "",
    student_name: str = "",
    teacher_name: str = "",
    variant: str = "",
    faculty: str = "",
    department: str = "",
    lab_number: str = "",
    student_info: str = "",
) -> StudentFields:
    """Собрать поля из отдельных инпутов формы (приоритет над текстом)."""
    parsed = parse_student_info(student_info, variant=variant)
    return StudentFields(
        group=(group or parsed.group).strip(),
        student_name=(student_name or parsed.student_name).strip(),
        teacher_name=(teacher_name or parsed.teacher_name).strip(),
        variant=(variant or parsed.variant).strip(),
        faculty=(faculty or parsed.faculty).strip(),
        department=(department or parsed.department).strip(),
        lab_number=(lab_number or parsed.lab_number).strip(),
    )
