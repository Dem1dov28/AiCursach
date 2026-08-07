import { AppIcon } from '@/presentation/icons'

interface Props {
  onStart: () => void
}

const AGENTS = ['Supervisor', 'Analyzer', 'Team Planner', 'Writer', 'Reviewer', 'DocxBuilder']

export function CreateProjectCard({ onStart }: Props) {
  return (
    <section className="dashboard-create">
      <article className="template-card template-card--landing template-card--solo dashboard-create-card">
        <div className="template-card__top">
          <div className="template-card__icon" aria-hidden>
            <AppIcon name="sparkles" size={22} />
          </div>
          <div>
            <p className="landing-eyebrow">Авторежим</p>
            <h3>Новый проект</h3>
          </div>
        </div>
        <p className="template-card__desc">
          Загрузите задание и методичку — Supervisor определит лабораторную или курсовую,
          а Team Planner подберёт нужных агентов без ручного выбора шаблона.
        </p>
        <ul className="template-card__agents" aria-label="Команда агентов">
          {AGENTS.map((agent) => (
            <li key={agent}>{agent}</li>
          ))}
        </ul>
        <button type="button" className="btn btn-primary template-card__btn" onClick={onStart}>
          Создать проект
        </button>
      </article>
    </section>
  )
}
