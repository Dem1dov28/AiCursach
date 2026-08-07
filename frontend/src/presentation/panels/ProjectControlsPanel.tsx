import { useJobActions } from '@/application/jobs/useJobActions'
import { useWorkbench } from '@/application/workbench/WorkbenchContext'
import { useProjectControlsViewModel } from '@/application/workbench/useProjectControlsViewModel'
import { RevisionLimitControl } from '@/presentation/components/inspector/RevisionLimitControl'
import { StylePolisherToggle } from '@/presentation/components/inspector/StylePolisherToggle'
import { BibliographyVerifierToggle } from '@/presentation/components/inspector/BibliographyVerifierToggle'
import { AutonomyLevelControl } from '@/presentation/components/hitl/AutonomyLevelControl'
import { RosterStatusIcon } from '@/presentation/icons'
import { normalizeAutonomyLevel } from '@/domain/jobs/autonomy'

export function ProjectControlsPanel() {
  const {
    jobId,
    job,
    steps,
    statePatch,
    topology,
    activeAgent,
    awaitingPlanApproval,
    awaitingClarification,
    awaitingTeamApproval,
    clarificationAgent,
    connected,
    reconnecting,
    streamError,
    onNew,
    handleContinue,
    handleSelectAgent,
  } = useWorkbench()

  const { downloading, retrying, error: actionsError, downloadZip, retry } = useJobActions(jobId)

  const { phase, pct, roster, showContinue } = useProjectControlsViewModel({
    job,
    steps,
    topology,
    activeAgent,
    awaitingPlanApproval,
    awaitingClarification,
    awaitingTeamApproval,
    clarificationAgent,
  })
  const topic = statePatch.topic || job?.topic || ''
  const tokensTotal =
    statePatch.tokens_total ??
    (statePatch.tokens_input ?? 0) + (statePatch.tokens_output ?? 0)
  const costUsd = statePatch.estimated_cost_usd
  const maxRevisions = statePatch.max_revisions ?? 3
  const settingsDisabled = job?.status === 'completed' || job?.status === 'failed'

  return (
    <div className="panel project-controls-panel">
      <h2 className="panel-title">Проект</h2>

      <div className="panel-body">
      <div className="progress-track progress-track--compact">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="hint progress-hint">{steps.length} шагов агентов · {pct}%</p>

      <div className="field">
        <label htmlFor="project-topic">Тема работы</label>
        <input
          id="project-topic"
          type="text"
          readOnly
          value={topic}
          placeholder="Появится после анализа или из формы"
          className="project-topic-input"
        />
      </div>

      <div className={`project-status project-status--${phase.tone}`}>
        <span className="project-status__dot" aria-hidden />
        <span className="project-status__label">{phase.label}</span>
        <span className={`stream-dot ${connected ? 'live' : reconnecting ? 'reconnect' : ''}`}>
          {connected ? 'live' : reconnecting ? 'reconnect…' : 'offline'}
        </span>
      </div>

      <div className="project-actions">
        {showContinue && (
          <button type="button" className="btn btn-primary" onClick={handleContinue}>
            Продолжить
          </button>
        )}
        {job?.status === 'failed' && (
          <button
            type="button"
            className="btn btn-primary"
            disabled={retrying}
            onClick={() => void retry()}
          >
            {retrying ? 'Перезапуск…' : 'Повторить задачу'}
          </button>
        )}
        {job?.status === 'completed' && job.has_download && (
          <button
            type="button"
            className="btn btn-primary"
            disabled={downloading}
            onClick={downloadZip}
          >
            {downloading ? 'Скачивание…' : 'Экспорт .DOCX / ZIP'}
          </button>
        )}
        <button type="button" className="btn btn-secondary" onClick={onNew}>
          Сброс · новая работа
        </button>
      </div>

      {actionsError && <div className="alert alert-error">{actionsError}</div>}
      {streamError && <div className="alert alert-error">{streamError}</div>}
      {job?.error && <div className="alert alert-error">{job.error}</div>}

      <section className="controls-section">
        <h3>Команда агентов</h3>
        <ul className="agent-roster">
          {roster.map((agent) => (
            <li key={agent.id}>
              <button
                type="button"
                className={`agent-roster__item agent-roster__item--${agent.status}`}
                onClick={() => handleSelectAgent(agent.id)}
              >
                <span className="agent-roster__icon">
                  <RosterStatusIcon status={agent.status} />
                </span>
                <span className="agent-roster__name">{agent.label}</span>
              </button>
            </li>
          ))}
        </ul>
        <p className="hint">Клик по узлу на холсте → инспектор справа</p>
      </section>

      <section className="controls-section">
        <h3>Бюджет сессии</h3>
        <div className="metrics-grid metrics-grid--compact">
          <div className="metric-card">
            <span className="metric-value">{tokensTotal || '—'}</span>
            <span className="metric-label">токенов</span>
          </div>
          <div className="metric-card">
            <span className="metric-value">
              {costUsd != null ? `$${costUsd.toFixed(4)}` : '—'}
            </span>
            <span className="metric-label">оценка</span>
          </div>
        </div>
      </section>

      <section className="controls-section">
        <h3>Модель</h3>
        <p className="hint model-hint">LLM задаётся в <code>.env</code> (OPENROUTER_MODEL)</p>
      </section>

      <section className="controls-section">
        <AutonomyLevelControl
          jobId={jobId}
          autonomyLevel={normalizeAutonomyLevel(statePatch.autonomy_level)}
          disabled={settingsDisabled}
        />
      </section>

      <section className="controls-section">
        <BibliographyVerifierToggle
          jobId={jobId}
          enabled={statePatch.enable_bibliography_verifier !== false}
          disabled={settingsDisabled}
        />
      </section>

      <section className="controls-section">
        <StylePolisherToggle
          jobId={jobId}
          enabled={statePatch.enable_style_polisher !== false}
          disabled={settingsDisabled}
        />
      </section>

      <section className="controls-section">
        <RevisionLimitControl
          jobId={jobId}
          maxRevisions={maxRevisions}
          revisionNumber={statePatch.revision_number ?? 0}
          disabled={settingsDisabled}
        />
      </section>
      </div>
    </div>
  )
}
