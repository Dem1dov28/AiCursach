import type { DiffLine } from '@/domain/jobs/types'
import { useDraftDiff } from '@/application/document/useDraftDiff'

interface Props {
  jobId: string
}

function DiffView({ lines }: { lines: DiffLine[] }) {
  if (lines.length === 0) {
    return <p className="hint">Нет различий между выбранными версиями.</p>
  }

  return (
    <pre className="draft-diff">
      {lines.map((line, index) => (
        <div key={index} className={`draft-diff__line draft-diff__line--${line.kind}`}>
          {line.text || '\u00a0'}
        </div>
      ))}
    </pre>
  )
}

export function DraftDiffPanel({ jobId }: Props) {
  const { snapshots, fromId, toId, setFromId, setToId, diff, loading, error } =
    useDraftDiff(jobId)

  if (snapshots.length === 0 && !error) {
    return <p className="hint">Snapshots появятся после первого прохода Writer.</p>
  }

  return (
    <section className="draft-diff-panel">
      {error && <div className="alert alert-error">{error}</div>}
      <div className="draft-diff-controls">
        <label>
          От
          <select
            value={fromId}
            onChange={(event) => setFromId(Number(event.target.value))}
          >
            {snapshots.map((snap) => (
              <option key={snap.id} value={snap.id}>
                #{snap.id} · шаг {snap.step}
              </option>
            ))}
          </select>
        </label>
        <label>
          До
          <select value={toId} onChange={(event) => setToId(Number(event.target.value))}>
            {snapshots.map((snap) => (
              <option key={snap.id} value={snap.id}>
                #{snap.id} · шаг {snap.step}
              </option>
            ))}
          </select>
        </label>
      </div>
      {loading && <p className="hint">Сравнение…</p>}
      {diff && !loading && <DiffView lines={diff.lines} />}
    </section>
  )
}
