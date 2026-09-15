import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from '../src/App'
import type { Look, Meta } from '../src/lib/types'

const meta: Meta = {
  styles: [
    { id: 'minimal', label: 'Минимализм', emoji: '◻️', description: 'Чистые линии', palette_hint: ['black'] },
    { id: 'streetwear', label: 'Стритвир', emoji: '🛹', description: 'Оверсайз', palette_hint: ['black'] },
  ],
  moods: [
    { id: 'calm', label: 'Спокойствие', emoji: '🍃', description: 'Мягко' },
    { id: 'bold', label: 'Дерзость', emoji: '⚡', description: 'Ярко' },
  ],
  occasions: [{ id: 'everyday', label: 'Каждый день' }],
  seasons: [{ id: 'all', label: 'Любой сезон' }],
  presentations: [{ id: 'unisex', label: 'Унисекс' }],
  categories: [{ id: 'top', label: 'Верх' }],
  slots: [{ id: 'top', label: 'Верх' }],
  colors: [
    { id: 'black', label: 'чёрный', hex: '#111114', temperature: 'neutral', neutral: true },
    { id: 'camel', label: 'кэмел', hex: '#B08050', temperature: 'warm', neutral: false },
  ],
  plans: [{ id: 'layered', description: 'Многослойный' }],
  budget: { min_rub: 10000, max_rub: 100000, currency: 'RUB' },
  ranking_weights: { style: 0.5, color: 0.5 },
  sources: [],
  demo_mode: true,
  telegram: { configured: false, web_app_url: null, bot_link: null },
  ai_provider: 'local',
  version: '0.1.0',
}

const look: Look = {
  id: 7,
  style: 'minimal',
  mood: 'calm',
  occasion: 'everyday',
  season: 'all',
  presentation: 'unisex',
  height_cm: 172,
  weight_kg: 68,
  budget_rub: 50000,
  total_rub: 32990,
  budget_utilization: 0.66,
  score: 91.4,
  verdict: { grade: 'A', title: 'Образ уровня стилиста', note: 'Собрано цельно' },
  cohesion: { overall: 0.9 },
  summary: 'Минимализм: 2 вещи на 32 990 ₽ из 50 000 ₽.',
  tips: ['Держите одну вертикаль цвета.'],
  body: {
    height_cm: 172,
    weight_kg: 68,
    bmi: 23.0,
    bmi_label: 'норма',
    height_class: 'average',
    silhouette: 'balanced',
    silhouette_ru: 'Сбалансированный силуэт',
    confidence: 0.45,
    recommended_fits: ['regular'],
    avoid_fits: [],
    recommended_lengths: ['regular'],
    tips: [],
    signals: ['Рост и вес → оценка ИМТ'],
  },
  palette: {
    temperature: 'neutral',
    depth: 'medium',
    chroma: 'soft',
    season_label: 'Мягкий переходный тип',
    recommended: ['black', 'camel'],
    avoid: [],
    confidence: 0.25,
    source: 'defaults',
    dominant_colors: [],
    signals: [],
  },
  plan: 'layered',
  engine_version: '1.0.0',
  diagnostics: { candidates_total: 42, rejected_total: 4, warnings: [], dropped_slots: [], plan_description: 'Многослойный' },
  items: [
    {
      position: 0,
      slot: 'top',
      slot_label: 'Верх',
      sku: 'TP-001',
      category: 'top',
      name: 'Футболка базовая плотная',
      brand: 'Uniqlo',
      price_rub: 1990,
      url: 'https://www.uniqlo.com/p/tp-001',
      image_url: '',
      colors: ['black'],
      color_hexes: ['#111114'],
      fit: 'regular',
      score: 0.88,
      breakdown: { style: 1, color: 0.8 },
      reasons: ['Точное попадание в стиль «Минимализм»'],
      verification_status: 'verified',
      verification_score: 0.99,
      source: 'uniqlo',
      alternatives: [],
    },
    {
      position: 1,
      slot: 'shoes',
      slot_label: 'Обувь',
      sku: 'SH-001',
      category: 'shoes',
      name: 'Кроссовки белые кожаные',
      brand: 'Uniqlo Sport',
      price_rub: 8990,
      url: 'https://www.uniqlo.com/p/sh-001',
      image_url: '',
      colors: ['white'],
      color_hexes: ['#F6F6F4'],
      fit: 'regular',
      score: 0.82,
      breakdown: { style: 1, color: 0.7 },
      reasons: ['Цвет входит в вашу палитру'],
      verification_status: 'verified',
      verification_score: 0.99,
      source: 'uniqlo',
      alternatives: [],
    },
  ],
  is_favorite: false,
  version: 1,
  ai_provider: 'local',
  photo_digest: '',
}

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve({
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response)
}

