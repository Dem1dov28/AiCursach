import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  Bot,
  Check,
  CheckCircle2,
  Circle,
  CircleDot,
  ClipboardList,
  Clock,
  Code2,
  FileText,
  Folder,
  FolderOpen,
  GitBranch,
  Hand,
  Hexagon,
  History,
  Library,
  MessageSquareText,
  Network,
  Pause,
  PenLine,
  Play,
  Search,
  Sparkles,
  Target,
  XCircle,
} from 'lucide-react'
import type { AppIconName } from '@/domain/icons/types'

const ICON_MAP: Record<AppIconName, LucideIcon> = {
  sparkles: Sparkles,
  target: Target,
  'clipboard-list': ClipboardList,
  'folder-open': FolderOpen,
  search: Search,
  'pen-line': PenLine,
  'message-square': MessageSquareText,
  code: Code2,
  play: Play,
  network: Network,
  'bar-chart': BarChart3,
  'file-text': FileText,
  pause: Pause,
  bot: Bot,
  users: Hexagon,
  hand: Hand,
  'git-branch': GitBranch,
  history: History,
  library: Library,
  hexagon: Hexagon,
  check: Check,
  'check-circle': CheckCircle2,
  'x-circle': XCircle,
  'play-circle': Play,
  clock: Clock,
  folder: Folder,
  circle: Circle,
  'circle-dot': CircleDot,
}

interface Props {
  name: AppIconName
  size?: number
  className?: string
  strokeWidth?: number
}

export function AppIcon({ name, size = 18, className, strokeWidth = 1.75 }: Props) {
  const Icon = ICON_MAP[name]
  return (
    <Icon
      size={size}
      strokeWidth={strokeWidth}
      className={['app-icon', className].filter(Boolean).join(' ')}
      aria-hidden
    />
  )
}

export function isAppIconName(value: string): value is AppIconName {
  return value in ICON_MAP
}
