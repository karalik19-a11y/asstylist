import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from '../src/App'
import type { EngineSearchResult, Look, Meta } from '../src/lib/types'

const meta: Meta = {
  styles: [
    { id: 'grunge', label: 'Гранж', emoji: '🖤', description: 'Потертости и деним', palette_hint: ['black'] },
    { id: 'minimal', label: 'Минимализм', emoji: '◻️', description: 'Чистые линии', palette_hint: ['black'] },
  ],
  moods: [{ id: 'bold', label: 'Дерзость', emoji: '⚡', description: 'Ярко' }],
  occasions: [{ id: 'everyday', label: 'Каждый день' }],
  seasons: [{ id: 'autumn', label: 'Осень' }],
  presentations: [{ id: 'feminine', label: 'Женская подача' }],
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

const engineSearch: EngineSearchResult = {
  query: 'индустриальный образ с прозрачным верхом',
  engine: {
    pipeline: 'asstylist-fashion-engine',
    engine_version: '1.0.0',
    styling_thesis: 'Industrial Romanticism',
    styling_thesis_ru: 'Индустриальная романтика',
    aesthetic: 'industrial romanticism',
    outfit_score: 74.0,
    critic_decision: 'REBUILD',
    critic_feedback: ['No clear hero piece. The outfit lacks a strong focal point.'],
    queries_used: ['индустриальный образ с прозрачным верхом sheer top'],
    queries_total: 11,
    candidates: { raw_items: 1442, considered: 103, validated: 100, outfits_built: 4 },
    taste_mix: { interesting: 7, designer: 2 },
    niche_level: 82,
    aesthetics: ['gothic', 'archive'],
  },
  thesis_options: ['Индустриальная романтика', 'Нео-готический эдиториал'],
  items: [
    {
      sku: 'TP-006',
      name: 'Топ-бюстье',
      brand: 'Atelier No.5',
      category: 'top',
      slot: 'top',
      slot_label: 'Верх',
      price_rub: 4990,
      url: 'https://example.test/tp-006',
      colors: ['black'],
      color_hexes: ['#111114'],
      score: 0.74,
      engine: {
        role: 'hero',
        role_label: 'ключевая вещь',
        taste_category: 'designer',
        taste_label: 'дизайнерская вещь',
        fashion_score: 71,
        silhouette: ['fitted'],
        material: 'silk',
        engine_category: 'top',
      },
      reasons: ['Разбор: ключевая вещь · дизайнерская вещь (71/100)'],
      verification_status: 'verified',
      verification_score: 0.99,
    },
  ],
  total_rub: 4990,
  budget_rub: 60000,
  suggested_request: {
    query: 'индустриальный образ с прозрачным верхом',
    style: 'grunge',
    mood: 'bold',
    occasion: 'everyday',
    season: 'autumn',
    presentation: 'feminine',
    budget_rub: 60000,
    height_cm: 172,
    weight_kg: 68,
    niche_level: 82,
  },
}

const look: Look = {
  id: 12,
  style: 'grunge',
  mood: 'bold',
  occasion: 'everyday',
  season: 'autumn',
  presentation: 'feminine',
  height_cm: 172,
  weight_kg: 68,
  budget_rub: 60000,
  total_rub: 47870,
  budget_utilization: 0.8,
  score: 81.9,
  verdict: { grade: 'B', title: 'Сильный образ', note: 'Почти идеально' },
  cohesion: { overall: 0.85 },
  summary: '«Индустриальная романтика» · оценка 72/100. Гранж: 4 вещи на 47 870 ₽ из 60 000 ₽.',
  personal_note: 'Гранж под уверенное настроение — нишевый референс-ряд.',
  tips: ['Один акцент на образ.'],
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
    signals: [],
  },
  palette: {
    temperature: 'neutral',
    depth: 'medium',
    chroma: 'soft',
    season_label: 'Мягкий переходный тип',
    recommended: ['black'],
    avoid: [],
    confidence: 0.25,
    source: 'defaults',
    dominant_colors: [],
    signals: [],
  },
  plan: 'layered',
  engine_version: '1.0.0',
  engine: {
    pipeline: 'asstylist-fashion-engine',
    engine_version: '1.0.0',
    styling_thesis: 'Industrial Romanticism',
    styling_thesis_ru: 'Индустриальная романтика',
    aesthetic: 'industrial',
    outfit_score: 72.0,
    app_score: 86.1,
    final_score: 81.9,
    score_formula: '70% приложение + 30% движок',
    critic_decision: 'REBUILD',
    critic_feedback: ['No clear hero piece. The outfit lacks a strong focal point.'],
    queries_used: ['индустриальный образ sheer top leather'],
    queries_total: 11,
    candidates: { raw_items: 1442, considered: 103, validated: 100, outfits_built: 4 },
    taste_mix: { interesting: 3, designer: 1 },
    niche_level: 78,
  },
  diagnostics: { candidates_total: 103, rejected_total: 4, warnings: [], dropped_slots: [], plan_description: 'Многослойный' },
  items: [
    {
      position: 0,
      slot: 'top',
      slot_label: 'Верх',
      sku: 'TP-006',
      category: 'top',
      name: 'Топ-бюстье',
      brand: 'Atelier No.5',
      price_rub: 4990,
      url: 'https://example.test/tp-006',
      image_url: '',
      colors: ['black'],
      color_hexes: ['#111114'],
      fit: 'regular',
      score: 0.74,
      breakdown: { style: 0.6, engine: 0.71 },
      engine: {
        role: 'layer',
        role_label: 'слой',
        taste_category: 'designer',
        taste_label: 'дизайнерская вещь',
        fashion_score: 71,
        in_engine_outfit: true,
        engine_category: 'top',
        material: 'silk',
      },
      reasons: ['Разбор: слой · дизайнерская вещь (71/100)'],
      verification_status: 'verified',
      verification_score: 0.99,
      source: 'lamoda',
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
    if (url.includes('/api/engine/search')) return jsonResponse(engineSearch)
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

async function openEngineSearch() {
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Найти вещи словами' }))
  expect(await screen.findByRole('heading', { name: /Что ищем/ })).toBeInTheDocument()
}

describe('Fashion Engine search screen', () => {
  it('searches the catalog through the engine and shows its thesis', async () => {
    const fetchMock = mockFetch()
    await openEngineSearch()

    fireEvent.change(screen.getByLabelText('Поисковый запрос'), {
      target: { value: 'индустриальный образ с прозрачным верхом' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Гранж' }))
    fireEvent.click(screen.getByRole('button', { name: 'Найти вещи' }))

    expect(await screen.findByText('Индустриальная романтика')).toBeInTheDocument()
    expect(screen.getByText('Топ-бюстье')).toBeInTheDocument()
    expect(screen.getByText('дизайнерская вещь')).toBeInTheDocument()
    expect(screen.getByText('fashion 71/100')).toBeInTheDocument()
    expect(screen.getByText(/Тезис образа/)).toBeInTheDocument()

    const searchCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/api/engine/search'))
    expect(searchCall).toBeTruthy()
    const body = JSON.parse(String((searchCall?.[1] as RequestInit).body))
    expect(body.query).toBe('индустриальный образ с прозрачным верхом')
    expect(body.style).toBe('grunge')
    expect(body.limit).toBe(8)
  })

  it('builds a look from the engine query and renders engine metadata', async () => {
    const fetchMock = mockFetch()
    await openEngineSearch()

    fireEvent.click(screen.getByRole('button', { name: 'Индустриальная романтика' }))
    await screen.findByText('Топ-бюстье')

    fireEvent.click(screen.getByRole('button', { name: 'Собрать образ по этому запросу' }))

    await waitFor(() => expect(screen.getByText('Тезис образа')).toBeInTheDocument())
    expect(screen.getByText('Индустриальная романтика')).toBeInTheDocument()
    expect(screen.getByText(/fit score/)).toBeInTheDocument()

    const generateCall = fetchMock.mock.calls.find(([url]) => String(url).includes('/api/looks/generate'))
    expect(generateCall).toBeTruthy()
    const body = (generateCall?.[1] as RequestInit).body as FormData
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('query')).toBe('индустриальный образ с прозрачным верхом')
    expect(body.get('niche_level')).toBe('82')
    expect(body.get('style')).toBe('grunge')
  })

  it('renders engine badges on look items', async () => {
    mockFetch()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Собрать образ' }))
    for (const step of ['Параметры', 'Стиль', 'Настроение', 'Детали']) {
      fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
      await screen.findByRole('heading', { name: new RegExp(step) })
    }
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByRole('heading', { name: /Проверка/ })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Своя формулировка образа'), {
      target: { value: 'грязный индустриальный образ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Сгенерировать' }))

    expect(await screen.findByText('Сильный образ')).toBeInTheDocument()
    expect(screen.getByText('слой')).toBeInTheDocument()
    expect(screen.getByText('fashion 71/100')).toBeInTheDocument()
    expect(screen.getByText(/Разбор: слой · дизайнерская вещь/)).toBeInTheDocument()
  })

  it('shows the engine error when search fails', async () => {
    mockFetch({ '/api/engine/search': () => jsonResponse({ detail: 'Нужен текстовый запрос длиной от 2 символов' }, 422) })
    await openEngineSearch()

    fireEvent.change(screen.getByLabelText('Поисковый запрос'), { target: { value: 'образ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Найти вещи' }))

    expect(await screen.findByText('Нужен текстовый запрос длиной от 2 символов')).toBeInTheDocument()
  })
})
