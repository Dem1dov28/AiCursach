import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import { AgentIcon } from '@/presentation/icons'
import type { JobStep } from '@/domain/jobs/types'

interface Props {
  steps: JobStep[]
  activeAgent: string | null
  selectedStepIndex: number | null
  onSelectStep: (index: number, agentId: string) => void
}

export function ExecutionTimeline({
  steps,
  activeAgent,
  selectedStepIndex,
  onSelectStep,
}: Props) {
  if (steps.length === 0) {
    return (
      <div className="execution-timeline execution-timeline--empty">
        <span className="hint">Шаги появятся, когда команда начнёт работу…</span>
      </div>
    )
  }

  return (
    <div className="execution-timeline">
      <div className="execution-timeline__head">
        <span className="execution-timeline__title">Хронология</span>
        <span className="execution-timeline__count">{steps.length} шагов</span>
      </div>
      <div className="execution-timeline__track">
        {steps.map((step, index) => {
          const isSelected = selectedStepIndex === index
          const isLive = activeAgent === step.agent && selectedStepIndex === null && index === steps.length - 1
          const label = AGENT_LABELS[step.agent] ?? step.agent

          return (
            <button
              key={step.step}
              type="button"
              className={`timeline-chip${isSelected ? ' timeline-chip--active' : ''}${isLive ? ' timeline-chip--live' : ''}`}
              title={step.detail ? `${step.message}\n${step.detail}` : step.message}
              onClick={() => onSelectStep(index, step.agent)}
            >
              <span className="timeline-chip__row">
                <span className="timeline-chip__icon">
                  <AgentIcon agentId={step.agent} size={14} />
                </span>
                <span className="timeline-chip__agent">{label}</span>
                <span className="timeline-chip__step">#{step.step}</span>
              </span>
              <span className="timeline-chip__message">{step.message}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
