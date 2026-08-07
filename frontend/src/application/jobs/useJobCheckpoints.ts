import { useCallback, useEffect, useState } from 'react'
import type { JobCheckpoint } from '@/domain/jobs/types'
import { jobFeaturesGateway } from '@/application/container'

export function useJobCheckpoints(jobId: string) {
  const [checkpoints, setCheckpoints] = useState<JobCheckpoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1)
  }, [])

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    setLoading(true)
    setError('')

    jobFeaturesGateway.fetchCheckpoints(jobId)
      .then((items) => {
        if (!cancelled) setCheckpoints(items)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки checkpoints')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [jobId, reloadToken])

  return { checkpoints, loading, error, reload }
}
