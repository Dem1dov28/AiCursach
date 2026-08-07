import { useJobCheckpoints } from '@/application/jobs/useJobCheckpoints'
import { useCheckpointActions } from '@/application/jobs/useCheckpointActions'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { JobCheckpoint, JobStatePatch, JobStatus, StreamEvent } from '@/domain/jobs/types'

interface Props {
  jobId: string
  jobStatus?: JobStatus
  selectedCheckpointId: string | null
  onPreview: (checkpoint: JobCheckpoint, patch: JobStatePatch) => void
  onClearPreview: () => void
  applyEvent: (event: StreamEvent) => void
}

function formatCheckpointLabel(item: JobCheckpoint): string {
  const parts: string[] = [`Версия ${item.index + 1}`]
  if (item.topic) parts.push(`«${item.topic.slice(0, 40)}»`)
  else if (item.structure_outline_preview) parts.push(item.structure_outline_preview.slice(0, 50))
  if (item.has_content_draft) parts.push('есть черновик')
  if (item.awaiting_plan_approval) parts.push('ожидание плана')
  return parts.join(' · ')
}

export function CheckpointPanel({
  jobId,
  jobStatus,
  selectedCheckpointId,
  onPreview,
  onClearPreview,
  applyEvent,
}: Props) {
  const { checkpoints, loading, error, reload } = useJobCheckpoints(jobId)
  const { error: actionError, isBusy, previewCheckpoint, restoreCheckpointState } =
    useCheckpointActions(jobId)

  const handlePreview = async (item: JobCheckpoint) => {
    if (!item.checkpoint_id) return
    try {
      const patch = await previewCheckpoint(item.checkpoint_id)
      onPreview(item, patch)
    } catch {
      /* error surfaced via actionError */
    }
  }

  const handleRestore = async (item: JobCheckpoint) => {
    if (!item.checkpoint_id) return
    const ok = window.confirm(
      `Вернуть проект к версии ${item.index + 1}? Текущий прогресс будет заменён.`,
    )
    if (!ok) return

    try {
      const patch = await restoreCheckpointState(item.checkpoint_id)
      if (patch) {
        applyEvent({ type: 'state_patch', patch })
      }
      applyEvent({ type: 'status', status: 'paused' })
      onClearPreview()
      reload()
    } catch {
      /* error surfaced via actionError */
    }
  }

  const displayError = actionError || error

  if (loading) return <p className="hint">Загрузка истории…</p>
  if (displayError && checkpoints.length === 0) {
    return <div className="alert alert-error">{displayError}</div>
  }
  if (checkpoints.length === 0) {
    return (
      <p className="hint">
        Пока нет сохранённых версий. Они появятся по мере работы агентов.
      </p>
    )
  }

  const canRestore = jobStatus !== 'running' && jobStatus !== 'queued'

  return (
    <div className="checkpoint-list">
      <p className="hint checkpoint-list__hint">
        «Просмотр» открывает документ на тот момент. «Вернуть» откатывает весь workflow.
      </p>
      {displayError && <div className="alert alert-error">{displayError}</div>}
      <ul>
        {checkpoints.map((item) => {
          const selected = selectedCheckpointId === item.checkpoint_id
          const busy = isBusy(item)
          const nextLabel = item.next_step
            ? AGENT_LABELS[item.next_step] ?? item.next_step
            : null
          return (
            <li
              key={`${item.index}-${item.checkpoint_id}`}
              className={`checkpoint-item${selected ? ' checkpoint-item--selected' : ''}`}
            >
              <div className="checkpoint-item__head">
                <strong>{formatCheckpointLabel(item)}</strong>
              </div>
              <div className="checkpoint-item__meta">
                {nextLabel && <span>Далее: {nextLabel}</span>}
                {item.revision_number > 0 && <span>правка {item.revision_number}</span>}
              </div>
              <div className="checkpoint-item__actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={busy || !item.checkpoint_id}
                  onClick={() => void handlePreview(item)}
                >
                  {busy ? '…' : 'Просмотр'}
                </button>
                {canRestore && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    disabled={busy || !item.checkpoint_id}
                    onClick={() => void handleRestore(item)}
                  >
                    Вернуть
                  </button>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
