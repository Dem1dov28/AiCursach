export type WorkType = 'auto' | 'lab' | 'coursework'
export type JobStatus = 'queued' | 'running' | 'paused' | 'completed' | 'failed'

export interface JobStep {
  step: number
  agent: string
  message: string
  detail?: string
}

export interface Job {
  id: string
  status: JobStatus
  created_at: string
  project_name: string
  work_type: WorkType
  topic: string
  custom_pipeline?: string[]
  steps: JobStep[]
  error: string
  has_download: boolean
  output_docx: string
  code_ok: boolean
  diagrams_count: number
  storage: string
  state_patch?: JobStatePatch
}

export interface CitationIssue {
  citation: string
  reason: string
}

export interface StyleIssue {
  phrase: string
  reason: string
  count: number
}

export interface BibliographySourceReport {
  index: number
  text: string
  doi: string
  doi_status: string
  cited_in_text: boolean
  issues: CitationIssue[]
}

export interface BibliographyReport {
  summary: {
    total_sources: number
    citations_in_text: number
    orphan_citations: number
    doi_verified: number
    doi_failed: number
    issues_total: number
    score: number
  }
  sources: BibliographySourceReport[]
  issues_by_category: Record<string, CitationIssue[]>
  citation_issues: CitationIssue[]
}

export interface BibliographyReportResponse {
  job_id: string
  ready: boolean
  message?: string
  bibliography_verified?: boolean
  report: BibliographyReport
}

export interface AgentTokenUsage {
  input: number
  output: number
  total: number
}

export type AutonomyLevel = 'full_auto' | 'interactive'

export interface ClarificationRequest {
  type?: string
  agent: string
  scenario?: string
  question: string
  options: string[]
  confidence?: number
}

export interface TaskBreakdownItem {
  task: string
  deliverable?: string
  agent: string
}

export interface TeamProposal {
  pipeline: string[]
  rationale: string
  task_breakdown: TaskBreakdownItem[]
  topic?: string
  detected_work_kind?: string
  discipline?: string
  structure_outline?: string
  work_brief_summary?: string
  structure_source?: string
}

export interface JobStatePatch {
  topic?: string
  structure_outline?: string
  content_draft?: string
  content_draft_truncated?: boolean
  critique_notes?: string
  revision_number?: number
  max_revisions?: number
  next_step?: string
  current_sub_task?: string
  awaiting_plan_approval?: boolean
  awaiting_clarification?: boolean
  awaiting_team_approval?: boolean
  pending_clarification?: ClarificationRequest
  pending_team?: TeamProposal
  custom_pipeline?: string[]
  team_rationale?: string
  task_breakdown?: TaskBreakdownItem[]
  detected_work_kind?: string
  discipline?: string
  work_brief?: string
  materials_roles?: Record<string, string>
  autonomy_level?: AutonomyLevel
  confidence_threshold?: number
  agent_confidence?: number
  citation_issues?: CitationIssue[]
  style_issues?: StyleIssue[]
  enable_style_polisher?: boolean
  enable_bibliography_verifier?: boolean
  tokens_input?: number
  tokens_output?: number
  tokens_total?: number
  tokens_by_agent?: Record<string, AgentTokenUsage>
  estimated_cost_usd?: number
}

export type StreamEvent =
  | { type: 'snapshot'; job: Job }
  | { type: 'status'; status: JobStatus }
  | { type: 'step'; step: number; agent: string; message: string; detail?: string }
  | { type: 'state_patch'; patch: JobStatePatch }
  | { type: 'breakpoint'; reason: string; patch: JobStatePatch; clarification?: ClarificationRequest; team?: TeamProposal }
  | { type: 'done'; status: JobStatus; job: Job; error?: string }
  | { type: 'heartbeat' }

export interface Health {
  ok: boolean
  llm_configured: boolean
  database: string
  database_ok: boolean
  database_error: string | null
}

export interface JobMetrics {
  job_id: string
  status: JobStatus
  revision_number: number
  max_revisions: number
  tokens_input?: number
  tokens_output?: number
  tokens_total?: number
  tokens_by_agent?: Record<string, AgentTokenUsage>
  estimated_cost_usd?: number
}

export interface JobCheckpoint {
  index: number
  checkpoint_id: string
  next_nodes: string[]
  topic: string
  next_step: string
  revision_number: number
  awaiting_plan_approval: boolean
  structure_outline_preview?: string
  has_content_draft?: boolean
  content_draft_chars?: number
  created_at?: string
}

export interface CheckpointState {
  checkpoint_id: string
  next_nodes: string[]
  state: JobStatePatch
  created_at?: string
}

export interface DraftSnapshot {
  id: number
  step: number
  agent: string
  created_at: string
}

export interface DiffLine {
  kind: 'add' | 'remove' | 'same'
  text: string
}

export interface DraftDiff {
  from: { id: number; step: number; agent: string }
  to: { id: number; step: number; agent: string }
  lines: DiffLine[]
}

export type AssignmentMode = 'file' | 'text'
