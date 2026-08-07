/** Static flowchart for sorting benchmark pipeline. */

export function FlowchartDiagramPreview() {
  return (
    <div className="result-diagram-preview">
      <div className="result-diagram-preview__head">
        <strong>Блок-схема</strong>
        <span className="hint">Алгоритм профилирования</span>
      </div>
      <svg viewBox="0 0 760 380" className="result-diagram-preview__svg" aria-label="Блок-схема профилирования">
        <defs>
          <marker id="flow-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" />
          </marker>
        </defs>

        <rect x="300" y="16" width="160" height="40" rx="20" className="flow-node flow-node--terminal" />
        <text x="380" y="41" textAnchor="middle" className="flow-label">Старт</text>

        <line x1="380" y1="56" x2="380" y2="76" className="flow-edge" markerEnd="url(#flow-arrow)" />

        <rect x="250" y="76" width="260" height="44" rx="6" className="flow-node" />
        <text x="380" y="103" textAnchor="middle" className="flow-label">Сгенерировать массив size=n</text>

        <line x1="380" y1="120" x2="380" y2="140" className="flow-edge" markerEnd="url(#flow-arrow)" />

        <rect x="230" y="140" width="300" height="44" rx="6" className="flow-node" />
        <text x="380" y="167" textAnchor="middle" className="flow-label">Для каждого алгоритма из ALGORITHMS</text>

        <line x1="380" y1="184" x2="380" y2="204" className="flow-edge" markerEnd="url(#flow-arrow)" />

        <polygon points="380,204 470,248 380,292 290,248" className="flow-node flow-node--decision" />
        <text x="380" y="252" textAnchor="middle" className="flow-label">runs &lt; 30?</text>

        <line x1="470" y1="248" x2="560" y2="248" className="flow-edge" markerEnd="url(#flow-arrow)" />
        <rect x="560" y="226" width="160" height="44" rx="6" className="flow-node" />
        <text x="640" y="253" textAnchor="middle" className="flow-label">Замерить time()</text>
        <line x1="640" y1="226" x2="640" y2="167" className="flow-edge" />
        <line x1="640" y1="167" x2="530" y2="167" className="flow-edge" markerEnd="url(#flow-arrow)" />

        <line x1="380" y1="292" x2="380" y2="312" className="flow-edge" markerEnd="url(#flow-arrow)" />
        <rect x="250" y="312" width="260" height="44" rx="6" className="flow-node" />
        <text x="380" y="339" textAnchor="middle" className="flow-label">Сохранить median / p95 в CSV</text>

        <text x="380" y="372" textAnchor="middle" className="idef0-caption">
          Рисунок 2.3 — блок-схема основного цикла бенчмаркинга
        </text>
      </svg>
    </div>
  )
}
