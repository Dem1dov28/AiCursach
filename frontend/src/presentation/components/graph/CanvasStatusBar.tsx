import { STATUS_LABELS } from '@/domain/graph/agentPresentation'

interface Props {
  doneCount: number
  totalCount: number
  currentTask?: string
}

export function CanvasStatusBar({ doneCount, totalCount, currentTask }: Props) {
  const pct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0

  return (
    <div className="canvas-status-bar">
      <div className="canvas-status-bar__main">
        <div>
          <h2 className="canvas-status-bar__title">Команда агентов</h2>
          {currentTask ? (
            <p className="canvas-status-bar__task">{currentTask}</p>
          ) : (
            <p className="canvas-status-bar__task hint">Клик по агенту — детали в инспекторе</p>
          )}
        </div>
        <div className="canvas-status-bar__progress" aria-label={`Прогресс ${pct}%`}>
          <div className="canvas-status-bar__progress-track">
            <div className="canvas-status-bar__progress-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="canvas-status-bar__progress-label">
            {doneCount}/{totalCount}
          </span>
        </div>
      </div>
      <ul className="canvas-legend" aria-label="Статусы агентов">
        {(['done', 'active', 'awaiting', 'revision', 'idle'] as const).map((status) => (
          <li key={status}>
            <span className={`canvas-legend__dot canvas-legend__dot--${status}`} />
            {STATUS_LABELS[status]}
          </li>
        ))}
      </ul>
    </div>
  )
}
