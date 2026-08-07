import { useJobFeatureToggle } from '@/application/jobs/useJobFeatureToggle'

interface Props {
  jobId: string
  enabled: boolean
  disabled?: boolean
}

export function BibliographyVerifierToggle({ jobId, enabled, disabled = false }: Props) {
  const { value: checked, saving, error, save } = useJobFeatureToggle(
    jobId,
    'enable_bibliography_verifier',
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
        <span>Проверка библиографии (DOI)</span>
      </label>
      <p className="hint">
        Агент Bibliography проверяет список источников и ссылки [N]. Отключите для лаб без списка
        литературы.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
    </div>
  )
}
