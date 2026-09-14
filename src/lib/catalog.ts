import type {
  Category,
  OccasionKey,
  Profile,
  SeasonKey,
  StyleKey,
  WardrobeItem,
} from '../types'

export const CATEGORY_ORDER: Category[] = [
  'outerwear',
  'top',
  'bottom',
  'dress',
  'shoes',
  'bag',
  'accessory',
]

export const CATEGORY_LABEL: Record<Category, { one: string; many: string; icon: string }> = {
  outerwear: { one: 'Верхняя одежда', many: 'Верхняя одежда', icon: '🧥' },
  top: { one: 'Верх', many: 'Верх', icon: '👕' },
  bottom: { one: 'Низ', many: 'Низ', icon: '👖' },
  dress: { one: 'Платье', many: 'Платья', icon: '👗' },
  shoes: { one: 'Обувь', many: 'Обувь', icon: '👟' },
  bag: { one: 'Сумка', many: 'Сумки', icon: '👜' },
  accessory: { one: 'Аксессуар', many: 'Аксессуары', icon: '✨' },
}

export const STYLE_ORDER: StyleKey[] = [
  'casual',
  'business',
  'minimal',
  'street',
  'romantic',
  'evening',
  'sport',
]

export const STYLE_LABEL: Record<StyleKey, string> = {
  casual: 'Повседневный',
  business: 'Деловой',
  minimal: 'Минимализм',
  street: 'Стрит',
  romantic: 'Романтичный',
  evening: 'Вечерний',
  sport: 'Спорт',
}

export const SEASON_ORDER: SeasonKey[] = ['winter', 'spring', 'summer', 'autumn']

export const SEASON_LABEL: Record<SeasonKey, string> = {
  winter: 'Зима',
  spring: 'Весна',
  summer: 'Лето',
  autumn: 'Осень',
  all: 'Круглый год',
}

export interface SlotSpec {
  category: Category
  required: boolean
}

export interface OccasionConfig {
  key: OccasionKey
  label: string
  icon: string
  description: string
  /** Целевая формальность комплекта, 1..5 */
  targetFormality: number
  /** Стили, ожидаемые от образа */
  styles: StyleKey[]
  /** Альтернативные схемы комплекта (платье vs верх+низ) */
  templates: SlotSpec[][]
}

export const OCCASIONS: OccasionConfig[] = [
  {
    key: 'work',
    label: 'Работа / офис',
    icon: '💼',
    description: 'сдержанный комплект, формальность 3–5',
    targetFormality: 3.8,
    styles: ['business', 'minimal'],
    templates: [
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'bag', required: false },
        { category: 'accessory', required: false },
      ],
      [
        { category: 'dress', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'bag', required: false },
        { category: 'accessory', required: false },
      ],
    ],
  },
  {
    key: 'walk',
    label: 'Прогулка / город',
    icon: '🌿',
    description: 'комфорт и слои по погоде',
    targetFormality: 2.2,
    styles: ['casual', 'street'],
    templates: [
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'bag', required: false },
        { category: 'accessory', required: false },
      ],
      [
        { category: 'dress', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'bag', required: false },
      ],
    ],
  },
  {
    key: 'date',
    label: 'Свидание / ужин',
    icon: '🌙',
    description: 'акцент на силуэте и деталях',
    targetFormality: 3.6,
    styles: ['romantic', 'evening', 'minimal'],
    templates: [
      [
        { category: 'dress', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'accessory', required: true },
        { category: 'bag', required: false },
      ],
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'accessory', required: false },
        { category: 'bag', required: false },
      ],
    ],
  },
  {
    key: 'party',
    label: 'Вечеринка / выход',
    icon: '✨',
    description: 'максимум выразительности',
    targetFormality: 4.4,
    styles: ['evening', 'romantic', 'street'],
    templates: [
      [
        { category: 'dress', required: true },
        { category: 'shoes', required: true },
        { category: 'accessory', required: true },
        { category: 'bag', required: false },
      ],
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'accessory', required: true },
        { category: 'bag', required: false },
      ],
    ],
  },
  {
    key: 'sport',
    label: 'Спорт / тренировка',
    icon: '🏃',
    description: 'только функциональные вещи',
    targetFormality: 1.4,
    styles: ['sport'],
    templates: [
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
      ],
    ],
  },
  {
    key: 'travel',
    label: 'Поездка / дорога',
    icon: '🧳',
    description: 'слои, удобная обувь, вместительная сумка',
    targetFormality: 2.3,
    styles: ['casual', 'street', 'minimal'],
    templates: [
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: true },
        { category: 'outerwear', required: false },
        { category: 'bag', required: true },
      ],
    ],
  },
  {
    key: 'home',
    label: 'Дом / отдых',
    icon: '☕',
    description: 'мягкие ткани и свобода движений',
    targetFormality: 1.6,
    styles: ['casual', 'sport'],
    templates: [
      [
        { category: 'top', required: true },
        { category: 'bottom', required: true },
        { category: 'shoes', required: false },
      ],
    ],
  },
]

