/** Rich static samples for the landing «Result» section. */

export const RESULT_DOCX_TITLE = {
  university: 'Министерство науки и высшего образования Российской Федерации',
  institution: 'Федеральное государственное автономное образовательное учреждение высшего образования',
  shortName: '«Университет»',
  type: 'КУРСОВАЯ РАБОТА',
  discipline: 'по дисциплине «Алгоритмы и структуры данных»',
  topic: 'на тему: «Сравнительный анализ алгоритмов сортировки и построение программного комплекса бенчмаркинга»',
  student: 'Выполнил: студент группы ИВТ-401',
  supervisor: 'Научный руководитель: к.т.н., доцент кафедры ПИ',
  cityYear: 'Москва — 2026',
} as const

export const RESULT_DOCX_BODY = {
  sections: [
    {
      title: 'Введение',
      paragraphs: [
        'Актуальность темы обусловлена широким применением алгоритмов упорядочивания данных в системах баз данных, ETL-конвейерах, аналитических платформах и прикладном программном обеспечении. Выбор структуры сортировки напрямую влияет на время отклика сервиса и объём потребляемой памяти.',
        'Цель работы — реализовать программный комплекс для сравнения QuickSort, MergeSort, HeapSort и RadixSort на наборах различной мощности и степени предварительной упорядоченности, а также оформить результаты в виде отчёта по методическим требованиям.',
      ],
    },
    {
      title: '2.1 Общая характеристика алгоритмов',
      paragraphs: [
        'QuickSort (C.A.R. Hoare, 1962) относится к алгоритмам «разделяй и властвуй». Средняя трудоёмкость составляет O(n log n), худший случай — O(n²) при неудачном выборе опорного элемента. MergeSort гарантирует O(n log n) в любых условиях, но требует O(n) дополнительной памяти.',
        'HeapSort выполняется in-place с O(n log n) в худшем случае; RadixSort эффективен для целочисленных ключей фиксированной разрядности и демонстрирует линейную асимптотику при ограничениях на диапазон значений.',
      ],
      figure: 'Рисунок 2.1 — IDEF0-диаграмма контекста A-0 «Система сравнительного анализа алгоритмов сортировки»',
    },
    {
      title: '2.2 Методика эксперимента',
      paragraphs: [
        'Для каждого алгоритма выполнялось не менее 30 прогонов на массивах размером от 10³ до 10⁵ элементов. Фиксировались медианное время выполнения, размах и 95-% доверительный интервал. Графики строились средствами matplotlib; исходные логи сохранялись в каталоге data/benchmarks/.',
      ],
    },
  ],
  bibliography: [
    'Cormen T. H. Introduction to Algorithms. — 4th ed. — MIT Press, 2022. — 1292 p.',
    'Knuth D. E. The Art of Computer Programming, Vol. 3: Sorting and Searching. — Addison-Wesley, 1998.',
    'Hoare C. A. R. Quicksort // The Computer Journal. — 1962. — Vol. 5, № 1. — P. 10–16.',
  ],
} as const

export const RESULT_CODE_SAMPLE = `# sort_benchmark_suite.py — лабораторная №3, вариант 12
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np

Array = list[int]
SortFn = Callable[[Array], Array]


@dataclass(frozen=True)
class RunStats:
    algorithm: str
    size: int
    median_ms: float
    p95_ms: float
    runs: int = 30


@dataclass
class BenchmarkSuite:
    sizes: Iterable[int] = field(default_factory=lambda: range(2_000, 20_001, 2_000))
    seeds: Iterable[int] = field(default_factory=lambda: range(30))

    def measure(self, name: str, fn: SortFn, data: Array) -> RunStats:
        timings: list[float] = []
        for _ in self.seeds:
            payload = data.copy()
            t0 = time.perf_counter()
            fn(payload)
            timings.append((time.perf_counter() - t0) * 1000)
        return RunStats(name, len(data), statistics.median(timings), np.percentile(timings, 95))


def quicksort_inplace(a: Array, lo: int = 0, hi: int | None = None) -> None:
    hi = len(a) - 1 if hi is None else hi
    if lo >= hi:
        return
    pivot = a[(lo + hi) // 2]
    i, j = lo, hi
    while i <= j:
        while a[i] < pivot:
            i += 1
        while a[j] > pivot:
            j -= 1
        if i <= j:
            a[i], a[j] = a[j], a[i]
            i += 1
            j -= 1
    quicksort_inplace(a, lo, j)
    quicksort_inplace(a, i, hi)


def merge_sort(a: Array) -> Array:
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left, right = merge_sort(a[:mid]), merge_sort(a[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    return out + left[i:] + right[j:]


def heapify(a: Array, n: int, i: int) -> None:
    largest, left, right = i, 2 * i + 1, 2 * i + 2
    if left < n and a[left] > a[largest]:
        largest = left
    if right < n and a[right] > a[largest]:
        largest = right
    if largest != i:
        a[i], a[largest] = a[largest], a[i]
        heapify(a, n, largest)


def heap_sort(a: Array) -> Array:
    arr = a.copy()
    for i in range(len(arr) // 2 - 1, -1, -1):
        heapify(arr, len(arr), i)
    for end in range(len(arr) - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        heapify(arr, end, 0)
    return arr


def radix_sort_lsd(a: Array) -> Array:
    if not a:
        return []
    arr = a.copy()
    exp, base = 1, 10
    while exp <= max(arr):
        buckets: list[list[int]] = [[] for _ in range(base)]
        for value in arr:
            buckets[(value // exp) % base].append(value)
        arr = [x for bucket in buckets for x in bucket]
        exp *= base
    return arr


ALGORITHMS: dict[str, SortFn] = {
    "QuickSort": lambda x: (quicksort_inplace(x), x)[1],
    "MergeSort": merge_sort,
    "HeapSort": heap_sort,
    "RadixSort": radix_sort_lsd,
}


def run_all() -> list[RunStats]:
    rng = np.random.default_rng(42)
    results: list[RunStats] = []
    suite = BenchmarkSuite()
    for size in suite.sizes:
        base = rng.integers(0, 10_000, size=int(size)).tolist()
        for name, fn in ALGORITHMS.items():
            results.append(suite.measure(name, fn, base))
    return results


def export_plots(results: list[RunStats], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_name: dict[str, list[RunStats]] = {}
    for row in results:
        by_name.setdefault(row.algorithm, []).append(row)
    plt.figure(figsize=(9, 5))
    for name, rows in by_name.items():
        xs = [r.size for r in rows]
        ys = [r.median_ms for r in rows]
        plt.plot(xs, ys, marker="o", label=name)
    plt.xlabel("Размер массива, элементов")
    plt.ylabel("Медианное время, мс")
    plt.title("Сравнение алгоритмов сортировки")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "sort_benchmark.png", dpi=160)
`

export const RESULT_CODE_META = {
  filename: 'sort_benchmark_suite.py',
  status: 'Запуск кода · 30 прогонов · OK',
  output: `MergeSort  n=20000  median=18.4 ms  p95=19.1 ms
QuickSort  n=20000  median=12.7 ms  p95=14.2 ms
HeapSort   n=20000  median=21.3 ms  p95=22.0 ms
RadixSort  n=20000  median= 8.9 ms  p95= 9.4 ms
→ figures/sort_benchmark.png сохранён`,
} as const

export const RESULT_DIAGRAM_TABS = [
  { id: 'idef0', label: 'IDEF0' },
  { id: 'uml', label: 'UML' },
  { id: 'flowchart', label: 'Блок-схема' },
] as const

export type ResultDiagramTab = (typeof RESULT_DIAGRAM_TABS)[number]['id']
