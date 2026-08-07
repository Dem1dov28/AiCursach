import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import type { TeamProposal } from '@/domain/jobs/types'
import { buildRevisionDialogue } from '@/domain/workflow/buildRevisionDialogue'
import { canRerunJob } from '@/domain/jobs/context'
import { useJobActions } from '@/application/jobs/useJobActions'
import { useJobContext } from '@/application/jobs/useJobContext'
import { useWorkbench } from '@/application/workbench/WorkbenchContext'
import { PlanApprovalBanner } from '@/presentation/components/hitl/PlanApprovalBanner'
import { TeamApprovalCard } from '@/presentation/components/hitl/TeamApprovalCard'
import { AgentClarificationCard } from '@/presentation/components/hitl/AgentClarificationCard'
import { DraftDiffPanel } from '@/presentation/components/document/DraftDiffPanel'
import { SharedMemoryPanel } from '@/presentation/components/inspector/SharedMemoryPanel'
import { CheckpointPanel } from '@/presentation/components/inspector/CheckpointPanel'
import { SessionMetricsPanel } from '@/presentation/components/inspector/SessionMetricsPanel'
import { InspectorOverview } from '@/presentation/components/inspector/InspectorOverview'
import { AgentInspectorSection } from '@/presentation/components/inspector/AgentInspectorSection'
import { BibliographyReportPanel } from '@/presentation/components/inspector/BibliographyReportPanel'
import { StructureOutlineNav } from '@/presentation/components/document/StructureOutlineNav'
import { AppIcon } from '@/presentation/icons'
import { RevisionDialogue } from '@/presentation/components/loop/RevisionDialogue'

const DocumentEditor = lazy(() =>
  import('@/presentation/components/document/DocumentEditor').then((module) => ({
    default: module.DocumentEditor,
  })),
)

type DocView = 'editor' | 'diff'

