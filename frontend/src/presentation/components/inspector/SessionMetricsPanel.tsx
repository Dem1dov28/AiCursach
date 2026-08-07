import { useState } from 'react'
import { AGENT_LABELS } from '@/domain/jobs/agentLabels'
import type { JobStatePatch } from '@/domain/jobs/types'

interface Props {
  statePatch: JobStatePatch
}

export function SessionMetricsPanel({ statePatch }: Props) {
  const [expanded, setExpanded] = useState(false)
  const byAgent = statePatch.tokens_by_agent ?? {}
  const agents = Object.entries(byAgent).sort((a, b) => b[1].total - a[1].total)
  const tokensTotal =
    statePatch.tokens_total ??
    (statePatch.tokens_input ?? 0) + (statePatch.tokens_output ?? 0)
  const cost = statePatch.estimated_cost_usd

  if (agents.length === 0 && !tokensTotal) {
    return <p className="hint">Статистика появится после первых шагов с LLM.</p>
  }

  return (
    <div className="agent-metrics agent-metrics--compact">
      <p className="agent-metrics__summary">
        {tokensTotal > 0 && <span>{tokensTotal.toLocaleString('ru-RU')} токенов</span>}
        {cost != null && tokensTotal > 0 && ' · '}
        {cost != null && <span>≈ ${cost.toFixed(4)}</span>}
      </p>

      {agents.length > 0 && (
        <>
          <ul className="agent-metrics__top">
            {agents.slice(0, 3).map(([agent, usage]) => (
              <li key={agent}>
                <span>{AGENT_LABELS[agent] ?? agent}</span>
                <span className="hint">{usage.total.toLocaleString('ru-RU')}</span>
              </li>
            ))}
          </ul>

          {agents.length > 3 && (
            <button
              type="button"
              className="btn btn-ghost btn-sm agent-metrics__toggle"
              onClick={() => setExpanded((value) => !value)}
            >
              {expanded ? 'Скрыть детали' : 'Показать всех агентов'}
            </button>
          )}

          {expanded && (
            <table className="agent-metrics__table">
              <thead>
                <tr>
                  <th>Агент</th>
                  <th>Токены</th>
                </tr>
              </thead>
              <tbody>
                {agents.map(([agent, usage]) => (
                  <tr key={agent}>
                    <td>{AGENT_LABELS[agent] ?? agent}</td>
                    <td>{usage.total.toLocaleString('ru-RU')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  )
}
