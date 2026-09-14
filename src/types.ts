export type Category = 'outerwear' | 'top' | 'bottom' | 'dress' | 'shoes' | 'bag' | 'accessory'

export type StyleKey =
  | 'casual'
  | 'business'
  | 'sport'
  | 'evening'
  | 'street'
  | 'minimal'
  | 'romantic'

export type SeasonKey = 'winter' | 'spring' | 'summer' | 'autumn' | 'all'

export type OccasionKey = 'work' | 'walk' | 'date' | 'party' | 'sport' | 'travel' | 'home'

export type ColorSeason = 'winter' | 'summer' | 'spring' | 'autumn'

export interface WardrobeItem {
  id: string
  name: string
  category: Category
  colorHex: string
  styles: StyleKey[]
  seasons: SeasonKey[]
  /** Тепло вещи: 1 — для жары, 5 — для мороза */
  warmth: number
  /** Формальность: 1 — спорт/дом, 5 — выход в свет */
  formality: number
  image?: string
  favorite: boolean
  /** ISO-даты (YYYY-MM-DD), когда вещь была в образе */
  wornDates: string[]
}

export interface ScorePart {
  key: 'harmony' | 'occasion' | 'style' | 'palette' | 'weather' | 'freshness'
  label: string
  /** 0..1 */
  value: number
  weight: number
  hint: string
}

export interface OutfitAnalysis {
  total: number
  parts: ScorePart[]
  tips: string[]
  scheme: string
}

export interface Outfit {
  id: string
  itemIds: string[]
  occasion: OccasionKey
  season: SeasonKey
  temperature: number
  score: number
  analysis: OutfitAnalysis
  saved: boolean
  createdAt: string
  /** ISO-дата, на которую образ запланирован (для календаря недели) */
  plannedFor?: string
}

export interface Profile {
  name: string
  colorSeason: ColorSeason
  preferredStyles: StyleKey[]
  avoidColors: string[]
  notes: string
}

export interface AppData {
  version: number
  profile: Profile
  items: WardrobeItem[]
  outfits: Outfit[]
}
