import { useState } from 'react'
import { AgentIcon, AppIcon } from '@/presentation/icons'
import { useJobHitl } from '@/application/jobs/useJobHitl'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { ClarificationRequest } from '@/domain/jobs/types'

interface Props {
  jobId: string
  clarification: ClarificationRequest
  onAnswered: () => void
}

export function AgentClarificationCard({ jobId, clarification, onAnswered }: Props) {
  const { loading, error, submitClarification } = useJobHitl(jobId)
  const [selected, setSelected] = useState('')
  const [custom, setCustom] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [localError, setLocalError] = useState('')

  const agentLabel = AGENT_LABELS[clarification.agent] ?? clarification.agent
  const confidence =
    clarification.confidence != null ? `${Math.round(clarification.confidence * 100)}%` : '—'

  const handleSubmit = async () => {
    const choice = custom.trim() || selected
    if (!choice) {
      setLocalError('Выберите вариант или введите свой ответ')
      return
    }
    setLocalError('')
    try {
      await submitClarification(selected, custom.trim())
      setSubmitted(true)
      onAnswered()
    } catch {
      /* error in hook */
    }
  }

  const displayError = localError || error

  if (submitted) {
    return (
      <section className="clarification-card clarification-card--sent">
        <p className="hint">Ответ отправлен — workflow продолжается…</p>
      </section>
    )
  }

  return (
    <section className="clarification-card" id="agent-clarification">
      <div className="clarification-card__head">
        <span className="clarification-card__badge">?</span>
        <div>
          <h3>Агент просит уточнения</h3>
          <p className="hint clarification-card__meta">
            <AgentIcon agentId={clarification.agent} size={14} />
            {agentLabel} · confidence {confidence}
          </p>
        </div>
      </div>

      <p className="clarification-card__question">{clarification.question}</p>

      <div className="clarification-card__options">
        {clarification.options.map((option, index) => (
          <label key={option} className="clarification-option">
            <input
              type="radio"
              name="clarification-option"
              checked={selected === option}
              onChange={() => setSelected(option)}
            />
            <span>
              <strong>Вариант {String.fromCharCode(65 + index)}:</strong> {option}
            </span>
          </label>
        ))}
        <label className="clarification-option clarification-option--custom">
          <input
            type="radio"
            name="clarification-option"
            checked={Boolean(custom.trim()) && !selected}
            onChange={() => setSelected('')}
          />
          <span>
            <strong>Свой вариант</strong>
          </span>
          <textarea
            value={custom}
            onChange={(event) => setCustom(event.target.value)}
            rows={3}
            placeholder="Опишите директиву для агента…"
          />
        </label>
      </div>

      {displayError && <div className="alert alert-error">{displayError}</div>}

      <button
        type="button"
        className="btn btn-primary btn-with-icon"
        disabled={loading === 'clarification' || submitted}
        onClick={handleSubmit}
      >
        {loading === 'clarification' ? 'Отправка…' : (
          <>
            Отправить ответ и продолжить
            <AppIcon name="play" size={16} />
          </>
        )}
      </button>
    </section>
  )
}
