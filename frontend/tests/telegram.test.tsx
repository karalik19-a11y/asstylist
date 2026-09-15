import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import App from '../src/App'
import type { Meta } from '../src/lib/types'

const meta: Meta = {
  styles: [{ id: 'minimal', label: 'Минимализм', emoji: '◻️', description: 'Чистые линии', palette_hint: ['black'] }],
  moods: [{ id: 'calm', label: 'Спокойствие', emoji: '🍃', description: 'Мягко' }],
  occasions: [{ id: 'everyday', label: 'Каждый день' }],
  seasons: [{ id: 'all', label: 'Любой сезон' }],
  presentations: [{ id: 'unisex', label: 'Унисекс' }],
  categories: [{ id: 'top', label: 'Верх' }],
  slots: [{ id: 'top', label: 'Верх' }],
  colors: [{ id: 'black', label: 'чёрный', hex: '#111114', temperature: 'neutral', neutral: true }],
  plans: [{ id: 'layered', description: 'Многослойный' }],
  budget: { min_rub: 10000, max_rub: 100000, currency: 'RUB' },
  ranking_weights: { style: 0.5, color: 0.5 },
  sources: [],
  demo_mode: true,
  telegram: { configured: false, web_app_url: null, bot_link: null },
  ai_provider: 'local',
  version: '0.1.0',
}

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response)
}

function mockFetch() {
  const fn = vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes('/api/meta')) return jsonResponse(meta)
    if (url.includes('/api/telegram/auth'))
      return jsonResponse({ user: { id: 1, telegram_id: '42', first_name: 'Ася' }, demo: false, mode: 'telegram' })
    if (url.includes('/api/looks')) return jsonResponse({ items: [] })
    return jsonResponse({ status: 'ok' })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

/** Полнофункциональный мок клиента Telegram (Bot API 8.x). */
function makeTelegram(colorScheme: 'light' | 'dark' = 'dark') {
  const backClicks: Array<() => void> = []
  const webApp = {
    ready: vi.fn(),
    expand: vi.fn(),
    disableVerticalSwipes: vi.fn(),
    requestFullscreen: vi.fn(),
    isFullscreen: false,
    initData: 'query_id=AAE&auth_date=1',
    initDataUnsafe: { user: { id: 42, first_name: 'Ася', username: 'asya' } },
    colorScheme,
    setHeaderColor: vi.fn(),
    setBackgroundColor: vi.fn(),
    enableClosingConfirmation: vi.fn(),
    disableClosingConfirmation: vi.fn(),
    onEvent: vi.fn(),
    offEvent: vi.fn(),
    BackButton: {
      show: vi.fn(),
      hide: vi.fn(),
      isVisible: false,
      onClick: vi.fn((cb: () => void) => backClicks.push(cb)),
      offClick: vi.fn(),
    },
    HapticFeedback: { impactOccurred: vi.fn(), notificationOccurred: vi.fn() },
  }
  return { webApp, backClicks }
}

beforeEach(() => {
  mockFetch()
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  delete (window as unknown as { Telegram?: unknown }).Telegram
  document.documentElement.removeAttribute('data-theme')
})

describe('Telegram Mini App integration', () => {
  it('ready/expand, blocks swipe-close, requests fullscreen and follows the client theme', async () => {
    const { webApp } = makeTelegram('dark')
    ;(window as unknown as { Telegram: unknown }).Telegram = { WebApp: webApp }

    render(<App />)
    expect(await screen.findByRole('button', { name: 'Собрать образ' })).toBeInTheDocument()

    expect(webApp.ready).toHaveBeenCalled()
    expect(webApp.expand).toHaveBeenCalled()
    expect(webApp.disableVerticalSwipes).toHaveBeenCalled()
    expect(webApp.requestFullscreen).toHaveBeenCalled()

    // Клиент в тёмной теме → приложение открылось в noir и подсветило хедер.
    expect(document.documentElement.getAttribute('data-theme')).toBe('noir')
    expect(webApp.setHeaderColor).toHaveBeenCalledWith('#0b1a26')
  })

  it('shows the native BackButton off-home and navigates back on click', async () => {
    const { webApp, backClicks } = makeTelegram('light')
    ;(window as unknown as { Telegram: unknown }).Telegram = { WebApp: webApp }

    render(<App />)
    const start = await screen.findByRole('button', { name: 'Собрать образ' })
    expect(webApp.BackButton.hide).toHaveBeenCalled()

    fireEvent.click(start)
    expect(await screen.findByRole('heading', { name: 'Фото' })).toBeInTheDocument()
    expect(webApp.BackButton.show).toHaveBeenCalled()
    expect(webApp.enableClosingConfirmation).toHaveBeenCalled()

    // Нативная кнопка «назад» клиента возвращает на главную в один клик.
    expect(backClicks.length).toBeGreaterThan(0)
    backClicks.forEach((cb) => cb())
    expect(await screen.findByRole('button', { name: 'Собрать образ' })).toBeInTheDocument()
    expect(webApp.disableClosingConfirmation).toHaveBeenCalled()
  })

  it('switches Telegram chrome colors together with the in-app theme toggle', async () => {
    const { webApp } = makeTelegram('light')
    ;(window as unknown as { Telegram: unknown }).Telegram = { WebApp: webApp }

    render(<App />)
    const toggle = await screen.findByRole('button', { name: 'Тёмная' })

    fireEvent.click(toggle)
    expect(document.documentElement.getAttribute('data-theme')).toBe('noir')
    expect(webApp.setBackgroundColor).toHaveBeenLastCalledWith('#0b1a26')
  })
})
