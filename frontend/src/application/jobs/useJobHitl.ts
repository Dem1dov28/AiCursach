import { useCallback, useState } from 'react'
import { jobGateway } from '@/application/container'

type HitlAction = 'save' | 'approve' | 'clarification' | 'team'

export function useJobHitl(jobId: string) {
  const [loading, setLoading] = useState<HitlAction | null>(null)
  const [error, setError] = useState('')

  const clearError = useCallback(() => setError(''), [])

  const savePlan = useCallback(
    async (structureOutline: string, topic = '') => {
      setLoading('save')
      setError('')
      try {
        await jobGateway.saveJobPlan(jobId, structureOutline, topic)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка сохранения'
        setError(message)
        throw err
      } finally {
        setLoading(null)
      }
    },
    [jobId],
  )

  const approvePlan = useCallback(
    async (structureOutline: string) => {
      setLoading('approve')
      setError('')
      try {
        await jobGateway.resumeJob(jobId, structureOutline)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка возобновления'
        setError(message)
        throw err
      } finally {
        setLoading(null)
      }
    },
    [jobId],
  )

  const submitClarification = useCallback(
    async (selectedOption: string, customText: string) => {
      setLoading('clarification')
      setError('')
      try {
        await jobGateway.submitClarificationAnswer(jobId, selectedOption, customText)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка отправки'
        setError(message)
        throw err
      } finally {
        setLoading(null)
      }
    },
    [jobId],
  )

  const approveTeam = useCallback(
    async (pipeline: string[]) => {
      setLoading('team')
      setError('')
      try {
        await jobGateway.approveTeam(jobId, pipeline)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Ошибка утверждения команды'
        setError(message)
        throw err
      } finally {
        setLoading(null)
      }
    },
    [jobId],
  )

  return {
    loading,
    error,
    clearError,
    savePlan,
    approvePlan,
    submitClarification,
    approveTeam,
  }
}
