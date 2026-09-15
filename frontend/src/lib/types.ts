export interface StyleOption {
  id: string
  label: string
  emoji: string
  description: string
  palette_hint: string[]
}

export interface MoodOption {
  id: string
  label: string
  emoji: string
  description: string
}

export interface SimpleOption {
  id: string
  label: string
  formality?: number
}

export interface ColorOption {
  id: string
  label: string
  hex: string
  temperature: string
  neutral: boolean
}

export interface Meta {
  styles: StyleOption[]
  moods: MoodOption[]
  occasions: SimpleOption[]
  seasons: SimpleOption[]
  presentations: SimpleOption[]
  categories: SimpleOption[]
  slots: SimpleOption[]
  colors: ColorOption[]
  plans: { id: string; description: string }[]
  budget: { min_rub: number; max_rub: number; currency: string }
  ranking_weights: Record<string, number>
  sources: { id: string; label: string; kind: string; trust: number; note: string }[]
  demo_mode: boolean
  telegram: { configured: boolean; web_app_url: string | null; bot_link: string | null }
  ai_provider: string
  version: string
}

export interface TelegramStatus {
  configured: boolean
  bot: { id: number; username: string; first_name: string } | null
  bot_link: string | null
  web_app_url: string | null
  demo_mode: boolean
  init_data_expected: boolean
  error: string | null
}

export interface SetupResponse {
  ok: boolean
  bot: { id: number; username: string; first_name: string }
  web_app_url: string
  actions: string[]
  persisted_keys: string[]
  demo_mode: boolean
  next_step: string
}

export interface Alternative {
  sku: string
  name: string
  brand: string
  price_rub: number
  score?: number
  colors?: string[]
}

export interface LookItem {
  position: number
  slot: string
  slot_label: string
  sku: string
  category: string
  name: string
  brand: string
  price_rub: number
  url: string
  image_url: string
  colors: string[]
  color_hexes: string[]
  fit: string
  score: number
  breakdown: Record<string, number>
  reasons: string[]
  verification_status: 'verified' | 'warning' | 'failed' | string
  verification_score: number
  source: string
  alternatives: Alternative[]
}

export interface BodyProfile {
  height_cm: number
  weight_kg: number
  bmi: number
  bmi_label: string
  height_class: string
  silhouette: string
  silhouette_ru: string
  confidence: number
  recommended_fits: string[]
  avoid_fits: string[]
  recommended_lengths: string[]
  tips: string[]
  signals: string[]
}

export interface PaletteProfile {
  temperature: string
  depth: string
  chroma: string
  season_label: string
  recommended: string[]
  avoid: string[]
  confidence: number
  source: string
  dominant_colors: string[]
  signals: string[]
}

export interface Look {
  id: number | null
  created_at?: string
  user_id?: number
  style: string
  mood: string
  occasion: string
  season: string
  presentation: string
  height_cm: number
  weight_kg: number
  budget_rub: number
  total_rub: number
  budget_utilization: number
  score: number
  verdict: { grade: string; title: string; note: string }
  cohesion: Record<string, number>
  summary: string
  tips: string[]
  body: BodyProfile
  palette: PaletteProfile
  plan: string
  engine_version: string
  diagnostics: Record<string, unknown>
  items: LookItem[]
  is_favorite: boolean
  version: number
  ai_provider: string
  photo_digest: string
}

export interface HistoryEntry {
  id: number
  created_at: string
  style: string
  mood: string
  occasion: string
  season: string
  total_rub: number
  budget_rub: number
  score: number
  is_favorite: boolean
  items_count: number
  summary: string
}

export interface WizardState {
  style: string
  mood: string
  occasion: string
  season: string
  presentation: string
  height_cm: number
  weight_kg: number
  budget_rub: number
  preferred_colors: string[]
  avoid_colors: string[]
  size: string | null
  photoDataUrl: string | null
  photoFile: File | null
}
