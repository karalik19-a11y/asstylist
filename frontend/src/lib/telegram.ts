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
  initData?: string
  initDataUnsafe?: {
    user?: {
      id: number
      username?: string
      first_name?: string
      last_name?: string
      photo_url?: string
    }
  }
  colorScheme?: 'light' | 'dark'
  ready?: () => void
  expand?: () => void
  close?: () => void
  disableVerticalSwipes?: () => void
  enableClosingConfirmation?: () => void
  disableClosingConfirmation?: () => void
  setHeaderColor?: (color: string) => void
  setBackgroundColor?: (color: string) => void
  openLink?: (url: string, options?: { try_instant_view?: boolean }) => void
  openTelegramLink?: (url: string) => void
  onEvent?: (event: EventName, handler: () => void) => void
  offEvent?: (event: EventName, handler: () => void) => void
  HapticFeedback?: {
    impactOccurred?: (style: HapticStyle) => void
    notificationOccurred?: (type: 'error' | 'success' | 'warning') => void
  }
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
  safeAreaInset?: SafeAreaInset
  contentSafeAreaInset?: SafeAreaInset
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

const HEADER_COLORS = { parchment: '#7eb8d4', noir: '#0b1a26' } as const

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

export function telegramColorScheme(): 'light' | 'dark' | null {
  return getWebApp()?.colorScheme ?? null
}

export function onTelegramEvent(event: EventName, handler: () => void): () => void {
  const app = getWebApp()
  app?.onEvent?.(event, handler)
  return () => app?.offEvent?.(event, handler)
}

function applyContentInsets(app: TelegramWebApp): void {
  const root = document.documentElement
  const safe = app.safeAreaInset
  const content = app.contentSafeAreaInset
  root.style.setProperty('--tg-safe-top', `${safe?.top ?? 0}px`)
  root.style.setProperty('--tg-safe-bottom', `${safe?.bottom ?? 0}px`)
  root.style.setProperty('--tg-content-safe-top', `${content?.top ?? 0}px`)
}

export function initTelegram(): void {
  const app = getWebApp()
  if (!app) return
  try {
    app.ready?.()
    app.expand?.()
    app.disableVerticalSwipes?.()
    applyContentInsets(app)
  } catch {
    /* ignore */
  }
}

export function haptic(style: HapticStyle = 'light'): void {
  try {
    if (style === 'success' || style === 'error') {
      getWebApp()?.HapticFeedback?.notificationOccurred?.(style === 'success' ? 'success' : 'error')
    } else {
      getWebApp()?.HapticFeedback?.impactOccurred?.(style)
    }
  } catch {
    /* ignore */
  }
}

export function setBackButtonVisible(visible: boolean): void {
  const btn = getWebApp()?.BackButton
  if (!btn) return
  try {
    if (visible) btn.show()
    else btn.hide()
  } catch {
    /* ignore */
  }
}

export function setClosingConfirmation(enabled: boolean): void {
  const app = getWebApp()
  try {
    if (enabled) app?.enableClosingConfirmation?.()
    else app?.disableClosingConfirmation?.()
  } catch {
    /* ignore */
  }
}

export function onBackButton(handler: () => void): () => void {
  const btn = getWebApp()?.BackButton
  if (!btn) return () => undefined
  btn.onClick(handler)
  return () => btn.offClick(handler)
}

export function telegramUserId(): string | null {
  const app = getWebApp()
  const id = app?.initDataUnsafe?.user?.id
  return id != null ? String(id) : null
}

export function telegramUserName(): string | null {
  const app = getWebApp()
  return app?.initDataUnsafe?.user?.first_name ?? app?.initDataUnsafe?.user?.username ?? null
}

/** Open http(s) links via Telegram client or window.open fallback. */
export function openExternal(url: string): void {
  const app = getWebApp()
  if (app?.openLink) {
    app.openLink(url, { try_instant_view: false })
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

/** Open t.me links inside Telegram when possible. */
export function openTelegramLink(url: string): void {
  const app = getWebApp()
  if (app?.openTelegramLink) {
    app.openTelegramLink(url)
    return
  }
  openExternal(url)
}

/** URL аватарки Telegram (если клиент отдал photo_url). */
export function telegramUserPhoto(): string | null {
  const url = getWebApp()?.initDataUnsafe?.user?.photo_url
  return url || null
}

export function telegramUsername(): string | null {
  return getWebApp()?.initDataUnsafe?.user?.username ?? null
}
