import { useEffect, useState } from 'react'
import type { DraftDiff, DraftSnapshot } from '@/domain/jobs/types'
import { jobFeaturesGateway } from '@/application/container'

export function useDraftDiff(jobId: string) {
  const [snapshots, setSnapshots] = useState<DraftSnapshot[]>([])
  const [fromId, setFromId] = useState<number | ''>('')
  const [toId, setToId] = useState<number | ''>('')
  const [diff, setDiff] = useState<DraftDiff | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    jobFeaturesGateway.fetchDraftSnapshots(jobId)
      .then((items) => {
        if (cancelled) return
        setSnapshots(items)
        if (items.length >= 2) {
          setFromId(items[items.length - 2].id)
          setToId(items[items.length - 1].id)
        } else if (items.length === 1) {
          setFromId(items[0].id)
          setToId(items[0].id)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки snapshots')
        }
      })
    return () => {
      cancelled = true
    }
  }, [jobId])

  useEffect(() => {
    if (!jobId || fromId === '' || toId === '' || fromId === toId) {
      setDiff(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError('')

    jobFeaturesGateway.fetchDraftDiff(jobId, fromId, toId)
      .then((result) => {
        if (!cancelled) setDiff(result)
      })
      .catch((err) => {
        if (!cancelled) {
          setDiff(null)
          setError(err instanceof Error ? err.message : 'Ошибка diff')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [jobId, fromId, toId])

  return {
    snapshots,
    fromId,
    toId,
    setFromId,
    setToId,
    diff,
    loading,
    error,
  }
}
