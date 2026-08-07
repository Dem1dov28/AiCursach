import { useEffect, useMemo, useState } from 'react'
import { useJobHitl } from '@/application/jobs/useJobHitl'

interface Props {
  jobId: string
  structureOutline: string
  onApproved: () => void
  onPlanSaved?: (outline: string) => void
}

export function PlanApprovalBanner({ jobId, structureOutline, onApproved, onPlanSaved }: Props) {
  const { loading, error, savePlan, approvePlan } = useJobHitl(jobId)
  const [plan, setPlan] = useState(structureOutline)
  const [savedAt, setSavedAt] = useState<number | null>(null)

  const preview = useMemo(() => plan.trim() || structureOutline, [plan, structureOutline])
  const dirty = preview !== structureOutline.trim()

  useEffect(() => {
    setPlan(structureOutline)
  }, [structureOutline])

  const handleSave = async () => {
    try {
      await savePlan(preview)
      setSavedAt(Date.now())
      onPlanSaved?.(preview)
    } catch {
      /* error in hook */
    }
  }

  const handleApprove = async () => {
    try {
      if (dirty) {
        await savePlan(preview)
      }
      await approvePlan(preview)
      onApproved()
    } catch {
      /* error in hook */
    }
  }

  return (
    <section className="plan-approval" id="plan-approval">
      <h3>Human-in-the-Loop: утверждение плана</h3>
      <p className="hint">
        Архитектор и Исследователь завершили работу. Отредактируйте план, сохраните черновик в
        workflow и нажмите «Утвердить», чтобы запустить Писателя.
      </p>
      <textarea
        value={plan}
        onChange={(event) => setPlan(event.target.value)}
        rows={8}
        placeholder="Структура глав…"
      />
      {error && <div className="alert alert-error">{error}</div>}
      <div className="plan-approval__actions">
        <button
          type="button"
          className="btn btn-secondary"
          disabled={loading !== null || !preview.trim()}
          onClick={handleSave}
        >
          {loading === 'save' ? 'Сохранение…' : dirty ? 'Сохранить план' : 'План сохранён'}
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={loading !== null || !preview.trim()}
          onClick={handleApprove}
        >
          {loading === 'approve' ? 'Запуск…' : 'Утвердить план и продолжить'}
        </button>
      </div>
      {savedAt && !dirty && (
        <p className="hint plan-approval__saved">
          Черновик записан в workflow · {new Date(savedAt).toLocaleTimeString()}
        </p>
      )}
    </section>
  )
}
