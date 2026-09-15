/**
 * Thin wrapper around window.Telegram.WebApp (Bot API 8.x).
 *
 * The app must work in a normal browser too (demo/local mode), so every call
 * degrades gracefully when the Telegram SDK is absent.
 */

type HapticStyle = 'light' | 'medium' | 'heavy' | 'success' | 'error'
type EventName =
  | 'themeChanged'
  | 'viewportChanged'
  | 'safeAreaChanged'
  | 'contentSafeAreaChanged'
  | 'fullscreenChanged'

interface SafeAreaInset {
  top: number
  bottom: number
  left: number
  right: number
}

export interface TelegramWebApp {
  ready?: () => void
  expand?: () => void
  disableVerticalSwipes?: () => void
  requestFullscreen?: () => void
  exitFullscreen?: () => void
  isFullscreen?: boolean
  isExpanded?: boolean
  initData?: string
  initDataUnsafe?: { user?: { id: number; username?: string; first_name?: string } }
  colorScheme?: 'light' | 'dark'
  themeParams?: Record<string, string>
  safeAreaInset?: SafeAreaInset
  contentSafeAreaInset?: SafeAreaInset
  setHeaderColor?: (color: string) => void
  setBackgroundColor?: (color: string) => void
  enableClosingConfirmation?: () => void
  disableClosingConfirmation?: () => void
  onEvent?: (event: EventName, handler: () => void) => void
  offEvent?: (event: EventName, handler: () => void) => void
  HapticFeedback?: { impactOccurred?: (style: HapticStyle) => void; notificationOccurred?: (style: HapticStyle) => void }
  openLink?: (url: string, options?: { try_instant_view?: boolean }) => void
  openTelegramLink?: (url: string) => void
  sendData?: (data: string) => void
  BackButton?: {
    show: () => void
    hide: () => void
    isVisible?: boolean
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
  MainButton?: {
    setText: (text: string) => void
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
    setParams?: (params: Record<string, unknown>) => void
  }
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp }
  }
}

export function getWebApp(): TelegramWebApp | null {
  if (typeof window === 'undefined') return null
  return window.Telegram?.WebApp ?? null
}

export const isTelegram = (): boolean => getWebApp() !== null && Boolean(getWebApp()?.initData)

/* -------------------------------------------------------------------------- */
/* Конфигурация клиента                                                       */
/* -------------------------------------------------------------------------- */

const HEADER_COLORS = { parchment: '#cdeaf6', noir: '#0b1a26' } as const

/** Твик «шапки» Telegram и meta theme-color под текущую тему приложения. */
export function syncTelegramChrome(theme: 'noir' | 'parchment'): void {
  const app = getWebApp()
  const color = HEADER_COLORS[theme]
  try {
    app?.setHeaderColor?.(color)
    app?.setBackgroundColor?.(color)
  } catch {
    /* older clients */
  }
  const meta = document.querySelector('meta[name="theme-color"]')
  meta?.setAttribute('content', color)
}

/** Системная тема Telegram ('light' | 'dark'), если приложение открыто в клиенте. */
export function telegramColorScheme(): 'light' | 'dark' | null {
  return getWebApp()?.colorScheme ?? null
}

/** Подписка на события WebApp с функцией отписки. */
export function onTelegramEvent(event: EventName, handler: () => void): () => void {
  const app = getWebApp()
  app?.onEvent?.(event, handler)
  return () => app?.offEvent?.(event, handler)
}

/** Прокидываем безопасные отступы клиента (fullscreen/нотч) в CSS-переменные. */
function applyContentInsets(app: TelegramWebApp): void {
  const root = document.documentElement
  const safe = app.safeAreaInset
  const content = app.contentSafeAreaInset
  root.style.setProperty('--tg-safe-top', `${safe?.top ?? 0}px`)
  root.style.setProperty('--tg-safe-bottom', `${safe?.bottom ?? 0}px`)
  root.style.setProperty('--tg-content-safe-top', `${content?.top ?? 0}px`)
}

/**
 * Инициализация Mini App: разворачиваем, блокируем случайное закрытие
 * свайпом, просим полноэкранный режим, подписываемся на смену отступов.
 */
export function initTelegram(): void {
  const app = getWebApp()
  if (!app) return

  app.ready?.()
  app.expand?.()

  // Bot API 7.7+: свайп вниз не закрывает приложение посреди работы.
  try {
    app.disableVerticalSwipes?.()
  } catch {
    /* older clients */
  }

  // Bot API 8.0+: полный экран для погружения (клиент может проигнорировать).
  try {
    if (app.isFullscreen === false) app.requestFullscreen?.()
  } catch {
    /* ignore */
  }

  applyContentInsets(app)
  app.onEvent?.('safeAreaChanged', () => applyContentInsets(app))
  app.onEvent?.('contentSafeAreaChanged', () => applyContentInsets(app))
}

/* -------------------------------------------------------------------------- */
/* Нативная кнопка «Назад» и подтверждение закрытия                           */
/* -------------------------------------------------------------------------- */

let backHandler: (() => void) | null = null

/** Единая подписка на нативную BackButton (перерегистрация безопасна). */
export function onBackButton(handler: () => void): () => void {
  const app = getWebApp()
  const button = app?.BackButton
  if (!button) return () => undefined

  const wrapped = () => handler()
  button.onClick(wrapped)
  backHandler = wrapped
  return () => {
    button.offClick(wrapped)
    if (backHandler === wrapped) backHandler = null
  }
}

export function setBackButtonVisible(visible: boolean): void {
  const button = getWebApp()?.BackButton
  if (!button) return
  if (visible) button.show()
  else button.hide()
}

/** Показывать диалог «закрыть приложение?» только когда есть несохранённый прогресс. */
export function setClosingConfirmation(enabled: boolean): void {
  const app = getWebApp()
  if (!app) return
  try {
    if (enabled) app.enableClosingConfirmation?.()
    else app.disableClosingConfirmation?.()
  } catch {
    /* older clients */
  }
}

/* -------------------------------------------------------------------------- */
/* Взаимодействие                                                             */
/* -------------------------------------------------------------------------- */

export function haptic(style: HapticStyle = 'light'): void {
  const app = getWebApp()
  const feedback = app?.HapticFeedback
  if (!feedback) return
  if (style === 'success' || style === 'error') feedback.notificationOccurred?.(style)
  else feedback.impactOccurred?.(style)
}

export function openExternal(url: string): void {
  const app = getWebApp()
  if (!url) return
  if (app?.openLink) {
    app.openLink(url, { try_instant_view: false })
    return
  }
  if (typeof window !== 'undefined') window.open(url, '_blank', 'noopener,noreferrer')
}

/** Opens a t.me link inside Telegram when we run there, in a new tab otherwise. */
export function openTelegramLink(url: string): void {
  if (!url) return
  const app = getWebApp()
  if (app?.openTelegramLink) {
    app.openTelegramLink(url)
    return
  }
  if (typeof window !== 'undefined') window.open(url, '_blank', 'noopener,noreferrer')
}

export function telegramUserId(): string | null {
  const app = getWebApp()
  const id = app?.initDataUnsafe?.user?.id
  return id ? String(id) : null
}

export function telegramUserName(): string | null {
  const app = getWebApp()
  return app?.initDataUnsafe?.user?.first_name ?? app?.initDataUnsafe?.user?.username ?? null
}

export function sendToBot(payload: unknown): void {
  const app = getWebApp()
  if (app?.sendData) app.sendData(JSON.stringify(payload).slice(0, 4000))
}
