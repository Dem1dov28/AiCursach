import { FEATURE_CARDS } from '@/domain/landing/demoPresets'
import { AppIcon } from '@/presentation/icons'

export function FeaturesSection() {
  return (
    <section className="landing-section landing-features" id="features">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Возможности</p>
        <h2>Студия агентов для лабораторных и курсовых</h2>
        <p className="landing-section__lead">
          Не один чат, а оркестр специалистов: каждый агент отвечает за свой этап — от разбора
          методички до финального docx.
        </p>
      </div>

      <div className="features-grid">
        {FEATURE_CARDS.map((feature) => (
          <article key={feature.title} className="feature-card">
            <span className="feature-card__icon" aria-hidden>
              <AppIcon name={feature.icon} size={20} />
            </span>
            <h3>{feature.title}</h3>
            <p>{feature.text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
