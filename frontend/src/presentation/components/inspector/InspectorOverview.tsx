import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { Job, JobStatePatch, JobStep } from '@/domain/jobs/types'

const STATUS_LABELS: Record<string, string> = {
  queued: 'В очереди',
  running: 'Выполняется',
  paused: 'Ожидает вашего действия',
  completed: 'Завершена',
  failed: 'Ошибка',
}

interface Props {
  job: Job | null
  statePatch: JobStatePatch
  activeAgent: string | null
  steps: JobStep[]
}

export function InspectorOverview({ job, statePatch, activeAgent, steps }: Props) {
  const status = job?.status ?? 'queued'
  const lastStep = steps.length > 0 ? steps[steps.length - 1] : null
  const subTask = statePatch.current_sub_task?.trim()

  return (
    <div className="inspector-overview">
      <div className="inspector-overview__row">
        <span className="inspector-overview__label">Статус</span>
        <span className={`inspector-overview__value inspector-overview__value--${status}`}>
          {STATUS_LABELS[status] ?? status}
        </span>
      </div>
      {statePatch.topic && (
        <div className="inspector-overview__row">
          <span className="inspector-overview__label">Тема</span>
          <span className="inspector-overview__value">{statePatch.topic}</span>
        </div>
      )}
      {subTask && (
        <div className="inspector-overview__row">
          <span className="inspector-overview__label">Сейчас</span>
          <span className="inspector-overview__value">{subTask}</span>
        </div>
      )}
      {activeAgent && status === 'running' && (
        <div className="inspector-overview__row">
          <span className="inspector-overview__label">Активный агент</span>
          <span className="inspector-overview__value">
            {AGENT_LABELS[activeAgent] ?? activeAgent}
          </span>
        </div>
      )}
      {lastStep && !activeAgent && (
        <div className="inspector-overview__row">
          <span className="inspector-overview__label">Последний шаг</span>
          <span className="inspector-overview__value">
            {AGENT_LABELS[lastStep.agent] ?? lastStep.agent}: {lastStep.message}
          </span>
        </div>
      )}
      {statePatch.revision_number != null && statePatch.revision_number > 0 && (
        <div className="inspector-overview__row">
          <span className="inspector-overview__label">Правки</span>
          <span className="inspector-overview__value">
            раунд {statePatch.revision_number} из {statePatch.max_revisions ?? 3}
          </span>
        </div>
      )}
    </div>
  )
}
