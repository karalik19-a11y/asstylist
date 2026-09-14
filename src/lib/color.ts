import type { ColorSeason } from '../types'

export interface Hsl {
  h: number // 0..360
  s: number // 0..1
  l: number // 0..1
}

export function normalizeHex(input: string): string {
  let hex = (input || '').trim().replace(/^#/, '')
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map((c) => c + c)
      .join('')
  }
  if (!/^[0-9a-fA-F]{6}$/.test(hex)) return '#808080'
  return `#${hex.toLowerCase()}`
}

export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const h = normalizeHex(hex).slice(1)
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

export function hexToHsl(hex: string): Hsl {
  const { r, g, b } = hexToRgb(hex)
  const rn = r / 255
  const gn = g / 255
  const bn = b / 255
  const max = Math.max(rn, gn, bn)
  const min = Math.min(rn, gn, bn)
  const l = (max + min) / 2
  const d = max - min
  if (d === 0) return { h: 0, s: 0, l }
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
  let h: number
  if (max === rn) h = ((gn - bn) / d) % 6
  else if (max === gn) h = (bn - rn) / d + 2
  else h = (rn - gn) / d + 4
  h *= 60
  if (h < 0) h += 360
  return { h, s, l }
}

export function hslToHex({ h, s, l }: Hsl): string {
  const c = (1 - Math.abs(2 * l - 1)) * s
  const hp = (((h % 360) + 360) % 360) / 60
  const x = c * (1 - Math.abs((hp % 2) - 1))
  let rgb: [number, number, number]
  if (hp < 1) rgb = [c, x, 0]
  else if (hp < 2) rgb = [x, c, 0]
  else if (hp < 3) rgb = [0, c, x]
  else if (hp < 4) rgb = [0, x, c]
  else if (hp < 5) rgb = [x, 0, c]
  else rgb = [c, 0, x]
  const m = l - c / 2
  const toHex = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, '0')
  return `#${toHex(rgb[0])}${toHex(rgb[1])}${toHex(rgb[2])}`
}

/** Кратчайшее расстояние между оттенками, 0..180 */
export function hueDistance(a: number, b: number): number {
  const d = Math.abs((((a - b) % 360) + 360) % 360)
  return d > 180 ? 360 - d : d
}

export function isNeutral(hsl: Hsl): boolean {
  return hsl.s < 0.14 || hsl.l > 0.92 || hsl.l < 0.09
}

export function relativeLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex)
  const chan = (v: number) => {
    const c = v / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  }
  return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)
}

export function contrastRatio(a: string, b: string): number {
  const la = relativeLuminance(a)
  const lb = relativeLuminance(b)
  const hi = Math.max(la, lb)
  const lo = Math.min(la, lb)
  return (hi + 0.05) / (lo + 0.05)
}

/** Текст, который читается на данном фоне */
export function readableText(hex: string): string {
  return contrastRatio(hex, '#111111') >= contrastRatio(hex, '#ffffff') ? '#111111' : '#ffffff'
}

export interface HarmonyResult {
  /** 0..1 */
  score: number
  scheme: string
  note: string
}

const PAIR_RULES: Array<{ max: number; score: number; scheme: string }> = [
  { max: 12, score: 0.86, scheme: 'монохром' },
  { max: 45, score: 0.9, scheme: 'родственные оттенки' },
  { max: 75, score: 0.6, scheme: 'сложное сочетание' },
  { max: 105, score: 0.45, scheme: 'сложное сочетание' },
  { max: 135, score: 0.78, scheme: 'триада' },
  { max: 165, score: 0.82, scheme: 'split-комплемент' },
  { max: 195, score: 0.93, scheme: 'комплементарная пара' },
]

function pairScore(hueA: number, hueB: number): { score: number; scheme: string } {
  const d = hueDistance(hueA, hueB)
  for (const rule of PAIR_RULES) {
    if (d <= rule.max) return { score: rule.score, scheme: rule.scheme }
  }
  return { score: 0.5, scheme: 'сложное сочетание' }
}

/**
 * Оценка цветового решения комплекта.
 * Нейтральные вещи (чёрный, белый, серый, беж) сочетаются почти со всем,
 * поэтому набор «нейтральная база + один акцент» получает высокий балл.
 */
