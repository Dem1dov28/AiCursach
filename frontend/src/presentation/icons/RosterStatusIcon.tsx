import { AppIcon } from './AppIcon'

interface Props {
  status: 'idle' | 'active' | 'done' | string
}

export function RosterStatusIcon({ status }: Props) {
  if (status === 'active') {
    return <AppIcon name="circle-dot" size={10} strokeWidth={2.5} className="roster-status roster-status--active" />
  }
  if (status === 'done') {
    return <AppIcon name="check" size={12} strokeWidth={2.5} className="roster-status roster-status--done" />
  }
  return <AppIcon name="circle" size={10} strokeWidth={1.5} className="roster-status roster-status--idle" />
}
