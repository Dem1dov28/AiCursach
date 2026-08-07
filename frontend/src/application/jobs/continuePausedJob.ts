import type { Job, JobStatePatch } from '@/domain/jobs/types'
import { jobGateway } from '@/application/container'

export type ContinueJobResult = 'resumed' | 'needs_workbench'

function needsWorkbenchInteraction(patch: JobStatePatch): boolean {
  if (patch.awaiting_clarification || patch.awaiting_team_approval) {
    return true
  }
  if (patch.awaiting_plan_approval && !String(patch.structure_outline ?? '').trim()) {
    return true
  }
  return false
}

/** Resume a paused job from the dashboard when no HITL form is required. */
export async function continuePausedJob(jobId: string): Promise<ContinueJobResult> {
  const job: Job = await jobGateway.fetchJob(jobId)
  if (job.status !== 'paused') {
    throw new Error(`Задача не на паузе (статус: ${job.status})`)
  }

  const patch = job.state_patch ?? {}
  if (needsWorkbenchInteraction(patch)) {
    return 'needs_workbench'
  }

  if (patch.awaiting_plan_approval) {
    await jobGateway.resumeJob(jobId, String(patch.structure_outline ?? ''))
  } else {
    await jobGateway.retryJob(jobId)
  }
  return 'resumed'
}
