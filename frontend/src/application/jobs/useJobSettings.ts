import { useCallback, useEffect, useState } from 'react'
import type { AutonomyLevel } from '@/domain/jobs/types'
import { normalizeAutonomyLevel } from '@/domain/jobs/autonomy'
import { jobFeaturesGateway } from '@/application/container'

export function useJobSettings(
  jobId: string,
  initial: {
    maxRevisions: number
    autonomyLevel?: AutonomyLevel
  },
) {
  const [maxRevisions, setMaxRevisions] = useState(initial.maxRevisions)
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>(
    initial.autonomyLevel ?? 'interactive',
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setMaxRevisions(initial.maxRevisions)
  }, [initial.maxRevisions])

  useEffect(() => {
    if (initial.autonomyLevel) setAutonomyLevel(initial.autonomyLevel)
  }, [initial.autonomyLevel])

  const saveMaxRevisions = useCallback(
    async (nextValue: number) => {
      if (nextValue === initial.maxRevisions) return
      setSaving(true)
      setError('')
      try {
        await jobFeaturesGateway.updateJobSettings(jobId, { max_revisions: nextValue })
        setMaxRevisions(nextValue)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка сохранения')
        setMaxRevisions(initial.maxRevisions)
      } finally {
        setSaving(false)
      }
    },
    [initial.maxRevisions, jobId],
  )

  const saveAutonomy = useCallback(
    async (nextLevel: AutonomyLevel) => {
      if (nextLevel === autonomyLevel) return
      setSaving(true)
      setError('')
      try {
        await jobFeaturesGateway.updateJobSettings(jobId, { autonomy_level: nextLevel })
        setAutonomyLevel(nextLevel)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка сохранения')
        setAutonomyLevel(normalizeAutonomyLevel(initial.autonomyLevel))
      } finally {
        setSaving(false)
      }
    },
    [autonomyLevel, initial.autonomyLevel, jobId],
  )

  return {
    maxRevisions,
    setMaxRevisions,
    saveMaxRevisions,
    autonomyLevel,
    saveAutonomy,
    saving,
    error,
    value: maxRevisions,
    setValue: setMaxRevisions,
    save: saveMaxRevisions,
  }
}
