import { useMemo } from 'react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import { resolveNodeVisualStates } from '@/domain/graph/resolveNodeVisualState'
import { deriveProjectPhase } from '@/domain/workflow/projectStatus'
import type { Job, JobStep } from '@/domain/jobs/types'
import type { GraphTopologyDto } from '@/domain/graph/types'

interface Params {
  job: Job | null
  steps: JobStep[]
  topology: GraphTopologyDto | null
  activeAgent: string | null
  awaitingPlanApproval: boolean
  awaitingClarification: boolean
  awaitingTeamApproval: boolean
  clarificationAgent: string | null
}

export function useProjectControlsViewModel({
  job,
  steps,
  topology,
  activeAgent,
  awaitingPlanApproval,
  awaitingClarification,
  awaitingTeamApproval,
  clarificationAgent,
}: Params) {
  const phase = deriveProjectPhase(job?.status, activeAgent, awaitingPlanApproval)
  const pct = job?.status === 'completed' ? 100 : Math.min(95, Math.round((steps.length / 12) * 100))

  const roster = useMemo(() => {
    if (!topology) return []
    const visual = resolveNodeVisualStates(
      topology.nodes.map((n) => n.id),
      steps,
      activeAgent,
      undefined,
      { awaitingAgent: clarificationAgent },
    )
    const statusById = new Map(visual.map((v) => [v.id, v.status]))
    return topology.nodes
      .filter((n) => n.id !== 'supervisor')
      .map((n) => ({
        id: n.id,
        label: AGENT_LABELS[n.id] ?? n.label,
        status: statusById.get(n.id) ?? 'idle',
      }))
  }, [topology, steps, activeAgent, clarificationAgent])

  const showContinue =
    awaitingPlanApproval ||
    awaitingClarification ||
    awaitingTeamApproval ||
    job?.status === 'paused'

  return { phase, pct, roster, showContinue }
}
