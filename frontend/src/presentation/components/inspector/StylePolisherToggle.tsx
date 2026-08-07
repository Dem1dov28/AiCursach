import { useJobFeatureToggle } from '@/application/jobs/useJobFeatureToggle'

interface Props {
  jobId: string
  enabled: boolean
  disabled?: boolean
}

export function StylePolisherToggle({ jobId, enabled, disabled = false }: Props) {
  const { value: checked, saving, error, save } = useJobFeatureToggle(
    jobId,
    'enable_style_polisher',
    enabled,
    disabled,
  )

  return (
    <div className="style-polisher-toggle">
      <label className="style-polisher-toggle__label">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled || saving}
          onChange={(event) => void save(event.target.checked)}
        />
        <span>Полировка стиля (de-AI)</span>
      </label>
      <p className="hint">
        Агент StylePolisher убирает AI-клише из текста. Отключите, если нужен «сырой» черновик Writer.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
    </div>
  )
}
