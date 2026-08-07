import type { JobStep } from '@/domain/jobs/types'

export interface DialogueTurn {
  agent: 'writer' | 'critiquer'
  message: string
  detail?: string
  round: number
}

/** Pure mapper: step log → Writer ↔ Reviewer dialogue. */
export function buildRevisionDialogue(steps: JobStep[]): DialogueTurn[] {
  const turns: DialogueTurn[] = []
  let round = 0

  for (const step of steps) {
    if (step.agent === 'critiquer') {
      round += 1
      turns.push({
        agent: 'critiquer',
        message: step.message,
        detail: step.detail,
        round,
      })
      continue
    }
    if (
      step.agent === 'writer' &&
      turns.length > 0 &&
      turns[turns.length - 1].agent === 'critiquer'
    ) {
      turns.push({
        agent: 'writer',
        message: step.message,
        detail: step.detail,
        round,
      })
    }
  }

  return turns
}

export function countRevisionRounds(steps: JobStep[]): number {
  return steps.filter((step) => step.agent === 'critiquer').length
}
