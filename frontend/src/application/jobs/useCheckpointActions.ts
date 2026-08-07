import { useCallback, useState } from 'react'
import type { JobCheckpoint, JobStatePatch } from '@/domain/jobs/types'
import { jobFeaturesGateway } from '@/application/container'

export function useCheckpointActions(jobId: string) {
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const previewCheckpoint = useCallback(
    async (checkpointId: string): Promise<JobStatePatch> => {
      setBusyId(checkpointId)
      setError('')
      try {
        const data = await jobFeaturesGateway.fetchCheckpointState(jobId, checkpointId)
        return data.state
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка загрузки'
        setError(message)
        throw err
      } finally {
        setBusyId(null)
      }
    },
    [jobId],
  )

  const restoreCheckpointState = useCallback(
    async (checkpointId: string): Promise<JobStatePatch | undefined> => {
      setBusyId(checkpointId)
      setError('')
      try {
        const data = await jobFeaturesGateway.restoreCheckpoint(jobId, checkpointId)
        return data.patch
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка восстановления'
        setError(message)
        throw err
      } finally {
        setBusyId(null)
      }
    },
    [jobId],
  )

  const isBusy = useCallback(
    (checkpoint: JobCheckpoint) => busyId === checkpoint.checkpoint_id,
    [busyId],
  )

  return {
    busyId,
    error,
    isBusy,
    previewCheckpoint,
    restoreCheckpointState,
    clearError: () => setError(''),
  }
}