export function analyzeHarmony(colors: string[]): HarmonyResult {
  const hsls = colors.filter(Boolean).map(hexToHsl)
  if (hsls.length === 0) return { score: 0.5, scheme: '—', note: 'нет данных о цвете' }
  if (hsls.length === 1) return { score: 0.9, scheme: 'один цвет', note: 'один предмет — сочетать нечего' }

  const neutrals = hsls.filter(isNeutral)
  const chroma = hsls.filter((c) => !isNeutral(c))

  if (chroma.length === 0) {
    const spread = Math.max(...hsls.map((c) => c.l)) - Math.min(...hsls.map((c) => c.l))
    return {
      score: spread > 0.25 ? 0.95 : 0.8,
      scheme: 'total-neutral',
      note: spread > 0.25 ? 'монохромная база с игрой светлоты' : 'нейтральный монохром',
    }
  }

  if (chroma.length === 1) {
    return {
      score: 0.94,
      scheme: 'нейтральная база + акцент',
      note: 'нейтральная база с одним цветовым акцентом — самый безопасный приём',
    }
  }

  let sum = 0
  let pairs = 0
  const schemes = new Map<string, number>()
  for (let i = 0; i < chroma.length; i++) {
    for (let j = i + 1; j < chroma.length; j++) {
      const res = pairScore(chroma[i].h, chroma[j].h)
      sum += res.score
      pairs++
      schemes.set(res.scheme, (schemes.get(res.scheme) ?? 0) + 1)
    }
  }
  let score = pairs > 0 ? sum / pairs : 0.7

  // Чем больше насыщенных цветов в комплекте, тем выше риск «пестроты».
  if (chroma.length === 3) score *= 0.93
  if (chroma.length >= 4) score *= 0.8

  // Нейтральные вещи «гасят» риск и слегка повышают оценку.
  if (neutrals.length > 0) score = Math.min(1, score + 0.04 * Math.min(neutrals.length, 3))

  const dominant =
    Array.from(schemes.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'смешанная схема'

  return {
    score: Math.max(0.2, Math.min(1, score)),
    scheme: dominant,
    note:
      chroma.length >= 3
        ? `${chroma.length} насыщенных цвета — держите остальные вещи нейтральными`
        : `схема: ${dominant}`,
  }
}

interface SeasonPalette {
  label: string
  tagline: string
  /** Референсные цвета палитры */
  refs: string[]
  swatches: string[]
}

export const SEASON_PALETTES: Record<ColorSeason, SeasonPalette> = {
  winter: {
    label: 'Зима',
    tagline: 'холодные, чистые, контрастные оттенки: белый, чёрный, синий, фуксия, изумруд',
    refs: ['#ffffff', '#0b0b0f', '#1b3a8f', '#00a3a3', '#b3123f', '#5b2a86', '#e9edf5'],
    swatches: ['#ffffff', '#111318', '#1b3a8f', '#00a3a3', '#b3123f', '#5b2a86'],
  },
  summer: {
    label: 'Лето',
    tagline: 'мягкие припылённые холодные тона: лаванда, пыльная роза, серо-голубой',
    refs: ['#f3f4f8', '#9fb0c9', '#c9b8dd', '#e3b9c4', '#7f9d9a', '#5f6b84', '#ffffff'],
    swatches: ['#f3f4f8', '#9fb0c9', '#c9b8dd', '#e3b9c4', '#7f9d9a', '#5f6b84'],
  },
  spring: {
    label: 'Весна',
    tagline: 'тёплые светлые и чистые оттенки: персик, коралл, мята, золотистый жёлтый',
    refs: ['#fff6ea', '#ffb27a', '#f6cf5b', '#8dc63f', '#79d1c0', '#ff9aa2', '#8a5a3b'],
    swatches: ['#fff6ea', '#ffb27a', '#f6cf5b', '#8dc63f', '#79d1c0', '#ff9aa2'],
  },
  autumn: {
    label: 'Осень',
    tagline: 'тёплые глубокие приглушённые тона: терракота, горчица, олива, шоколад',
    refs: ['#f2e3d0', '#b5561f', '#d99b27', '#6e7b3c', '#7a3b2e', '#1f4f4a', '#8a6b4a'],
    swatches: ['#f2e3d0', '#b5561f', '#d99b27', '#6e7b3c', '#7a3b2e', '#1f4f4a'],
  },
}

/** Насколько цвет близок к палитре цветотипа: 0..1 */
export function seasonFit(hex: string, season: ColorSeason): number {
  const c = hexToHsl(hex)
  let best = 0
  for (const ref of SEASON_PALETTES[season].refs) {
    const r = hexToHsl(ref)
    const eitherNeutral = isNeutral(c) || isNeutral(r)
    const dh = eitherNeutral ? 0 : hueDistance(c.h, r.h) / 180
    const ds = Math.abs(c.s - r.s)
    const dl = Math.abs(c.l - r.l)
    const dist = Math.sqrt((eitherNeutral ? 0 : 0.45 * dh * dh) + 0.3 * ds * ds + 0.25 * dl * dl)
    const score = Math.max(0, 1 - dist * 1.35)
    if (score > best) best = score
  }
  return best
}

/** Пример «лучшего» оттенка из палитры рядом с заданным цветом */
export function closestPaletteColor(hex: string, season: ColorSeason): string {
  const c = hexToHsl(hex)
  let best = SEASON_PALETTES[season].refs[0]
  let bestScore = -1
  for (const ref of SEASON_PALETTES[season].refs) {
    const s = seasonFit(ref, season)
    const r = hexToHsl(ref)
    const dh = hueDistance(c.h, r.h) / 180
    const score = s - dh * 0.5
    if (score > bestScore) {
      bestScore = score
      best = ref
    }
  }
  return best
}

/** Базовые нейтральные оттенки, которые стоит иметь в гардеробе */
export const NEUTRALS = ['#ffffff', '#f2efe9', '#c9c4bb', '#8b8b8b', '#3a3a3a', '#111111', '#8a6b4a', '#c8b9a6']

export function isNeutralHex(hex: string): boolean {
  return isNeutral(hexToHsl(hex))
}

export function randomId(prefix = 'id'): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}${Date.now().toString(36).slice(-4)}`
}
