import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { WorkbenchLayout } from '@/layouts/WorkbenchLayout'
import { ProjectControlsPanel } from '@/presentation/panels/ProjectControlsPanel'
import { CanvasPanel } from '@/presentation/panels/CanvasPanel'
import { DocumentInspectorPanel } from '@/presentation/panels/DocumentInspectorPanel'
import { useJobStream } from '@/application/jobs/useJobStream'
import { useAgentGraphViewModel } from '@/application/graph/useAgentGraphViewModel'
import {
  WorkbenchProvider,
  type WorkbenchContextValue,
  type WorkbenchTab,
} from '@/application/workbench/WorkbenchContext'
import type { JobStatePatch } from '@/domain/jobs/types'

interface Props {
  jobId: string
  onNew: () => void
  footer: ReactNode
}

export function WorkbenchPage({ jobId, onNew, footer }: Props) {
  const stream = useJobStream(jobId)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null)
  const [rightTab, setRightTab] = useState<WorkbenchTab>('document')
  const [rerunNode, setRerunNode] = useState<string | null>(null)
  const [outlineHighlight, setOutlineHighlight] = useState('')
  const [timeTravelPatch, setTimeTravelPatch] = useState<JobStatePatch | null>(null)
  const [timeTravelLabel, setTimeTravelLabel] = useState<string | null>(null)
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<string | null>(null)
  const prevPaused = useRef(false)

  const displayPatch = timeTravelPatch ?? stream.statePatch

  const activePipeline =
    stream.job?.custom_pipeline?.length
      ? stream.job.custom_pipeline
      : stream.statePatch.custom_pipeline
  const graphWorkType = activePipeline?.length ? 'custom' : stream.job?.work_type ?? 'auto'

  const clarificationAgent =
    stream.clarificationAgent ??
    stream.statePatch.pending_clarification?.agent ??
    null

  const graph = useAgentGraphViewModel(
    graphWorkType,
    stream.steps,
    stream.activeAgent,
    {
      revisionNumber: stream.statePatch.revision_number,
      critiqueNotes: stream.statePatch.critique_notes,
    },
    clarificationAgent,
    activePipeline,
  )

  useEffect(() => {
    const paused =
      stream.awaitingPlanApproval ||
      stream.awaitingClarification ||
      stream.awaitingTeamApproval ||
      stream.job?.status === 'paused'
    if (paused && !prevPaused.current) {
      setRightTab('document')
      requestAnimationFrame(() => {
        const target = stream.awaitingTeamApproval
          ? 'team-approval'
          : stream.awaitingClarification
            ? 'agent-clarification'
            : 'plan-approval'
        document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
    prevPaused.current = paused
  }, [
    stream.awaitingPlanApproval,
    stream.awaitingClarification,
    stream.awaitingTeamApproval,
    stream.job?.status,
  ])

  const handleCheckpointPreview = (
    checkpointId: string,
    patch: JobStatePatch,
    label: string,
  ) => {
    setSelectedCheckpointId(checkpointId)
    setTimeTravelPatch(patch)
    setTimeTravelLabel(label)
    setRightTab('document')
  }

  const handleClearTimeTravel = () => {
    setSelectedCheckpointId(null)
    setTimeTravelPatch(null)
    setTimeTravelLabel(null)
  }

  const handleContinue = () => {
    handleClearTimeTravel()
    setRightTab('document')
    document.getElementById('plan-approval')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleSelectAgent = (agentId: string) => {
    setSelectedNodeId(agentId)
    setSelectedStepIndex(null)
    setRightTab('inspector')
  }

  const contextValue = useMemo((): WorkbenchContextValue => ({
    jobId,
    onNew,
    job: stream.job,
    steps: stream.steps,
    statePatch: stream.statePatch,
    displayPatch,
    activeAgent: stream.activeAgent,
    clarificationAgent,
    awaitingPlanApproval: stream.awaitingPlanApproval,
    awaitingClarification: stream.awaitingClarification,
    awaitingTeamApproval: stream.awaitingTeamApproval,
    connected: stream.connected,
    reconnecting: stream.reconnecting,
    streamError: stream.error,
    topology: graph.topology,
    graphNodes: graph.nodes,
    graphEdges: graph.edges,
    graphLoading: graph.loading,
    graphError: graph.error,
    selectedNodeId,
    selectedStepIndex,
    rightTab,
    rerunNode,
    outlineHighlight,
    timeTravelLabel,
    selectedCheckpointId,
    setSelectedNodeId,
    setSelectedStepIndex,
    setRightTab,
    setRerunNode,
    setOutlineHighlight,
    handleContinue,
    handleSelectAgent,
    handleCheckpointPreview,
    handleClearTimeTravel,
    applyEvent: stream.applyEvent ?? (() => {}),
    jobStatus: stream.job?.status,
  }), [
    jobId,
    onNew,
    stream,
    displayPatch,
    clarificationAgent,
    graph,
    selectedNodeId,
    selectedStepIndex,
    rightTab,
    rerunNode,
    outlineHighlight,
    timeTravelLabel,
    selectedCheckpointId,
  ])

  return (
    <WorkbenchProvider value={contextValue}>
      <WorkbenchLayout
        footer={footer}
        left={<ProjectControlsPanel />}
        center={<CanvasPanel />}
        right={<DocumentInspectorPanel />}
      />
    </WorkbenchProvider>
  )
}
