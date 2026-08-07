import { WORKFLOW_STEPS } from '@/domain/landing/demoPresets'
import { AppIcon } from '@/presentation/icons'

interface Props {
  onEnterApp: () => void
}

export function WorkflowSection({ onEnterApp }: Props) {
  return (
    <section className="landing-section landing-workflow" id="how">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Процесс</p>
        <h2>От загрузки до готового отчёта</h2>
        <p className="landing-section__lead">
          Загрузите материалы — система сама определит тип работы, соберёт команду агентов
          и проведёт вас через согласование до финального документа.
        </p>
      </div>

      <div className="workflow-grid">
        {WORKFLOW_STEPS.map((item, index) => (
          <article key={item.step} className="workflow-card">
            <div className="workflow-card__head">
              <span className="workflow-card__num">{item.step}</span>
              {'badge' in item && item.badge && (
                <span className="workflow-card__badge">
                  <AppIcon name="sparkles" size={12} />
                  {item.badge}
                </span>
              )}
            </div>
            {index < WORKFLOW_STEPS.length - 1 && (
              <span className="workflow-card__connector" aria-hidden />
            )}
            <h3>{item.title}</h3>
            <p>{item.text}</p>
          </article>
        ))}
      </div>

      <div className="landing-workflow__cta">
        <button type="button" className="btn btn-primary btn-lg" onClick={onEnterApp}>
          Попробовать в приложении
        </button>
      </div>
    </section>
  )
}
