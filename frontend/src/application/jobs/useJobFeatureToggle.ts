import { useCallback, useEffect, useState } from 'react'
import { jobFeaturesGateway } from '@/application/container'
import type { JobSettingsUpdate } from '@/application/ports/jobGateway'

type SettingsPatch = JobSettingsUpdate

export function useJobFeatureToggle<K extends keyof SettingsPatch>(
  jobId: string,
  settingKey: K,
  initialValue: NonNullable<SettingsPatch[K]>,
  disabled = false,
) {
  const [value, setValue] = useState(initialValue)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setValue(initialValue)
  }, [initialValue])

  const save = useCallback(
    async (next: NonNullable<SettingsPatch[K]>) => {
      if (next === value || disabled) return
      setValue(next)
      setSaving(true)
      setError('')
      try {
        await jobFeaturesGateway.updateJobSettings(jobId, { [settingKey]: next } as SettingsPatch)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка сохранения')
        setValue(initialValue)
      } finally {
        setSaving(false)
      }
    },
    [disabled, initialValue, jobId, settingKey, value],
  )

  return { value, saving, error, save }
}
