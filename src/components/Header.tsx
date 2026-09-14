export const TABS = [
  { key: 'wardrobe', label: 'Гардероб' },
  { key: 'studio', label: 'Студия образов' },
  { key: 'week', label: 'План на неделю' },
  { key: 'profile', label: 'Профиль' },
] as const

export type TabKey = (typeof TABS)[number]['key']

interface HeaderProps {
  active: TabKey
  onChange: (tab: TabKey) => void
  itemsCount: number
  savedCount: number
}

export function Header({ active, onChange, itemsCount, savedCount }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark" aria-hidden>
          A
        </span>
        <div>
          <h1>Asstylist</h1>
          <p>ИИ-стилист: гардероб, образы по случаю, погоде и цветотипу</p>
        </div>
      </div>

      <nav className="tabs" aria-label="Разделы">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`tab ${active === tab.key ? 'is-active' : ''}`}
            onClick={() => onChange(tab.key)}
            aria-current={active === tab.key}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="header-meta">
        <span className="pill" title="Вещей в гардеробе">
          {itemsCount} вещ.
        </span>
        <span className="pill" title="Сохранённых образов">
          {savedCount} образ.
        </span>
      </div>
    </header>
  )
}
