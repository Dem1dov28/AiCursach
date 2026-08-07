import type { JobStepRef, NodeVisualState, NodeVisualStatus } from './types'

interface RevisionContext {
  revisionNumber?: number
  critiqueNotes?: string
}

interface ClarificationContext {
  awaitingAgent?: string | null
}

/** Pure domain rule: derive node status from execution timeline. */
export function resolveNodeVisualStates(
  nodeIds: string[],
  steps: JobStepRef[],
  activeAgent: string | null,
  revision?: RevisionContext,
  clarification?: ClarificationContext,
): NodeVisualState[] {
  return nodeIds.map((id) => ({
    id,
    status: resolveSingleNodeStatus(id, steps, activeAgent, revision, clarification),
  }))
}

function isRevisionCycle(revision?: RevisionContext): boolean {
  if (!revision) return false
  const notes = (revision.critiqueNotes ?? '').trim()
  if (!notes || notes.toUpperCase().includes('APPROVED')) return false
  return (revision.revisionNumber ?? 0) > 0
}

function resolveSingleNodeStatus(
  nodeId: string,
  steps: JobStepRef[],
  activeAgent: string | null,
  revision?: RevisionContext,
  clarification?: ClarificationContext,
): NodeVisualStatus {
  if (clarification?.awaitingAgent === nodeId) return 'awaiting'
  if (activeAgent === nodeId) {
    if (nodeId === 'writer' && isRevisionCycle(revision)) return 'revision'
    return 'active'
  }
  if (steps.some((step) => step.agent === nodeId)) return 'done'
  return 'idle'
}
