import { Suspense, lazy, useMemo, useState } from 'react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import { useJobActions } from '@/application/jobs/useJobActions'
import { useWorkbench } from '@/application/workbench/WorkbenchContext'
import { canRerunJob } from '@/domain/jobs/context'
import { PromptOverrideModal } from '@/presentation/components/hitl/PromptOverrideModal'
import { CanvasStatusBar } from '@/presentation/components/graph/CanvasStatusBar'
import { ExecutionTimeline } from '@/presentation/components/graph/ExecutionTimeline'

const AgentFlowGraph = lazy(() =>
  import('@/presentation/components/graph/AgentFlowGraph').then((module) => ({
    default: module.AgentFlowGraph,
  })),
)

export function CanvasPanel() {
  const {
    jobId,
    jobStatus,
    graphNodes: nodes,
    graphEdges: edges,
    graphLoading,
    graphError,
    steps,
    statePatch,
    activeAgent,
    selectedNodeId,
    selectedStepIndex,
    rerunNode,
    setSelectedNodeId,
    setSelectedStepIndex,
    setRightTab,
    setRerunNode,
  } = useWorkbench()

  const { rerun } = useJobActions(jobId)
  const [rerunError, setRerunError] = useState('')
  const [rerunning, setRerunning] = useState(false)
  const rerunEnabled = canRerunJob(jobStatus)

  const doneCount = useMemo(
    () => nodes.filter((node) => node.data.status === 'done').length,
    [nodes],
  )

  const flowNodes = nodes.map((n) => ({
    ...n,
    selected: n.id === selectedNodeId,
    data: { ...n.data, selected: n.id === selectedNodeId },
    className: [n.className, n.id === selectedNodeId ? 'flow-node-selected' : '']
      .filter(Boolean)
      .join(' '),
  }))

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId)
    setSelectedStepIndex(null)
    setRightTab('inspector')
  }

  const handleRerunConfirm = async (payload: {
    promptOverride: string
    structureOutline: string
  }) => {
    if (!rerunNode) return
    setRerunning(true)
    setRerunError('')
    try {
      await rerun(rerunNode, payload.structureOutline, payload.promptOverride)
      setRerunNode(null)
    } catch (err) {
      setRerunError(err instanceof Error ? err.message : 'Ошибка перезапуска')
    } finally {
      setRerunning(false)
    }
  }

  const currentTask =
    statePatch.current_sub_task?.trim() ||
    (activeAgent
      ? `Сейчас: ${AGENT_LABELS[activeAgent] ?? activeAgent}`
      : undefined)

  return (
    <div className="panel canvas-panel">
      <CanvasStatusBar
        doneCount={doneCount}
        totalCount={nodes.length}
        currentTask={currentTask}
      />

      {rerunError && <div className="alert alert-error">{rerunError}</div>}

      <Suspense fallback={<p className="hint flow-placeholder">Загрузка холста…</p>}>
        <AgentFlowGraph
          nodes={flowNodes}
          edges={edges}
          loading={graphLoading}
          error={graphError}
          rerunEnabled={rerunEnabled}
          onNodeClick={handleNodeClick}
        />
      </Suspense>

      <ExecutionTimeline
        steps={steps}
        activeAgent={activeAgent}
        selectedStepIndex={selectedStepIndex}
        onSelectStep={(index, agentId) => {
          setSelectedStepIndex(index)
          setSelectedNodeId(agentId)
          setRightTab('inspector')
        }}
      />

      <PromptOverrideModal
        nodeId={rerunNode ?? ''}
        open={rerunNode != null}
        submitting={rerunning}
        onCancel={() => setRerunNode(null)}
        onConfirm={handleRerunConfirm}
      />
    </div>
  )
}
