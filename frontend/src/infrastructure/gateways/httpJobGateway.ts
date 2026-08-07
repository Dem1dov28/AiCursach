import type {
  GraphGateway,
  JobFeaturesGateway,
  JobGateway,
} from '@/application/ports/jobGateway'
import * as graphClient from '@/infrastructure/api/graphClient'
import * as jobClient from '@/infrastructure/api/jobClient'
import * as jobFeaturesClient from '@/infrastructure/api/jobFeaturesClient'

export const httpJobGateway: JobGateway = {
  fetchHealth: jobClient.fetchHealth,
  createJob: jobClient.createJob,
  fetchJobs: jobClient.fetchJobs,
  fetchJob: jobClient.fetchJob,
  fetchJobContext: jobClient.fetchJobContext,
  streamJobUrl: jobClient.streamJobUrl,
  downloadUrl: jobClient.downloadUrl,
  downloadJob: jobClient.downloadJob,
  retryJob: jobClient.retryJob,
  pauseJob: jobClient.pauseJob,
  deleteJob: jobClient.deleteJob,
  resumeJob: jobClient.resumeJob,
  rerunJob: jobClient.rerunJob,
  saveJobPlan: jobClient.saveJobPlan,
  approveTeam: jobClient.approveTeam,
  submitClarificationAnswer: jobClient.submitClarificationAnswer,
}

export const httpJobFeaturesGateway: JobFeaturesGateway = {
  fetchJobMetrics: jobFeaturesClient.fetchJobMetrics,
  fetchCheckpoints: jobFeaturesClient.fetchCheckpoints,
  fetchCheckpointState: jobFeaturesClient.fetchCheckpointState,
  restoreCheckpoint: jobFeaturesClient.restoreCheckpoint,
  fetchDraftSnapshots: jobFeaturesClient.fetchDraftSnapshots,
  fetchDraftDiff: jobFeaturesClient.fetchDraftDiff,
  downloadLatex: jobFeaturesClient.downloadLatex,
  fetchBibliographyReport: jobFeaturesClient.fetchBibliographyReport,
  updateJobSettings: jobFeaturesClient.updateJobSettings,
}

export const httpGraphGateway: GraphGateway = {
  fetchGraphTopology: graphClient.fetchGraphTopology,
}
