import { useCallback, useState } from 'react'
import { continuePausedJob } from '@/application/jobs/continuePausedJob'
import { removeRecentJob } from '@/application/jobs/useRecentJobs'
import type { RecentJobEntry } from '@/domain/jobs/recentJob'
import { jobGateway } from '@/application/container'

export function useDashboardJobActions(onReload: () => void) {
  const [busyId, setBusyId] = useState<string | null>(null)
  const [action, setAction] = useState<string | null>(null)
  const [error, setError] = useState('')

  const run = useCallback(
    async (jobId: string, kind: string, fn: () => Promise<void>) => {
      setBusyId(jobId)
      setAction(kind)
      setError('')
      try {
        await fn()
        onReload()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка операции')
        throw err
      } finally {
        setBusyId(null)
        setAction(null)
      }
    },
    [onReload],
  )

  const pause = useCallback(
    (jobId: string) => run(jobId, 'pause', () => jobGateway.pauseJob(jobId).then(() => undefined)),
    [run],
  )

  const remove = useCallback(
    (jobId: string) =>
      run(jobId, 'delete', async () => {
        await jobGateway.deleteJob(jobId)
        removeRecentJob(jobId)
      }),
    [run],
  )

  const continueJob = useCallback(
    async (job: RecentJobEntry, onOpen: (id: string) => void) => {
      if (job.status === 'failed') {
        await run(job.id, 'retry', () => jobGateway.retryJob(job.id).then(() => undefined))
        return
      }
      if (job.status !== 'paused') {
        onOpen(job.id)
        return
      }
      setBusyId(job.id)
      setAction('continue')
      setError('')
      try {
        const result = await continuePausedJob(job.id)
        if (result === 'needs_workbench') {
          onOpen(job.id)
        } else {
          onReload()
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось продолжить')
        throw err
      } finally {
        setBusyId(null)
        setAction(null)
      }
    },
    [onReload, run],
  )

  return { busyId, action, error, pause, remove, continueJob, clearError: () => setError('') }
}
