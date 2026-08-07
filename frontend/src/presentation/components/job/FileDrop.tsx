import { useRef, useState } from 'react'
import { AppIcon } from '@/presentation/icons'

interface Props {
  label: string
  accept: string
  required?: boolean
  hint?: string
  compact?: boolean
  onChange: (file: File | null) => void
}

export function FileDrop({ label, accept, required, hint, compact, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [name, setName] = useState('')
  const [drag, setDrag] = useState(false)

  const pick = (file: File | null) => {
    setName(file?.name ?? '')
    onChange(file)
  }

  const zoneClass = [
    'file-zone',
    compact ? 'file-zone--compact' : '',
    name ? 'file-zone--filled' : '',
    drag ? 'dragover' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="field">
      <label>
        {label}
        {required && <span className="req"> *</span>}
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
          pick(e.dataTransfer.files[0] ?? null)
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          required={required}
          onChange={(e) => pick(e.target.files?.[0] ?? null)}
        />
        {compact ? (
          <div className="file-zone__row">
            <span className="file-zone__icon">
              <AppIcon name={name ? 'file-text' : 'folder-open'} size={22} />
            </span>
            <div className="file-zone__body">
              {name ? (
                <span className="filename">{name}</span>
              ) : (
                <span className="file-zone__placeholder">Перетащите или нажмите для выбора</span>
              )}
            </div>
            <span className="file-zone__action">{name ? 'Заменить' : 'Обзор'}</span>
          </div>
        ) : (
          <>
            <div className="file-zone__icon-lg">
              <AppIcon name={name ? 'file-text' : 'folder-open'} size={28} />
            </div>
            <div className="hint">
              {name ? 'Нажмите, чтобы заменить' : 'Перетащите файл или нажмите'}
            </div>
            {name && <div className="filename">{name}</div>}
          </>
        )}
      </div>
      {hint && <p className="hint">{hint}</p>}
    </div>
  )
}
