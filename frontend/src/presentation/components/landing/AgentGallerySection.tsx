import { AGENT_SHOWCASE } from '@/domain/landing/demoPresets'
import { AppIcon } from '@/presentation/icons'

export function AgentGallerySection() {
  return (
    <section className="landing-section landing-agents" id="agents">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Команда</p>
        <h2>12 специализированных агентов</h2>
        <p className="landing-section__lead">
          Не один универсальный чат, а оркестр ролей — каждый агент отвечает за свой этап,
          от разбора методички до финального docx.
        </p>
      </div>

      <div className="agent-showcase-grid">
        {AGENT_SHOWCASE.map((agent) => (
          <article key={agent.id} className="agent-showcase-card">
            <span className="agent-showcase-card__icon" aria-hidden>
              <AppIcon name={agent.icon} size={18} />
            </span>
            <h3>{agent.title}</h3>
            <p>{agent.text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
