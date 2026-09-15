import { useCallback, useEffect, useReducer, useState } from 'react'
import type { HistoryEntry, Look, Meta } from './lib/types'
import { api, ApiError } from './lib/api'
import { haptic, initTelegram } from './lib/telegram'
import { initialModel, wizardReducer } from './state/wizard'
import { Home } from './pages/Home'
import { Wizard } from './pages/Wizard'
import { History } from './pages/History'
import { Verification } from './pages/Verification'
import { LookResult } from './components/LookResult'
import { Header, Icon, type IconName } from './components/ui'

type Screen = 'home' | 'wizard' | 'result' | 'history' | 'verification'

type VerificationReport = {
  total: number
  verified: number
  warning: number
  failed: number
  eligible: number
  network_enabled: boolean
  ttl_days: number
  min_score: number
  items: { sku: string; name: string; source: string; status: string; score: number; issues: string[] }[]
}

const SCREEN_TITLES: Record<Screen, string> = {
  home: 'ASStylist',
  wizard: 'Новый образ',
  result: 'Твой образ',
  history: 'Мои образы',
  verification: 'Проверка товаров',
}

const SCREEN_SUBTITLES: Partial<Record<Screen, string>> = {
  result: 'Собран для тебя',
  history: 'Все собранные образы',
  verification: 'Статусы товаров каталога',
}

const TABS: { id: Screen; label: string; icon: IconName }[] = [
  { id: 'home', label: 'Главная', icon: 'spark' },
  { id: 'wizard', label: 'Образ', icon: 'star' },
  { id: 'history', label: 'Мои луки', icon: 'heart' },
  { id: 'verification', label: 'Проверка', icon: 'shield' },
]

const TAB_SCREENS: Screen[] = ['home', 'history', 'verification']

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Что-то пошло не так. Попробуйте ещё раз.'
}

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [screen, setScreen] = useState<Screen>('home')
  const [model, dispatch] = useReducer(wizardReducer, initialModel)
  const [look, setLook] = useState<Look | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [report, setReport] = useState<VerificationReport | null>(null)
  const [generating, setGenerating] = useState(false)
  const [swappingSlot, setSwappingSlot] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(false)

  const refreshHistory = useCallback(async () => {
    try {
      const response = await api.history(20)
      setHistory(response.items)
    } catch {
      setHistory([])
    }
  }, [])

  useEffect(() => {
    initTelegram()
    api
      .meta()
      .then(setMeta)
      .catch(() => setMeta(null))
    api.auth().catch(() => undefined)
    void refreshHistory()
  }, [refreshHistory])

  useEffect(() => {
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
  }, [screen])

  const goHome = useCallback(() => {
    setScreen('home')
    setError(null)
    void refreshHistory()
  }, [refreshHistory])

  const startWizard = useCallback(() => {
    dispatch({ type: 'reset' })
    setError(null)
    setScreen('wizard')
    haptic('light')
  }, [])

  const handleGenerate = useCallback(async () => {
    setGenerating(true)
    setError(null)
    try {
      const result = await api.generateLook(model.state)
      setLook(result)
      setScreen('result')
      haptic('success')
      void refreshHistory()
    } catch (caught) {
      setError(errorMessage(caught))
      haptic('error')
    } finally {
      setGenerating(false)
    }
  }, [model.state, refreshHistory])

  const handleSwap = useCallback(
    async (slot: string) => {
      if (!look?.id) return
      setSwappingSlot(slot)
      try {
        const updated = await api.swapItem(look.id, slot)
        setLook(updated)
        haptic('medium')
      } catch (caught) {
        setError(errorMessage(caught))
        haptic('error')
      } finally {
        setSwappingSlot(null)
      }
    },
    [look],
  )

  const handleFavorite = useCallback(async () => {
    if (!look?.id) return
    try {
      const response = await api.toggleFavorite(look.id)
      setLook({ ...look, is_favorite: response.is_favorite })
      haptic('light')
    } catch (caught) {
      setError(errorMessage(caught))
    }
  }, [look])

  const openLook = useCallback(async (id: number) => {
    setLoadingList(true)
    try {
      const result = await api.look(id)
      setLook(result)
      setScreen('result')
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setLoadingList(false)
    }
  }, [])

  const openHistory = useCallback(() => {
    setScreen('history')
    setLoadingList(true)
    void refreshHistory().finally(() => setLoadingList(false))
  }, [refreshHistory])

  const openVerification = useCallback(async () => {
    setScreen('verification')
    setLoadingList(true)
    try {
      setReport(await api.verification())
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setLoadingList(false)
    }
  }, [])

  const goTab = useCallback(
    (tab: Screen) => {
      haptic('light')
      if (tab === 'home') return goHome()
      if (tab === 'wizard') return startWizard()
      if (tab === 'history') return openHistory()
      if (tab === 'verification') return void openVerification()
    },
    [goHome, startWizard, openHistory, openVerification],
  )

  const showTabs = TAB_SCREENS.includes(screen)
  const showDock = screen === 'wizard'

  return (
    <>
      <div className="bg-scene" aria-hidden="true">
        <span className="orb" />
      </div>
      <div className="bg-grain" aria-hidden="true" />
      <div className={`app${showTabs ? ' has-tabs' : ''}${showDock ? ' has-dock' : ''}`}>
        <div className="screen" key={screen}>
          {screen !== 'home' && screen !== 'wizard' ? (
            <Header
              title={SCREEN_TITLES[screen]}
              subtitle={SCREEN_SUBTITLES[screen]}
              onBack={goHome}
            />
          ) : null}

          {screen === 'home' ? (
            <Home
              history={history}
              onStart={startWizard}
              onOpenHistory={openHistory}
              onOpenVerification={() => void openVerification()}
              onOpenLook={(id) => void openLook(id)}
            />
          ) : null}

          {screen === 'wizard' ? (
            <Wizard
              model={model}
              meta={meta}
              generating={generating}
              error={error}
              onPatch={(patch) => dispatch({ type: 'patch', patch })}
              onToggleColor={(id, field) => dispatch({ type: 'toggleColor', id, field })}
              onPhoto={(dataUrl, file) => dispatch({ type: 'setPhoto', dataUrl, file })}
              onClearPhoto={() => dispatch({ type: 'setPhoto', dataUrl: null, file: null })}
              onBack={() => dispatch({ type: 'back' })}
              onNext={() => dispatch({ type: 'next' })}
              onGenerate={() => void handleGenerate()}
              onExit={goHome}
            />
          ) : null}

          {screen === 'result' && look ? (
            <LookResult
              look={look}
              colors={meta?.colors ?? []}
              plans={meta?.plans ?? []}
              swappingSlot={swappingSlot}
              onSwap={(slot) => void handleSwap(slot)}
              onNewLook={startWizard}
              onFavorite={() => void handleFavorite()}
            />
          ) : null}

          {screen === 'history' ? (
            <History items={history} loading={loadingList} onOpen={(id) => void openLook(id)} />
          ) : null}

          {screen === 'verification' ? (
            <Verification report={report} loading={loadingList && !report} error={error} />
          ) : null}
        </div>

        {showTabs ? (
          <nav className="tabbar" aria-label="Навигация">
            <div className="tabbar-inner">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className="tab"
                  data-active={screen === tab.id}
                  onClick={() => goTab(tab.id)}
                  aria-current={screen === tab.id ? 'page' : undefined}
                >
                  <span className="ico" aria-hidden="true"><Icon name={tab.icon} size={21} /></span>
                  <span className="lbl">{tab.label}</span>
                </button>
              ))}
            </div>
          </nav>
        ) : null}
      </div>
    </>
  )
}
