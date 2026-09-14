import type {
  OccasionKey,
  Outfit,
  OutfitAnalysis,
  Profile,
  ScorePart,
  SeasonKey,
  WardrobeItem,
} from '../types'
import {
  analyzeHarmony,
  closestPaletteColor,
  hexToHsl,
  hueDistance,
  randomId,
  seasonFit,
} from './color'
import { CATEGORY_LABEL, OCCASION_MAP, SEASON_LABEL, STYLE_LABEL } from './catalog'

export function isoDate(d: Date = new Date()): string {
  const off = d.getTimezoneOffset()
  return new Date(d.getTime() - off * 60_000).toISOString().slice(0, 10)
}

export function addDays(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00`)
  d.setDate(d.getDate() + days)
  return isoDate(d)
}

export function daysBetween(a: string, b: string): number {
  const da = new Date(`${a}T00:00:00`).getTime()
  const db = new Date(`${b}T00:00:00`).getTime()
  return Math.round((db - da) / 86_400_000)
}

const WEEKDAY_LABELS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

export function weekdayLabel(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`)
  const idx = (d.getDay() + 6) % 7
  return WEEKDAY_LABELS[idx]
}

export function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split('-')
  return `${d}.${m}.${y}`
}

/** Подходит ли вещь для выбранного сезона */
export function suitsSeason(item: WardrobeItem, season: SeasonKey): boolean {
  if (season === 'all') return true
  return item.seasons.includes('all') || item.seasons.includes(season)
}

/** Сколько тепла нужно комплекту при заданной температуре (°C) */
export function warmthTarget(temperature: number): number {
  const table: Array<[number, number]> = [
    [-20, 9.5],
    [-10, 9.0],
    [-5, 8.6],
    [0, 8.0],
    [4, 7.4],
    [10, 6.2],
    [15, 4.8],
    [19, 3.4],
    [24, 2.4],
    [28, 1.6],
    [35, 1.2],
  ]
  if (temperature <= table[0][0]) return table[0][1]
  if (temperature >= table[table.length - 1][0]) return table[table.length - 1][1]
  for (let i = 0; i < table.length - 1; i++) {
    const [t0, v0] = table[i]
    const [t1, v1] = table[i + 1]
    if (temperature >= t0 && temperature <= t1) {
      return v0 + ((v1 - v0) * (temperature - t0)) / (t1 - t0)
    }
  }
  return 5
}

const CORE_CATEGORIES = new Set(['top', 'bottom', 'dress', 'outerwear'])

function outfitWarmth(items: WardrobeItem[]): number {
  let core = 0
  let outer = 0
  for (const it of items) {
    if (it.category === 'outerwear') outer = Math.max(outer, it.warmth)
    else if (CORE_CATEGORIES.has(it.category)) core = Math.max(core, it.warmth)
  }
  return core + outer * 0.8
}

function freshnessOfItem(item: WardrobeItem, today: string): number {
  const past = item.wornDates.filter((d) => daysBetween(d, today) >= 0)
  if (past.length === 0) return 1
  const last = past.sort().reverse()[0]
  const gap = daysBetween(last, today)
  if (gap < 2) return 0.2
  if (gap < 4) return 0.5
  if (gap < 7) return 0.78
  return 1
}

/** Вес сумки и аксессуаров: они дополняют комплект, но не определяют его характер */
const ACCENT_WEIGHT = 0.25

function isAccent(category: WardrobeItem['category']): boolean {
  return category === 'bag' || category === 'accessory'
}

function weightedFormality(items: WardrobeItem[]): number {
  let sum = 0
  let w = 0
  for (const it of items) {
    const weight = isAccent(it.category) ? ACCENT_WEIGHT : 1
    sum += it.formality * weight
    w += weight
  }
  return w === 0 ? 3 : sum / w
}

/**
 * Разбор образа: оценка 0..100 с расшифровкой по шести критериям
 * и списком советов стилиста.
 */
