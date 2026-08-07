import { useState } from 'react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { TaskBreakdownItem, TeamProposal } from '@/domain/jobs/types'
import { AppIcon } from '@/presentation/icons'
import { useJobHitl } from '@/application/jobs/useJobHitl'

interface Props {
  jobId: string
  team: TeamProposal
  onApproved: () => void
}

const KIND_LABELS: Record<string, string> = {
  lab: 'Лабораторная',
  coursework: 'Курсовая',
  diploma: 'Диплом',
  essay: 'Реферат',
  report: 'Отчёт',
  unknown: 'Не определено',
}

const DISCIPLINE_LABELS: Record<string, string> = {
  programming: 'Программирование / IT',
  economics: 'Экономика',
  humanities: 'Гуманитарные',
  engineering: 'Инженерия',
  management: 'Менеджмент',
  general: 'Общая',
}

export function TeamApprovalCard({ jobId, team, onApproved }: Props) {
  const { loading, error, approveTeam } = useJobHitl(jobId)
  const [submitted, setSubmitted] = useState(false)

  const handleApprove = async () => {
    try {
      await approveTeam(team.pipeline)
      setSubmitted(true)
      onApproved()
    } catch {
      /* error in hook */
    }
  }

  if (submitted) {
    return (
      <section className="team-approval-card team-approval-card--sent">
        <p className="hint">Команда утверждена — агенты приступают к работе…</p>
      </section>
    )
  }

  const kind = team.detected_work_kind ? KIND_LABELS[team.detected_work_kind] ?? team.detected_work_kind : null
  const discipline = team.discipline ? DISCIPLINE_LABELS[team.discipline] ?? team.discipline : null
  const structureSourceLabel: Record<string, string> = {
    example: 'из примера курсовой',
    methodical: 'из методички / ГОСТ',
    discipline_fallback: 'по шаблону дисциплины',
    assignment: 'из задания',
  }
  const structureSource = team.structure_source
    ? structureSourceLabel[team.structure_source] ?? team.structure_source
    : null

  return (
    <section className="team-approval-card" id="team-approval">
      <div className="team-approval-card__head">
        <span className="team-approval-card__badge">
          <AppIcon name="hexagon" size={18} />
        </span>
        <div>
          <h3>Команда агентов под задачу</h3>
          <p className="hint">
            Planner разобрал задание, пример и ГОСТ/методичку. Проверьте план и команду.
          </p>
        </div>
      </div>

      {(kind || discipline || structureSource) && (
        <dl className="team-profile-tags">
          {kind && (
            <div>
              <dt>Тип работы</dt>
              <dd>{kind}</dd>
            </div>
          )}
          {discipline && (
            <div>
              <dt>Дисциплина</dt>
              <dd>{discipline}</dd>
            </div>
          )}
          {structureSource && (
            <div>
              <dt>Источник структуры</dt>
              <dd>{structureSource}</dd>
            </div>
          )}
        </dl>
      )}

      {team.work_brief_summary && (
        <p className="team-approval-card__rationale">
          <strong>По материалам:</strong> {team.work_brief_summary}
        </p>
      )}

      {team.structure_outline && (
        <details className="team-approval-card__outline">
          <summary>План работы</summary>
          <pre className="team-approval-card__outline-pre">{team.structure_outline}</pre>
        </details>
      )}

      {team.rationale && <p className="team-approval-card__rationale">{team.rationale}</p>}

      <ol className="team-task-list">
        {team.task_breakdown.map((item: TaskBreakdownItem, index) => (
          <li key={`${item.agent}-${index}`}>
            <div className="team-task-list__top">
              <strong>{item.task}</strong>
              <span className="team-task-list__agent">
                {AGENT_LABELS[item.agent] ?? item.agent}
              </span>
            </div>
            {item.deliverable && (
              <span className="team-task-list__deliverable">→ {item.deliverable}</span>
            )}
          </li>
        ))}
      </ol>

      <div className="team-pipeline-preview">
        {team.pipeline
          .filter((id) => id !== 'supervisor')
          .map((id) => AGENT_LABELS[id] ?? id)
          .join(' → ')}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <button
        type="button"
        className="btn btn-primary btn-with-icon"
        disabled={loading === 'team'}
        onClick={() => void handleApprove()}
      >
        {loading === 'team' ? 'Запуск…' : (
          <>
            Запустить команду
            <AppIcon name="play" size={16} />
          </>
        )}
      </button>
    </section>
  )
}
