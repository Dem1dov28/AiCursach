#!/usr/bin/env python3
"""Сборка Excel-таблиц курсовой с формулами (xlsxwriter — совместимость с Excel macOS)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

BASE = Path(__file__).resolve().parent
TSV_SOURCE = BASE / "приложение_А_исходные_данные_50.tsv"
TSV_ABC = BASE / "результаты_ABC_XYZ.tsv"
OUT = BASE / "таблицы_для_курсовой.xlsx"

DAYS = 365
ABC_A = 0.8
ABC_B = 0.95
XYZ_X = 0.15
XYZ_Y = 0.25
T_FULL_BZ = 2.309

GROUPS = ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]
STRATEGY = {
    "AX": "Частичное совмещение (кратные периоды)",
    "BX": "Частичное совмещение (кратные периоды)",
    "AY": "Полное совмещение / страховой запас",
    "BY": "Полное совмещение / страховой запас",
    "CY": "Полное совмещение / страховой запас",
    "AZ": "Раздельная оптимизация",
    "BZ": "Раздельная оптимизация",
    "CZ": "Поставка под заказ",
    "CX": "нет позиций",
}

S_PARAMS = "Params"
S_SOURCE = "Source50"
S_ABC = "ABC_XYZ"
S_MATRIX = "Matrix"
S_DETAIL = "DetailEOQ"
S_OPT = "OptGroups"
S_BZ_CALC = "BZ_Calc"
S_BZ_CMP = "BZ_Compare"
S_BZ_GRAPH = "BZ_Graph12"


def ref(sheet: str, addr: str) -> str:
    return f"{sheet}!{addr}"


def read_source() -> list[dict[str, str]]:
    with TSV_SOURCE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_abc_sorted() -> list[dict[str, str]]:
    with TSV_ABC.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return sorted(rows, key=lambda r: -float(r["annual_value"]))


def bz_codes() -> list[str]:
    with (BASE / "матрица_ABC_XYZ.tsv").open(encoding="utf-8") as f:
        matrix = list(csv.DictReader(f, delimiter="\t"))
    row = next(r for r in matrix if r["group"] == "BZ")
    return [c.strip() for c in row["codes"].split(",")]


class Fmt:
    def __init__(self, wb: xlsxwriter.Workbook) -> None:
        self.header = wb.add_format(
            {
                "bold": True,
                "font_name": "Times New Roman",
                "font_size": 11,
                "bg_color": "#D9E1F2",
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )
        self.body = wb.add_format(
            {
                "font_name": "Times New Roman",
                "font_size": 11,
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )
        self.title = wb.add_format(
            {"bold": True, "font_name": "Times New Roman", "font_size": 12}
        )


def write_params_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_PARAMS)
    ws.write_row(0, 0, ["Параметр", "Значение", "Комментарий"], fmt.header)
    params = [
        ("DAYS", DAYS, "рабочих дней в году"),
        ("ABC_A", ABC_A, "граница A (накопленная доля)"),
        ("ABC_B", ABC_B, "граница B (накопленная доля)"),
        ("XYZ_X", XYZ_X, "граница X (CV)"),
        ("XYZ_Y", XYZ_Y, "граница Y (CV)"),
        ("T_FULL_BZ", T_FULL_BZ, "период T* полного совмещения BZ, сут."),
    ]
    for i, (name, val, note) in enumerate(params, start=1):
        ws.write(i, 0, name, fmt.body)
        ws.write(i, 1, val, fmt.body)
        ws.write(i, 2, note, fmt.body)
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 12)
    ws.set_column(2, 2, 42)


def write_source_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_SOURCE)
    headers = [
        "code",
        "name",
        "demand_v",
        "coef_variation_cv",
        "unit_price_c",
        "order_cost_K",
        "holding_cost_h",
        "storage_area_f",
    ]
    ws.write_row(0, 0, headers, fmt.header)
    for r, row in enumerate(read_source(), start=1):
        ws.write(r, 0, row["code"], fmt.body)
        ws.write(r, 1, row["name"], fmt.body)
        for c, key in enumerate(headers[2:], start=2):
            ws.write_number(r, c, float(row[key]), fmt.body)
    ws.freeze_panes(1, 0)
    ws.set_column(0, 0, 8)
    ws.set_column(1, 1, 38)
    ws.set_column(2, 7, 12)


def write_abc_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_ABC)
    headers = [
        "rank",
        "code",
        "name",
        "demand_v",
        "coef_variation_cv",
        "unit_price_c",
        "annual_value",
        "share",
        "cum_share",
        "abc",
        "xyz",
        "group",
    ]
    ws.write_row(0, 0, headers, fmt.header)
    sorted_rows = read_abc_sorted()
    n = len(sorted_rows)
    src = S_SOURCE
    for i, row in enumerate(sorted_rows, start=1):
        r = i + 1
        ws.write_number(r - 1, 0, i, fmt.body)
        ws.write(r - 1, 1, row["code"], fmt.body)
        ws.write_formula(
            r - 1,
            2,
            f"=INDEX({ref(src, 'B:B')},MATCH(B{r},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            r - 1,
            3,
            f"=INDEX({ref(src, 'C:C')},MATCH(B{r},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            r - 1,
            4,
            f"=INDEX({ref(src, 'D:D')},MATCH(B{r},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            r - 1,
            5,
            f"=INDEX({ref(src, 'E:E')},MATCH(B{r},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(r - 1, 6, f"=D{r}*F{r}*{ref(S_PARAMS, '$B$2')}", fmt.body)
        ws.write_formula(r - 1, 7, f"=G{r}/SUM($G$2:$G${n + 1})", fmt.body)
        ws.write_formula(r - 1, 8, f"=SUM($H$2:H{r})", fmt.body)
        ws.write_formula(
            r - 1,
            9,
            f'=IF(I{r}<={ref(S_PARAMS, "$B$3")},"A",IF(I{r}<={ref(S_PARAMS, "$B$4")},"B","C"))',
            fmt.body,
        )
        ws.write_formula(
            r - 1,
            10,
            f'=IF(E{r}<={ref(S_PARAMS, "$B$5")},"X",IF(E{r}<={ref(S_PARAMS, "$B$6")},"Y","Z"))',
            fmt.body,
        )
        ws.write_formula(r - 1, 11, f"=CONCATENATE(J{r},K{r})", fmt.body)
    ws.freeze_panes(1, 0)
    ws.set_column(0, 1, 8)
    ws.set_column(2, 2, 34)
    ws.set_column(6, 8, 12)


def write_matrix_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_MATRIX)
    ws.write_row(0, 0, ["group", "codes", "count"], fmt.header)
    abc = S_ABC
    helper_row_start = 12
    abc_last = 61

    for i, g in enumerate(GROUPS, start=2):
        ws.write(i - 1, 0, g, fmt.body)
        helper_col = xl_col_to_name(3 + i - 1)
        for hr in range(helper_row_start, abc_last + 1):
            abc_row = hr - 10
            ws.write_formula(
                hr - 1,
                3 + i - 1,
                f"=IF({ref(abc, f'L{abc_row}')}=$A{i},{ref(abc, f'B{abc_row}')},\"\")",
                fmt.body,
            )
        ws.write_formula(
            i - 1,
            1,
            f'=TEXTJOIN(", ",TRUE,{helper_col}{helper_row_start}:{helper_col}{abc_last})',
            fmt.body,
        )
        ws.write_formula(
            i - 1, 2, f"=COUNTIF({ref(abc, '$L$2:$L$51')},A{i})", fmt.body
        )

    ws.write(10, 0, "Расчёт codes: TEXTJOIN по столбцам E–M, строки 12–61", fmt.body)
    ws.set_column(0, 0, 8)
    ws.set_column(1, 1, 70)
    ws.set_column(2, 2, 8)


def write_detail_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_DETAIL)
    headers = [
        "Группа",
        "Код",
        "Номенклатура",
        "v, ед./день",
        "K, ден. ед.",
        "h, ден. ед./день",
        "Q*",
        "tau*",
        "Lдень",
        "Q*f, м2",
    ]
    ws.write_row(0, 0, headers, fmt.header)
    calc_groups = {"BX", "AY", "BY", "CY", "AZ", "BZ", "CZ"}
    detail_rows = [r for r in read_abc_sorted() if r["group"] in calc_groups]
    src = S_SOURCE
    for i, row in enumerate(detail_rows, start=2):
        ws.write(i - 1, 0, row["group"], fmt.body)
        ws.write(i - 1, 1, row["code"], fmt.body)
        ws.write_formula(
            i - 1,
            2,
            f"=INDEX({ref(src, 'B:B')},MATCH(B{i},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            i - 1,
            3,
            f"=INDEX({ref(src, 'C:C')},MATCH(B{i},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            i - 1,
            4,
            f"=INDEX({ref(src, 'F:F')},MATCH(B{i},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            i - 1,
            5,
            f"=INDEX({ref(src, 'G:G')},MATCH(B{i},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(i - 1, 6, f"=SQRT(2*E{i}*D{i}/F{i})", fmt.body)
        ws.write_formula(i - 1, 7, f"=G{i}/D{i}", fmt.body)
        ws.write_formula(i - 1, 8, f"=SQRT(2*E{i}*F{i}*D{i})", fmt.body)
        ws.write_formula(
            i - 1,
            9,
            f"=G{i}*INDEX({ref(src, 'H:H')},MATCH(B{i},{ref(src, 'A:A')},0))",
            fmt.body,
        )
    ws.freeze_panes(1, 0)
    ws.set_column(0, 1, 8)
    ws.set_column(2, 2, 34)


def write_opt_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_OPT)
    headers = [
        "Группа",
        "Кол-во позиций",
        "Стратегия",
        "Суточные затраты, ден. ед.",
        "Годовые затраты, ден. ед.",
        "Макс. площадь, м2",
    ]
    ws.write_row(0, 0, headers, fmt.header)
    det = S_DETAIL
    mat = S_MATRIX
    for i, g in enumerate(GROUPS, start=2):
        ws.write(i - 1, 0, g, fmt.body)
        ws.write_formula(i - 1, 1, f"={ref(mat, f'C{i}')}", fmt.body)
        ws.write(i - 1, 2, STRATEGY[g], fmt.body)
        if g in ("CX", "AX"):
            ws.write_number(i - 1, 3, 0, fmt.body)
            ws.write_number(i - 1, 4, 0, fmt.body)
            ws.write_number(i - 1, 5, 0, fmt.body)
        else:
            ws.write_formula(
                i - 1, 3, f"=SUMIF({ref(det, '$A:$A')},A{i},{ref(det, '$I:$I')})", fmt.body
            )
            ws.write_formula(i - 1, 4, f"=D{i}*{ref(S_PARAMS, '$B$2')}", fmt.body)
            ws.write_formula(
                i - 1, 5, f"=SUMIF({ref(det, '$A:$A')},A{i},{ref(det, '$J:$J')})", fmt.body
            )
    ws.set_column(2, 2, 36)


def write_bz_calc_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_BZ_CALC)
    ws.write(0, 0, "Расчёт стратегий для группы BZ", fmt.title)
    ws.write(2, 0, "N (позиций BZ)", fmt.body)
    ws.write_formula(2, 1, f'=COUNTIF({ref(S_ABC, "$L$2:$L$51")},"BZ")', fmt.body)
    ws.write(3, 0, "SUM(K)", fmt.body)
    ws.write_formula(
        3,
        1,
        f"=SUMIF({ref(S_DETAIL, '$A:$A')},\"BZ\",{ref(S_DETAIL, '$E:$E')})",
        fmt.body,
    )
    ws.write(4, 0, "SUM(h*v)", fmt.body)
    ws.write_formula(
        4,
        1,
        f"=SUMPRODUCT(({ref(S_DETAIL, '$A$2:$A$60')}=\"BZ\")*"
        f"{ref(S_DETAIL, '$D$2:$D$60')},{ref(S_DETAIL, '$F$2:$F$60')})",
        fmt.body,
    )
    ws.write(5, 0, "T* полного совмещения, сут.", fmt.body)
    ws.write_formula(5, 1, f"={ref(S_PARAMS, '$B$7')}", fmt.body)
    ws.write(6, 0, "tau* = SQRT(2*SUM(K)/SUM(hv))", fmt.body)
    ws.write_formula(6, 1, "=SQRT(2*B4/B5)", fmt.body)

    headers = ["Код", "v", "K", "h", "L разд.", "L частич.", "L полн."]
    ws.write_row(8, 0, headers, fmt.header)
    src = S_SOURCE
    codes = bz_codes()
    for idx, code in enumerate(codes, start=10):
        ws.write(idx - 1, 0, code, fmt.body)
        ws.write_formula(
            idx - 1,
            1,
            f"=INDEX({ref(src, 'C:C')},MATCH(A{idx},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            idx - 1,
            2,
            f"=INDEX({ref(src, 'F:F')},MATCH(A{idx},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(
            idx - 1,
            3,
            f"=INDEX({ref(src, 'G:G')},MATCH(A{idx},{ref(src, 'A:A')},0))",
            fmt.body,
        )
        ws.write_formula(idx - 1, 4, f"=SQRT(2*C{idx}*B{idx}*D{idx})", fmt.body)
        ws.write_formula(idx - 1, 5, f"=SQRT(2*($B$4/$B$3)*B{idx}*D{idx})", fmt.body)
        ws.write_formula(idx - 1, 6, f"=SQRT(2*(C{idx}/$B$6)*B{idx}*D{idx})", fmt.body)

    total = 10 + len(codes)
    ws.write(total - 1, 0, "ИТОГО", fmt.header)
    for col in range(4, 7):
        letter = xl_col_to_name(col)
        ws.write_formula(
            total - 1,
            col,
            f"=SUM({letter}10:{letter}{total - 1})",
            fmt.header,
        )


def write_bz_compare_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_BZ_CMP)
    ws.write_row(0, 0, ["Стратегия для BZ", "Суточные затраты", "Годовые затраты"], fmt.header)
    calc = S_BZ_CALC
    total_row = 17
    strategies = [
        ("Раздельная оптимизация", f"={ref(calc, f'E{total_row}')}"),
        ("Полное совмещение заказов", f"={ref(calc, f'G{total_row}')}"),
        ("Частичное совмещение (кратные периоды)", f"={ref(calc, f'F{total_row}')}"),
    ]
    for i, (name, daily) in enumerate(strategies, start=2):
        ws.write(i - 1, 0, name, fmt.body)
        ws.write_formula(i - 1, 1, daily, fmt.body)
        ws.write_formula(i - 1, 2, f"=B{i}*{ref(S_PARAMS, '$B$2')}", fmt.body)
    ws.write(5, 0, "Лучшая стратегия", fmt.body)
    ws.write_formula(5, 1, "=INDEX(A2:A4,MATCH(MIN(B2:B4),B2:B4,0))", fmt.body)
    ws.write_formula(5, 2, "=MIN(B2:B4)", fmt.body)
    ws.set_column(0, 0, 42)


def write_bz_graph_sheet(wb: xlsxwriter.Workbook, fmt: Fmt) -> None:
    ws = wb.add_worksheet(S_BZ_GRAPH)
    ws.write_row(0, 0, ["Период", "Занятая площадь склада, м2"], fmt.header)
    src = S_SOURCE
    codes = bz_codes()
    ws.write(0, 3, "Стратегия", fmt.header)
    ws.write(0, 4, "Полное совмещение заказов", fmt.body)
    ws.write(1, 3, "T*, сут.", fmt.body)
    ws.write_formula(1, 4, f"={ref(S_PARAMS, '$B$7')}", fmt.body)
    ws.write_row(0, 6, ["Код", "Q*", "v", "f"], fmt.header)

    for i, code in enumerate(codes, start=2):
        ws.write(i - 1, 6, code, fmt.body)
        ws.write_formula(
            i - 1,
            7,
            f"=SQRT(2*(INDEX({ref(src, 'F:F')},MATCH(G{i},{ref(src, 'A:A')},0))/{ref(S_PARAMS, '$B$7')})"
            f"*INDEX({ref(src, 'C:C')},MATCH(G{i},{ref(src, 'A:A')},0))/INDEX({ref(src, 'G:G')},MATCH(G{i},{ref(src, 'A:A')},0)))",
            fmt.body,
        )
        ws.write_formula(
            i - 1, 8, f"=INDEX({ref(src, 'C:C')},MATCH(G{i},{ref(src, 'A:A')},0))", fmt.body
        )
        ws.write_formula(
            i - 1, 9, f"=INDEX({ref(src, 'H:H')},MATCH(G{i},{ref(src, 'A:A')},0))", fmt.body
        )

    for p in range(1, 13):
        row = p + 1
        ws.write_number(row - 1, 0, p, fmt.body)
        parts = []
        for j, item_row in enumerate(range(2, 2 + len(codes))):
            col = xl_col_to_name(10 + j)
            ws.write_formula(
                row - 1,
                10 + j,
                f"=MAX(0,$H{item_row}-$I{item_row}*(($A{row}-1)*$E$2/12))*$J{item_row}",
                fmt.body,
            )
            parts.append(f"{col}{row}")
        ws.write_formula(row - 1, 1, f"=SUM({','.join(parts)})", fmt.body)

    ws.write(14, 0, "Максимально необходимая площадь склада, м2", fmt.header)
    ws.write_formula(14, 1, "=MAX(B2:B13)", fmt.header)
    ws.set_column(0, 0, 42)
    ws.set_column(1, 1, 22)


def verify_python() -> None:
    source = read_source()
    codes = bz_codes()
    items = [r for r in source if r["code"] in codes]
    n = len(items)
    ksum = sum(float(i["order_cost_K"]) for i in items)
    sep = sum(
        math.sqrt(
            2
            * float(i["order_cost_K"])
            * float(i["holding_cost_h"])
            * float(i["demand_v"])
        )
        for i in items
    )
    partial = sum(
        math.sqrt(2 * (ksum / n) * float(i["holding_cost_h"]) * float(i["demand_v"]))
        for i in items
    )
    full = sum(
        math.sqrt(
            2
            * (float(i["order_cost_K"]) / T_FULL_BZ)
            * float(i["holding_cost_h"])
            * float(i["demand_v"])
        )
        for i in items
    )
    print(f"  BZ раздельная (формула): {sep:.2f} (эталон 49.34)")
    print(f"  BZ полная (формула):     {full:.2f} (эталон 32.47)")
    print(f"  BZ частичная (формула):  {partial:.2f} (эталон 50.21)")


def main() -> None:
    wb = xlsxwriter.Workbook(
        str(OUT), {"strings_to_numbers": False, "use_future_functions": True}
    )
    fmt = Fmt(wb)
    write_params_sheet(wb, fmt)
    write_source_sheet(wb, fmt)
    write_abc_sheet(wb, fmt)
    write_matrix_sheet(wb, fmt)
    write_detail_sheet(wb, fmt)
    write_opt_sheet(wb, fmt)
    write_bz_calc_sheet(wb, fmt)
    write_bz_compare_sheet(wb, fmt)
    write_bz_graph_sheet(wb, fmt)
    wb.close()
    print(f"Created: {OUT}")
    verify_python()


if __name__ == "__main__":
    main()
