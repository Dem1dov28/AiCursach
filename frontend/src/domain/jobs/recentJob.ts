import type { JobStatus, WorkType } from '@/domain/jobs/types'

export interface RecentJobEntry {
  id: string
  projectName: string
  workType: WorkType
  topic: string
  status: JobStatus
  createdAt: string
  lastOpenedAt: string
  progress: number
  estimatedCostUsd: number
}
