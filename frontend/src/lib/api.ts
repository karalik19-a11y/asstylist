import type {
  EngineSearchResult,
  HistoryEntry,
  Look,
  Meta,
  SetupResponse,
  TelegramStatus,
  WizardState,
} from './types'
import { getWebApp, telegramUserId, telegramUserName } from './telegram'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
const REQUEST_TIMEOUT_MS = 90_000

export function photoProxyUrl(url: string): string {
  return `${BASE}/api/media/photo?u=${encodeURIComponent(url)}`
}

export function isAvitoPhotoUrl(url?: string | null): boolean {
  if (!url) return false
  try {
    const host = new URL(url, 'https://asstylist.local').hostname.toLowerCase()
    return host === 'avito.st' || host.endsWith('.avito.st') || host === 'avito.ru' || host.endsWith('.avito.ru')
  } catch {
    return url.includes('avito.st')
  }
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  const externalSignal = init.signal
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort()
    else externalSignal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  try {
    const response = await fetch(`${BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { Accept: 'application/json', ...(init.headers ?? {}) },
    })
    if (!response.ok) {
      let detail = `Ошибка запроса (${response.status})`
      try {
        const body = await response.json()
        if (body && typeof body.detail === 'string') detail = body.detail
      } catch {
        /* keep the generic message */
      }
      throw new ApiError(detail, response.status)
    }
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Сервер не ответил вовремя. Попробуйте ещё раз.', 408)
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}

function identityParams(): URLSearchParams {
  const params = new URLSearchParams()
  const initData = getWebApp()?.initData
  if (initData) params.set('init_data', initData)
  const id = telegramUserId()
  if (id) params.set('demo_user_id', id)
  return params
}

export const api = {
  health: () => request<Record<string, unknown>>('/api/health'),
  meta: () => request<Meta>('/api/meta'),
  auth: () =>
    request<{ user: { id: number; telegram_id: string; first_name: string | null }; demo: boolean; mode: string }>(
      '/api/telegram/auth',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          init_data: getWebApp()?.initData ?? null,
          demo_user_id: telegramUserId(),
          first_name: telegramUserName(),
          username: getWebApp()?.initDataUnsafe?.user?.username ?? null,
        }),
      },
    ),
  telegramStatus: () => request<TelegramStatus>('/api/telegram/status'),
  connectBot: (botToken: string, webAppUrl: string, keepDemoAccess = true) =>
    request<SetupResponse>('/api/telegram/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_token: botToken, web_app_url: webAppUrl, keep_demo_access: keepDemoAccess, persist: true }),
    }),
  generateLook: (state: WizardState) => {
    const form = new FormData()
    const fields: Record<string, string | number | null> = {
      style: state.style, mood: state.mood, occasion: state.occasion, season: state.season,
      presentation: state.presentation, height_cm: state.height_cm, weight_kg: state.weight_kg,
      budget_rub: state.budget_rub, preferred_colors: state.preferred_colors.join(','),
      avoid_colors: state.avoid_colors.join(','), size: state.size, query: state.query, niche_level: state.niche_level,
    }
    for (const [key, value] of Object.entries(fields)) {
      if (value !== null && value !== undefined && value !== '') form.set(key, String(value))
    }
    const initData = getWebApp()?.initData
    if (initData) form.set('init_data', initData)
    const userId = telegramUserId()
    if (userId) form.set('demo_user_id', userId)
    if (state.photoFile) form.set('photo', state.photoFile, state.photoFile.name || 'photo.jpg')
    return request<Look>('/api/looks/generate', { method: 'POST', body: form })
  },
  engineSearch: (params: {
    query: string; style?: string; mood?: string; occasion?: string; season?: string; presentation?: string;
    height_cm?: number; weight_kg?: number; budget_rub?: number; preferred_colors?: string[]; avoid_colors?: string[];
    size?: string | null; niche_level?: number | null; limit?: number
  }) =>
    request<EngineSearchResult>('/api/engine/search', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ limit: 8, ...params }),
    }),
  profile: () => request<{ saved: boolean; profile: { height_cm?: number; weight_kg?: number }; updated_at: string | null; used_count: number; problems?: string[]; user?: { id: number; telegram_id: string; username: string | null; first_name: string | null; is_demo: boolean; signature_color: string | null; registered: boolean } }>(`/api/profile?${identityParams().toString()}`),
  saveProfile: (payload: { height_cm?: number; weight_kg?: number }) => request<{ saved: boolean; profile: { height_cm?: number; weight_kg?: number }; updated_at: string | null; used_count: number; problems?: string[] }>(`/api/profile?${identityParams().toString()}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  useProfile: () => request<{ used_count: number }>(`/api/profile/used?${identityParams().toString()}`, { method: 'POST' }),
  forgetProfile: () => request<{ saved: boolean }>(`/api/profile/reset?${identityParams().toString()}`, { method: 'POST' }),
  registerProfile: () => request<{ ok: boolean; already_registered: boolean; user: { id: number; telegram_id: string; username: string | null; first_name: string | null; is_demo: boolean; signature_color: string | null; registered: boolean } }>(`/api/profile/register?${identityParams().toString()}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }),
  history: (limit = 100, favoriteOnly = false) => {
    const params = identityParams()
    params.set('limit', String(Math.min(Math.max(limit, 1), 100)))
    params.set('favorite', favoriteOnly ? 'true' : 'false')
    return request<{ items: HistoryEntry[] }>(`/api/looks?${params.toString()}`)
  },
  look: (id: number) => request<Look>(`/api/looks/${id}?${identityParams().toString()}`),
  swapItem: (id: number, slot: string, excludeSkus: string[] = []) => request<Look>(`/api/looks/${id}/swap?${identityParams().toString()}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot, exclude_skus: excludeSkus }) }),
  toggleFavorite: (id: number) => request<{ id: number; is_favorite: boolean }>(`/api/looks/${id}/favorite?${identityParams().toString()}`, { method: 'POST' }),
  verification: () => request<{ total: number; verified: number; warning: number; failed: number; eligible: number; network_enabled: boolean; ttl_days: number; min_score: number; items: { sku: string; name: string; source: string; status: string; score: number; issues: string[] }[] }>('/api/catalog/verification'),
}
