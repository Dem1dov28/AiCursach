import { Suspense, lazy } from 'react'
import { WorkbenchLayout } from '@/layouts/WorkbenchLayout'
import { CanvasStatusBar } from '@/presentation/components/graph/CanvasStatusBar'
import {
  LANDING_WORKBENCH_DRAFT,
  LANDING_WORKBENCH_EDGES,
  LANDING_WORKBENCH_NODES,
  LANDING_WORKBENCH_ROSTER,
} from '@/domain/landing/landingWorkbenchMock'
import { AppIcon, RosterStatusIcon } from '@/presentation/icons'

const AgentFlowGraph = lazy(() =>
  import('@/presentation/components/graph/AgentFlowGraph').then((module) => ({
    default: module.AgentFlowGraph,
  })),
)

function PreviewLeftPanel() {
  return (
    <div className="panel project-controls-panel">
      <h2 className="panel-title">Проект</h2>
      <div className="panel-body">
        <div className="progress-track progress-track--compact">
          <div className="progress-fill" style={{ width: '42%' }} />
        </div>
        <p className="hint progress-hint">5 шагов агентов · 42%</p>

        <div className="field">
          <label htmlFor="landing-preview-topic">Тема работы</label>
          <input
            id="landing-preview-topic"
            type="text"
            readOnly
            value="Сравнительный анализ алгоритмов сортировки"
            className="project-topic-input"
          />
        </div>

        <div className="project-status project-status--running">
          <span className="project-status__dot" aria-hidden />
          <span className="project-status__label">Написание текста</span>
          <span className="stream-dot live">live</span>
        </div>

        <section className="controls-section">
          <h3>Команда агентов</h3>
          <ul className="agent-roster">
            {LANDING_WORKBENCH_ROSTER.map((agent) => (
              <li key={agent.id}>
                <span className={`agent-roster__item agent-roster__item--${agent.status}`}>
                  <span className="agent-roster__icon">
                    <RosterStatusIcon status={agent.status} />
                  </span>
                  <span className="agent-roster__name">{agent.label}</span>
                </span>
              </li>
            ))}
          </ul>
          <p className="hint">Клик по узлу на холсте → инспектор справа</p>
        </section>

        <section className="controls-section">
          <h3>Бюджет сессии</h3>
          <div className="metrics-grid metrics-grid--compact">
            <div className="metric-card">
              <span className="metric-value">24 180</span>
              <span className="metric-label">токенов</span>
            </div>
            <div className="metric-card">
              <span className="metric-value">$0.0842</span>
              <span className="metric-label">оценка</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

function PreviewCenterPanel() {
  const doneCount = LANDING_WORKBENCH_NODES.filter((n) => n.data.status === 'done').length

  return (
    <div className="panel canvas-panel">
      <CanvasStatusBar
        doneCount={doneCount}
        totalCount={LANDING_WORKBENCH_NODES.length}
        currentTask="Сейчас: Писатель — Глава 2 «Анализ алгоритмов»"
      />
      <Suspense fallback={<p className="hint flow-placeholder">Загрузка холста…</p>}>
        <AgentFlowGraph
          nodes={LANDING_WORKBENCH_NODES}
          edges={LANDING_WORKBENCH_EDGES}
          rerunEnabled={false}
        />
      </Suspense>
    </div>
  )
}

function PreviewRightPanel() {
  const [heading, ...rest] = LANDING_WORKBENCH_DRAFT.split('\n\n')
  const body = rest.join('\n\n')
  const codeStart = body.indexOf('def quicksort')
  const prose = codeStart >= 0 ? body.slice(0, codeStart).trim() : body
  const code = codeStart >= 0 ? body.slice(codeStart).trim() : ''

  return (
    <div className="panel document-inspector-panel">
      <div className="doc-inspector-tabs">
        <button type="button" className="active">
          <AppIcon name="file-text" size={15} />
          Документ
        </button>
        <button type="button">
          <AppIcon name="search" size={15} />
          Инспектор
        </button>
      </div>

      <div className="doc-inspector-body">
        <div className="workspace-tabs doc-subtabs">
          <button type="button" className="active">
            Текст
          </button>
          <button type="button">Изменения</button>
        </div>

        <div className="landing-preview-draft">
          <h3>{heading}</h3>
          <p>{prose}</p>
          {code && <pre>{code}</pre>}
        </div>
      </div>
    </div>
  )
}

export function ProductPreviewSection() {
  return (
    <section className="landing-section landing-product-preview" id="inside">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Интерфейс</p>
        <h2>Как это выглядит внутри</h2>
        <p className="landing-section__lead">
          Тот же workbench, что и в приложении: проект слева, граф агентов по центру,
          черновик справа.
        </p>
      </div>

      <div className="landing-workbench-preview" aria-label="Пример интерфейса AiCursach">
        <div className="workbench landing-workbench-preview__shell">
          <WorkbenchLayout
            left={<PreviewLeftPanel />}
            center={<PreviewCenterPanel />}
            right={<PreviewRightPanel />}
          />
        </div>
      </div>
    </section>
  )
}
