import { describe, expect, it } from 'vitest'
import { initialState, LIMITS, progress, STEP_ORDER, validateStep, wizardReducer, initialModel } from '../src/state/wizard'

describe('wizardReducer', () => {
  it('patches state without mutating the previous model', () => {
    const next = wizardReducer(initialModel, { type: 'patch', patch: { style: 'streetwear' } })
    expect(next.state.style).toBe('streetwear')
    expect(initialModel.state.style).toBe('minimal')
  })

  it('walks forward and backward through the steps', () => {
    let model = initialModel
    for (const step of STEP_ORDER.slice(1)) {
      model = wizardReducer(model, { type: 'next' })
      expect(model.step).toBe(step)
    }
    // does not run past the last step
    expect(wizardReducer(model, { type: 'next' }).step).toBe('review')

    for (let index = STEP_ORDER.length - 1; index > 0; index -= 1) {
      model = wizardReducer(model, { type: 'back' })
      expect(model.step).toBe(STEP_ORDER[index - 1])
    }
    expect(wizardReducer(model, { type: 'back' }).step).toBe('photo')
  })

  it('toggles colours and keeps them out of both lists', () => {
    let model = wizardReducer(initialModel, { type: 'toggleColor', id: 'black', field: 'preferred_colors' })
    expect(model.state.preferred_colors).toEqual(['black'])

    // the same colour in the opposite list removes it from the first one
    model = wizardReducer(model, { type: 'toggleColor', id: 'black', field: 'avoid_colors' })
    expect(model.state.avoid_colors).toEqual(['black'])
    expect(model.state.preferred_colors).toEqual([])

    // toggling again removes it
    model = wizardReducer(model, { type: 'toggleColor', id: 'black', field: 'avoid_colors' })
    expect(model.state.avoid_colors).toEqual([])
  })

  it('caps colour lists at five entries', () => {
    let model = initialModel
    for (const id of ['black', 'white', 'navy', 'beige', 'camel', 'olive']) {
      model = wizardReducer(model, { type: 'toggleColor', id, field: 'preferred_colors' })
    }
    expect(model.state.preferred_colors).toHaveLength(5)
    expect(model.state.preferred_colors).not.toContain('black')
  })

  it('stores and clears the photo', () => {
    const withPhoto = wizardReducer(initialModel, {
      type: 'setPhoto',
      dataUrl: 'data:image/jpeg;base64,abc',
      file: new File(['x'], 'photo.jpg', { type: 'image/jpeg' }),
    })
    expect(withPhoto.state.photoDataUrl).toBe('data:image/jpeg;base64,abc')
    expect(withPhoto.state.photoFile?.name).toBe('photo.jpg')

    const cleared = wizardReducer(withPhoto, { type: 'setPhoto', dataUrl: null, file: null })
    expect(cleared.state.photoDataUrl).toBeNull()
  })

  it('resets back to the start', () => {
    const dirty = wizardReducer(initialModel, { type: 'patch', patch: { style: 'grunge', budget_rub: 90_000 } })
    const moved = wizardReducer(dirty, { type: 'next' })
    const reset = wizardReducer(moved, { type: 'reset' })
    expect(reset.step).toBe('photo')
    expect(reset.state).toEqual(initialState)
  })
})

describe('validateStep', () => {
  it('accepts the default state everywhere', () => {
    for (const step of STEP_ORDER) {
      expect(validateStep(step, initialState)).toBeNull()
    }
  })

  it('rejects impossible body measurements', () => {
    expect(validateStep('body', { ...initialState, height_cm: LIMITS.height.min - 1 })).toMatch(/Рост/)
    expect(validateStep('body', { ...initialState, weight_kg: LIMITS.weight.max + 1 })).toMatch(/Вес/)
    // 200 cm and 40 kg is a BMI of 10 — flagged as unrealistic
    expect(validateStep('body', { ...initialState, height_cm: 200, weight_kg: 40 })).toMatch(/нереалистично/)
  })

  it('guards the budget bounds', () => {
    expect(validateStep('tune', { ...initialState, budget_rub: 500 })).toMatch(/Минимальный бюджет/)
    expect(validateStep('tune', { ...initialState, budget_rub: 500_000 })).toMatch(/Максимальный бюджет/)
  })

  it('requires a style and a mood', () => {
    expect(validateStep('style', { ...initialState, style: '' })).toMatch(/стиль/i)
    expect(validateStep('mood', { ...initialState, mood: '' })).toMatch(/настроение/i)
  })
})

describe('progress', () => {
  it('grows monotonically across the steps', () => {
    const values = STEP_ORDER.map(progress)
    expect(values[0]).toBeCloseTo(1 / STEP_ORDER.length)
    expect(values[values.length - 1]).toBe(1)
    for (let index = 1; index < values.length; index += 1) {
      expect(values[index]).toBeGreaterThan(values[index - 1])
    }
  })
})
