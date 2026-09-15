import type { WizardState } from '../lib/types'

export type WizardStep = 'photo' | 'body' | 'style' | 'mood' | 'tune' | 'review'

export const STEP_ORDER: WizardStep[] = ['photo', 'body', 'style', 'mood', 'tune', 'review']

export const STEP_TITLES: Record<WizardStep, string> = {
  photo: 'Фото',
  body: 'Параметры',
  style: 'Стиль',
  mood: 'Настроение',
  tune: 'Детали',
  review: 'Проверка',
}

export const LIMITS = {
  height: { min: 140, max: 210 },
  weight: { min: 40, max: 180 },
  budget: { min: 10_000, max: 100_000, step: 1_000 },
}

export const initialState: WizardState = {
  style: 'minimal',
  mood: 'calm',
  occasion: 'everyday',
  season: 'all',
  presentation: 'unisex',
  height_cm: 172,
  weight_kg: 68,
  budget_rub: 50_000,
  preferred_colors: [],
  avoid_colors: [],
  size: null,
  query: '',
  niche_level: null,
  photoDataUrl: null,
  photoFile: null,
}

export type WizardAction =
  | { type: 'patch'; patch: Partial<WizardState> }
  | { type: 'toggleColor'; id: string; field: 'preferred_colors' | 'avoid_colors' }
  | { type: 'setPhoto'; dataUrl: string | null; file: File | null }
  | { type: 'reset' }
  | { type: 'next' }
  | { type: 'back' }

export interface WizardModel {
  step: WizardStep
  state: WizardState
}

export const initialModel: WizardModel = { step: 'photo', state: initialState }

/** Adds an id, keeping the list capped; the newest entry always survives. */
function withId(list: string[], id: string, max: number): string[] {
  const next = list.filter((entry) => entry !== id)
  next.push(id)
  return next.slice(-max)
}

export const MAX_COLORS_PER_LIST = 5

export function wizardReducer(model: WizardModel, action: WizardAction): WizardModel {
  switch (action.type) {
    case 'patch':
      return { ...model, state: { ...model.state, ...action.patch } }
    case 'toggleColor': {
      const field = action.field
      const otherField: 'preferred_colors' | 'avoid_colors' =
        field === 'preferred_colors' ? 'avoid_colors' : 'preferred_colors'
      const current = model.state[field]
      const other = model.state[otherField]

      // clicking an already-selected colour deselects it
      if (current.includes(action.id)) {
        return {
          ...model,
          state: { ...model.state, [field]: current.filter((id) => id !== action.id) },
        }
      }
      // a colour can never be both "loved" and "never" — it moves between lists
      return {
        ...model,
        state: {
          ...model.state,
          [field]: withId(current, action.id, MAX_COLORS_PER_LIST),
          [otherField]: other.filter((id) => id !== action.id),
        },
      }
    }
    case 'setPhoto':
      return { ...model, state: { ...model.state, photoDataUrl: action.dataUrl, photoFile: action.file } }
    case 'reset':
      return { step: 'photo', state: initialState }
    case 'next': {
      const index = STEP_ORDER.indexOf(model.step)
      if (index === -1 || index === STEP_ORDER.length - 1) return model
      return { ...model, step: STEP_ORDER[index + 1] }
    }
    case 'back': {
      const index = STEP_ORDER.indexOf(model.step)
      if (index <= 0) return model
      return { ...model, step: STEP_ORDER[index - 1] }
    }
    default:
      return model
  }
}

/** Human-readable blocker for the "Далее" button, or null when the step is valid. */
export function validateStep(step: WizardStep, state: WizardState): string | null {
  switch (step) {
    case 'body': {
      if (state.height_cm < LIMITS.height.min || state.height_cm > LIMITS.height.max)
        return `Рост должен быть от ${LIMITS.height.min} до ${LIMITS.height.max} см`
      if (state.weight_kg < LIMITS.weight.min || state.weight_kg > LIMITS.weight.max)
        return `Вес должен быть от ${LIMITS.weight.min} до ${LIMITS.weight.max} кг`
      const heightM = state.height_cm / 100
      const bmi = state.weight_kg / (heightM * heightM)
      if (bmi < 13 || bmi > 50) return 'Проверьте рост и вес — значения выглядят нереалистично'
      return null
    }
    case 'style':
      return state.style ? null : 'Выберите стиль'
    case 'mood':
      return state.mood ? null : 'Выберите настроение'
    case 'tune':
      if (state.budget_rub < LIMITS.budget.min) return `Минимальный бюджет — ${LIMITS.budget.min} ₽`
      if (state.budget_rub > LIMITS.budget.max) return `Максимальный бюджет — ${LIMITS.budget.max} ₽`
      return null
    default:
      return null
  }
}

export function progress(step: WizardStep): number {
  const index = STEP_ORDER.indexOf(step)
  return index === -1 ? 0 : (index + 1) / STEP_ORDER.length
}