export function analyzeOutfit(
  items: WardrobeItem[],
  profile: Profile,
  occasionKey: OccasionKey,
  temperature: number,
  today: string = isoDate(),
): OutfitAnalysis {
  const cfg = OCCASION_MAP[occasionKey]
  const harmony = analyzeHarmony(items.map((i) => i.colorHex))

  const occasionValue = Math.max(
    0,
    1 - Math.min(1, Math.abs(weightedFormality(items) - cfg.targetFormality) / 2.2),
  )

  const preferred = new Set([...cfg.styles, ...profile.preferredStyles])
  let matched = 0
  let weight = 0
  for (const it of items) {
    const w = isAccent(it.category) ? ACCENT_WEIGHT : 1
    weight += w
    if (it.styles.some((s) => preferred.has(s))) matched += w
  }
  const styleMatch = weight === 0 ? 0.5 : matched / weight

  // Согласованность: доля вещей, объединённых одним общим стилем.
  const counts = new Map<string, number>()
  for (const it of items) for (const s of it.styles) counts.set(s, (counts.get(s) ?? 0) + 1)
  const coherence = items.length === 0 ? 0.5 : Math.max(...counts.values()) / items.length
  const styleValue = Math.min(1, 0.6 * styleMatch + 0.4 * coherence)

  let paletteSum = 0
  let worstItem: WardrobeItem | null = null
  let worstFit = 2
  for (const it of items) {
    const fit = seasonFit(it.colorHex, profile.colorSeason)
    paletteSum += fit
    if (fit < worstFit) {
      worstFit = fit
      worstItem = it
    }
  }
  let paletteValue = items.length === 0 ? 0.5 : paletteSum / items.length

  let avoidHit = false
  for (const it of items) {
    const hsl = hexToHsl(it.colorHex)
    if (hsl.s < 0.15) continue
    for (const avoid of profile.avoidColors) {
      if (hueDistance(hsl.h, hexToHsl(avoid).h) < 18) avoidHit = true
    }
  }
  if (avoidHit) paletteValue = Math.max(0, paletteValue - 0.28)

  const warmth = outfitWarmth(items)
  const target = warmthTarget(temperature)
  let weatherValue = 1 - Math.min(1, Math.abs(warmth - target) / 3.2)
  const hasOuter = items.some((i) => i.category === 'outerwear')
  if (temperature < 8 && !hasOuter) weatherValue *= 0.55
  if (temperature > 24 && warmth > target + 1.5) weatherValue *= 0.7
  weatherValue = Math.max(0, weatherValue)

  let freshSum = 0
  for (const it of items) freshSum += freshnessOfItem(it, today)
  const freshnessValue = items.length === 0 ? 0.5 : freshSum / items.length

  const parts: ScorePart[] = [
    {
      key: 'harmony',
      label: 'Гармония цвета',
      value: harmony.score,
      weight: 26,
      hint: harmony.note,
    },
    {
      key: 'occasion',
      label: 'Соответствие случаю',
      value: occasionValue,
      weight: 22,
      hint: `формальность образа ${weightedFormality(items).toFixed(1)} из 5, нужно ${cfg.targetFormality.toFixed(1)}`,
    },
    {
      key: 'style',
      label: 'Стиль и целостность',
      value: styleValue,
      weight: 16,
      hint: `ожидаемые стили: ${cfg.styles.map((s) => STYLE_LABEL[s].toLowerCase()).join(', ')}`,
    },
    {
      key: 'palette',
      label: 'Цветотип',
      value: paletteValue,
      weight: 12,
      hint:
        avoidHit
          ? 'в образе есть оттенок из списка «не носить»'
          : `палитра «${SEASON_LABEL[profile.colorSeason]}»`,
    },
    {
      key: 'weather',
      label: 'Погода и сезон',
      value: weatherValue,
      weight: 14,
      hint: `тепло комплекта ${warmth.toFixed(1)}, нужно ${target.toFixed(1)} при ${temperature > 0 ? '+' : ''}${temperature} °C`,
    },
    {
      key: 'freshness',
      label: 'Свежесть ротации',
      value: freshnessValue,
      weight: 10,
      hint: 'насколько давно вещи выходили в свет',
    },
  ]

  const total = Math.round(parts.reduce((acc, p) => acc + p.value * p.weight, 0))

  const tips: string[] = []
  if (harmony.score >= 0.9) tips.push(`Цвет удачный: ${harmony.scheme}.`)
  else if (harmony.score < 0.62)
    tips.push('Цвета спорят друг с другом: оставьте один акцент, остальное переведите в нейтральное.')
  if (occasionValue < 0.6) {
    tips.push(
      weightedFormality(items) > cfg.targetFormality
        ? 'Для этого случая образ слишком строгий — опустите формальность: джинсы вместо брюк, кроссовки вместо лодер.'
        : 'Образ слишком расслабленный для случая — добавьте структурную вещь: жакет, рубашку или лоферы.',
    )
  }
  if (styleValue < 0.55) tips.push('Вещи из разных стилистических семейств — замените самую выбивающуюся.')
  if (worstItem && worstFit < 0.45 && !avoidHit) {
    tips.push(
      `«${worstItem.name}» далек от вашей палитры — попробуйте оттенок ${closestPaletteColor(worstItem.colorHex, profile.colorSeason).toUpperCase()}.`,
    )
  }
  if (avoidHit) tips.push('В комплекте есть цвет из вашего списка «не носить».')
  if (temperature < 8 && !hasOuter) tips.push('Ниже +8 °C без верхней одежды — добавьте пальто или куртку.')
  else if (warmth < target - 1.2) tips.push('Прохладно для этого комплекта: добавьте тёплый слой — свитер, кардиган, шарф.')
  else if (warmth > target + 1.2) tips.push('Будет жарко: замените самую тёплую вещь на более лёгкую.')
  if (freshnessValue < 0.6) tips.push('Часть вещей уже была на этой неделе — дайте им отдохнуть.')
  if (tips.length === 0) tips.push('Сбалансированный образ: цвет, случай, сезон и ротация совпали.')

  return { total, parts, tips, scheme: harmony.scheme }
}

