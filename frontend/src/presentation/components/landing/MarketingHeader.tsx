import { useEffect, useState } from 'react'

interface Props {
  isAuthenticated: boolean
  onEnterApp: () => void
}

export function MarketingHeader({ isAuthenticated, onEnterApp }: Props) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 320)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header className={`landing-header marketing-header${scrolled ? ' landing-header--scrolled' : ''}`}>
      <div className="landing-header__inner">
        <a className="landing-header__brand landing-header__brand--link" href="/">
          <div className="landing-logo" aria-hidden>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2L4 7v10l8 5 8-5V7l-8-5z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M12 12l8-5M12 12L4 7M12 12v10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div className="landing-header__titles">
            <strong>AiCursach</strong>
            <span className="landing-header__sub">Учебные работы</span>
          </div>
          <span className="landing-badge">BETA</span>
        </a>

        <div className="landing-header__actions">
          <button type="button" className="btn btn-primary" onClick={onEnterApp}>
            {isAuthenticated ? 'Открыть приложение' : 'Попробовать'}
          </button>
        </div>
      </div>
    </header>
  )
}
