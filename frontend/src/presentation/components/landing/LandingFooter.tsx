import type { Health } from '@/domain/jobs/types'

interface Props {
  health: Health | null
}

export function LandingFooter({ health }: Props) {
  const showUnavailable = health != null && !health.database_ok
  const year = new Date().getFullYear()

  return (
    <footer className="landing-footer">
      <div className="landing-footer__grid">
        <div className="landing-footer__brand">
          <strong>AiCursach</strong>
          <p className="landing-footer__tagline">
            Команда ИИ-агентов для лабораторных и курсовых работ.
          </p>
          <span className="landing-badge landing-footer__beta">BETA</span>
        </div>

        <div className="landing-footer__meta">
          <a href="#faq">Частые вопросы</a>
          <span className="landing-footer__sep" aria-hidden>
            ·
          </span>
          <span>Материалы хранятся в вашем проекте на сервере</span>
        </div>
      </div>

      <div className="landing-footer__bottom">
        <p className="landing-footer__copy">© {year} AiCursach</p>
        {showUnavailable && (
          <span className="landing-status warn">Сервис временно недоступен</span>
        )}
      </div>
    </footer>
  )
}
