import { useEffect, useState } from 'react'
import type { AssignmentMode } from '@/domain/jobs/types'
import { AppIcon } from '@/presentation/icons'
import { FileDrop } from './FileDrop'
import { MultiFileDrop } from './MultiFileDrop'

interface Props {
  loading: boolean
  error: string
  onSubmit: (form: FormData) => void
  initialTopic?: string
  initialProjectName?: string
}

const STEPS = [
  { id: 1, label: 'Материалы' },
  { id: 2, label: 'Данные' },
  { id: 3, label: 'Запуск' },
] as const

function buildFormData(state: {
  projectName: string
  assignmentText: string
  variant: string
  studentGroup: string
  studentName: string
  teacherName: string
  topic: string
  assignmentMode: AssignmentMode
  assignmentFile: File | null
  materialFiles: File[]
}): FormData {
  const fd = new FormData()
  fd.append('work_type', 'auto')
  fd.append('project_name', state.projectName)
  fd.append('student_group', state.studentGroup)
  fd.append('student_name', state.studentName)
  fd.append('teacher_name', state.teacherName)
  fd.append('assignment_variant', state.variant)
  fd.append('topic', state.topic)
  if (state.assignmentMode === 'text') {
    fd.append('assignment_text', state.assignmentText)
  } else if (state.assignmentFile) {
    fd.append('assignment', state.assignmentFile)
  }
  for (const file of state.materialFiles) {
    fd.append('materials', file)
  }
  return fd
}

