import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import type { HistoryEntry, Look, Meta, WizardState } from './lib/types'
import { api, ApiError } from './lib/api'
import {
  haptic,
  initTelegram,
  isTelegram,
  onBackButton,
  onTelegramEvent,
  setBackButtonVisible,
  setClosingConfirmation,
  syncTelegramChrome,
  telegramColorScheme,
  telegramUserName,
} from './lib/telegram'
import { initialModel, wizardReducer } from './state/wizard'
import { Home } from './pages/Home'
import { Wizard } from './pages/Wizard'
import type { BodyMemory } from './lib/profile'
import { loadBodyMemory, markBodyUsed, saveBodyMemory } from './lib/profile'
import { History } from './pages/History'
import { Verification } from './pages/Verification'
import { Search } from './pages/Search'
import { LookResult } from './components/LookResult'
import { Header, ThemeToggle } from './components/ui'
import { playClick, playSuccess } from './lib/sound'
import { LeopardPatternDef } from './lib/graphics'

type Screen = 'home' | 'wizard' | 'result' | 'history' | 'verification' | 'search'

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
  wizard: 'Новый гардероб',
  result: 'Персональная селекция',
  history: 'Архив образов',
  verification: 'Верификация каталога',
  search: 'Поиск вещей',
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Произошла ошибка при формировании гардероба. Повторите попытку.'
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
  // Память о человеке: рост и вес, введённые в прошлый раз.
  const [savedBody, setSavedBody] = useState<BodyMemory | null>(null)
  // По умолчанию — системная тема клиента Telegram, в браузере — светлая.
  const [theme, setTheme] = useState<'noir' | 'parchment'>(() =>
    telegramColorScheme() === 'dark' ? 'noir' : 'parchment',
  )

  // Атрибут data-theme и цвет хедера Telegram всегда следуют за состоянием.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    syncTelegramChrome(theme)
  }, [theme])

  const applyTheme = useCallback((next: 'noir' | 'parchment') => setTheme(next), [])

  const toggleTheme = useCallback(() => {
    playClick()
    applyTheme(theme === 'noir' ? 'parchment' : 'noir')
  }, [applyTheme, theme])

  const refreshHistory = useCallback(async () => {
    try {
      const response = await api.history(20)
      setHistory(response.items)
    } catch {
      setHistory([])
    }
  }, [])

  // Реакция на смену темы в самом Telegram (клиент может переключать на лету).
  useEffect(() => {
    const offTheme = onTelegramEvent('themeChanged', () => {
      applyTheme(telegramColorScheme() === 'dark' ? 'noir' : 'parchment')
    })
    return offTheme
  }, [applyTheme])

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
    // Память о росте и весе: сервер → локальная копия.
    void loadBodyMemory().then(setSavedBody)
    void refreshHistory()
  }, [refreshHistory])

  // Extract rest from original file via placeholder - STOP
