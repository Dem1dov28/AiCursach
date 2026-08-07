import type { StyleIssue } from '@/domain/jobs/types'

interface Props {
  issues: StyleIssue[]
}

export function StyleIssuesPanel({ issues }: Props) {
  if (issues.length === 0) return null

  return (
    <div className="style-issues">
      <strong>Шаблонные фразы</strong>
      <ul>
        {issues.map((issue) => (
          <li key={issue.phrase}>
            «{issue.phrase}» ×{issue.count} — {issue.reason}
          </li>
        ))}
      </ul>
    </div>
  )
}
