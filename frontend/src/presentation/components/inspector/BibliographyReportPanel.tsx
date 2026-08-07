import { useBibliographyReport } from '@/application/jobs/useBibliographyReport'
import { AppIcon } from '@/presentation/icons'

interface Props {
  jobId: string
  hasDraft: boolean
}

const DOI_LABELS: Record<string, string> = {
  ok: 'DOI проверен',
  present: 'DOI указан',
  missing: 'Без DOI',
  invalid: 'DOI не найден',
  mismatch: 'DOI не совпадает',
  unchecked: 'Не проверялся',
}

function scoreClass(score: number): string {
  if (score >= 80) return 'bib-report__score--good'
  if (score >= 50) return 'bib-report__score--warn'
  return 'bib-report__score--bad'
}

export function BibliographyReportPanel({ jobId, hasDraft }: Props) {
  const { data, loading, error, reload } = useBibliographyReport(jobId, hasDraft)

  if (!hasDraft) {
    return <p className="hint">Отчёт появится после того, как Writer сформирует черновик.</p>
  }

  if (loading && !data) {
    return <p className="hint">Загрузка отчёта по библиографии…</p>
  }

  if (error) {
    return (
      <div className="bib-report">
        <div className="alert alert-error">{error}</div>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => void reload()}>
          Повторить
        </button>
      </div>
    )
  }

  if (!data?.report) return null

  const { summary, sources, issues_by_category } = data.report

  return (
    <div className="bib-report">
      <div className="bib-report__header">
        <div className={`bib-report__score ${scoreClass(summary.score)}`}>
          <span className="bib-report__score-value">{summary.score}</span>
          <span className="bib-report__score-label">качество источников</span>
        </div>
        <div className="bib-report__stats">
          <div>
            <strong>{summary.total_sources}</strong>
            <span>источников</span>
          </div>
          <div>
            <strong>{summary.citations_in_text}</strong>
            <span>ссылок в тексте</span>
          </div>
          <div>
            <strong>{summary.doi_verified}</strong>
            <span>DOI OK</span>
          </div>
          <div>
            <strong>{summary.issues_total}</strong>
            <span>замечаний</span>
          </div>
        </div>
        {data.bibliography_verified && (
          <span className="bib-report__badge bib-report__badge--ok">
            Bibliography
            <AppIcon name="check" size={14} strokeWidth={2.5} />
          </span>
        )}
      </div>

      {(summary.orphan_citations > 0 || summary.doi_failed > 0) && (
        <div className="bib-report__alerts">
          {summary.orphan_citations > 0 && (
            <p className="bib-report__alert">
              {summary.orphan_citations} ссылок в тексте без записи в списке источников
            </p>
          )}
          {summary.doi_failed > 0 && (
            <p className="bib-report__alert">
              {summary.doi_failed} источников с проблемным DOI (CrossRef)
            </p>
          )}
        </div>
      )}

      {sources.length > 0 && (
        <div className="bib-report__sources">
          <h4>Список источников</h4>
          <ul>
            {sources.map((source) => (
              <li
                key={source.index}
                className={`bib-report__source${source.issues.length ? ' bib-report__source--issue' : ''}`}
              >
                <span className="bib-report__source-index">[{source.index}]</span>
                <span className="bib-report__source-text">{source.text}</span>
                <span className={`bib-report__doi bib-report__doi--${source.doi_status}`}>
                  {DOI_LABELS[source.doi_status] ?? source.doi_status}
                </span>
                {!source.cited_in_text && (
                  <span className="bib-report__tag">не цитируется</span>
                )}
                {source.issues.map((issue) => (
                  <span key={`${source.index}-${issue.reason}`} className="bib-report__issue">
                    {issue.reason}
                  </span>
                ))}
              </li>
            ))}
          </ul>
        </div>
      )}

      {Object.entries(issues_by_category).some(([, items]) => items.length > 0) && (
        <div className="bib-report__categories">
          <h4>Замечания по категориям</h4>
          {(['citation', 'doi', 'context', 'other'] as const).map((key) => {
            const items = issues_by_category[key]
            if (!items?.length) return null
            const labels: Record<string, string> = {
              citation: 'Ссылки [N]',
              doi: 'DOI / CrossRef',
              context: 'Соответствие материалам',
              other: 'Прочее',
            }
            return (
              <details key={key} className="bib-report__category" open={key === 'doi'}>
                <summary>
                  {labels[key]} ({items.length})
                </summary>
                <ul>
                  {items.map((issue) => (
                    <li key={`${issue.citation}-${issue.reason}`}>
                      <strong>{issue.citation}</strong> — {issue.reason}
                    </li>
                  ))}
                </ul>
              </details>
            )
          })}
        </div>
      )}

      <button
        type="button"
        className="btn btn-secondary btn-sm bib-report__refresh"
        disabled={loading}
        onClick={() => void reload()}
      >
        {loading ? 'Обновление…' : 'Обновить отчёт'}
      </button>
    </div>
  )
}
