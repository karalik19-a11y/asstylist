import type { AppData, Outfit, Profile, WardrobeItem } from '../types'
import { randomId } from './color'
import { CATEGORY_ORDER, DEFAULT_PROFILE, DEMO_ITEMS, STYLE_ORDER } from './catalog'

export const STORAGE_KEY = 'asstylist:v1'
export const DATA_VERSION = 1

export function emptyData(): AppData {
  return { version: DATA_VERSION, profile: { ...DEFAULT_PROFILE }, items: [], outfits: [] }
}

export function createDemoData(): AppData {
  return {
    version: DATA_VERSION,
    profile: { ...DEFAULT_PROFILE, name: 'Мой гардероб' },
    items: DEMO_ITEMS.map((item) => ({ ...item, id: randomId('item'), wornDates: [] })),
    outfits: [],
  }
}

function coerceItem(raw: unknown): WardrobeItem | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const category = CATEGORY_ORDER.includes(r.category as never) ? (r.category as WardrobeItem['category']) : null
  if (!category || typeof r.name !== 'string') return null
  return {
    id: typeof r.id === 'string' ? r.id : randomId('item'),
    name: r.name,
    category,
    colorHex: typeof r.colorHex === 'string' ? r.colorHex : '#808080',
    styles: Array.isArray(r.styles) ? (r.styles.filter((s) => STYLE_ORDER.includes(s as never)) as WardrobeItem['styles']) : ['casual'],
    seasons: Array.isArray(r.seasons) && r.seasons.length ? (r.seasons as WardrobeItem['seasons']) : ['all'],
    warmth: clamp(Number(r.warmth) || 2, 1, 5),
    formality: clamp(Number(r.formality) || 3, 1, 5),
    image: typeof r.image === 'string' ? r.image : undefined,
    favorite: Boolean(r.favorite),
    wornDates: Array.isArray(r.wornDates) ? r.wornDates.filter((d): d is string => typeof d === 'string') : [],
  }
}

function coerceOutfit(raw: unknown, validIds: Set<string>): Outfit | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const itemIds = Array.isArray(r.itemIds) ? r.itemIds.filter((id): id is string => typeof id === 'string' && validIds.has(id)) : []
  if (itemIds.length === 0) return null
  const analysis = (r.analysis ?? {}) as Outfit['analysis']
  return {
    id: typeof r.id === 'string' ? r.id : randomId('outfit'),
    itemIds,
    occasion: (r.occasion as Outfit['occasion']) ?? 'walk',
    season: (r.season as Outfit['season']) ?? 'all',
    temperature: Number(r.temperature) || 15,
    score: Number(r.score) || 0,
    analysis: {
      total: Number(analysis?.total) || Number(r.score) || 0,
      parts: Array.isArray(analysis?.parts) ? analysis.parts : [],
      tips: Array.isArray(analysis?.tips) ? analysis.tips : [],
      scheme: typeof analysis?.scheme === 'string' ? analysis.scheme : '—',
    },
    saved: true,
    createdAt: typeof r.createdAt === 'string' ? r.createdAt : new Date().toISOString(),
    plannedFor: typeof r.plannedFor === 'string' ? r.plannedFor : undefined,
  }
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

export function loadData(): AppData {
  if (typeof localStorage === 'undefined') return emptyData()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return emptyData()
    return normalize(JSON.parse(raw))
  } catch {
    return emptyData()
  }
}

export function normalize(input: unknown): AppData {
  if (!input || typeof input !== 'object') return emptyData()
  const data = input as Record<string, unknown>
  const items = Array.isArray(data.items)
    ? data.items.map(coerceItem).filter((i): i is WardrobeItem => i !== null)
    : []
  const validIds = new Set(items.map((i) => i.id))
  const outfits = Array.isArray(data.outfits)
    ? data.outfits.map((o) => coerceOutfit(o, validIds)).filter((o): o is Outfit => o !== null)
    : []
  const profileRaw = (data.profile ?? {}) as Partial<Profile>
  return {
    version: DATA_VERSION,
    profile: {
      name: typeof profileRaw.name === 'string' ? profileRaw.name : '',
      colorSeason: profileRaw.colorSeason ?? DEFAULT_PROFILE.colorSeason,
      preferredStyles: Array.isArray(profileRaw.preferredStyles)
        ? (profileRaw.preferredStyles.filter((s) => STYLE_ORDER.includes(s as never)) as Profile['preferredStyles'])
        : [...DEFAULT_PROFILE.preferredStyles],
      avoidColors: Array.isArray(profileRaw.avoidColors)
        ? profileRaw.avoidColors.filter((c): c is string => typeof c === 'string')
        : [],
      notes: typeof profileRaw.notes === 'string' ? profileRaw.notes : '',
    },
    items,
    outfits,
  }
}

export function saveData(data: AppData): void {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // переполнение localStorage (большие фото) — молча продолжаем работать в памяти
  }
}

export function exportJson(data: AppData): string {
  return JSON.stringify(data, null, 2)
}
