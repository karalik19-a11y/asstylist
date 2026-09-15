import { useState } from 'react'
import { SectionTitle } from '../components/ui'
import { playClick } from '../lib/sound'

interface VerificationItem {
  sku: string
  name: string
  source: string
  status: string
  score: number
  issues: string[]
}

const CHECKS = [
  { id: 'schema', label: 'Обязательные поля карточки заполнены' },
  { id: 'price', label: 'Цена актуальна, в рублях и в диапазоне' },
  { id: 'category', label: 'Категория валидирована движком' },
  { id: 'url', label: 'Ссылка ведёт на доверенный онлайн-магазин' },
  { id: 'source', label: 'Источник проверен и авторизован' },
  { id: 'sizes', label: 'Размерная сетка подтверждена' },
  { id: 'attributes', label: 'Указаны материалы, оттенки и крой' },
  { id: 'checksum', label: 'Контрольная сумма карточки неизменна' },
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

  if (loading) return <div className="skeleton page-transition" style={{ height: 180 }} />
  if (error) return <div className="error-box page-transition">{error}</div>
  if (!report) return null

  const items = onlyBad ? report.items.filter((item) => item.status !== 'verified') : report.items

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      <section className="card stack" style={{ gap: 10 }}>
        <div className="grid-3">
          <Stat label="проверено" value={report.verified} tone="ok" />
          <Stat label="с пометкой" value={report.warning} tone="warn" />
          <Stat label="отклонено" value={report.failed} tone="bad" />
        </div>
        <div className="muted small">
          В каталоге {report.total} позиций, в формировании гардероба участвуют {report.eligible}. Верификация
          повторяется каждые {report.ttl_days} дней, минимальный порог соответствия — {Math.round(report.min_score * 100)}%.
        </div>
        <div className="muted small">
          Сетевой контроль ссылок: {report.network_enabled ? 'активен' : 'локальный режим (безопасно для превью)'}.
        </div>
      </section>

      <section className="card stack" style={{ gap: 8 }}>
        <SectionTitle index="01">Параметры контроля</SectionTitle>
        <ul className="reasons">
          {CHECKS.map((check) => (
            <li key={check.id}>{check.label}</li>
          ))}
        </ul>
        <div className="muted small">
          При критическом отклонении (недостоверная цена, нерабочая ссылка, несоответствие кроя) позиция не допускается в гардероб.
        </div>
      </section>

      <section className="stack" style={{ gap: 10 }}>
        <div className="row-between">
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 18 }}>Реестр каталога</strong>
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              playClick()
              setOnlyBad((value) => !value)
            }}
          >
            {onlyBad ? 'показать все' : 'только проблемные'}
          </button>
        </div>

        {items.slice(0, 60).map((item, index) => (
          <div key={`${item.sku}-${item.source}`} className="card stack" style={{ gap: 6 }}>
            <div className="row-between" style={{ gap: 8 }}>
              <strong style={{ fontSize: 14 }}>
                <span
                  style={{
                    display: 'inline-block',
                    marginRight: 6,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    color: 'var(--accent-leopard)',
                  }}
                >
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
        ))}
      </section>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: number; tone: 'ok' | 'warn' | 'bad' }) {
  const color = tone === 'ok' ? 'var(--ok)' : tone === 'warn' ? 'var(--warn)' : 'var(--bad)'
  return (
    <div className="card" style={{ background: 'var(--surface-2)', padding: 12, textAlign: 'center' }}>
      <div
        style={{
          fontSize: 28,
          fontWeight: 800,
          color,
          fontFamily: 'var(--font-display)',
          lineHeight: 1.1,
        }}
      >
        {value}
      </div>
      <div className="muted tiny" style={{ marginTop: 2 }}>
        {label}
      </div>
    </div>
  )
}
