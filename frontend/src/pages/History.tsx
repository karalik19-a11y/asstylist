import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, Reveal } from '../components/ui'

export function History({
  items,
  loading,
  onOpen,
}: {
  items: HistoryEntry[]
  loading: boolean
  onOpen: (id: number) => void
}) {
  if (loading) {
    return (
      <div className="stack">
        {[0, 1, 2].map((index) => (
          <div key={index} className="skeleton" style={{ height: 84 }} />
        ))}
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '36px 20px' }}>
        <div style={{ fontSize: 40, color: 'var(--pink)' }} aria-hidden="true">✦</div>
        <h3 style={{ marginTop: 10 }}>Пока тихо…</h3>
        <p className="muted small" style={{ margin: '8px 0 0' }}>
          Собери первый образ — он поселится здесь.
        </p>
      </div>
    )
  }

  return (
    <div className="card index-list">
      {items.map((entry, index) => (
        <Reveal key={entry.id} delay={Math.min(index, 8) * 0.05}>
          <button
            type="button"
            className="index-row"
            style={{ borderRadius: 'var(--r)' }}
            onClick={() => onOpen(entry.id)}
          >
            <span className="index-num">{String(index + 1).padStart(2, '0')}</span>
            <span className="stack" style={{ flex: 1, minWidth: 0, gap: 4 }}>
              <span className="row-between" style={{ gap: 8 }}>
                <strong style={{ fontSize: 14.5 }}>
                  {entry.style} · {entry.mood}
                </strong>
                <span className="muted small" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  {formatRub(entry.total_rub)}
                </span>
              </span>
              <span className="muted small">
                {itemsWord(entry.items_count)} · {relativeTime(entry.created_at)} · бюджет {formatRub(entry.budget_rub)}
              </span>
              <span className="wrap" style={{ gap: 6 }}>
                <Badge tone={entry.score >= 80 ? 'ok' : 'warn'}>оценка {Math.round(entry.score)}</Badge>
                {entry.is_favorite ? <Badge tone="pop">★ избранное</Badge> : null}
              </span>
            </span>
            <span className="index-arrow" aria-hidden="true">→</span>
          </button>
        </Reveal>
      ))}
    </div>
  )
}
