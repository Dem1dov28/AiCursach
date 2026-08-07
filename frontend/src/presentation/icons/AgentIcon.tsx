import { AGENT_ICONS } from '@/domain/graph/agentPresentation'
import type { AppIconName } from '@/domain/icons/types'
import { AppIcon } from './AppIcon'

interface Props {
  agentId: string
  size?: number
  className?: string
}

export function AgentIcon({ agentId, size = 18, className }: Props) {
  const name: AppIconName = AGENT_ICONS[agentId] ?? 'bot'
  return <AppIcon name={name} size={size} className={className} />
}
