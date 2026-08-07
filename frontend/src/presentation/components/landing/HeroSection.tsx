import { HERO_STATS } from '@/domain/landing/demoPresets'
import { InteractiveDemoWidget } from './InteractiveDemoWidget'

interface Props {
  onEnterApp: () => void
  onScrollToHow: () => void
}

export function HeroSection({ onEnterApp, onScrollToHow }: Props) {
  return (
    <section className="landing-hero">
      <div className="landing-hero__copy">
        <p className="landing-eyebrow">
          <span className="landing-eyebrow__dot" aria-hidden />
          AiCursach
        </p>
        <h1>
          Лабораторные и курсовые —{' '}
          <span className="landing-gradient-text">текст, код, диаграммы и docx</span>
          {' '}в одном рабочем пространстве
        </h1>
        <p className="landing-lead">
          Загрузите задание — система соберёт команду ИИ-агентов, покажет живой граф
          выполнения и остановится, когда нужно ваше согласование.
        </p>

        <div className="landing-hero__cta">
          <button type="button" className="btn btn-primary btn-lg" onClick={onEnterApp}>
            Попробовать бесплатно
          </button>
          <button type="button" className="btn btn-ghost btn-lg" onClick={onScrollToHow}>
            Как это работает
          </button>
        </div>

        <ul className="landing-stats" aria-label="Ключевые возможности">
          {HERO_STATS.map((item) => (
            <li key={item.label}>
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="landing-hero__visual">
        <InteractiveDemoWidget />
      </div>
    </section>
  )
}
