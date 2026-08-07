import type { RecentJobEntry } from '@/domain/jobs/recentJob'
import { JobStatusBadge } from '@/presentation/icons'

const WORK_TYPE_LABELS: Record<RecentJobEntry['workType'], string> = {
  auto: 'Учебная работа',
  lab: 'Лабораторная',
  coursework: 'Курсовая',
}

interface Props {
  jobs: RecentJobEntry[]
  loading?: boolean
  busyId?: string | null
  onOpen: (jobId: string) => void
  onCreate: () => void
  onPause: (jobId: string) => void
  onContinue: (job: RecentJobEntry) => void
  onDelete: (jobId: string) => void
}

function formatRelative(iso: string): string {
  const date = new Date(iso)
  const diffMs = Date.now() - date.getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'только что'
  if (mins < 60) return `${mins} мин назад`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} ч назад`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'вчера'
  return `${days} дн назад`
}

function primaryActionLabel(status: RecentJobEntry['status']): string {
  if (status === 'completed') return 'Открыть'
  if (status === 'paused') return 'Продолжить'
  if (status === 'failed') return 'Повторить'
  return 'Открыть'
}

export function RecentProjectsTable({
  jobs,
  loading,
  busyId,
  onOpen,
  onCreate,
  onPause,
  onContinue,
  onDelete,
}: Props) {
  const handlePrimary = (job: RecentJobEntry) => {
    if (job.status === 'paused' || job.status === 'failed') {
      onContinue(job)
      return
    }
    onOpen(job.id)
  }

  const handleDelete = (job: RecentJobEntry) => {
    const label = job.projectName || job.id
    if (!window.confirm(`Удалить проект «${label}»? Это действие необратимо.`)) {
      return
    }
    onDelete(job.id)
  }

  return (
    <section className="dashboard-block">
      <div className="dashboard-block__head">
        <h2>Мои проекты</h2>
      </div>

      {loading && jobs.length === 0 && <p className="hint">Загрузка проектов…</p>}

      {jobs.length === 0 ? (
        <div className="dashboard-empty">
          <p>Пока нет проектов. Создайте первый — система сама подберёт команду агентов.</p>
          <button type="button" className="btn btn-primary" onClick={onCreate}>
            Создать первый проект
          </button>
        </div>
      ) : (
        <div className="projects-table-wrap">
          <table className="projects-table">
            <thead>
              <tr>
                <th>Название</th>
                <th>Статус</th>
                <th>Прогресс</th>
                <th>Затраты ($)</th>
                <th>Изменение</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const isBusy = busyId === job.id
                return (
                  <tr key={job.id}>
                    <td>
                      <strong>{job.projectName || job.id}</strong>
                      <div className="hint">{WORK_TYPE_LABELS[job.workType]}</div>
                    </td>
                    <td>
                      <JobStatusBadge status={job.status} progress={job.progress} />
                    </td>
                    <td>
                      <div className="progress-bar" aria-hidden>
                        <div className="progress-fill" style={{ width: `${job.progress}%` }} />
                      </div>
                      <span className="hint">{job.progress}%</span>
                    </td>
                    <td>{job.estimatedCostUsd > 0 ? job.estimatedCostUsd.toFixed(4) : '—'}</td>
                    <td className="hint">{formatRelative(job.lastOpenedAt)}</td>
                    <td>
                      <div className="projects-table__actions">
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          disabled={isBusy}
                          onClick={() => handlePrimary(job)}
                        >
                          {primaryActionLabel(job.status)}
                        </button>
                        {job.status === 'running' && (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            disabled={isBusy}
                            onClick={() => onPause(job.id)}
                          >
                            Пауза
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm projects-table__delete"
                          disabled={isBusy}
                          onClick={() => handleDelete(job)}
                        >
                          Удалить
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
