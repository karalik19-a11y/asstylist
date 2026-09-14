import { describe, expect, it } from 'vitest'
import { bmiLabel, budgetLeft, formatCompactRub, formatPercent, formatRub, formatScore, itemsWord, plural, relativeTime } from '../src/lib/format'

describe('formatRub', () => {
  it('groups thousands with a non-breaking space', () => {
    expect(formatRub(100000)).toBe('100 000 ₽')
    expect(formatRub(1000)).toBe('1 000 ₽')
    expect(formatRub(999)).toBe('999 ₽')
  })

  it('rounds fractional rubles', () => {
    expect(formatRub(1234.4)).toBe('1 234 ₽')
    expect(formatRub(1234.6)).toBe('1 235 ₽')
  })
})

describe('formatCompactRub', () => {
  it('switches to thousands', () => {
    expect(formatCompactRub(100000)).toBe('100 тыс. ₽')
    expect(formatCompactRub(12500)).toBe('12,5 тыс. ₽')
    expect(formatCompactRub(999)).toBe('999 ₽')
  })
})

describe('percent, score and plural helpers', () => {
  it('formats percentages and scores', () => {
    expect(formatPercent(0.87)).toBe('87%')
    expect(formatPercent(0.876, 1)).toBe('87,6%')
    expect(formatScore(92.4)).toBe('92/100')
  })

  it('picks the right Russian plural form', () => {
    expect(itemsWord(1)).toBe('1 вещь')
    expect(itemsWord(3)).toBe('3 вещи')
    expect(itemsWord(5)).toBe('5 вещей')
    expect(itemsWord(11)).toBe('11 вещей')
    expect(itemsWord(21)).toBe('21 вещь')
    expect(plural(2, ['день', 'дня', 'дней'])).toBe('дня')
  })
})

describe('bmiLabel and budgetLeft', () => {
  it('labels BMI bands', () => {
    expect(bmiLabel(17)).toBe('ниже нормы')
    expect(bmiLabel(22)).toBe('норма')
    expect(bmiLabel(27)).toBe('выше нормы')
    expect(bmiLabel(33)).toBe('высокий')
  })

  it('never returns a negative remainder', () => {
    expect(budgetLeft(50000, 32000)).toBe(18000)
    expect(budgetLeft(50000, 60000)).toBe(0)
  })
})

describe('relativeTime', () => {
  it('describes fresh timestamps in Russian', () => {
    expect(relativeTime(new Date().toISOString())).toBe('только что')
    expect(relativeTime(new Date(Date.now() - 5 * 60_000).toISOString())).toBe('5 минут назад')
    expect(relativeTime('not-a-date')).toBe('')
    expect(relativeTime(undefined)).toBe('')
  })
})
