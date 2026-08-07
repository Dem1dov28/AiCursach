import type { JobStatus } from '@/domain/jobs/types'

export type StatusTone = 'ok' | 'warn' | 'error' | 'idle' | 'running'

export interface ProjectPhase {
  label: string
  tone: StatusTone
}

const PLANNING_AGENTS = new Set(['analyzer', 'researcher', 'supervisor'])
const WRITING_AGENTS = new Set(['writer', 'coder_gen', 'code_runner'])
const BUILD_AGENTS = new Set(['diagrammer', 'assets_builder', 'antiplagiat', 'annex_builder', 'docx_builder'])
const REVIEW_AGENTS = new Set(['critiquer'])

export function deriveProjectPhase(
  jobStatus: JobStatus | undefined,
  activeAgent: string | null,
  awaitingPlanApproval: boolean,
): ProjectPhase {
  if (jobStatus === 'failed') {
    return { label: 'Ошибка', tone: 'error' }
  }
  if (jobStatus === 'completed') {
    return { label: 'Завершено', tone: 'ok' }
  }
  if (awaitingPlanApproval || jobStatus === 'paused') {
    return { label: 'Ожидание ответа пользователя', tone: 'warn' }
  }
  if (jobStatus === 'queued') {
    return { label: 'В очереди', tone: 'idle' }
  }
  if (activeAgent) {
    if (PLANNING_AGENTS.has(activeAgent)) {
      return { label: 'Проектирование плана', tone: 'running' }
    }
    if (WRITING_AGENTS.has(activeAgent)) {
      return { label: 'Написание текста / код', tone: 'running' }
    }
    if (BUILD_AGENTS.has(activeAgent)) {
      return { label: 'Сборка и оформление', tone: 'running' }
    }
    if (REVIEW_AGENTS.has(activeAgent)) {
      return { label: 'Редактура и проверка', tone: 'running' }
    }
    return { label: 'Выполнение', tone: 'running' }
  }
  if (jobStatus === 'running') {
    return { label: 'Выполнение', tone: 'running' }
  }
  return { label: 'Готов к запуску', tone: 'idle' }
}
