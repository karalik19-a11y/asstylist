import { useCallback, useEffect, useReducer, useState } from 'react'
import type { HistoryEntry, Look, Meta } from './lib/types'
import { api, ApiError } from './lib/api'
import { haptic, initTelegram, isTelegram, telegramUserName } from './lib/telegram'
import { initialModel, wizardReducer } from './state/wizard'
import { Home } from './pages/Home'
import { Wizard } from './pages/Wizard'
import { History } from './pages/History'
import { Verification } from './pages/Verification'
import { LookResult } from './components/LookResult'
import { Header } from './components/ui'

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
  home: 'asStylist',
  wizard: 'Новый образ',
  result: 'Ваш образ',
  history: 'Мои образы',
  verification: 'Проверка товаров',
}

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
  const [userName, setUserName] = useState<string | null>(null)

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
    setUserName(telegramUserName())
    api
      .meta()
      .then(setMeta)
      .catch(() => setMeta(null))
    api
      .auth()
      .then((response) => setUserName(response.user.first_name ?? response.user.telegram_id))
      .catch(() => undefined)
    void refreshHistory()
  }, [refreshHistory])

  const goHome = useCallback(() => {
    setScreen('home')
    setError(null)
    void refreshHistory()
  }, [refreshHistory])

  const startWizard = useCallback(() => {
    dispatch({ type: 'reset' })
    setError(null)
    setScreen('wizard')
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

  return (
    <div className="app">
      {screen !== 'home' ? (
        <Header title={SCREEN_TITLES[screen]} onBack={screen === 'result' ? goHome : () => setScreen('home')} />
      ) : null}

      {screen === 'home' ? (
        <Home
          meta={meta}
          history={history}
          userName={userName}
          onBotConnected={() => {
            api
              .meta()
              .then(setMeta)
              .catch(() => undefined)
          }}
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

      {screen === 'home' && !isTelegram() ? (
        <footer className="muted tiny" style={{ textAlign: 'center', paddingTop: 8 }}>
          Работает в браузере в демо-режиме · в Telegram Mini App доступна авторизация по аккаунту
        </footer>
      ) : null}
    </div>
  )
}
