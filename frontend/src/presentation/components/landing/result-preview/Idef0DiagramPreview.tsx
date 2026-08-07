/** Static IDEF0 A-0 + A0 preview for landing. */

function Idef0Box({
  x,
  y,
  w,
  h,
  label,
  sublabel,
}: {
  x: number
  y: number
  w: number
  h: number
  label: string
  sublabel?: string
}) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={4} className="idef0-box" />
      <rect x={x} y={y} width={6} height={h} rx={2} className="idef0-box__control-side" />
      <text x={x + w / 2 + 3} y={y + h / 2 - (sublabel ? 4 : 0)} textAnchor="middle" className="idef0-box__label">
        {label}
      </text>
      {sublabel && (
        <text x={x + w / 2 + 3} y={y + h / 2 + 12} textAnchor="middle" className="idef0-box__sublabel">
          {sublabel}
        </text>
      )}
    </g>
  )
}

function Arrow({
  x1,
  y1,
  x2,
  y2,
  label,
  labelX,
  labelY,
}: {
  x1: number
  y1: number
  x2: number
  y2: number
  label?: string
  labelX?: number
  labelY?: number
}) {
  return (
    <g>
      <line x1={x1} y1={y1} x2={x2} y2={y2} className="idef0-arrow" markerEnd="url(#idef0-arrowhead)" />
      {label && (
        <text x={labelX ?? (x1 + x2) / 2} y={labelY ?? (y1 + y2) / 2 - 6} textAnchor="middle" className="idef0-arrow__label">
          {label}
        </text>
      )}
    </g>
  )
}

export function Idef0DiagramPreview() {
  return (
    <div className="result-diagram-preview">
      <div className="result-diagram-preview__head">
        <strong>IDEF0 A-0</strong>
        <span className="hint">Контекстная диаграмма</span>
      </div>
      <svg viewBox="0 0 760 380" className="result-diagram-preview__svg" aria-label="IDEF0 A-0 и A0">
        <defs>
          <marker id="idef0-arrowhead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" />
          </marker>
        </defs>

        {/* A-0 context */}
        <text x="380" y="22" textAnchor="middle" className="idef0-title">
          A-0 · Система сравнительного анализа алгоритмов сортировки
        </text>

        <Arrow x1={60} y1={95} x2={175} y2={95} label="I: массивы данных" labelX={118} labelY={84} />
        <Arrow x1={380} y1={38} x2={380} y2={68} label="C: методичка" labelX={430} labelY={56} />
        <Idef0Box x={180} y={72} w={400} h={56} label="Выполнить сравнительный анализ" sublabel="алгоритмов сортировки" />
        <Arrow x1={585} y1={100} x2={700} y2={100} label="O: отчёт + графики" labelX={642} labelY={89} />
        <Arrow x1={380} y1={128} x2={380} y2={158} label="M: Python / Jupyter" labelX={455} labelY={146} />

        {/* A0 decomposition */}
        <text x="380" y="188" textAnchor="middle" className="idef0-title">
          A0 · Декомпозиция
        </text>

        <Idef0Box x={24} y={210} w={150} h={52} label="A1" sublabel="Загрузить данные" />
        <Idef0Box x={204} y={210} w={150} h={52} label="A2" sublabel="Профилировать" />
        <Idef0Box x={384} y={210} w={150} h={52} label="A3" sublabel="Построить графики" />
        <Idef0Box x={564} y={210} w={150} h={52} label="A4" sublabel="Собрать docx" />

        <Arrow x1={174} y1={236} x2={204} y2={236} />
        <Arrow x1={354} y1={236} x2={384} y2={236} />
        <Arrow x1={534} y1={236} x2={564} y2={236} />

        <text x="380" y="300" textAnchor="middle" className="idef0-caption">
          Рисунок 2.1 — функциональная модель по стандарту IDEF0 (вставляется в docx)
        </text>

        {/* ICOM legend */}
        <g transform="translate(24, 318)">
          <text className="idef0-legend">I — вход</text>
          <text x="70" className="idef0-legend">C — управление</text>
          <text x="175" className="idef0-legend">O — выход</text>
          <text x="260" className="idef0-legend">M — механизм</text>
        </g>
      </svg>
    </div>
  )
}