function mockFetch(overrides: Record<string, (init?: RequestInit) => Promise<Response>> = {}) {
  const fn = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    for (const [pattern, handler] of Object.entries(overrides)) {
      if (url.includes(pattern)) return handler(init)
    }
    if (url.includes('/api/meta')) return jsonResponse(meta)
    if (url.includes('/api/telegram/auth'))
      return jsonResponse({ user: { id: 1, telegram_id: 'demo-1', first_name: 'Тест' }, demo: true, mode: 'demo' })
    if (url.includes('/api/looks/generate')) return jsonResponse(look)
    if (url.includes('/api/looks')) return jsonResponse({ items: [] })
    return jsonResponse({ status: 'ok' })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

beforeEach(() => {
  mockFetch()
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

async function walkToReview() {
  fireEvent.click(await screen.findByRole('button', { name: 'Собрать образ' }))
  expect(await screen.findByRole('heading', { name: 'Фото' })).toBeInTheDocument()
  for (const step of ['Параметры', 'Стиль', 'Настроение', 'Детали']) {
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByRole('heading', { name: step })).toBeInTheDocument()
  }
  fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
  expect(await screen.findByRole('heading', { name: 'Проверка' })).toBeInTheDocument()
}

describe('App flow', () => {
  it('renders the home screen with catalog metadata', async () => {
    render(<App />)
    expect(await screen.findByText(/соберём образ/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('2 стилей')).toBeInTheDocument())
    expect(screen.getByText('демо-режим')).toBeInTheDocument()
  })

  it('walks the whole wizard and renders the generated look', async () => {
    render(<App />)
    await walkToReview()

    fireEvent.click(screen.getByRole('button', { name: 'Сгенерировать' }))

    expect(await screen.findByText('Образ уровня стилиста')).toBeInTheDocument()
    expect(screen.getByText('Футболка базовая плотная')).toBeInTheDocument()
    expect(screen.getByText('Кроссовки белые кожаные')).toBeInTheDocument()
    expect(screen.getByText(/Силуэт/)).toBeInTheDocument()
    expect(screen.getByText('Сбалансированный силуэт')).toBeInTheDocument()
    expect(screen.getByText('Держите одну вертикаль цвета.')).toBeInTheDocument()
  })

  it('posts the wizard state as multipart form data', async () => {
    const fetchMock = mockFetch()
    render(<App />)
    await walkToReview()
    fireEvent.click(screen.getByRole('button', { name: 'Сгенерировать' }))
    await screen.findByText('Образ уровня стилиста')

    const generateCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/api/looks/generate'))
    expect(generateCall).toBeTruthy()
    const body = (generateCall?.[1] as RequestInit).body as FormData
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('style')).toBe('minimal')
    expect(body.get('mood')).toBe('calm')
    expect(body.get('budget_rub')).toBe('50000')
    expect(body.get('height_cm')).toBe('172')
  })

  it('shows a server error instead of crashing', async () => {
    mockFetch({ '/api/looks/generate': () => jsonResponse({ detail: 'Недостаточно подходящих товаров' }, 422) })
    render(<App />)
    await walkToReview()
    fireEvent.click(screen.getByRole('button', { name: 'Сгенерировать' }))
    expect(await screen.findByText('Недостаточно подходящих товаров')).toBeInTheDocument()
  })

  it('blocks an unrealistic body measurement', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Собрать образ' }))
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByRole('heading', { name: 'Параметры' })).toBeInTheDocument()

    const height = screen.getByLabelText('Рост') as HTMLInputElement
    fireEvent.change(height, { target: { value: '210' } })
    const weight = screen.getByLabelText('Вес') as HTMLInputElement
    fireEvent.change(weight, { target: { value: '40' } })

    expect(await screen.findByText(/нереалистично/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Далее' })).toBeDisabled()
  })

  it('opens the verification report', async () => {
    mockFetch({
      '/api/catalog/verification': () =>
        jsonResponse({
          total: 107,
          verified: 103,
          warning: 0,
          failed: 4,
          eligible: 103,
          network_enabled: false,
          ttl_days: 30,
          min_score: 0.6,
          items: [{ sku: 'BAD-001', name: 'Футболка с подозрительного сайта', source: 'unknown', status: 'failed', score: 0.3, issues: ['url: хост не в белом списке'] }],
        }),
    })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Проверка товаров' }))
    expect(await screen.findByText('103')).toBeInTheDocument()
    expect(screen.getByText('Футболка с подозрительного сайта')).toBeInTheDocument()
  })
})
