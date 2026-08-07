import type { RecentJobEntry } from '@/domain/jobs/recentJob'
import type { AppIconName } from '@/domain/icons/types'
import { AppIcon } from './AppIcon'

const STATUS_ICON: Record<RecentJobEntry['status'], AppIconName> = {
  paused: 'pause',
  completed: 'check-circle',
  failed: 'x-circle',
  running: 'play-circle',
  queued: 'clock',
}

const STATUS_TEXT: Record<RecentJobEntry['status'], string> = {
  paused: 'На паузе',
  completed: 'Завершено',
  failed: 'Ошибка',
  running: 'Выполняется',
  queued: 'В очереди',
}

interface Props {
  status: RecentJobEntry['status']
  progress?: number
}

export function JobStatusBadge({ status, progress }: Props) {
  const label =
    status === 'paused' && progress != null
      ? `${STATUS_TEXT[status]} · ${progress}%`
      : STATUS_TEXT[status]

  return (
    <span className={`job-status job-status--${status}`}>
      <AppIcon name={STATUS_ICON[status]} size={14} strokeWidth={2} />
      {label}
    </span>
  )
}
