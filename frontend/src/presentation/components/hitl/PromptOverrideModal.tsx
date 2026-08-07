import type { FormEvent } from 'react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'

interface Props {
  nodeId: string
  open: boolean
  submitting?: boolean
  onCancel: () => void
  onConfirm: (payload: { promptOverride: string; structureOutline: string }) => void
}

export function PromptOverrideModal({
  nodeId,
  open,
  submitting = false,
  onCancel,
  onConfirm,
}: Props) {
  if (!open) return null

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    onConfirm({
      promptOverride: String(form.get('prompt_override') ?? ''),
      structureOutline: String(form.get('structure_outline') ?? ''),
    })
  }

  const label = AGENT_LABELS[nodeId] ?? nodeId

  return (
    <div className="modal-overlay" role="presentation" onClick={onCancel}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rerun-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 id="rerun-modal-title">Rerun: {label}</h3>
        <p className="hint">
          Workflow перезапустится с узла «{nodeId}». Можно добавить инструкции для агента.
        </p>
        <form onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="prompt_override">
            Доп. инструкции (prompt override)
          </label>
          <textarea
            id="prompt_override"
            name="prompt_override"
            rows={4}
            placeholder="Например: сократи теорию, добавь больше примеров…"
          />

          <label className="field-label" htmlFor="structure_outline">
            План / structure outline (опционально)
          </label>
          <textarea
            id="structure_outline"
            name="structure_outline"
            rows={3}
            placeholder="Оставьте пустым, чтобы не менять план"
          />

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" disabled={submitting} onClick={onCancel}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Запуск…' : 'Перезапустить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
