import { useState } from 'react'
import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge } from '../components/ui'
import { StarIcon } from '../lib/graphics'
import { playClick } from '../lib/sound'

export function History({
  items,
  loading,
  onOpen,
  favoriteOnly,
  onToggleFavoriteOnly,
}: {
  items: HistoryEntry[]
  loading: boolean
  onOpen: (id: number) => void
  favoriteOnly: boolean
  onToggleFavoriteOnly: () => void
}) {
  const [pressingId, setPressingId] = useState<number | null>(null)

  if (loading) {
    return (
      <div className="stack page-transition" style={{ gap: 10 }}>
        <div className="archive-toolbar skeleton" style={{ height: 58 }} />
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="skeleton" style={{ height: 92 }} />
        ))}
      </div>
    )
  }

  return (
    <div className="stack page-transition archive-page" style={{ gap: 14 }}>
      <div className="archive-toolbar" role="group" aria-label="Фильтр архива">
        <div className="archive-toolbar-copy">
          <span className="tiny muted">Фильтр</span>
          <strong>{favoriteOnly ? 'Только избранное' : 'Все образы'}</strong>
        </div>
        <button
          type="button"
          className={`favorite-filter ${favoriteOnly ? 'is-on' : ''}`}
          aria-pressed={favoriteOnly}
          onClick={() => {
            playClick()
            onToggleFavoriteOnly()
          }}
        >
          <span className="favorite-filter-star"><StarIcon filled={favoriteOnly} size={15} /></span>
          <span>Избранное</span>
          <span className="favorite-filter-state">{favoriteOnly ? 'ВКЛ' : 'ВЫКЛ'}</span>
        </button>
      </div>

      {!items.length ? (
        <div className="card archive-empty">
          <div className="archive-empty-icon"><StarIcon filled={favoriteOnly} size={22} /></div>
          <h3>{favoriteOnly ? 'Избранных образов пока нет' : 'Архив пока пуст'}</h3>
          <p className="muted small">
            {favoriteOnly
              ? 'Добавляйте понравившиеся образы в избранное — они появятся здесь.'
              : 'Соберите первый персональный гардероб — он сохранится здесь для быстрого доступа.'}
          </p>
        </div>
      ) : (
        <div className="card index-list archive-list">
          {items.map((entry, index) => (
            <button
              key={entry.id}
              type="button"
              className={`index-row archive-row ${pressingId === entry.id ? 'is-pressing' : ''}`}
              onPointerDown={() => setPressingId(entry.id)}
              onPointerCancel={() => setPressingId(null)}
              onPointerUp={() => setPressingId(null)}
              onClick={() => {
                playClick()
                onOpen(entry.id)
              }}
            >
              <span className="index-num">{String(index + 1).padStart(2, '0')}</span>
              <span className="stack archive-row-main" style={{ flex: 1, minWidth: 0, gap: 5 }}>
                <span className="row-between archive-row-title" style={{ gap: 10 }}>
                  <strong>{entry.style} · {entry.mood}</strong>
                  <span className="archive-price">{formatRub(entry.total_rub)}</span>
                </span>
                <span className="muted small archive-meta">
                  {itemsWord(entry.items_count)} · {relativeTime(entry.created_at)} · бюджет {formatRub(entry.budget_rub)}
                </span>
                <span className="wrap archive-badges" style={{ gap: 6 }}>
                  <Badge tone={entry.score >= 80 ? 'ok' : 'warn'}>индекс {Math.round(entry.score)}</Badge>
                  {entry.is_favorite ? (
                    <Badge tone="favorite">
                      <StarIcon filled size={11} /> избранное
                    </Badge>
                  ) : null}
                </span>
              </span>
              <span className="archive-chevron" aria-hidden="true">›</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