export function gradeOf(score: number): string {
  if (score >= 85) return 'отлично'
  if (score >= 72) return 'хорошо'
  if (score >= 58) return 'нормально'
  return 'рискованно'
}

/** Вещи, из которых вообще можно собирать образ для данного повода и сезона */
export function poolFor(
  items: WardrobeItem[],
  occasion: OccasionKey,
  season: SeasonKey,
): WardrobeItem[] {
  return items.filter(
    (i) =>
      suitsSeason(i, season) &&
      (occasion !== 'sport' || i.styles.includes('sport') || i.category === 'accessory'),
  )
}

/** Каких обязательных категорий не хватает для выбранного повода */
export function missingSlots(
  items: WardrobeItem[],
  occasion: OccasionKey,
  season: SeasonKey,
): string[] {
  const pool = poolFor(items, occasion, season)
  const have = new Set(pool.map((i) => i.category))
  let best: string[] | null = null
  for (const template of OCCASION_MAP[occasion].templates) {
    const missing = template
      .filter((slot) => slot.required && !have.has(slot.category))
      .map((slot) => CATEGORY_LABEL[slot.category].one.toLowerCase())
    if (!best || missing.length < best.length) best = missing
  }
  return best ?? []
}

interface GenerateOptions {
  items: WardrobeItem[]
  profile: Profile
  occasion: OccasionKey
  season: SeasonKey
  temperature: number
  limit?: number
  /** Меняйте seed, чтобы получить другие варианты при тех же вводных */
  seed?: number
  today?: string
}

function hashUnit(str: string, seed: number): number {
  let h = 2166136261 ^ (seed * 2654435761)
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 10000) / 10000
}

/**
 * Генератор образов: перебирает схемы комплекта, отбирает лучшие вещи
 * в каждый слот и оценивает получившиеся сочетания.
 */
