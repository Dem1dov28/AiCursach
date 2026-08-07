import type {
  BibliographyReportResponse,
  CheckpointState,
  DraftDiff,
  DraftSnapshot,
  JobCheckpoint,
  JobMetrics,
  JobStatePatch,
} from '@/domain/jobs/types'

const API = ''

export async function fetchCheckpoints(jobId: string): Promise<JobCheckpoint[]> {
  const res = await fetch(`${API}/api/jobs/${jobId}/checkpoints`)
  if (!res.ok) throw new Error('История checkpoint недоступна')
  const data = await res.json()
  return data.checkpoints as JobCheckpoint[]
}

export async function fetchCheckpointState(
  jobId: string,
  checkpointId: string,
): Promise<CheckpointState> {
  const res = await fetch(`${API}/api/jobs/${jobId}/checkpoints/${encodeURIComponent(checkpointId)}`)
  if (!res.ok) {
    let message = 'Checkpoint недоступен'
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* not JSON */
    }
    throw new Error(message)
  }
  return res.json()
}

export async function restoreCheckpoint(
  jobId: string,
  checkpointId: string,
): Promise<{ ok: boolean; patch: JobStatePatch }> {
  const res = await fetch(
    `${API}/api/jobs/${jobId}/checkpoints/${encodeURIComponent(checkpointId)}/restore`,
    { method: 'POST' },
  )
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось восстановить checkpoint')
  }
  return data
}

export async function fetchDraftSnapshots(jobId: string): Promise<DraftSnapshot[]> {
  const res = await fetch(`${API}/api/jobs/${jobId}/draft-snapshots`)
  if (!res.ok) throw new Error('Snapshots черновика недоступны')
  const data = await res.json()
  return data.snapshots as DraftSnapshot[]
}

export async function fetchDraftDiff(
  jobId: string,
  fromId: number,
  toId: number,
): Promise<DraftDiff> {
  const params = new URLSearchParams({ from: String(fromId), to: String(toId) })
  const res = await fetch(`${API}/api/jobs/${jobId}/draft-diff?${params}`)
  if (!res.ok) throw new Error('Diff недоступен')
  return res.json()
}

export async function downloadLatex(jobId: string): Promise<void> {
  const res = await fetch(latexExportUrl(jobId))
  if (!res.ok) {
    let message = 'Не удалось экспортировать LaTeX'
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* not JSON */
    }
    throw new Error(message)
  }

  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') ?? ''
  const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i)
  const rawName = match?.[1] ? decodeURIComponent(match[1]) : match?.[2]
  const filename = rawName?.endsWith('.tex') ? rawName : `${jobId}.tex`

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function latexExportUrl(jobId: string): string {
  return `${API}/api/jobs/${jobId}/export/latex`
}

export async function fetchJobMetrics(jobId: string): Promise<JobMetrics> {
  const res = await fetch(`${API}/api/jobs/${jobId}/metrics`)
  if (!res.ok) throw new Error('Метрики недоступны')
  return res.json() as Promise<JobMetrics>
}

export async function fetchBibliographyReport(jobId: string): Promise<BibliographyReportResponse> {
  const res = await fetch(`${API}/api/jobs/${jobId}/bibliography-report`)
  if (!res.ok) {
    let message = 'Отчёт по библиографии недоступен'
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* not JSON */
    }
    throw new Error(message)
  }
  return res.json() as Promise<BibliographyReportResponse>
}

export async function updateJobSettings(
  jobId: string,
  settings: {
    max_revisions?: number
    autonomy_level?: string
    confidence_threshold?: number
    enable_style_polisher?: boolean
    enable_bibliography_verifier?: boolean
  },
) {
  const res = await fetch(`${API}/api/jobs/${jobId}/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось сохранить настройки')
  }
  return data
}
