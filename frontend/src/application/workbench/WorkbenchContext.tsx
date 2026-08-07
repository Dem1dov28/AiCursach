import {
  createContext,
  useContext,
  useMemo,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react'
import type { Edge, Node } from '@xyflow/react'
import type { GraphTopologyDto } from '@/domain/graph/types'
import type { Job, JobStatePatch, JobStep, JobStatus, StreamEvent } from '@/domain/jobs/types'
import type { AgentFlowNodeData } from '@/application/graph/mapTopologyToFlow'

export type WorkbenchTab = 'document' | 'inspector'

export interface WorkbenchContextValue {
  jobId: string
  onNew: () => void

  job: Job | null
  steps: JobStep[]
  statePatch: JobStatePatch
  displayPatch: JobStatePatch
  activeAgent: string | null
  clarificationAgent: string | null

  awaitingPlanApproval: boolean
  awaitingClarification: boolean
  awaitingTeamApproval: boolean

  connected: boolean
  reconnecting: boolean
  streamError: string

  topology: GraphTopologyDto | null
  graphNodes: Node<AgentFlowNodeData>[]
  graphEdges: Edge[]
  graphLoading: boolean
  graphError: string

  selectedNodeId: string | null
  selectedStepIndex: number | null
  rightTab: WorkbenchTab
  rerunNode: string | null
  outlineHighlight: string
  timeTravelLabel: string | null
  selectedCheckpointId: string | null

  setSelectedNodeId: Dispatch<SetStateAction<string | null>>
  setSelectedStepIndex: Dispatch<SetStateAction<number | null>>
  setRightTab: Dispatch<SetStateAction<WorkbenchTab>>
  setRerunNode: Dispatch<SetStateAction<string | null>>
  setOutlineHighlight: Dispatch<SetStateAction<string>>

  handleContinue: () => void
  handleSelectAgent: (agentId: string) => void
  handleCheckpointPreview: (checkpointId: string, patch: JobStatePatch, label: string) => void
  handleClearTimeTravel: () => void
  applyEvent: (event: StreamEvent) => void

  jobStatus: JobStatus | undefined
}

const WorkbenchContext = createContext<WorkbenchContextValue | null>(null)

export function WorkbenchProvider({
  value,
  children,
}: {
  value: WorkbenchContextValue
  children: ReactNode
}) {
  const memo = useMemo(() => value, [value])
  return <WorkbenchContext.Provider value={memo}>{children}</WorkbenchContext.Provider>
}

export function useWorkbench(): WorkbenchContextValue {
  const ctx = useContext(WorkbenchContext)
  if (!ctx) {
    throw new Error('useWorkbench must be used within WorkbenchProvider')
  }
  return ctx
}