export function generateOutfits(opts: GenerateOptions): Outfit[] {
  const { items, profile, occasion, season, temperature, limit = 6, seed = 1 } = opts
  const today = opts.today ?? isoDate()
  const cfg = OCCASION_MAP[occasion]
  const pool = poolFor(items, occasion, season)

  const scoreItem = (item: WardrobeItem) => {
    const formalityFit = 1 - Math.min(1, Math.abs(item.formality - cfg.targetFormality) / 3)
    const styleFit = item.styles.some((s) => cfg.styles.includes(s) || profile.preferredStyles.includes(s))
      ? 1
      : 0
    const palette = seasonFit(item.colorHex, profile.colorSeason)
    const fresh = freshnessOfItem(item, today)
    const favorite = item.favorite ? 0.05 : 0
    return (
      0.4 * formalityFit +
      0.28 * styleFit +
      0.17 * palette +
      0.1 * fresh +
      favorite +
      0.08 * hashUnit(item.id, seed)
    )
  }

  const byCategory = new Map<string, WardrobeItem[]>()
  for (const item of pool) {
    const list = byCategory.get(item.category) ?? []
    list.push(item)
    byCategory.set(item.category, list)
  }
  for (const list of byCategory.values()) list.sort((a, b) => scoreItem(b) - scoreItem(a))

  const candidates: WardrobeItem[][] = []
  const MAX_COMBOS = 4000

  for (const template of cfg.templates) {
    const slots = template.map((slot) => {
      const list = (byCategory.get(slot.category) ?? []).slice(0, 6)
      const options: Array<WardrobeItem | null> = [...list]
      if (!slot.required) options.push(null)
      return options
    })
    if (slots.some((s, idx) => template[idx].required && s.length === 0)) continue

    const build = (idx: number, acc: WardrobeItem[]) => {
      if (candidates.length >= MAX_COMBOS) return
      if (idx === slots.length) {
        if (acc.length > 0) candidates.push([...acc])
        return
      }
      for (const option of slots[idx]) {
        if (candidates.length >= MAX_COMBOS) return
        if (option) acc.push(option)
        build(idx + 1, acc)
        if (option) acc.pop()
      }
    }
    build(0, [])
  }

  const scored: Outfit[] = []
  const seen = new Set<string>()
  for (const combo of candidates) {
    if (combo.length < 2) continue
    const key = combo
      .map((i) => i.id)
      .sort()
      .join('|')
    if (seen.has(key)) continue
    seen.add(key)

    const filled = combo.length
    const maxSlots = Math.max(...cfg.templates.map((t) => t.length))
    const completeness = 0.93 + 0.07 * Math.min(1, filled / Math.min(maxSlots, 5))

    const analysis = analyzeOutfit(combo, profile, occasion, temperature, today)
    const total = Math.round(analysis.total * completeness)
    scored.push({
      id: randomId('outfit'),
      itemIds: combo.map((i) => i.id),
      occasion,
      season,
      temperature,
      score: total,
      analysis: { ...analysis, total },
      saved: false,
      createdAt: new Date().toISOString(),
    })
  }

  scored.sort((a, b) => b.score - a.score)

  // Ре-ранжирование ради разнообразия: штрафуем похожие на уже выбранные комплекты.
  const picked: Outfit[] = []
  const pickedSets = picked.map((o) => new Set(o.itemIds))
  for (const outfit of scored) {
    if (picked.length >= limit) break
    let penalty = 0
    const ids = new Set(outfit.itemIds)
    for (const set of pickedSets) {
      let shared = 0
      for (const id of ids) if (set.has(id)) shared++
      if (shared >= 2) penalty += 4 * (shared - 1)
    }
    const adjusted = outfit.score - Math.min(penalty, 14)
    if (picked.length >= limit && adjusted <= 60) continue
    picked.push({ ...outfit, score: Math.round(adjusted), analysis: { ...outfit.analysis, total: Math.round(adjusted) } })
    pickedSets.push(new Set(outfit.itemIds))
  }
  picked.sort((a, b) => b.score - a.score)
  return picked
}

export interface WeekDayPlan {
  date: string
  label: string
  occasion: OccasionKey
  outfit: Outfit | null
}

export interface WeekPlanOptions {
  items: WardrobeItem[]
  profile: Profile
  season: SeasonKey
  temperature: number
  startDate: string
  occasionsByDate: Record<string, OccasionKey>
}

/**
 * План на 7 дней: каждый день генерируется отдельно, а надетые вещи
 * учитываются при подборе следующих дней — гардероб равномерно rotates.
 */
export function buildWeekPlan(opts: WeekPlanOptions): WeekDayPlan[] {
  const { items, profile, season, temperature, startDate, occasionsByDate } = opts
  const simulated = items.map((i) => ({ ...i, wornDates: [...i.wornDates] }))
  const days: WeekDayPlan[] = []

  for (let i = 0; i < 7; i++) {
    const date = addDays(startDate, i)
    const occasion = occasionsByDate[date] ?? 'work'
    const outfits = generateOutfits({
      items: simulated,
      profile,
      occasion,
      season,
      temperature,
      limit: 4,
      seed: 7 + i * 13,
      today: date,
    })
    const chosen = outfits[0] ?? null
    if (chosen) {
      for (const id of chosen.itemIds) {
        const item = simulated.find((it) => it.id === id)
        if (item) item.wornDates = [...item.wornDates, date]
      }
    }
    days.push({ date, label: weekdayLabel(date), occasion, outfit: chosen })
  }
  return days
}

