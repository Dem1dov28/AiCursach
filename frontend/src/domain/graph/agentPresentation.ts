import type { AppIconName } from '@/domain/icons/types'

/** User-facing presentation for workflow agents on the canvas. */

export const AGENT_ICONS: Record<string, AppIconName> = {
  supervisor: 'target',
  analyzer: 'clipboard-list',
  project_init: 'folder-open',
  researcher: 'search',
  writer: 'pen-line',
  critiquer: 'message-square',
  coder_gen: 'code',
  code_runner: 'play',
  diagrammer: 'network',
  assets_builder: 'bar-chart',
  antiplagiat: 'check-circle',
  annex_builder: 'folder',
  docx_builder: 'file-text',
  breakpoint: 'pause',
}

export const STATUS_LABELS: Record<string, string> = {
  idle: 'Ожидает',
  active: 'В работе',
  done: 'Готово',
  revision: 'Правки',
  awaiting: 'Нужен ответ',
}

export const EDGE_KIND_LABELS: Record<string, string> = {
  loop: 'цикл правок',
  route: 'маршрут',
  flow: 'далее',
}
