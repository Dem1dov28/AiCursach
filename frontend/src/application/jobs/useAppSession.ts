import { useCallback, useEffect, useState } from 'react'
import type { Health } from '@/domain/jobs/types'
import { jobGateway } from '@/application/container'

export function useHealthCheck(intervalMs = 15_000) {
  const [health, setHealth] = useState<Health | null>(null)

  useEffect(() => {
    const check = () =>
      jobGateway
        .fetchHealth()
        .then(setHealth)
        .catch(() => setHealth(null))
    check()
    const timer = setInterval(check, intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs])

  return health
}

export function useServerFooter(health: Health | null) {
  if (!health) {
    return { className: 'footer warn', text: 'Сервер недоступен' }
  }
  if (health.llm_configured && health.database_ok) {
    return { className: 'footer ok', text: 'Сервер готов · PostgreSQL · LLM · SSE' }
  }
  if (!health.database_ok) {
    return { className: 'footer warn', text: 'PostgreSQL недоступен — bash scripts/start-db.sh' }
  }
  return { className: 'footer warn', text: 'Нет API-ключа LLM — настройте .env' }
}

export function useCreateJob(onCreated: (jobId: string, form: FormData) => void) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = useCallback(
    async (form: FormData) => {
      setLoading(true)
      setError('')
      try {
        const { job_id } = await jobGateway.createJob(form)
        onCreated(job_id, form)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Ошибка')
      } finally {
        setLoading(false)
      }
    },
    [onCreated],
  )

  return { loading, error, submit, setError }
}
