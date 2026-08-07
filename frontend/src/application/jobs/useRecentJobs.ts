import { useCallback, useEffect, useState } from 'react'
import type { JobStatus, WorkType } from '@/domain/jobs/types'
import type { RecentJobEntry } from '@/domain/jobs/recentJob'
import { jobFeaturesGateway } from '@/application/container'
import { jobGateway } from '@/application/container'

export type { RecentJobEntry }

const STORAGE_KEY = 'bsuir_recent_jobs_v1'
const MAX_JOBS = 50

function loadStoredEntries(): RecentJobEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as RecentJobEntry[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveStoredEntries(entries: RecentJobEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_JOBS)))
}

function localMetaFromEntries(entries: RecentJobEntry[]): Record<string, { lastOpenedAt: string }> {
  return Object.fromEntries(entries.map((item) => [item.id, { lastOpenedAt: item.lastOpenedAt }]))
}

function upsertStoredEntry(partial: RecentJobEntry): void {
  const stored = loadStoredEntries()
  const index = stored.findIndex((item) => item.id === partial.id)
  const next =
    index >= 0
      ? stored.map((item, i) => (i === index ? { ...item, ...partial } : item))
      : [partial, ...stored]
  saveStoredEntries(next)
}

function estimateProgress(status: JobStatus, stepsCount: number): number {
  if (status === 'completed') return 100
  if (status === 'failed') return Math.min(90, Math.max(15, stepsCount * 12))
  if (status === 'paused') return Math.min(85, Math.max(40, stepsCount * 14))
  if (status === 'running') return Math.min(95, Math.max(20, stepsCount * 15))
  return Math.min(30, stepsCount * 10)
}

export function registerRecentJob(entry: {
  id: string
  projectName: string
  workType: WorkType
  topic?: string
}) {
  const now = new Date().toISOString()
  upsertStoredEntry({
    id: entry.id,
    projectName: entry.projectName,
    workType: entry.workType,
    topic: entry.topic ?? '',
    status: 'queued',
    createdAt: now,
    lastOpenedAt: now,
    progress: 5,
    estimatedCostUsd: 0,
  })
}

export function touchRecentJob(jobId: string) {
  const now = new Date().toISOString()
  const stored = loadStoredEntries()
  const existing = stored.find((item) => item.id === jobId)
  upsertStoredEntry(
    existing
      ? { ...existing, lastOpenedAt: now }
      : {
          id: jobId,
          projectName: jobId,
          workType: 'auto',
          topic: '',
          status: 'queued',
          createdAt: now,
          lastOpenedAt: now,
          progress: 0,
          estimatedCostUsd: 0,
        },
  )
}

export function removeRecentJob(jobId: string) {
  const stored = loadStoredEntries().filter((item) => item.id !== jobId)
  saveStoredEntries(stored)
}

async function mapRemoteJob(
  remote: Record<string, unknown>,
  localMeta: Record<string, { lastOpenedAt: string }>,
): Promise<RecentJobEntry> {
  const id = String(remote.id ?? '')
  const stepsCount = Number(remote.step_count ?? 0)
  const status = (remote.status as JobStatus) ?? 'queued'
  let cost = Number(remote.estimated_cost_usd ?? 0)

  if (!cost && status !== 'queued') {
    try {
      const metrics = await jobFeaturesGateway.fetchJobMetrics(id)
      cost = Number(metrics.estimated_cost_usd ?? 0)
    } catch {
      /* metrics optional */
    }
  }

  return {
    id,
    projectName: String(remote.project_name ?? id),
    workType: (remote.work_type as WorkType) ?? 'auto',
    topic: String(remote.topic ?? ''),
    status,
    createdAt: String(remote.created_at ?? new Date().toISOString()),
    lastOpenedAt: localMeta[id]?.lastOpenedAt ?? String(remote.created_at ?? new Date().toISOString()),
    progress: estimateProgress(status, stepsCount),
    estimatedCostUsd: cost,
  }
}

export function useRecentJobs(refreshToken = 0) {
  const [jobs, setJobs] = useState<RecentJobEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    setLoading(true)
    setError('')
    const localMeta = localMetaFromEntries(loadStoredEntries())

    try {
      const remoteList = await jobGateway.fetchJobs(MAX_JOBS)
      const mapped = await Promise.all(remoteList.map((item) => mapRemoteJob(item, localMeta)))
      mapped.sort(
        (a, b) => new Date(b.lastOpenedAt).getTime() - new Date(a.lastOpenedAt).getTime(),
      )
      saveStoredEntries(mapped)
      setJobs(mapped)
    } catch {
      const fallbackIds = Object.keys(localMeta)
      if (fallbackIds.length === 0) {
        setJobs([])
        setError('Не удалось загрузить проекты')
        setLoading(false)
        return
      }
      const mapped = await Promise.all(
        fallbackIds.map(async (id) => {
          try {
            const remote = await jobGateway.fetchJob(id)
            return mapRemoteJob(remote as unknown as Record<string, unknown>, localMeta)
          } catch {
            return null
          }
        }),
      )
      const items = mapped.filter((item): item is RecentJobEntry => item != null)
      setJobs(items)
      setError('Список с сервера недоступен — показаны локальные проекты')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [refreshToken, reload])

  return { jobs, loading, error, reload }
}
