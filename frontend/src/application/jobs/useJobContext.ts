import { useEffect, useState } from 'react'
import type { JobContext } from '@/domain/jobs/context'
import { jobGateway } from '@/application/container'

export function useJobContext(jobId: string | null) {
  const [context, setContext] = useState<JobContext | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    setLoading(true)
    setError('')
    jobGateway.fetchJobContext(jobId)
      .then((data: JobContext) => {
        if (!cancelled) setContext(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки контекста')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [jobId])

  return { context, loading, error }
}
