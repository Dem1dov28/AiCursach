import { useEffect } from 'react'
import { useJobSettings } from '@/application/jobs/useJobSettings'

interface Props {
  jobId: string
  maxRevisions: number
  revisionNumber: number
  disabled?: boolean
}

export function RevisionLimitControl({
  jobId,
  maxRevisions,
  revisionNumber,
  disabled = false,
}: Props) {
  const { value, setValue, saving, error, save } = useJobSettings(jobId, { maxRevisions })

  useEffect(() => {
    setValue(maxRevisions)
  }, [maxRevisions, setValue])

  return (
    <div className="revision-limit">
      <label className="revision-limit__label" htmlFor="max_revisions">
        Лимит итераций Writer ↔ Reviewer
      </label>
      <div className="revision-limit__row">
        <input
          id="max_revisions"
          type="range"
          min={1}
          max={10}
          value={value}
          disabled={disabled || saving}
          onChange={(event) => setValue(Number(event.target.value))}
          onMouseUp={() => save(value)}
          onTouchEnd={() => save(value)}
        />
        <span className="revision-limit__value">
          {revisionNumber}/{value}
        </span>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <p className="hint">Текущий прогресс: {revisionNumber} из {value} допустимых.</p>
    </div>
  )
}
