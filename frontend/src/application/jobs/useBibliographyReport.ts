import { useCallback, useEffect, useState } from 'react'
import type { BibliographyReportResponse } from '@/domain/jobs/types'
import { jobFeaturesGateway } from '@/application/container'

export function useBibliographyReport(jobId: string, enabled: boolean) {
  const [data, setData] = useState<BibliographyReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    if (!enabled) return
    setLoading(true)
    setError('')
    try {
      const report = await jobFeaturesGateway.fetchBibliographyReport(jobId)
      setData(report)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить отчёт')
    } finally {
      setLoading(false)
    }
  }, [enabled, jobId])

  useEffect(() => {
    void reload()
  }, [reload])

  return { data, loading, error, reload }
}
