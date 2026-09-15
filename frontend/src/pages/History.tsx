import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, SectionTitle } from '../components/ui'

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
          <div key={index} className="skeleton" style={{ height: 76 }} />
        ))}
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="card">
        <SectionTitle>Пока пусто</SectionTitle>
        <p className="muted small" style={{ margin: 0 }}>
          Соберите первый образ — он появится здесь.
        </p>
      </div>
    )
  }

  return (
    <div className="stack">
      {items.map((entry) => (
        <button key={entry.id} type="button" className="card stack" style={{ gap: 6, textAlign: 'left' }} onClick={() => onOpen(entry.id)}>
          <div className="row-between">
            <strong>
              {entry.style} · {entry.mood}
            </strong>
            <span style={{ fontVariantNumeric: 'tabular-nums' }}>{formatRub(entry.total_rub)}</span>
          </div>
          <div className="muted small">
            {itemsWord(entry.items_count)} · {relativeTime(entry.created_at)} · бюджет {formatRub(entry.budget_rub)}
          </div>
          <div className="wrap">
            <Badge tone={entry.score >= 80 ? 'ok' : 'warn'}>оценка {Math.round(entry.score)}</Badge>
            {entry.is_favorite ? <Badge tone="ok">★ избранное</Badge> : null}
          </div>
        </button>
      ))}
    </div>
  )
}