export function DocumentInspectorPanel() {
  const {
    jobId,
    job,
    steps,
    statePatch,
    displayPatch,
    timeTravelLabel,
    activeAgent,
    awaitingPlanApproval,
    awaitingClarification,
    awaitingTeamApproval,
    streamError,
    selectedNodeId,
    selectedStepIndex,
    rightTab: activeTab,
    outlineHighlight,
    selectedCheckpointId,
    setOutlineHighlight,
    setRightTab: onTabChange,
    setRerunNode: onRequestRerun,
    handleCheckpointPreview: onCheckpointPreview,
    handleClearTimeTravel: onClearTimeTravel,
    applyEvent,
  } = useWorkbench()
  const [docView, setDocView] = useState<DocView>('editor')
  const [planDismissed, setPlanDismissed] = useState(false)
  const { exportingLatex, exportLatex } = useJobActions(jobId)
  const { context, loading, error } = useJobContext(jobId)

  useEffect(() => {
    if (awaitingPlanApproval) setPlanDismissed(false)
  }, [awaitingPlanApproval])

  const workType = job?.work_type ?? 'lab'
  const isTimeTravel = Boolean(timeTravelLabel)
  const clarification = statePatch.pending_clarification
  const teamProposal: TeamProposal | null = statePatch.pending_team
    ? {
        pipeline: statePatch.pending_team.pipeline ?? statePatch.custom_pipeline ?? [],
        rationale: statePatch.pending_team.rationale ?? statePatch.team_rationale ?? '',
        task_breakdown:
          statePatch.pending_team.task_breakdown ?? statePatch.task_breakdown ?? [],
        topic: statePatch.pending_team.topic ?? statePatch.topic,
        detected_work_kind:
          statePatch.pending_team.detected_work_kind ?? statePatch.detected_work_kind,
        discipline: statePatch.pending_team.discipline ?? statePatch.discipline,
        structure_outline:
          statePatch.pending_team.structure_outline ?? statePatch.structure_outline,
        work_brief_summary: statePatch.pending_team.work_brief_summary,
        structure_source: statePatch.pending_team.structure_source,
      }
    : null

  const documentWorkType =
    statePatch.detected_work_kind === 'coursework' ||
    statePatch.detected_work_kind === 'diploma' ||
    statePatch.detected_work_kind === 'essay'
      ? 'coursework'
      : workType === 'auto'
        ? 'lab'
        : workType
  const showTeamApproval = awaitingTeamApproval && teamProposal && !isTimeTravel
  const showClarification = awaitingClarification && clarification && !isTimeTravel && !showTeamApproval
  const showPlanApproval = awaitingPlanApproval && !planDismissed && !showClarification && !showTeamApproval
  const rerunEnabled = canRerunJob(job?.status)
  const selectedStep = selectedStepIndex != null ? steps[selectedStepIndex] : null
  const nodeStep = selectedNodeId
    ? [...steps].reverse().find((s) => s.agent === selectedNodeId)
    : null
  const inspectStep = selectedStep ?? nodeStep
  const revisionTurns = useMemo(() => buildRevisionDialogue(steps), [steps])
  const hasDraft = Boolean(displayPatch.content_draft?.trim())

  return (
    <div className="panel document-inspector-panel">
      <div className="doc-inspector-tabs">
        <button
          type="button"
          className={activeTab === 'document' ? 'active' : ''}
          onClick={() => onTabChange('document')}
        >
          <AppIcon name="file-text" size={15} />
          Документ
        </button>
        <button
          type="button"
          className={activeTab === 'inspector' ? 'active' : ''}
          onClick={() => onTabChange('inspector')}
        >
          <AppIcon name="search" size={15} />
          Инспектор
        </button>
      </div>

      {activeTab === 'document' && (
        <div className="doc-inspector-body">
          {isTimeTravel && (
            <section className="time-travel-banner">
              <div>
                <strong>Просмотр прошлой версии</strong>
                <p className="hint">{timeTravelLabel} · только чтение</p>
              </div>
              <button type="button" className="btn btn-secondary btn-sm" onClick={onClearTimeTravel}>
                К текущей версии
              </button>
            </section>
          )}

          {showTeamApproval && teamProposal && (
            <TeamApprovalCard
              jobId={jobId}
              team={teamProposal}
              onApproved={() => setPlanDismissed(true)}
            />
          )}

          {showClarification && clarification && (
            <AgentClarificationCard
              jobId={jobId}
              clarification={clarification}
              onAnswered={() => setPlanDismissed(true)}
            />
          )}

          {showPlanApproval && !isTimeTravel && (
            <PlanApprovalBanner
              jobId={jobId}
              structureOutline={statePatch.structure_outline ?? ''}
              onApproved={() => setPlanDismissed(true)}
            />
          )}

          <div className="workspace-tabs doc-subtabs">
            <button
              type="button"
              className={docView === 'editor' ? 'active' : ''}
              onClick={() => setDocView('editor')}
            >
              Текст
            </button>
            <button
              type="button"
              className={docView === 'diff' ? 'active' : ''}
              onClick={() => setDocView('diff')}
            >
              Изменения
            </button>
          </div>

          {docView === 'editor' ? (
            <Suspense fallback={<p className="hint">Загрузка редактора…</p>}>
              <DocumentEditor
                workType={documentWorkType}
                contentDraft={displayPatch.content_draft}
                structureOutline={displayPatch.structure_outline}
                critiqueNotes={displayPatch.critique_notes}
                citationIssues={displayPatch.citation_issues}
                styleIssues={displayPatch.style_issues}
                truncated={displayPatch.content_draft_truncated}
                writingActive={!isTimeTravel && activeAgent === 'writer'}
                highlightQuery={outlineHighlight}
              />
            </Suspense>
          ) : (
            <DraftDiffPanel jobId={jobId} />
          )}

          {displayPatch.structure_outline && (
            <StructureOutlineNav
              outline={displayPatch.structure_outline}
              onSelectLine={setOutlineHighlight}
            />
          )}

          {hasDraft && !isTimeTravel && (
            <div className="doc-export-row">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={exportingLatex}
                onClick={exportLatex}
              >
                {exportingLatex ? 'Экспорт…' : 'Скачать LaTeX (.tex)'}
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'inspector' && (
        <div className="doc-inspector-body doc-inspector-body--scroll">
          {streamError && <div className="alert alert-error">{streamError}</div>}

          <section className="inspector-section">
            <h3>Обзор проекта</h3>
            <InspectorOverview
              job={job}
              statePatch={statePatch}
              activeAgent={activeAgent}
              steps={steps}
            />
          </section>

          <section className="inspector-section">
            <h3>{selectedNodeId || inspectStep ? 'Выбранный агент' : 'Детали агента'}</h3>
            <AgentInspectorSection
              selectedNodeId={selectedNodeId}
              inspectStep={inspectStep}
              statePatch={statePatch}
              rerunEnabled={rerunEnabled}
              onRequestRerun={onRequestRerun}
            />
          </section>

          {revisionTurns.length > 0 && (
            <section className="inspector-section">
              <h3>
                Правки текста
                <span className="inspector-section__badge">
                  {revisionTurns[revisionTurns.length - 1]?.round ?? 0}/
                  {statePatch.max_revisions ?? 3}
                </span>
              </h3>
              <RevisionDialogue steps={steps} maxRounds={statePatch.max_revisions ?? 3} hideTitle />
            </section>
          )}

          <section className="inspector-section">
            <h3>Библиография</h3>
            <BibliographyReportPanel jobId={jobId} hasDraft={hasDraft} />
          </section>

          <section className="inspector-section">
            <h3>Исходные материалы</h3>
            <SharedMemoryPanel inputs={context?.inputs ?? []} loading={loading} error={error} />
          </section>

          <section className="inspector-section">
            <h3>История версий</h3>
            <CheckpointPanel
              jobId={jobId}
              jobStatus={job?.status}
              selectedCheckpointId={selectedCheckpointId}
              onPreview={(item, patch) =>
                onCheckpointPreview(
                  item.checkpoint_id,
                  patch,
                  `Версия ${item.index + 1}`,
                )
              }
              onClearPreview={onClearTimeTravel}
              applyEvent={applyEvent}
            />
          </section>

          <section className="inspector-section">
            <h3>Расход ресурсов</h3>
            <SessionMetricsPanel statePatch={statePatch} />
          </section>
        </div>
      )}
    </div>
  )
}
