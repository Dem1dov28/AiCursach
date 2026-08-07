import { JobForm } from '@/presentation/components/job/JobForm'

interface Props {
  open: boolean
  title: string
  loading: boolean
  error: string
  initialTopic?: string
  initialProjectName?: string
  onClose: () => void
  onSubmit: (form: FormData) => void
}

export function JobFormModal({
  open,
  title,
  loading,
  error,
  initialTopic,
  initialProjectName,
  onClose,
  onSubmit,
}: Props) {
  if (!open) return null

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-card modal-card--wide">
        <div className="modal-card__head">
          <h3>{title}</h3>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            ✕
          </button>
        </div>
        <JobForm
          loading={loading}
          error={error}
          onSubmit={onSubmit}
          initialTopic={initialTopic}
          initialProjectName={initialProjectName}
        />
      </div>
    </div>
  )
}
