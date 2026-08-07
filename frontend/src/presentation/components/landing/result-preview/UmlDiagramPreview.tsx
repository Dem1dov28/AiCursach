/** Static UML use-case preview for landing. */

export function UmlDiagramPreview() {
  return (
    <div className="result-diagram-preview">
      <div className="result-diagram-preview__head">
        <strong>UML Use Case</strong>
        <span className="hint">Диаграмма прецедентов</span>
      </div>
      <svg viewBox="0 0 760 340" className="result-diagram-preview__svg" aria-label="UML Use Case">
        <rect x="120" y="24" width="520" height="292" rx="8" className="uml-system" />
        <text x="380" y="48" textAnchor="middle" className="uml-system__label">
          Программный комплекс бенчмаркинга
        </text>

        {/* Actors */}
        <g className="uml-actor">
          <circle cx="52" cy="120" r="14" />
          <line x1="52" y1="134" x2="52" y2="168" />
          <line x1="32" y1="148" x2="72" y2="148" />
          <line x1="52" y1="168" x2="36" y2="196" />
          <line x1="52" y1="168" x2="68" y2="196" />
          <text x="52" y="214" textAnchor="middle">
            Студент
          </text>
        </g>

        <g className="uml-actor">
          <circle cx="708" cy="120" r="14" />
          <line x1="708" y1="134" x2="708" y2="168" />
          <line x1="688" y1="148" x2="728" y2="148" />
          <line x1="708" y1="168" x2="692" y2="196" />
          <line x1="708" y1="168" x2="724" y2="196" />
          <text x="708" y="214" textAnchor="middle">
            Преподаватель
          </text>
        </g>

        {/* Use cases */}
        {[
          { x: 220, y: 88, label: 'Загрузить набор данных' },
          { x: 430, y: 88, label: 'Запустить бенчмарк' },
          { x: 320, y: 158, label: 'Сравнить алгоритмы' },
          { x: 220, y: 228, label: 'Экспортировать отчёт' },
          { x: 430, y: 228, label: 'Проверить результаты' },
        ].map((uc) => (
          <g key={uc.label}>
            <ellipse cx={uc.x + 90} cy={uc.y + 18} rx="90" ry="26" className="uml-usecase" />
            <text x={uc.x + 90} y={uc.y + 22} textAnchor="middle" className="uml-usecase__label">
              {uc.label}
            </text>
          </g>
        ))}

        {/* Relations */}
        <line x1="66" y1="120" x2="220" y2="106" className="uml-link" />
        <line x1="66" y1="130" x2="220" y2="246" className="uml-link" />
        <line x1="694" y1="120" x2="520" y2="246" className="uml-link" />
        <line x1="310" y1="114" x2="340" y2="140" className="uml-link" />
        <line x1="520" y1="114" x2="410" y2="140" className="uml-link" />

        <text x="380" y="318" textAnchor="middle" className="idef0-caption">
          Рисунок 2.2 — UML-диаграмма прецедентов (PlantUML → PNG в docx)
        </text>
      </svg>
    </div>
  )
}
