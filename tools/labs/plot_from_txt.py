from pathlib import Path
import csv
from collections import defaultdict
import pygal

# Use paths relative to this script location
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'иоуз4_данные.txt'
OUT_DIR = BASE_DIR / 'graphs_from_txt'


def to_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == '':
        return None
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    grouped = defaultdict(list)

    with DATA_FILE.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            scenario = row['scenario']
            grouped[scenario].append({
                'day': int(float(row['day'])),
                'stock_start': to_float(row['stock_start']),
                'demand': to_float(row['demand']),
                'stock_end': to_float(row['stock_end']),
                'order_flag': to_float(row['order_flag']) or 0.0,
                'receipt': to_float(row['receipt']) or 0.0,
                'stock_after_receipt': to_float(row['stock_after_receipt']),
                'sz': to_float(row.get('sz')),
                'tz': to_float(row.get('tz')),
                'mzz': to_float(row.get('mzz')),
            })

    for scenario, rows in grouped.items():
        rows.sort(key=lambda x: x['day'])
        days = [r['day'] for r in rows]
        step = max(1, len(days) // 20)
        xlabels = [str(d) if i % step == 0 else '' for i, d in enumerate(days)]

        current_stock = [r['stock_after_receipt'] for r in rows]
        tz_value = rows[0]['tz']
        sz_value = rows[0]['sz']
        mzz_value = rows[0]['mzz']
        tz_line = [tz_value] * len(rows)
        sz_line = [sz_value] * len(rows)
        mzz_line = [mzz_value] * len(rows)

        order_points = [
            current_stock[i] if rows[i]['order_flag'] > 0 else None
            for i in range(len(rows))
        ]
        receipt_points = [
            current_stock[i] if rows[i]['receipt'] > 0 else None
            for i in range(len(rows))
        ]

        chart1 = pygal.Line(
            show_dots=False,
            x_label_rotation=20,
            legend_at_bottom=True,
            show_minor_x_labels=False,
        )
        chart1.title = f'{scenario}: график движения запаса'
        chart1.x_labels = xlabels
        chart1.add('Текущий запас', current_stock)
        chart1.add('ТЗ', tz_line)
        chart1.add('СЗ', sz_line)
        chart1.add('МЖЗ', mzz_line)
        chart1.add('Момент заказа', order_points, dots_size=4, stroke=False)
        chart1.add('Момент поступления', receipt_points, dots_size=4, stroke=False)
        chart1.render_to_file(str(OUT_DIR / f'{scenario}_движение_запаса.svg'))

    print(f'Charts saved to: {OUT_DIR}')


if __name__ == '__main__':
    main()
