/**
 * Память о росте и весе: при следующем входе человек выбирает между
 * сохранёнными данными и новыми — и ничего больше не заполняет заново.
 */

import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { Wizard } from '../src/pages/Wizard'
import { initialModel } from '../src/state/wizard'
import type { BodyMemory } from '../src/lib/profile'

const savedBody: BodyMemory = {
  height_cm: 174,
  weight_kg: 64,
  updatedAt: '2026-09-16T10:00:00Z',
  usedCount: 2,
}

function renderWizard(overrides: Partial<Parameters<typeof Wizard>[0]> = {}) {
  const props: Parameters<typeof Wizard>[0] = {
    model: initialModel,
    meta: null,
    onPatch: vi.fn(),
    onToggleColor: vi.fn(),
    onPhoto: vi.fn(),
    onClearPhoto: vi.fn(),
    onBack: vi.fn(),
    onNext: vi.fn(),
    onGenerate: vi.fn(),
    onExit: vi.fn(),
    generating: false,
    error: null,
  }
  return render(<Wizard {...props} {...overrides} />)
}

describe('память о пользователе', () => {
  it('показывает выбор, когда рост и вес уже сохранены', () => {
    renderWizard({ model: { ...initialModel, step: 'memory' }, savedBody })

    expect(screen.getByText('С возвращением')).toBeTruthy()
    expect(screen.getByText('174 см · 64 кг')).toBeTruthy()
    expect(screen.getByText('Собрать по сохранённым данным')).toBeTruthy()
    expect(screen.getByText('Ввести новые рост и вес')).toBeTruthy()
    expect(screen.getByText('Пройти настройку полностью заново')).toBeTruthy()
  })

  it('по кнопке «сохранённые» идёт дальше без повторного ввода', () => {
    const onUseSavedBody = vi.fn()
    renderWizard({ model: { ...initialModel, step: 'memory' }, savedBody, onUseSavedBody })

    fireEvent.click(screen.getByText('Собрать по сохранённым данным'))
    expect(onUseSavedBody).toHaveBeenCalledTimes(1)
  })

  it('по кнопке «новые» ведёт на шаг роста и веса', () => {
    const onNewBody = vi.fn()
    renderWizard({ model: { ...initialModel, step: 'memory' }, savedBody, onNewBody })

    fireEvent.click(screen.getByText('Ввести новые рост и вес'))
    expect(onNewBody).toHaveBeenCalledTimes(1)
  })

  it('без сохранённых данных сразу показывает первый шаг сценария', () => {
    renderWizard()

    expect(screen.queryByText('С возвращением')).toBeNull()
    expect(screen.getByText('Фото')).toBeTruthy()
  })

  it('запоминает память в модели — рост и вес подставлены в шаг', () => {
    const { container } = renderWizard({
      model: {
        ...initialModel,
        step: 'memory',
        state: { ...initialModel.state, height_cm: savedBody.height_cm, weight_kg: savedBody.weight_kg },
      },
      savedBody,
    })
    expect(container.textContent).toContain('174 см · 64 кг')
  })
})
