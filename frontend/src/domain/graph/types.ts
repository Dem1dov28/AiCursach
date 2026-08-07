export type NodeKind = 'supervisor' | 'worker'
export type EdgeKind = 'flow' | 'loop' | 'route'
export type NodeVisualStatus = 'idle' | 'active' | 'done' | 'revision' | 'awaiting'

export interface GraphNodeDto {
  id: string
  label: string
  role: string
  kind: NodeKind
  position: { x: number; y: number }
}

export interface GraphEdgeDto {
  id: string
  source: string
  target: string
  kind: EdgeKind
  label?: string
}

export interface GraphTopologyDto {
  work_type: string
  nodes: GraphNodeDto[]
  edges: GraphEdgeDto[]
}

export interface JobStepRef {
  agent: string
}

export interface AgentCatalogEntry {
  id: string
  label: string
  role: string
}

export interface NodeVisualState {
  id: string
  status: NodeVisualStatus
}
