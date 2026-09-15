import { useState } from 'react'
import type { LookItem } from '../lib/types'
import { formatRub } from '../lib/format'
import { openExternal } from '../lib/telegram'
import { Badge, verificationLabel, verificationTone } from './ui'

const FALLBACK_IMAGE: Record<string, string> = {
  top: '/img/babytee.jpg',
  bottom: '/img/baggyjeans.jpg',
  knitwear: '/img/velour.jpg',
  outerwear: '/img/puffer.jpg',
  dress: '/img/halter.jpg',
  shoes: '/img/sneakers.jpg',
  bag: '/img/baguette.jpg',
  accessory: '/img/shades.jpg',
}

function imageFor(item: LookItem): string {
  if (item.image_url) return item.image_url
  const tone = item.colors[0] ?? ''
  if (item.category === 'accessory') return tone === 'head' ? '/img/bucket.jpg' : '/img/shades.jpg'
  if (item.category === 'bottom') return tone === 'mini' ? '/img/miniskirt.jpg' : '/img/baggyjeans.jpg'
  return FALLBACK_IMAGE[item.category] ?? '/img/babytee.jpg'
}

const BREAKDOWN_LABELS: Record<string, string> = {
  style: 'стиль',
  mood: 'настроение',
  silhouette: 'силуэт',
  color: 'цвет',
  formality: 'формальность',
  season: 'сезон',
  value: 'цена/качество',
  verification: 'проверка',
}

export function ItemCard({
  item,
  onSwap,
  swapping,
}: {
  item: LookItem
  onSwap: (slot: string) => void
  swapping: boolean
}) {
  const [open, setOpen] = useState(false)
  const swatch =
    item.color_hexes.length > 0
      ? `linear-gradient(140deg, ${item.color_hexes.map((hex, index) => `${hex} ${index * 45}%`).join(', ')})`
      : 'var(--surface-2)'

  return (
    <article className="item-card">
      <div className="item-head">
        <div className="item-photo">
          <img src={imageFor(item)} alt={item.name} loading="lazy" />
          <span className="item-photo-swatch" style={{ background: swatch }} aria-hidden="true" />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="row-between">
            <span className="tiny">{item.slot_label}</span>
            <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{formatRub(item.price_rub)}</strong>
          </div>
          <div style={{ fontWeight: 600, marginTop: 2 }}>{item.name}</div>
          <div className="muted small">
            {item.brand} · {item.fit}
          </div>
          <div className="wrap" style={{ marginTop: 8 }}>
            <Badge tone={verificationTone(item.verification_status)}>
              {verificationLabel(item.verification_status)} · {Math.round(item.verification_score * 100)}%
            </Badge>
            <Badge>матч {Math.round(item.score * 100)}%</Badge>
          </div>
        </div>
      </div>

      <ul className="reasons">
        {item.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>

      <div className="row" style={{ gap: 8 }}>
        <button type="button" className="btn btn-sm" onClick={() => onSwap(item.slot)} disabled={swapping}>
          {swapping ? 'Меняем…' : 'Заменить'}
        </button>
        <button type="button" className="btn btn-sm btn-ghost" onClick={() => openExternal(item.url)}>
          Открыть товар
        </button>
        <button type="button" className="link-btn" style={{ marginLeft: 'auto' }} onClick={() => setOpen((v) => !v)}>
          {open ? 'скрыть оценки' : 'почему эта вещь'}
        </button>
      </div>

      {open ? (
        <div className="breakdown">
          {Object.entries(item.breakdown).map(([key, value]) => (
            <div className="breakdown-row" key={key}>
              <span style={{ width: 78, flex: '0 0 auto' }}>{BREAKDOWN_LABELS[key] ?? key}</span>
              <span className="bar">
                <span style={{ width: `${Math.round(value * 100)}%` }} />
              </span>
              <span style={{ width: 28, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {Math.round(value * 100)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  )
}
