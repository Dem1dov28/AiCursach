import type { GraphTopologyDto } from '@/domain/graph/types'
import type { JobContext } from '@/domain/jobs/context'
import type {
  BibliographyReportResponse,
  CheckpointState,
  DraftDiff,
  DraftSnapshot,
  Health,
  Job,
  JobCheckpoint,
  JobMetrics,
  JobStatePatch,
} from '@/domain/jobs/types'

export type JobSettingsUpdate = {
  max_revisions?: number
  autonomy_level?: string
  confidence_threshold?: number
  enable_style_polisher?: boolean
  enable_bibliography_verifier?: boolean
}

export interface JobGateway {
  fetchHealth(): Promise<Health>
  createJob(form: FormData): Promise<{ job_id: string; status: string }>
  fetchJobs(limit?: number, offset?: number): Promise<Array<Record<string, unknown>>>
  fetchJob(jobId: string): Promise<Job>
  fetchJobContext(jobId: string): Promise<JobContext>
  streamJobUrl(jobId: string): string
  downloadUrl(jobId: string): string
  downloadJob(jobId: string): Promise<void>
  retryJob(jobId: string): Promise<unknown>
  pauseJob(jobId: string): Promise<{ ok: boolean; job_id: string; status: string }>
  deleteJob(jobId: string): Promise<{ ok: boolean; job_id: string }>
  resumeJob(jobId: string, structureOutline: string): Promise<unknown>
  rerunJob(
    jobId: string,
    fromNode: string,
    structureOutline?: string,
    promptOverride?: string,
  ): Promise<unknown>
  saveJobPlan(
    jobId: string,
    structureOutline: string,
    topic?: string,
  ): Promise<{ job_id: string; patch: JobStatePatch }>
  approveTeam(jobId: string, pipeline: string[]): Promise<unknown>
  submitClarificationAnswer(
    jobId: string,
    selectedOption: string,
    customText: string,
  ): Promise<unknown>
}

export interface JobFeaturesGateway {
  fetchJobMetrics(jobId: string): Promise<JobMetrics>
  fetchCheckpoints(jobId: string): Promise<JobCheckpoint[]>
  fetchCheckpointState(jobId: string, checkpointId: string): Promise<CheckpointState>
  restoreCheckpoint(
    jobId: string,
    checkpointId: string,
  ): Promise<{ ok: boolean; patch: JobStatePatch }>
  fetchDraftSnapshots(jobId: string): Promise<DraftSnapshot[]>
  fetchDraftDiff(jobId: string, fromId: number, toId: number): Promise<DraftDiff>
  downloadLatex(jobId: string): Promise<void>
  fetchBibliographyReport(jobId: string): Promise<BibliographyReportResponse>
  updateJobSettings(jobId: string, settings: JobSettingsUpdate): Promise<unknown>
}

export interface GraphGateway {
  fetchGraphTopology(workType: string, pipeline?: string[]): Promise<GraphTopologyDto>
}
