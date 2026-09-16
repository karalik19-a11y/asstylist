import { playClick } from '../lib/sound'

type TabId = 'home' | 'archive' | 'journal' | 'profile'

export function TabBar({
  active,
  onHome,
  onArchive,
  onJournal,
  onProfile,
}: {
  active: TabId
  onHome: () => void
  onArchive: () => void
  onJournal: () => void
  onProfile: () => void
}) {
  return (
    <nav className="tab-bar" aria-label="Основная навигация">
      <button type="button" className="tab-bar-btn" data-active={active === 'home'} onClick={() => { playClick(); onHome() }} aria-current={active === 'home' ? 'page' : undefined}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z" /></svg>
        <span>Главная</span>
      </button>
      <button type="button" className="tab-bar-btn" data-active={active === 'archive'} onClick={() => { playClick(); onArchive() }} aria-current={active === 'archive' ? 'page' : undefined}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7z" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /><path d="M9 12h6" /></svg>
        <span>Архив</span>
      </button>
      <button type="button" className="tab-bar-btn" data-active={active === 'journal'} onClick={() => { playClick(); onJournal() }} aria-current={active === 'journal' ? 'page' : undefined}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4.5h11a3 3 0 0 1 3 3V20H8a3 3 0 0 1-3-3V4.5z" /><path d="M8 20V7.5a3 3 0 0 1 3-3" /><path d="M11 9h5M11 12h5M11 15h3" /></svg>
        <span>Журнал</span>
      </button>
      <button type="button" className="tab-bar-btn" data-active={active === 'profile'} onClick={() => { playClick(); onProfile() }} aria-current={active === 'profile' ? 'page' : undefined}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5" /><path d="M5 19.5c1.8-3.2 4.2-4.5 7-4.5s5.2 1.3 7 4.5" /></svg>
        <span>Кабинет</span>
      </button>
    </nav>
  )
}
