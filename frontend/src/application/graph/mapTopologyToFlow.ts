import type { Edge, Node } from '@xyflow/react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import { AGENT_ICONS, EDGE_KIND_LABELS } from '@/domain/graph/agentPresentation'
import type { AppIconName } from '@/domain/icons/types'
import type { GraphEdgeDto, GraphNodeDto, GraphTopologyDto, NodeVisualState } from '@/domain/graph/types'

export type AgentFlowNodeData = {
  label: string
  displayLabel: string
  iconName: AppIconName
  role: string
  kind: string
  status: 'idle' | 'active' | 'done' | 'revision' | 'awaiting'
  miniLog?: string
  stepNumber?: number
  selected?: boolean
}

const STATUS_CLASS: Record<string, string> = {
  idle: 'flow-node-idle',
  active: 'flow-node-active',
  done: 'flow-node-done',
  revision: 'flow-node-revision',
  awaiting: 'flow-node-awaiting',
}

const BASE_GAP_Y = 128
const EXTRA_GAP_AWAITING = 40
const EXTRA_GAP_REVISION = 32
const EXTRA_GAP_LOG = 28

function layoutPipelinePositions(
  topologyNodes: GraphNodeDto[],
  dataById: Map<string, { status: string; miniLog?: string }>,
): Map<string, { x: number; y: number }> {
  const sorted = [...topologyNodes].sort((a, b) => a.position.y - b.position.y)
  const positions = new Map<string, { x: number; y: number }>()
  const centerX = sorted[0]?.position.x ?? 400
  let y = 0

  for (const node of sorted) {
    positions.set(node.id, { x: centerX, y })
    const meta = dataById.get(node.id)
    let gap = BASE_GAP_Y
    if (meta?.status === 'awaiting') gap += EXTRA_GAP_AWAITING
    else if (meta?.status === 'revision') gap += EXTRA_GAP_REVISION
    if (meta?.miniLog) gap += EXTRA_GAP_LOG
    y += gap
  }

  return positions
}

function lastStepByAgent(steps: { agent: string; step?: number }[]): Map<string, number> {
  const map = new Map<string, number>()
  for (const step of steps) {
    if (typeof step.step === 'number') {
      map.set(step.agent, step.step)
    }
  }
  return map
}

export function mapTopologyToFlow(
  topology: GraphTopologyDto,
  visualStates: NodeVisualState[],
  steps: { agent: string; message?: string; step?: number }[] = [],
): { nodes: Node<AgentFlowNodeData>[]; edges: Edge[] } {
  const statusById = new Map(visualStates.map((item) => [item.id, item.status]))
  const lastLogByAgent = new Map<string, string>()
  const stepByAgent = lastStepByAgent(steps)

  for (const step of steps) {
    if (step.message) lastLogByAgent.set(step.agent, step.message)
  }

  const dataById = new Map<string, { status: string; miniLog?: string }>()
  for (const node of topology.nodes) {
    const status = statusById.get(node.id) ?? 'idle'
    dataById.set(node.id, {
      status,
      miniLog: lastLogByAgent.get(node.id),
    })
  }

  const layout = layoutPipelinePositions(topology.nodes, dataById)

  const nodes: Node<AgentFlowNodeData>[] = topology.nodes.map((node: GraphNodeDto) => {
    const status = statusById.get(node.id) ?? 'idle'
    const pos = layout.get(node.id) ?? node.position
    const agentId = node.id
    return {
      id: agentId,
      type: 'agent',
      position: pos,
      data: {
        label: node.label,
        displayLabel: AGENT_LABELS[agentId] ?? node.label,
        iconName: AGENT_ICONS[agentId] ?? 'bot',
        role: node.role,
        kind: node.kind,
        status,
        miniLog: lastLogByAgent.get(agentId),
        stepNumber: stepByAgent.get(agentId),
      },
      className: STATUS_CLASS[status],
    }
  })

  const edges: Edge[] = topology.edges.map((edge: GraphEdgeDto) => {
    const isLoop = edge.kind === 'loop'
    const isRoute = edge.kind === 'route'
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: isLoop ? EDGE_KIND_LABELS.loop : isRoute ? undefined : undefined,
      labelStyle: isLoop
        ? { fill: '#fca5a5', fontSize: 10, fontWeight: 600 }
        : undefined,
      labelBgStyle: isLoop ? { fill: 'rgba(15,23,42,0.85)' } : undefined,
      animated: isLoop || isRoute,
      className: isLoop ? 'flow-edge-loop' : isRoute ? 'flow-edge-route' : 'flow-edge-flow',
      type: 'smoothstep',
    }
  })

  return { nodes, edges }
}
