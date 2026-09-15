import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge } from '../components/ui'
import { StarIcon } from '../lib/graphics'
import { playClick } from '../lib/sound'

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
      <div className="stack page-transition" style={{ gap: 10 }}>
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="skeleton" style={{ height: 82 }} />
        ))}
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="card page-transition" style={{ textAlign: 'center', padding: '36px 16px' }}>
        <h3>Архив пока пуст</h3>
        <p className="muted small" style={{ margin: '8px 0 0' }}>
          Соберите первый персональный гардероб — он сохранится здесь для быстрого доступа.
        </p>
      </div>
    )
  }

  return (
    <div className="card index-list page-transition">
      {items.map((entry, index) => (
        <button
          key={entry.id}
          type="button"
          className="index-row"
          onClick={() => {
            playClick()
            onOpen(entry.id)
          }}
        >
          <span className="index-num">{String(index + 1).padStart(2, '0')}</span>
          <span className="stack" style={{ flex: 1, minWidth: 0, gap: 4 }}>
            <span className="row-between" style={{ gap: 8 }}>
              <strong style={{ fontSize: 15 }}>
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
              <Badge tone={entry.score >= 80 ? 'ok' : 'warn'}>индекс {Math.round(entry.score)}</Badge>
              {entry.is_favorite ? (
                <Badge tone="ok">
                  <StarIcon filled size={11} /> избранное
                </Badge>
              ) : null}
            </span>
          </span>
        </button>
      ))}
    </div>
  )
}
