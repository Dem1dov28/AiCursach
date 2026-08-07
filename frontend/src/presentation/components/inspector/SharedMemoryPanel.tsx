import type { JobInputFile } from '@/domain/jobs/context'

const KIND_LABELS: Record<string, string> = {
  assignment: 'Задание',
  example: 'Пример работы',
  methodical: 'Методичка',
}

interface Props {
  inputs: JobInputFile[]
  loading?: boolean
  error?: string
}

export function SharedMemoryPanel({ inputs, loading, error }: Props) {
  if (loading) return <p className="hint">Загрузка материалов…</p>
  if (error) return <div className="alert alert-error">{error}</div>

  if (inputs.length === 0) {
    return <p className="hint">Файлы не прикреплены — использовался только текст из формы.</p>
  }

  return (
    <div className="shared-memory">
      {inputs.map((file) => (
        <article key={file.kind} className="memory-file">
          <header className="memory-file__header">
            <strong>{KIND_LABELS[file.kind] ?? file.kind}</strong>
            <span className="memory-file__name">{file.filename}</span>
          </header>
          {file.size_bytes > 0 && (
            <span className="hint">{(file.size_bytes / 1024).toFixed(1)} КБ</span>
          )}
          {file.preview ? (
            <p className="memory-file__preview">{file.preview}</p>
          ) : (
            <p className="hint">Текст не извлечён (бинарный файл)</p>
          )}
        </article>
      ))}
    </div>
  )
}
