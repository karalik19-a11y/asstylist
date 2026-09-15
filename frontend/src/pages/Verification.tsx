import { useState } from 'react'

interface VerificationItem {
  sku: string
  name: string
  source: string
  status: string
  score: number
  issues: string[]
}

const CHECKS = [
  { id: 'schema', label: 'Обязательные поля заполнены' },
  { id: 'price', label: 'Цена адекватна и в рублях' },
  { id: 'category', label: 'Категория известна движку' },
  { id: 'url', label: 'Ссылка на разрешённый магазин' },
  { id: 'source', label: 'Источник вызывает доверие' },
  { id: 'sizes', label: 'Указаны размеры' },
  { id: 'attributes', label: 'Заполнены цвета, стили, сезоны' },
  { id: 'checksum', label: 'Карточка не изменена после проверки' },
]

export function Verification({
  report,
  loading,
  error,
}: {
  report: {
    total: number
    verified: number
    warning: number
    failed: number
    eligible: number
    network_enabled: boolean
    ttl_days: number
    min_score: number
    items: VerificationItem[]
  } | null
  loading: boolean
  error: string | null
}) {
  const [onlyBad, setOnlyBad] = useState(false)

  if (loading) return <div className="skeleton" style={{ height: 180 }} />
  if (error) return <div className="error-box">{error}</div>
  if (!report) return null

  const items = onlyBad ? report.items.filter((item) => item.status !== 'verified') : report.items

  return (
    <div className="stack">
      <section className="card stack" style={{ gap: 10 }}>
        <div className="grid-3">
          <Stat label="проверено" value={report.verified} tone="ok" />
          <Stat label="с пометкой" value={report.warning} tone="warn" />
          <Stat label="отклонено" value={report.failed} tone="bad" />
        </div>
        <div className="muted small">
          В каталоге {report.total} позиций, в сборке образов участвуют {report.eligible}. Проверка повторяется каждые{' '}
          {report.ttl_days} дней, порог прохождения — {Math.round(report.min_score * 100)}%.
        </div>
        <div className="muted small">
          Сетевые проверки ссылок: {report.network_enabled ? 'включены' : 'выключены (офлайн-режим, безопасно для демо)'}.
        </div>
      </section>

      <section className="card stack" style={{ gap: 8 }}>
        <strong>Что проверяется</strong>
        <ul className="reasons">
          {CHECKS.map((check) => (
            <li key={check.id}>{check.label}</li>
          ))}
        </ul>
        <div className="muted small">
          Критическая ошибка (цена, ссылка, категория, источник, контрольная сумма) — товар не попадает в образ вовсе.
        </div>
      </section>

      <section className="stack" style={{ gap: 10 }}>
        <div className="row-between">
          <strong>Отчёт по каталогу</strong>
          <button type="button" className="link-btn" onClick={() => setOnlyBad((value) => !value)}>
            {onlyBad ? 'показать все' : 'только проблемные'}
          </button>
        </div>
        {items.slice(0, 60).map((item) => (
          <div key={`${item.sku}-${item.source}`} className="card stack" style={{ gap: 4 }}>
            <div className="row-between">
              <strong style={{ fontSize: 14 }}>{item.name}</strong>
              <span className="muted small">{Math.round(item.score * 100)}%</span>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <span className="tiny">
                {item.sku} · {item.source}
              </span>
              <span
                className={`badge ${item.status === 'verified' ? 'badge-ok' : item.status === 'warning' ? 'badge-warn' : 'badge-bad'}`}
              >
                {item.status}
              </span>
            </div>
            {item.issues.length ? <div className="muted small">{item.issues.join('; ')}</div> : null}
          </div>
        ))}
      </section>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: number; tone: 'ok' | 'warn' | 'bad' }) {
  const color = tone === 'ok' ? 'var(--ok)' : tone === 'warn' ? 'var(--warn)' : 'var(--bad)'
  return (
    <div className="card" style={{ background: 'var(--surface-2)', padding: 12, textAlign: 'center' }}>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
      <div className="muted tiny">{label}</div>
    </div>
  )
}
