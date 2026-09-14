import type { HistoryEntry, Look, Meta, SetupResponse, TelegramStatus, WizardState } from './types'
import { getWebApp, telegramUserId, telegramUserName } from './telegram'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
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

  /** Connects a real bot: validates the token and sets the Mini App menu button. */
  connectBot: (botToken: string, webAppUrl: string, keepDemoAccess = true) =>
    request<SetupResponse>('/api/telegram/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bot_token: botToken,
        web_app_url: webAppUrl,
        keep_demo_access: keepDemoAccess,
        persist: true,
      }),
    }),

  /** Multipart so the photo travels with the parameters in a single call. */
  generateLook: (state: WizardState) => {
    const form = new FormData()
    const fields: Record<string, string | number | null> = {
      style: state.style,
      mood: state.mood,
      occasion: state.occasion,
      season: state.season,
      presentation: state.presentation,
      height_cm: state.height_cm,
      weight_kg: state.weight_kg,
      budget_rub: state.budget_rub,
      preferred_colors: state.preferred_colors.join(','),
      avoid_colors: state.avoid_colors.join(','),
      size: state.size,
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

  history: (limit = 20) =>
    request<{ items: HistoryEntry[] }>(`/api/looks?${identityParams().toString()}&limit=${limit}`),

  look: (id: number) => request<Look>(`/api/looks/${id}?${identityParams().toString()}`),

  swapItem: (id: number, slot: string, excludeSkus: string[] = []) =>
    request<Look>(`/api/looks/${id}/swap?${identityParams().toString()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot, exclude_skus: excludeSkus }),
    }),

  toggleFavorite: (id: number) =>
    request<{ id: number; is_favorite: boolean }>(`/api/looks/${id}/favorite?${identityParams().toString()}`, {
      method: 'POST',
    }),

  verification: () =>
    request<{
      total: number
      verified: number
      warning: number
      failed: number
      eligible: number
      network_enabled: boolean
      ttl_days: number
      min_score: number
      items: { sku: string; name: string; source: string; status: string; score: number; issues: string[] }[]
    }>('/api/catalog/verification'),
}
