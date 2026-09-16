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

/** Метаданные вещи от движка ASSTYLIST Fashion Engine. */
export interface EngineItemMeta {
  slot?: string
  slot_label?: string
  role?: string | null
  role_label?: string
  /** true — вещь выбрана самим движком в его образе */
  in_engine_outfit?: boolean
  source_in_run?: 'engine-outfit' | 'engine-shortlist' | 'budget-guard' | string
  taste_category?: string
  taste_label?: string
  fashion_score?: number
  trend_relevance?: number
  uniqueness?: number
  generic_score?: number
  silhouette?: string[]
  material?: string | null
  aesthetic?: string | null
  engine_category?: string
  provider?: string
}

/** Результат прогона движка: тезис образа, оценка, критик, статистика поиска. */
export interface LookEngine {
  pipeline?: string
  enabled?: boolean
  runtime_mode?: string
  engine_version?: string
  styling_thesis?: string
  styling_thesis_ru?: string
  aesthetic?: string
  /** Эстетика по-русски: тезис + доминирующий оттенок образа. */
  aesthetic_ru?: string
  /** Сколько вещей дала живая выдача Авито, а сколько — снимок выдачи. */
  feeds?: { live?: number; snapshot?: number }
  /** Пояснения к источникам вещей (например, дата снимка выдачи). */
  feed_notes?: string[]
  /** Почему не пустили живой поиск: капча, сеть и т. п. */
  live_error?: string | null
  /** Дата снимка выдачи Авито, из которого взяты вещи. */
  snapshot_captured_at?: string | null
  outfit_score?: number
  app_score?: number
  final_score?: number
  score_formula?: string
  critic_decision?: string
  critic_feedback?: string[]
  styling_logic?: Record<string, unknown>
  roles?: Record<string, string>
  queries_used?: string[]
  queries_total?: number
  candidates?: {
    raw_items?: number
    considered?: number
    validated?: number
    outfits_built?: number
    dropped?: Record<string, number>
  }
  taste_mix?: Record<string, number>
  niche_level?: number
  aesthetics?: string[]
  fit_preference?: string
  theses?: string[]
  repair?: string | null
  fallback?: string | null
  fallback_reason?: string
  /** Задействованные провайдеры поиска и настроенные живые источники. */
  providers?: string[]
  web_sources?: string[]
}

/** Вещь из свободного поиска по движку (/api/engine/search). */
export interface EngineSearchItem {
  sku: string
  name: string
  brand: string
  category: string
  slot: string
  slot_label: string
  price_rub: number
  /** Например «420 EUR» — исходная цена для позиций в валюте, не в ₽. */
  price_note?: string
  url: string
  image_url?: string
  colors: string[]
  color_hexes: string[]
  score: number
  engine: EngineItemMeta
  reasons: string[]
  verification_status: string
  verification_score: number
  /** web-search (онлайн-нахождение), mock-real-catalog (архетип), каталог приложения. */
  source?: string
  /** Откуда вещь: живая выдача Авито или снимок реальных объявлений. */
  feed?: 'live' | 'snapshot' | 'search' | string | null
  /** Куда ведёт ссылка: конкретное объявление или подборка Авито. */
  link_kind?: 'listing' | 'search' | string | null
  /** Паспорт объявления — город, состояние, размер, дата снимка. */
  listing?: ListingInfo | null
  snapshot_captured_at?: string | null
}

export interface EngineSearchResult {
  query: string
  engine: LookEngine
  thesis_options: string[]
  items: EngineSearchItem[]
  total_rub: number
  budget_rub: number
  suggested_request: {
    query: string
    style: string
    mood: string
    occasion: string
    season: string
    presentation: string
    budget_rub: number
    height_cm: number
    weight_kg: number
    niche_level: number
  }
}

/** Паспорт конкретного объявления Авито: город, состояние, размеры, дата снимка. */
export interface ListingInfo {
  /** Куда ведёт ссылка: `listing` — конкретное объявление, `search` — подборка. */
  kind?: 'listing' | 'search' | string
  /** Живая выдача или снимок реальных объявлений. */
  feed?: 'live' | 'snapshot' | string
  avito_id?: string
  city?: string
  condition?: string
  sizes?: string[]
  captured_at?: string
  /** Совпадение по внешнему виду: оттенки, силуэт, состояние, фото. */
  appearance_score?: number
  appearance_components?: Record<string, number>
  /** Разбирали ли фото объявления (Pillow) — тогда есть и его оттенки. */
  photo_analyzed?: boolean
  colors_hex?: string[]
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
  /** Роль, taste-категория и Fashion Score от движка (может быть пустым). */
  engine?: EngineItemMeta
  reasons: string[]
  verification_status: 'verified' | 'warning' | 'failed' | string
  verification_score: number
  source: string
  /** Откуда вещь: живая выдача Авито или снимок реальных объявлений. */
  feed?: 'live' | 'snapshot' | 'search' | string | null
  /** Куда ведёт ссылка: конкретное объявление или подборка Авито. */
  link_kind?: 'listing' | 'search' | string | null
  /** Паспорт объявления — город, состояние, размер, дата снимка. */
  listing?: ListingInfo | null
  snapshot_captured_at?: string | null
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
  /** Разбор внешности по фото: цветотип, подтон, контраст, свой металл. */
  color_type?: string
  color_type_ru?: string
  undertone?: string
  undertone_ru?: string
  contrast?: string
  contrast_ru?: string
  metal?: string
  metal_ru?: string
  hair_depth?: string | null
  skin_hex?: string | null
  hair_hex?: string | null
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
  /** Короткое объяснение, почему образ собран именно для этого пользователя. */
  personal_note: string
  tips: string[]
  body: BodyProfile
  palette: PaletteProfile
  plan: string
  engine_version: string
  /** Блок движка ASSTYLIST: тезис, оценка образа, критик, статистика поиска. */
  engine?: LookEngine
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
  /** Свободная формулировка образа — уходит в движок как поисковый запрос. */
  query: string
  /** Явный уровень ниши движка 0…100 (иначе выводится из стиля). */
  niche_level: number | null
  photoDataUrl: string | null
  photoFile: File | null
}
