import { useState } from 'react'
import { Loader, Reveal, SectionTitle } from '../components/ui'

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

  if (loading) return (
    <div className="stack">
      <Loader text="Проверяем каталог…" />
      <div className="skeleton" style={{ height: 120 }} />
    </div>
  )
  if (error) return <div className="error-box">{error}</div>
  if (!report) return null

  const items = onlyBad ? report.items.filter((item) => item.status !== 'verified') : report.items

  return (
    <div className="stack">
      <Reveal delay={0}>
        <section className="card stack" style={{ gap: 12 }}>
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
            Сетевые проверки ссылок: {report.network_enabled ? 'включены' : 'выключены (офлайн-режим)'}.
          </div>
        </section>
      </Reveal>

      <Reveal delay={0.08}>
        <section className="card stack" style={{ gap: 8 }}>
          <SectionTitle index="01">Что проверяется</SectionTitle>
          <ul className="reasons">
            {CHECKS.map((check) => (
              <li key={check.id}>{check.label}</li>
            ))}
          </ul>
          <div className="muted small">
            Критическая ошибка (цена, ссылка, категория, источник, контрольная сумма) — товар не попадает в образ вовсе.
          </div>
        </section>
      </Reveal>

      <section className="stack" style={{ gap: 10 }}>
        <div className="row-between">
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 19 }}>Отчёт по каталогу</strong>
          <button type="button" className="link-btn" onClick={() => setOnlyBad((value) => !value)}>
            {onlyBad ? 'показать все' : 'только проблемные'}
          </button>
        </div>
        {items.slice(0, 60).map((item, index) => (
          <Reveal key={`${item.sku}-${item.source}`} delay={Math.min(index, 10) * 0.04}>
            <div className="card stack" style={{ gap: 6 }}>
              <div className="row-between" style={{ gap: 8 }}>
                <strong style={{ fontSize: 14 }}>
                  <span className="sec-num" style={{ display: 'inline-block', marginRight: 8 }}>
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  {item.name}
                </strong>
                <span className="muted small" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  {Math.round(item.score * 100)}%
                </span>
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
          </Reveal>
        ))}
      </section>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: number; tone: 'ok' | 'warn' | 'bad' }) {
  const color = tone === 'ok' ? 'var(--ok)' : tone === 'warn' ? 'var(--warn)' : 'var(--bad)'
  return (
    <div className="stat-card">
      <b style={{ color }}>{value}</b>
      <span>{label}</span>
    </div>
  )
}
