import { useState } from 'react'
import { FAQ_ITEMS } from '@/domain/landing/demoPresets'

export function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const toggle = (index: number) => {
    setOpenIndex((current) => (current === index ? null : index))
  }

  return (
    <section className="landing-section landing-faq" id="faq">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">FAQ</p>
        <h2>Частые вопросы</h2>
        <p className="landing-section__lead">
          Коротко о том, как работает AiCursach и чего ожидать от beta-версии.
        </p>
      </div>

      <div className="faq-list">
        {FAQ_ITEMS.map((item, index) => {
          const isOpen = openIndex === index
          return (
            <article key={item.question} className={`faq-item${isOpen ? ' faq-item--open' : ''}`}>
              <button
                type="button"
                className="faq-item__trigger"
                aria-expanded={isOpen}
                onClick={() => toggle(index)}
              >
                <span>{item.question}</span>
                <span className="faq-item__chevron" aria-hidden />
              </button>
              {isOpen && (
                <div className="faq-item__answer">
                  <p>{item.answer}</p>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
