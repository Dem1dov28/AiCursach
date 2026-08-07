import { useCallback, useState } from 'react'
import { jobFeaturesGateway, jobGateway } from '@/application/container'

export function useJobActions(jobId: string) {
  const [downloading, setDownloading] = useState(false)
  const [exportingLatex, setExportingLatex] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [error, setError] = useState('')

  const downloadZip = useCallback(async () => {
    setDownloading(true)
    setError('')
    try {
      await jobGateway.downloadJob(jobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка скачивания')
    } finally {
      setDownloading(false)
    }
  }, [jobId])

  const exportLatex = useCallback(async () => {
    setExportingLatex(true)
    setError('')
    try {
      await jobFeaturesGateway.downloadLatex(jobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка экспорта LaTeX')
    } finally {
      setExportingLatex(false)
    }
  }, [jobId])

  const resume = useCallback(
    (structureOutline: string) => jobGateway.resumeJob(jobId, structureOutline),
    [jobId],
  )

  const rerun = useCallback(
    (fromNode: string, structureOutline = '', promptOverride = '') =>
      jobGateway.rerunJob(jobId, fromNode, structureOutline, promptOverride),
    [jobId],
  )

  const retry = useCallback(async () => {
    setRetrying(true)
    setError('')
    try {
      await jobGateway.retryJob(jobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка перезапуска')
      throw err
    } finally {
      setRetrying(false)
    }
  }, [jobId])

  return {
    downloading,
    exportingLatex,
    retrying,
    error,
    setError,
    downloadZip,
    exportLatex,
    resume,
    rerun,
    retry,
  }
}