export function JobForm({
  loading,
  error,
  onSubmit,
  initialTopic = '',
  initialProjectName = 'MyWork',
}: Props) {
  const [step, setStep] = useState(1)
  const [stepError, setStepError] = useState('')

  const [assignmentMode, setAssignmentMode] = useState<AssignmentMode>('file')
  const [projectName, setProjectName] = useState(initialProjectName)
  const [assignmentText, setAssignmentText] = useState('')
  const [variant, setVariant] = useState('')
  const [studentGroup, setStudentGroup] = useState('')
  const [studentName, setStudentName] = useState('')
  const [teacherName, setTeacherName] = useState('')
  const [topic, setTopic] = useState(initialTopic)
  const [assignmentFile, setAssignmentFile] = useState<File | null>(null)
  const [materialFiles, setMaterialFiles] = useState<File[]>([])

  useEffect(() => {
    setTopic(initialTopic)
    setProjectName(initialProjectName)
  }, [initialTopic, initialProjectName])

  const formState = {
    projectName,
    assignmentText,
    variant,
    studentGroup,
    studentName,
    teacherName,
    topic,
    assignmentMode,
    assignmentFile,
    materialFiles,
  }

  const hasMaterials =
    materialFiles.length > 0 ||
    (assignmentMode === 'file' && assignmentFile) ||
    (assignmentMode === 'text' && assignmentText.trim())

  const validateStep = (target: number): string => {
    if (target >= 2 && !hasMaterials) {
      return 'Загрузите материалы или укажите текст задания'
    }
    if (target >= 3 && !projectName.trim()) {
      return 'Укажите имя проекта'
    }
    return ''
  }

  const goNext = () => {
    const err = validateStep(step + 1)
    if (err) {
      setStepError(err)
      return
    }
    setStepError('')
    setStep((s) => Math.min(s + 1, 3))
  }

  const goBack = () => {
    setStepError('')
    setStep((s) => Math.max(s - 1, 1))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const err = validateStep(3)
    if (err) {
      setStepError(err)
      return
    }
    onSubmit(buildFormData(formState))
  }

  const assignmentSummary =
    materialFiles.length > 0
      ? `${materialFiles.length} файл(ов)`
      : assignmentMode === 'file'
        ? assignmentFile?.name ?? '—'
        : assignmentText.trim()
          ? `Текст (${assignmentText.trim().length} симв.)`
          : '—'

  return (
    <section className="job-wizard">
      <nav className="wizard-steps" aria-label="Шаги создания работы">
        {STEPS.map((item, index) => {
          const done = step > item.id
          const active = step === item.id
          return (
            <div
              key={item.id}
              className={`wizard-step${active ? ' wizard-step--active' : ''}${done ? ' wizard-step--done' : ''}`}
            >
              <span className="wizard-step__num">
                {done ? <AppIcon name="check" size={14} strokeWidth={2.5} /> : item.id}
              </span>
              <span className="wizard-step__label">{item.label}</span>
              {index < STEPS.length - 1 && <span className="wizard-step__line" aria-hidden />}
            </div>
          )
        })}
      </nav>

      <div className="job-wizard__card card">
        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div className="wizard-panel">
              <header className="wizard-panel__header">
                <h2>Исходные материалы</h2>
                <p>
                  Загрузите задание, пример курсовой и ГОСТ/методичку (можно одним пакетом
                  файлов). Planner разметит роли, извлечёт правила и соберёт команду агентов.
                </p>
              </header>

              <MultiFileDrop
                label="Материалы работы"
                accept=".pdf,.docx,.txt,.md,.rtf,.xlsx,.xls"
                onChange={setMaterialFiles}
                hint="DOCX, PDF, TXT, Excel. Задание + пример + ГОСТ/методичка — всё сразу."
              />

              <details className="wizard-optional">
                <summary>Или укажите задание отдельно (файл / текст)</summary>
                <div className="wizard-section">
                  <div className="wizard-section__head">
                    <h3>Задание</h3>
                    <div className="segmented">
                      <button
                        type="button"
                        className={assignmentMode === 'file' ? 'active' : ''}
                        onClick={() => setAssignmentMode('file')}
                      >
                        Файл
                      </button>
                      <button
                        type="button"
                        className={assignmentMode === 'text' ? 'active' : ''}
                        onClick={() => setAssignmentMode('text')}
                      >
                        Текст
                      </button>
                    </div>
                  </div>

                  {assignmentMode === 'file' ? (
                    <FileDrop
                      label="Файл задания"
                      accept=".pdf,.docx,.txt,.md,.rtf"
                      compact
                      onChange={setAssignmentFile}
                      hint="Если задание уже в общем пакете материалов — можно не загружать."
                    />
                  ) : (
                    <div className="field">
                      <label htmlFor="assignment_text">Текст задания</label>
                      <textarea
                        id="assignment_text"
                        rows={6}
                        placeholder="Вставьте формулировку задания…"
                        value={assignmentText}
                        onChange={(e) => setAssignmentText(e.target.value)}
                      />
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}

          {step === 2 && (
            <div className="wizard-panel">
              <header className="wizard-panel__header">
                <h2>Данные для титульного листа</h2>
                <p>Можно пропустить пустые поля — Planner извлечёт недостающее из материалов.</p>
              </header>

              <div className="field">
                <label htmlFor="topic">Тема работы</label>
                <input
                  id="topic"
                  type="text"
                  autoComplete="off"
                  placeholder="Если знаете тему — укажите; иначе Planner определит из задания"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="project_name">Имя проекта</label>
                <input
                  id="project_name"
                  type="text"
                  autoComplete="off"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
                <p className="hint">Папка проекта в data/projects/</p>
              </div>

              <div className="grid-2">
                <div className="field">
                  <label htmlFor="student_group">Группа</label>
                  <input
                    id="student_group"
                    type="text"
                    autoComplete="off"
                    placeholder="473601"
                    value={studentGroup}
                    onChange={(e) => setStudentGroup(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="variant">Вариант</label>
                  <input
                    id="variant"
                    type="text"
                    autoComplete="off"
                    placeholder="Например: 5"
                    value={variant}
                    onChange={(e) => setVariant(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid-2">
                <div className="field">
                  <label htmlFor="student_name">ФИО студента</label>
                  <input
                    id="student_name"
                    type="text"
                    autoComplete="name"
                    placeholder="И. С. Демидов"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="teacher_name">Преподаватель</label>
                  <input
                    id="teacher_name"
                    type="text"
                    autoComplete="off"
                    placeholder="Е. И. Пономарева"
                    value={teacherName}
                    onChange={(e) => setTeacherName(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="wizard-panel">
              <header className="wizard-panel__header">
                <h2>Проверьте и запустите</h2>
                <p>Planner проанализирует материалы, соберёт команду агентов и покажет её на согласование.</p>
              </header>

              <dl className="review-list">
                {topic.trim() && (
                  <div className="review-item">
                    <dt>Тема (если указали)</dt>
                    <dd>{topic.trim()}</dd>
                  </div>
                )}
                <div className="review-item">
                  <dt>Имя проекта</dt>
                  <dd>{projectName || '—'}</dd>
                </div>
                <div className="review-item">
                  <dt>Материалы</dt>
                  <dd className="review-item__file">{assignmentSummary}</dd>
                </div>
                {(studentGroup || studentName || teacherName || variant) && (
                  <div className="review-item review-item--block">
                    <dt>Титульный лист</dt>
                    <dd>
                      <ul className="review-meta">
                        {studentGroup && <li>Группа: {studentGroup}</li>}
                        {variant && <li>Вариант: {variant}</li>}
                        {studentName && <li>Студент: {studentName}</li>}
                        {teacherName && <li>Преподаватель: {teacherName}</li>}
                      </ul>
                    </dd>
                  </div>
                )}
              </dl>

              <div className="review-flow">
                <span className="review-flow__label">Далее</span>
                <div className="review-flow__steps">
                  <span>Анализ материалов</span>
                  <span className="review-flow__arrow">→</span>
                  <span>Согласование команды</span>
                  <span className="review-flow__arrow">→</span>
                  <span>Готовый docx + ZIP</span>
                </div>
              </div>
            </div>
          )}

          {(stepError || error) && (
            <div className="alert alert-error">{stepError || error}</div>
          )}

          <div className="wizard-actions">
            {step > 1 && (
              <button type="button" className="btn btn-secondary" onClick={goBack} disabled={loading}>
                Назад
              </button>
            )}
            {step < 3 ? (
              <button type="button" className="btn btn-primary" onClick={goNext}>
                Далее
              </button>
            ) : (
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Запуск…' : 'Запустить агентов'}
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  )
}
