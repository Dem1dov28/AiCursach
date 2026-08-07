interface Props {
  onBackToMarketing: () => void
}

export function AppHeader({ onBackToMarketing }: Props) {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__brand">
          <a className="app-header__brand-link" href="/app">
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
            <strong>AiCursach</strong>
          </a>
        </div>

        <nav className="app-header__nav" aria-label="Приложение">
          <button type="button" className="app-header__nav-link app-header__nav-link--active">
            Проекты
          </button>
          <button type="button" className="app-header__nav-link" onClick={onBackToMarketing}>
            О продукте
          </button>
        </nav>
      </div>
    </header>
  )
}
