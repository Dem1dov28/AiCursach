import type { JobContext } from '@/domain/jobs/context'
import type { Health, Job, JobStatePatch } from '@/domain/jobs/types'

const API = ''

export async function fetchJobs(limit = 50, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const res = await fetch(`${API}/api/jobs?${params}`)
  if (!res.ok) throw new Error('Не удалось загрузить список задач')
  const data = await res.json()
  return data.jobs as Array<Record<string, unknown>>
}

export async function retryJob(jobId: string) {
  const res = await fetch(`${API}/api/jobs/${jobId}/retry`, { method: 'POST' })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось перезапустить задачу')
  }
  return data
}

export async function pauseJob(jobId: string) {
  const res = await fetch(`${API}/api/jobs/${jobId}/pause`, { method: 'POST' })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось поставить на паузу')
  }
  return data as { ok: boolean; job_id: string; status: string }
}

export async function deleteJob(jobId: string) {
  const res = await fetch(`${API}/api/jobs/${jobId}`, { method: 'DELETE' })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось удалить проект')
  }
  return data as { ok: boolean; job_id: string }
}

export async function fetchHealth(): Promise<Health> {
  const res = await fetch(`${API}/api/health`)
  if (!res.ok) throw new Error('Сервер недоступен')
  return res.json() as Promise<Health>
}

export async function createJob(form: FormData) {
  const res = await fetch(`${API}/api/jobs`, { method: 'POST', body: form })
  const data = await res.json()
  if (!res.ok) {
    const detail = data.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (Array.isArray(detail)) {
      throw new Error(detail.map((item: { msg?: string }) => item.msg).join('; '))
    }
    throw new Error('Ошибка создания задачи')
  }
  return data as { job_id: string; status: string }
}

export async function fetchJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API}/api/jobs/${jobId}`)
  if (!res.ok) throw new Error('Задача не найдена')
  return res.json() as Promise<Job>
}

export function downloadUrl(jobId: string): string {
  return `${API}/api/jobs/${jobId}/download`
}

export function streamJobUrl(jobId: string): string {
  return `${API}/api/jobs/${jobId}/stream`
}

export async function saveJobPlan(jobId: string, structureOutline: string, topic = '') {
  const res = await fetch(`${API}/api/jobs/${jobId}/plan`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ structure_outline: structureOutline, topic }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось сохранить план')
  }
  return data as { job_id: string; patch: JobStatePatch }
}

export async function approveTeam(jobId: string, pipeline: string[]) {
  const res = await fetch(`${API}/api/jobs/${jobId}/team`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ custom_pipeline: pipeline }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось утвердить команду')
  }
  return data
}

export async function submitClarificationAnswer(
  jobId: string,
  selectedOption: string,
  customText: string,
) {
  const body = JSON.stringify({ selected_option: selectedOption, custom_text: customText })
  let lastError = 'Не удалось отправить ответ'

  for (let attempt = 0; attempt < 4; attempt += 1) {
    const res = await fetch(`${API}/api/jobs/${jobId}/clarification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })
    const data = await res.json()
    if (res.ok) return data
    lastError = typeof data.detail === 'string' ? data.detail : lastError
    if (res.status !== 409 || attempt === 3) {
      throw new Error(lastError)
    }
    await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)))
  }

  throw new Error(lastError)
}

export async function resumeJob(jobId: string, structureOutline: string) {
  const res = await fetch(`${API}/api/jobs/${jobId}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ structure_outline: structureOutline }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось возобновить задачу')
  }
  return data
}

export async function rerunJob(
  jobId: string,
  fromNode: string,
  structureOutline = '',
  promptOverride = '',
) {
  const res = await fetch(`${API}/api/jobs/${jobId}/rerun`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_node: fromNode,
      structure_outline: structureOutline,
      prompt_override: promptOverride,
    }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось перезапустить узел')
  }
  return data
}

export async function fetchJobContext(jobId: string): Promise<JobContext> {
  const res = await fetch(`${API}/api/jobs/${jobId}/context`)
  if (!res.ok) throw new Error('Контекст задачи недоступен')
  return res.json() as Promise<JobContext>
}

export async function downloadJob(jobId: string): Promise<void> {
  const res = await fetch(downloadUrl(jobId))
  if (!res.ok) {
    let message = 'Не удалось скачать архив'
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
  const filename = rawName?.endsWith('.zip') ? rawName : `${jobId}.zip`

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
