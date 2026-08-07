import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import { shouldShowStepDetail } from '@/domain/inspector/formatStepDetail'
import type { JobStatePatch, JobStep } from '@/domain/jobs/types'
import { RERUN_NODE_IDS } from '@/domain/jobs/context'

interface Props {
  selectedNodeId: string | null
  inspectStep: JobStep | null | undefined
  statePatch: JobStatePatch
  rerunEnabled: boolean
  onRequestRerun: (nodeId: string) => void
}

export function AgentInspectorSection({
  selectedNodeId,
  inspectStep,
  statePatch,
  rerunEnabled,
  onRequestRerun,
}: Props) {
  const agentId = selectedNodeId ?? inspectStep?.agent ?? null
  const agentLabel = agentId ? (AGENT_LABELS[agentId] ?? agentId) : null

  if (!agentId && !inspectStep) {
    return (
      <p className="hint inspector-empty-hint">
        Нажмите на агента на холсте или точку в хронологии — здесь появится, что он сделал и какие
        данные использовал.
      </p>
    )
  }

  const showDetail =
    inspectStep && shouldShowStepDetail(inspectStep.detail, inspectStep.message)

  const canRerun =
    selectedNodeId &&
    rerunEnabled &&
    RERUN_NODE_IDS.includes(selectedNodeId as (typeof RERUN_NODE_IDS)[number])

  return (
    <div className="node-inspector">
      <p className="node-inspector__meta">
        {agentLabel}
        {inspectStep ? ` · шаг ${inspectStep.step}` : ''}
      </p>

      {inspectStep && (
        <>
          <p className="node-inspector__message">{inspectStep.message}</p>
          {showDetail && (
            <div className="node-inspector__extra">
              <span className="node-inspector__extra-label">Подробнее</span>
              <p className="node-inspector__detail-text">{inspectStep.detail}</p>
            </div>
          )}
        </>
      )}

      {(agentId === 'writer' || agentId === 'analyzer') && statePatch.structure_outline && (
        <div className="node-inspector__block">
          <h4>План работы</h4>
          <pre className="node-inspector__detail">{statePatch.structure_outline}</pre>
        </div>
      )}

      {agentId === 'critiquer' && statePatch.critique_notes && (
        <div className="node-inspector__block">
          <h4>Замечания редактора</h4>
          <pre className="node-inspector__detail">{statePatch.critique_notes}</pre>
        </div>
      )}

      {agentId === 'writer' && (statePatch.citation_issues?.length ?? 0) > 0 && (
        <div className="node-inspector__block">
          <h4>Ссылки и источники</h4>
          <ul className="inspector-issues-list">
            {statePatch.citation_issues!.slice(0, 5).map((issue) => (
              <li key={issue.citation}>{issue.reason}</li>
            ))}
          </ul>
        </div>
      )}

      {agentId === 'bibliography_verifier' && (statePatch.citation_issues?.length ?? 0) > 0 && (
        <div className="node-inspector__block">
          <h4>Остаточные замечания</h4>
          <ul className="inspector-issues-list">
            {statePatch.citation_issues!.map((issue) => (
              <li key={`${issue.citation}-${issue.reason}`}>
                <strong>{issue.citation}</strong> — {issue.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(agentId === 'writer' || agentId === 'style_polisher') &&
        (statePatch.style_issues?.length ?? 0) > 0 && (
        <div className="node-inspector__block">
          <h4>Стиль текста</h4>
          <ul className="inspector-issues-list">
            {statePatch.style_issues!.slice(0, 5).map((issue) => (
              <li key={issue.phrase}>
                «{issue.phrase}» — {issue.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {canRerun && selectedNodeId && (
        <button
          type="button"
          className="btn btn-secondary node-inspector__rerun"
          onClick={() => onRequestRerun(selectedNodeId)}
        >
          Запустить «{AGENT_LABELS[selectedNodeId] ?? selectedNodeId}» заново
        </button>
      )}
    </div>
  )
}
