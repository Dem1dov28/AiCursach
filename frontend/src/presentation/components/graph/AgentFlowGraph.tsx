import { useEffect, useMemo } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { AgentFlowNodeData } from '@/application/graph/mapTopologyToFlow'
import { AgentFlowNode } from './AgentFlowNode'

const nodeTypes = { agent: AgentFlowNode }

const defaultEdgeOptions = {
  type: 'smoothstep' as const,
  pathOptions: { borderRadius: 16 },
}

interface FlowProps {
  nodes: Node<AgentFlowNodeData>[]
  edges: Edge[]
  onNodeClick?: (nodeId: string) => void
  rerunEnabled?: boolean
  fitKey: string
}

function FlowInner({ nodes, edges, onNodeClick, rerunEnabled, fitKey }: FlowProps) {
  const { fitView } = useReactFlow()

  useEffect(() => {
    const timer = window.setTimeout(
      () => fitView({ padding: 0.22, minZoom: 0.5, maxZoom: 1.15, duration: 280 }),
      60,
    )
    return () => window.clearTimeout(timer)
  }, [fitKey, fitView])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      defaultEdgeOptions={defaultEdgeOptions}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={rerunEnabled}
      onNodeClick={(_event, node) => onNodeClick?.(node.id)}
      proOptions={{ hideAttribution: true }}
      minZoom={0.35}
      maxZoom={1.4}
    >
      <Background
        variant={BackgroundVariant.Dots}
        gap={20}
        size={1}
        color="rgba(148,163,184,0.12)"
      />
      <Controls showInteractive={false} position="bottom-right" />
    </ReactFlow>
  )
}

interface Props {
  nodes: Node<AgentFlowNodeData>[]
  edges: Edge[]
  loading?: boolean
  error?: string
  onNodeClick?: (nodeId: string) => void
  rerunEnabled?: boolean
}

export function AgentFlowGraph({
  nodes,
  edges,
  loading,
  error,
  onNodeClick,
  rerunEnabled,
}: Props) {
  const fitKey = useMemo(
    () => nodes.map((node) => `${node.id}:${node.data.status}:${node.position.y}`).join('|'),
    [nodes],
  )

  if (loading) {
    return (
      <div className="agent-flow-canvas agent-flow-canvas--loading">
        <p className="hint">Загрузка схемы команды…</p>
      </div>
    )
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>
  }

  return (
    <div className="agent-flow-canvas">
      <ReactFlowProvider>
        <FlowInner
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          rerunEnabled={rerunEnabled}
          fitKey={fitKey}
        />
      </ReactFlowProvider>
    </div>
  )
}
