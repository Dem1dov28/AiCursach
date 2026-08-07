import { useEffect, useMemo, useState } from 'react'
import type { Edge, Node } from '@xyflow/react'
import { resolveNodeVisualStates } from '@/domain/graph/resolveNodeVisualState'
import type { GraphTopologyDto, JobStepRef } from '@/domain/graph/types'
import { graphGateway } from '@/application/container'
import { mapTopologyToFlow, type AgentFlowNodeData } from './mapTopologyToFlow'

export function useAgentGraphViewModel(
  workType: string,
  steps: JobStepRef[],
  activeAgent: string | null,
  revision?: { revisionNumber?: number; critiqueNotes?: string },
  clarificationAgent?: string | null,
  customPipeline?: string[],
) {
  const [topology, setTopology] = useState<GraphTopologyDto | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const pipelineKey = customPipeline?.join(',') ?? ''

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    graphGateway.fetchGraphTopology(workType, customPipeline)
      .then((data) => {
        if (!cancelled) setTopology(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки графа')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [workType, pipelineKey, customPipeline])

  const flow = useMemo((): { nodes: Node<AgentFlowNodeData>[]; edges: Edge[] } => {
    if (!topology) return { nodes: [], edges: [] }
    const visualStates = resolveNodeVisualStates(
      topology.nodes.map((node) => node.id),
      steps,
      activeAgent,
      revision,
      { awaitingAgent: clarificationAgent },
    )
    return mapTopologyToFlow(topology, visualStates, steps)
  }, [topology, steps, activeAgent, revision, clarificationAgent])

  return { ...flow, loading, error, topology }
}
