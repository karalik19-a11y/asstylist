import { useState } from 'react'
import { Header, type TabKey } from './components/Header'
import { WardrobeView } from './components/WardrobeView'
import { StudioView } from './components/StudioView'
import { WeekView } from './components/WeekView'
import { ProfileView } from './components/ProfileView'
import { useAppState } from './state/AppState'

export default function App() {
  const [tab, setTab] = useState<TabKey>('wardrobe')
  const { items, outfits } = useAppState()

  return (
    <div className="app">
      <Header
        active={tab}
        onChange={setTab}
        itemsCount={items.length}
        savedCount={outfits.length}
      />
      <main className="app-main">
        {tab === 'wardrobe' && <WardrobeView />}
        {tab === 'studio' && <StudioView onGoWardrobe={() => setTab('wardrobe')} />}
        {tab === 'week' && <WeekView />}
        {tab === 'profile' && <ProfileView />}
      </main>
      <footer className="app-footer">
        Asstylist · образы собраны локальными правилами стилиста: цветовые схемы, формальность,
        цветотип, погода и ротация вещей
      </footer>
    </div>
  )
}
