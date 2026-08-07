import { buildRevisionDialogue } from '@/domain/workflow/buildRevisionDialogue'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { JobStep } from '@/domain/jobs/types'

interface Props {
  steps: JobStep[]
  maxRounds?: number
  hideTitle?: boolean
}

export function RevisionDialogue({ steps, maxRounds = 3, hideTitle = false }: Props) {
  const turns = buildRevisionDialogue(steps)
  if (turns.length === 0) return null

  const lastRound = turns[turns.length - 1]?.round ?? 0

  return (
    <section className="revision-dialogue">
      {!hideTitle && (
        <div className="revision-dialogue__header">
          <h3>Writer ↔ Reviewer</h3>
          <span className="revision-dialogue__rounds">
            {lastRound}/{maxRounds} итераций
          </span>
        </div>
      )}
      <ul className="revision-dialogue__list">
        {turns.map((turn, index) => (
          <li key={`${turn.round}-${turn.agent}-${index}`} className={`turn turn--${turn.agent}`}>
            <strong>{AGENT_LABELS[turn.agent] ?? turn.agent}</strong>
            <span>{turn.message}</span>
            {turn.detail && <pre>{turn.detail}</pre>}
          </li>
        ))}
      </ul>
    </section>
  )
}