export const OCCASION_MAP: Record<OccasionKey, OccasionConfig> = OCCASIONS.reduce(
  (acc, o) => {
    acc[o.key] = o
    return acc
  },
  {} as Record<OccasionKey, OccasionConfig>,
)

export const DEFAULT_PROFILE: Profile = {
  name: '',
  colorSeason: 'summer',
  preferredStyles: ['casual', 'minimal'],
  avoidColors: [],
  notes: '',
}

export const DEMO_ITEMS: Omit<WardrobeItem, 'id' | 'wornDates'>[] = [
  {
    name: 'Белая хлопковая рубашка',
    category: 'top',
    colorHex: '#f7f5f0',
    styles: ['business', 'minimal', 'casual'],
    seasons: ['all'],
    warmth: 2,
    formality: 4,
    image: '/items/shirt-white.jpg',
    favorite: true,
  },
  {
    name: 'Голубой кашемировый свитер',
    category: 'top',
    colorHex: '#9fc4dd',
    styles: ['casual', 'minimal', 'romantic'],
    seasons: ['winter', 'spring', 'autumn'],
    warmth: 4,
    formality: 3,
    image: '/items/sweater-blue.jpg',
    favorite: false,
  },
  {
    name: 'Чёрные прямые брюки',
    category: 'bottom',
    colorHex: '#1c1c1e',
    styles: ['business', 'minimal', 'evening'],
    seasons: ['all'],
    warmth: 2,
    formality: 4,
    image: '/items/trousers-black.jpg',
    favorite: true,
  },
  {
    name: 'Синие прямые джинсы',
    category: 'bottom',
    colorHex: '#3c5a86',
    styles: ['casual', 'street'],
    seasons: ['spring', 'autumn', 'winter'],
    warmth: 3,
    formality: 2,
    image: '/items/jeans-blue.jpg',
    favorite: false,
  },
  {
    name: 'Бежевое шерстяное пальто',
    category: 'outerwear',
    colorHex: '#c8b191',
    styles: ['minimal', 'business', 'casual'],
    seasons: ['autumn', 'winter', 'spring'],
    warmth: 5,
    formality: 4,
    image: '/items/coat-beige.jpg',
    favorite: true,
  },
  {
    name: 'Белые кожаные кроссовки',
    category: 'shoes',
    colorHex: '#f2f0ea',
    styles: ['casual', 'street', 'sport'],
    seasons: ['all'],
    warmth: 2,
    formality: 2,
    image: '/items/sneakers-white.jpg',
    favorite: false,
  },
  {
    name: 'Чёрные кожаные лоферы',
    category: 'shoes',
    colorHex: '#17171a',
    styles: ['business', 'minimal', 'evening'],
    seasons: ['spring', 'summer', 'autumn'],
    warmth: 2,
    formality: 4,
    image: '/items/loafers-black.jpg',
    favorite: false,
  },
  {
    name: 'Чёрное коктейльное платье',
    category: 'dress',
    colorHex: '#15151a',
    styles: ['evening', 'romantic', 'minimal'],
    seasons: ['all'],
    warmth: 1,
    formality: 5,
    image: '/items/dress-black.jpg',
    favorite: true,
  },
  {
    name: 'Серая сумка-тоут',
    category: 'bag',
    colorHex: '#8d8d8d',
    styles: ['minimal', 'business', 'casual'],
    seasons: ['all'],
    warmth: 1,
    formality: 3,
    image: '/items/bag-grey.jpg',
    favorite: false,
  },
  {
    name: 'Карамельный кожаный ремень',
    category: 'accessory',
    colorHex: '#a9713f',
    styles: ['casual', 'business', 'street'],
    seasons: ['all'],
    warmth: 1,
    formality: 3,
    image: '/items/belt-caramel.jpg',
    favorite: false,
  },
  {
    name: 'Чёрные ботинки на шнуровке',
    category: 'shoes',
    colorHex: '#1b1b1e',
    styles: ['casual', 'street', 'minimal'],
    seasons: ['winter', 'autumn', 'spring'],
    warmth: 4,
    formality: 3,
    favorite: false,
  },
  {
    name: 'Серое спортивное худи',
    category: 'top',
    colorHex: '#9a9a9a',
    styles: ['sport', 'casual', 'street'],
    seasons: ['all'],
    warmth: 3,
    formality: 1,
    favorite: false,
  },
  {
    name: 'Чёрные леггинсы',
    category: 'bottom',
    colorHex: '#17171a',
    styles: ['sport', 'casual'],
    seasons: ['all'],
    warmth: 2,
    formality: 1,
    favorite: false,
  },
]
