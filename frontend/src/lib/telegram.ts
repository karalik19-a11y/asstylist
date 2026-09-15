/**
 * Thin wrapper around window.Telegram.WebApp.
 *
 * The app must work in a normal browser too, so every call
 * degrades gracefully when the Telegram SDK is absent.
 */

type HapticStyle = 'light' | 'medium' | 'heavy' | 'success' | 'error'

export interface TelegramWebApp {
  ready?: () => void
  expand?: () => void
  initData?: string
  initDataUnsafe?: { user?: { id: number; username?: string; first_name?: string } }
  colorScheme?: 'light' | 'dark'
  themeParams?: Record<string, string>
  setHeaderColor?: (color: string) => void
  setBackgroundColor?: (color: string) => void
  enableClosingConfirmation?: () => void
  HapticFeedback?: { impactOccurred?: (style: HapticStyle) => void; notificationOccurred?: (style: HapticStyle) => void }
  openLink?: (url: string, options?: { try_instant_view?: boolean }) => void
  openTelegramLink?: (url: string) => void
  sendData?: (data: string) => void
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

export function initTelegram(): void {
  const app = getWebApp()
  if (!app) return
  app.ready?.()
  app.expand?.()
  app.setHeaderColor?.('#f4efe4')
  app.setBackgroundColor?.('#f4efe4')
}

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
