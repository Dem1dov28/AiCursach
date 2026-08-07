interface Props {
  onEnterApp: () => void
}

export function CtaSection({ onEnterApp }: Props) {
  return (
    <section className="landing-cta">
      <div className="landing-cta__glow" aria-hidden />
      <div className="landing-cta__inner">
        <p className="landing-eyebrow">Готовы начать?</p>
        <h2>Загрузите задание — агенты возьмут рутину на себя</h2>
        <p className="landing-cta__text">
          Перейдите в приложение, добавьте методичку и формулировку темы — дальше система
          сама определит формат работы и соберёт команду агентов.
        </p>
        <div className="landing-hero__cta landing-hero__cta--center">
          <button type="button" className="btn btn-primary btn-lg" onClick={onEnterApp}>
            Перейти в приложение
          </button>
        </div>
      </div>
    </section>
  )
}
