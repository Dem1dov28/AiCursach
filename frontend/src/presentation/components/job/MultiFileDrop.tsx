import { useRef, useState } from 'react'
import { AppIcon } from '@/presentation/icons'

interface Props {
  label: string
  accept: string
  hint?: string
  onChange: (files: File[]) => void
}

export function MultiFileDrop({ label, accept, hint, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])
  const [drag, setDrag] = useState(false)

  const pick = (next: File[]) => {
    setFiles(next)
    onChange(next)
  }

  const addFiles = (incoming: FileList | File[]) => {
    const list = Array.from(incoming)
    if (!list.length) return
    pick([...files, ...list])
  }

  const removeAt = (index: number) => {
    pick(files.filter((_, i) => i !== index))
  }

  const zoneClass = [
    'file-zone',
    'file-zone--compact',
    files.length ? 'file-zone--filled' : '',
    drag ? 'dragover' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="field">
      <label>
        {label}
        <span className="req"> *</span>
      </label>
      <div
        className={zoneClass}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          addFiles(e.dataTransfer.files)
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple
          onChange={(e) => addFiles(e.target.files ?? [])}
        />
        <div className="file-zone__row">
          <span className="file-zone__icon">
            <AppIcon name={files.length ? 'library' : 'folder-open'} size={22} />
          </span>
          <div className="file-zone__body">
            {files.length ? (
              <span className="filename">{files.length} файл(ов) выбрано</span>
            ) : (
              <span className="file-zone__placeholder">
                Перетащите задание, пример, ГОСТ/методичку — всё сразу
              </span>
            )}
          </div>
          <span className="file-zone__action">{files.length ? 'Добавить' : 'Обзор'}</span>
        </div>
      </div>
      {files.length > 0 && (
        <ul className="materials-list">
          {files.map((file, index) => (
            <li key={`${file.name}-${index}`}>
              <span>{file.name}</span>
              <button type="button" className="btn-link" onClick={() => removeAt(index)}>
                Удалить
              </button>
            </li>
          ))}
        </ul>
      )}
      {hint && <p className="hint">{hint}</p>}
    </div>
  )
}
