import { useState } from 'react'
import type { WardrobeItem } from '../types'
import { CATEGORY_LABEL, SEASON_LABEL, STYLE_LABEL } from '../lib/catalog'
import { readableText } from '../lib/color'

interface ItemCardProps {
  item: WardrobeItem
  onEdit: (item: WardrobeItem) => void
  onDelete: (item: WardrobeItem) => void
  onToggleFavorite: (id: string) => void
}

export function ItemCard({ item, onEdit, onDelete, onToggleFavorite }: ItemCardProps) {
  const [broken, setBroken] = useState(false)
  const showImage = Boolean(item.image) && !broken
  const seasons = item.seasons.includes('all')
    ? 'круглый год'
    : item.seasons.map((s) => SEASON_LABEL[s].toLowerCase()).join(', ')

  return (
    <article className="item-card">
      <div className="item-media">
        {showImage ? (
          <img
            src={item.image}
            alt={item.name}
            loading="lazy"
            onError={() => setBroken(true)}
          />
        ) : (
          <div className="item-swatch" style={{ background: item.colorHex, color: readableText(item.colorHex) }}>
            <span>{CATEGORY_LABEL[item.category].icon}</span>
          </div>
        )}
        <button
          type="button"
          className={`fav-btn ${item.favorite ? 'is-on' : ''}`}
          onClick={() => onToggleFavorite(item.id)}
          aria-pressed={item.favorite}
          title={item.favorite ? 'Убрать из избранного' : 'В избранное'}
        >
          {item.favorite ? '★' : '☆'}
        </button>
      </div>

      <div className="item-body">
        <h3 title={item.name}>{item.name}</h3>
        <p className="item-meta">
          <span className="dot" style={{ background: item.colorHex }} aria-hidden />
          {CATEGORY_LABEL[item.category].one} · {seasons}
        </p>
        <div className="chips">
          {item.styles.map((s) => (
            <span key={s} className="chip">
              {STYLE_LABEL[s]}
            </span>
          ))}
        </div>
        <dl className="scales">
          <div>
            <dt>Тепло</dt>
            <dd>
              <Scale value={item.warmth} />
            </dd>
          </div>
          <div>
            <dt>Формальность</dt>
            <dd>
              <Scale value={item.formality} />
            </dd>
          </div>
        </dl>
        {item.wornDates.length > 0 && (
          <p className="item-worn">Надето {item.wornDates.length} раз</p>
        )}
        <div className="item-actions">
          <button type="button" className="btn tiny" onClick={() => onEdit(item)}>
            Изменить
          </button>
          <button type="button" className="btn tiny ghost danger" onClick={() => onDelete(item)}>
            Удалить
          </button>
        </div>
      </div>
    </article>
  )
}

export function Scale({ value, max = 5 }: { value: number; max?: number }) {
  return (
    <span className="scale" aria-label={`${value} из ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <i key={i} className={i < value ? 'on' : ''} />
      ))}
    </span>
  )
}
