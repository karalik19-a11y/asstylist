/**
 * Память о человеке: рост и вес.
 *
 * Данные вводятся один раз. При следующем входе сервис показывает выбор —
 * «собрать по сохранённым» или «ввести новые рост и вес». Хранится ровно это:
 * стиль, настроение и бюджет спрашиваются каждый раз, иначе образ застынет.
 *
 * Память дублируется: мгновенно — в localStorage (работает и без сети), и на
 * сервере (переживает переустановку и другой телефон), см. /api/profile.
 */

import { api } from './api'

export interface BodyMemory {
  height_cm: number
  weight_kg: number
  updatedAt: string | null
  usedCount: number
}

const STORAGE_KEY = 'asstylist.body.v1'

interface StoredBody {
  height_cm: number
  weight_kg: number
  updatedAt?: string | null
  usedCount?: number
}

function isBody(value: unknown): value is StoredBody {
  const candidate = value as { height_cm?: unknown; weight_kg?: unknown } | null
  const height = Number(candidate?.height_cm)
  const weight = Number(candidate?.weight_kg)
  return Number.isFinite(height) && Number.isFinite(weight) && height >= 120 && weight >= 30
}

/** Что помним локально (мгновенно, без сети). */
export function readLocalBody(): BodyMemory | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Record<string, unknown>
    if (!isBody(parsed)) return null
    return {
      height_cm: Number(parsed.height_cm),
      weight_kg: Number(parsed.weight_kg),
      updatedAt: typeof parsed.updatedAt === 'string' ? parsed.updatedAt : null,
      usedCount: Number(parsed.usedCount ?? 0),
    }
  } catch {
    return null
  }
}

/** Запомнить локально (молча — локальное хранилище может быть запрещено). */
export function writeLocalBody(memory: BodyMemory | null): void {
  try {
    if (!memory) {
      localStorage.removeItem(STORAGE_KEY)
      return
    }
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        height_cm: memory.height_cm,
        weight_kg: memory.weight_kg,
        updatedAt: memory.updatedAt,
        usedCount: memory.usedCount,
      }),
    )
  } catch {
    /* приватный режим браузера — не беда */
  }
}

/**
 * Память с сервера (там она надёжнее), с откатом на локальную копию:
 * приложение должно предлагать выбор даже без сети.
 */
export async function loadBodyMemory(): Promise<BodyMemory | null> {
  try {
    const remote = await api.profile()
    if (remote?.saved && isBody(remote.profile)) {
      const memory: BodyMemory = {
        height_cm: Number(remote.profile.height_cm),
        weight_kg: Number(remote.profile.weight_kg),
        updatedAt: remote.updated_at ?? null,
        usedCount: Number(remote.used_count ?? 0),
      }
      writeLocalBody(memory)
      return memory
    }
    if (remote && !remote.saved) {
      // На сервере пусто — значит и локальная копия неактуальна.
      writeLocalBody(null)
      return null
    }
  } catch {
    /* сервер недоступен — покажем локальную память */
  }
  return readLocalBody()
}

/** Сохранить рост и вес (на сервере и локально). Возвращает то, что запомнили. */
export async function saveBodyMemory(heightCm: number, weightKg: number): Promise<BodyMemory> {
  const local: BodyMemory = {
    height_cm: heightCm,
    weight_kg: weightKg,
    updatedAt: new Date().toISOString(),
    usedCount: 0,
  }
  writeLocalBody(local)
  try {
    const remote = await api.saveProfile({ height_cm: heightCm, weight_kg: weightKg })
    if (remote?.saved && isBody(remote.profile)) {
      const memory: BodyMemory = {
        height_cm: Number(remote.profile.height_cm),
        weight_kg: Number(remote.profile.weight_kg),
        updatedAt: remote.updated_at ?? local.updatedAt,
        usedCount: Number(remote.used_count ?? 0),
      }
      writeLocalBody(memory)
      return memory
    }
  } catch {
    /* офлайн: локальная копия всё равно работает */
  }
  return local
}

/** Отметить, что сохранёнными данными воспользовались (счётчик в ответе). */
export async function markBodyUsed(): Promise<void> {
  try {
    await api.useProfile()
  } catch {
    /* не критично */
  }
}

/** «Забыть мои данные» — чистка и на сервере, и локально. */
export async function forgetBodyMemory(): Promise<void> {
  writeLocalBody(null)
  try {
    await api.forgetProfile()
  } catch {
    /* не критично: локально уже забыли */
  }
}

/** Человеческая подпись сохранённых данных: «174 см · 64 кг». */
export function bodyLabel(memory: BodyMemory | null): string {
  if (!memory) return ''
  return `${Math.round(memory.height_cm)} см · ${Math.round(memory.weight_kg)} кг`
}

/** Когда данные обновляли: «12.09» или «12.09.2025». */
export function bodyUpdatedLabel(memory: BodyMemory | null): string {
  if (!memory?.updatedAt) return ''
  const date = new Date(memory.updatedAt)
  if (Number.isNaN(date.getTime())) return ''
  const now = new Date()
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  if (date.getFullYear() === now.getFullYear()) return `${day}.${month}`
  return `${day}.${month}.${date.getFullYear()}`
}
