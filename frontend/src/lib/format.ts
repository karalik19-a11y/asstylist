const NBSP = ' '

export function formatRub(value: number): string {
  const rounded = Math.round(value)
  const grouped = Math.abs(rounded)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, NBSP)
  return `${rounded < 0 ? '−' : ''}${grouped}${NBSP}₽`
}

export function formatCompactRub(value: number): string {
  if (value >= 1000) {
    const thousands = value / 1000
    const text = Number.isInteger(thousands) ? String(thousands) : thousands.toFixed(1).replace('.', ',')
    return `${text} тыс. ₽`
  }
  return formatRub(value)
}

export function formatPercent(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits).replace('.', ',')}%`
}

export function formatScore(value: number): string {
  return `${Math.round(value)}/100`
}

export function plural(count: number, forms: [string, string, string]): string {
  const abs = Math.abs(count) % 100
  const last = abs % 10
  if (abs > 10 && abs < 20) return forms[2]
  if (last > 1 && last < 5) return forms[1]
  if (last === 1) return forms[0]
  return forms[2]
}

export function itemsWord(count: number): string {
  return `${count} ${plural(count, ['вещь', 'вещи', 'вещей'])}`
}

export function bmiLabel(bmi: number): string {
  if (bmi < 18.5) return 'ниже нормы'
  if (bmi < 25) return 'норма'
  if (bmi < 30) return 'выше нормы'
  return 'высокий'
}

export function relativeTime(iso: string | undefined): string {
  if (!iso) return ''
  const then = new Date(iso)
  if (Number.isNaN(then.getTime())) return ''
  const diff = Date.now() - then.getTime()
  const minutes = Math.round(diff / 60000)
  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} ${plural(minutes, ['минуту', 'минуты', 'минут'])} назад`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} ${plural(hours, ['час', 'часа', 'часов'])} назад`
  const days = Math.round(hours / 24)
  return `${days} ${plural(days, ['день', 'дня', 'дней'])} назад`
}

export function budgetLeft(budget: number, total: number): number {
  return Math.max(0, Math.round(budget - total))
}