export interface AuditNote {
  level: 'good' | 'warn' | 'info'
  title: string
  text: string
}

/** Аудит гардероба: что есть, чего не хватает и что мешает собирать образы */
export function wardrobeAudit(items: WardrobeItem[], profile: Profile): AuditNote[] {
  const notes: AuditNote[] = []
  if (items.length === 0) {
    return [
      {
        level: 'info',
        title: 'Гардероб пуст',
        text: 'Добавьте хотя бы 5–7 вещей или загрузите демо-гардероб — дальше стилист соберёт из них образы.',
      },
    ]
  }

  const count = (cat: string) => items.filter((i) => i.category === cat).length

  if (count('top') < 3)
    notes.push({
      level: 'warn',
      title: 'Мало верха',
      text: `Верхних вещей: ${count('top')}. Для ротации на неделю нужно минимум 3–4.`,
    })
  if (count('bottom') < 2)
    notes.push({
      level: 'warn',
      title: 'Мало низа',
      text: `Низов: ${count('bottom')}. Добавьте вторую пару брюк или юбку, чтобы образы не повторялись.`,
    })
  if (count('shoes') < 2)
    notes.push({
      level: 'warn',
      title: 'Мало обуви',
      text: `Пар обуви: ${count('shoes')}. Обувь сильнее всего меняет характер образа — нужно минимум две.`,
    })
  if (count('outerwear') === 0)
    notes.push({
      level: 'warn',
      title: 'Нет верхней одежды',
      text: 'Без пальто, куртки или жакета образы в прохладную погоду будут «недоукомплектованы».',
    })
  if (count('accessory') + count('bag') === 0)
    notes.push({
      level: 'info',
      title: 'Нет аксессуаров',
      text: 'Сумка, ремень или украшение добавят завершённости даже простому комплекту.',
    })

  const neutralShare =
    items.filter((i) => {
      const hsl = hexToHsl(i.colorHex)
      return hsl.s < 0.15 || hsl.l > 0.9 || hsl.l < 0.12
    }).length / items.length
  if (neutralShare < 0.35)
    notes.push({
      level: 'warn',
      title: 'Мало нейтральной базы',
      text: `Нейтральных вещей всего ${Math.round(neutralShare * 100)}%. База (чёрный, белый, серый, беж) нужна, чтобы вещи сочетались между собой.`,
    })

  for (const season of ['winter', 'spring', 'summer', 'autumn'] as SeasonKey[]) {
    const suitable = items.filter((i) => suitsSeason(i, season)).length
    if (suitable < 4)
      notes.push({
        level: 'warn',
        title: `Дыра в сезоне: ${SEASON_LABEL[season].toLowerCase()}`,
        text: `Подходящих вещей: ${suitable}. Стилист не сможет собрать разнообразные образы на этот сезон.`,
      })
  }

  const formal = items.filter((i) => i.formality >= 4).length
  if (formal < 2)
    notes.push({
      level: 'info',
      title: 'Нет нарядных вещей',
      text: `Вещей с формальностью 4+ всего ${formal}. Для выходов и мероприятий нужно минимум две.`,
    })

  const relaxed = items.filter((i) => i.formality <= 2).length
  if (relaxed < 2)
    notes.push({
      level: 'info',
      title: 'Нет расслабленных вещей',
      text: `Вещей с формальностью до 2 всего ${relaxed}. Без них не собрать образы на выходные и дом.`,
    })

  const offPalette = items.filter(
    (i) => seasonFit(i.colorHex, profile.colorSeason) < 0.45 && hexToHsl(i.colorHex).s >= 0.2,
  )
  if (offPalette.length > 0)
    notes.push({
      level: 'info',
      title: 'Вещи вне палитры',
      text: `${offPalette.length} вещ(и/ей) выбиваются из цветотипа «${SEASON_LABEL[profile.colorSeason]}»: ${offPalette
        .slice(0, 3)
        .map((i) => i.name)
        .join(', ')}. Носить можно, но сочетать их сложнее.`,
    })

  const good = notes.filter((n) => n.level === 'warn').length === 0
  if (good)
    notes.unshift({
      level: 'good',
      title: 'База укомплектована',
      text: 'В гардеробе есть верх, низ, обувь и нейтральная база — стилист может собирать образы на любой случай.',
    })

  return notes
}
