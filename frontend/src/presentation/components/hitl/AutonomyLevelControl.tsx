import type { AutonomyLevel } from '@/domain/jobs/types'
import { useJobSettings } from '@/application/jobs/useJobSettings'

const LEVELS: { id: AutonomyLevel; title: string; hint: string }[] = [
  {
    id: 'full_auto',
    title: 'Авто',
    hint: 'Без уточняющих вопросов — агенты действуют сами',
  },
  {
    id: 'interactive',
    title: 'С уточнениями',
    hint: 'Агенты могут сомневаться и задать вопрос, если в материалах пробел или неоднозначность',
  },
]

interface Props {
  jobId: string
  autonomyLevel: AutonomyLevel
  disabled?: boolean
}

export function AutonomyLevelControl({ jobId, autonomyLevel, disabled = false }: Props) {
  const { autonomyLevel: level, saveAutonomy, saving, error } = useJobSettings(jobId, {
    maxRevisions: 3,
    autonomyLevel,
  })

  return (
    <div className="autonomy-control">
      <label className="autonomy-control__label">Режим работы агентов</label>
      <div className="autonomy-control__levels">
        {LEVELS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`autonomy-chip${level === item.id ? ' autonomy-chip--active' : ''}`}
            disabled={disabled || saving}
            onClick={() => void saveAutonomy(item.id)}
          >
            <strong>{item.title}</strong>
            <span className="hint">{item.hint}</span>
          </button>
        ))}
      </div>
      {error && <div className="alert alert-error">{error}</div>}
    </div>
  )
}
