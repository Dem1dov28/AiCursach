import type { Job, JobStatePatch, JobStep, StreamEvent } from '@/domain/jobs/types'

export interface JobStreamState {
  job: Job | null
  steps: JobStep[]
  statePatch: JobStatePatch
  connected: boolean
  error: string
  activeAgent: string | null
  awaitingPlanApproval: boolean
  awaitingClarification: boolean
  awaitingTeamApproval: boolean
  clarificationAgent: string | null
  applyEvent?: (event: StreamEvent) => void
}

export const EMPTY_JOB_STREAM: JobStreamState = {
  job: null,
  steps: [],
  statePatch: {},
  connected: false,
  error: '',
  activeAgent: null,
  awaitingPlanApproval: false,
  awaitingClarification: false,
  awaitingTeamApproval: false,
  clarificationAgent: null,
}

/** Pure reducer for SSE events. */
export function applyStreamEvent(
  state: JobStreamState,
  event: StreamEvent,
): JobStreamState {
  switch (event.type) {
    case 'snapshot': {
      const patch = event.job.state_patch ?? {}
      return {
        ...state,
        job: event.job,
        steps: event.job.steps ?? [],
        statePatch: { ...state.statePatch, ...patch },
        activeAgent: null,
        awaitingPlanApproval: Boolean(patch.awaiting_plan_approval),
        awaitingClarification: Boolean(patch.awaiting_clarification),
        awaitingTeamApproval: Boolean(patch.awaiting_team_approval),
        clarificationAgent: patch.pending_clarification?.agent ?? null,
      }
    }
    case 'status': {
      const patch = state.statePatch
      const paused = event.status === 'paused'
      return {
        ...state,
        job: state.job ? { ...state.job, status: event.status } : state.job,
        awaitingPlanApproval: paused
          ? Boolean(patch.awaiting_plan_approval) &&
            !patch.awaiting_clarification &&
            !patch.awaiting_team_approval
          : false,
        awaitingClarification: paused ? Boolean(patch.awaiting_clarification) : false,
        awaitingTeamApproval: paused ? Boolean(patch.awaiting_team_approval) : false,
        clarificationAgent: paused
          ? patch.pending_clarification?.agent ?? state.clarificationAgent
          : null,
      }
    }
    case 'step':
      return {
        ...state,
        activeAgent: event.agent,
        steps: state.steps.some((item) => item.step === event.step)
          ? state.steps
          : [
              ...state.steps,
              {
                step: event.step,
                agent: event.agent,
                message: event.message,
                detail: event.detail,
              },
            ],
      }
    case 'state_patch': {
      const paused = state.job?.status === 'paused' || state.awaitingClarification
      return {
        ...state,
        statePatch: { ...state.statePatch, ...event.patch },
        awaitingPlanApproval: Boolean(event.patch.awaiting_plan_approval),
        awaitingClarification: paused
          ? Boolean(event.patch.awaiting_clarification)
          : state.awaitingClarification,
        awaitingTeamApproval: paused
          ? Boolean(event.patch.awaiting_team_approval)
          : state.awaitingTeamApproval,
        clarificationAgent: event.patch.pending_clarification?.agent ?? state.clarificationAgent,
      }
    }
    case 'breakpoint':
      return {
        ...state,
        statePatch: {
          ...state.statePatch,
          ...event.patch,
          ...(event.clarification ? { pending_clarification: event.clarification } : {}),
          ...(event.team ? { pending_team: event.team } : {}),
        },
        awaitingPlanApproval: event.reason === 'plan_approval',
        awaitingClarification: event.reason === 'clarification',
        awaitingTeamApproval: event.reason === 'team_approval',
        clarificationAgent:
          event.reason === 'clarification' ? event.clarification?.agent ?? null : null,
        job: state.job
          ? {
              ...state.job,
              status: 'paused',
            }
          : state.job,
      }
    case 'done':
      return {
        ...state,
        job: event.job,
        steps: event.job.steps ?? [],
        activeAgent: null,
        awaitingPlanApproval: false,
        error: event.error ?? state.error,
      }
    default:
      return state
  }
}
