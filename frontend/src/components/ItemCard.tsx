import { useState } from 'react'
import type { LookItem } from '../lib/types'
import { formatRub } from '../lib/format'
import { openExternal } from '../lib/telegram'
import { playClick, playTick } from '../lib/sound'
import { ExternalIcon, SwapIcon } from '../lib/graphics'
import { isAvitoUrl } from './ui'
import { ItemPhoto } from './ItemPhoto'

function shortDate(value?: string | null): string {
  if (!value) return ''
  const iso = value.length >= 10 ? value.slice(0, 10) : value
  const [year, month, day] = iso.split('-')
  if (!year || !month || !day) return ''
  const sameYear = year === String(new Date().getFullYear())
  return sameYear ? `${day}.${month}` : `${day}.${month}.${year}`
}

const BREAKDOWN_LABELS: Record<string, string> = {
  color: 'Цвет',
  silhouette: 'Силуэт',
  material: 'Материал',
  style: 'Стиль',
  price: 'Цена',
  fit: 'Посадка',
  novelty: 'Свежесть',
  niche: 'Нишевость',
}

export function ItemCard({
  item,
  swapping,
  onSwap,
}: {
  item: LookItem
  swapping: boolean
  onSwap: (slot: string) => void
}) {
  const [open, setOpen] = useState(false)
  const isListing = (item.link_kind ?? item.listing?.kind ?? 'listing') !== 'search'
  const feed = item.feed ?? item.listing?.feed
  const snapshotAt = item.snapshot_captured_at
  const swatch = item.color_hexes?.length
    ? `linear-gradient(135deg, ${item.color_hexes.map((hex, index) => `${hex} ${index * 45}%`).join(', ')})`
    : 'var(--surface-2)'

  return (
    <article className="item-card item-card-v2">
      <div className="item-card-media">
        <ItemPhoto
          src={item.image_url}
          alt={`${item.brand} — ${item.name}`}
          swatch={swatch}
          chips={item.color_hexes}
          fallbackLabel={isListing ? 'Фото объявления' : 'Фото вещи'}
          className="item-photo-card"
        />
        <span className="item-slot-badge">{item.slot_label || item.slot}</span>
      </div>

      <div className="item-card-body">
        <div className="item-card-top">
          <div className="item-brand">{item.brand}</div>
          <strong className="item-price">{formatRub(item.price_rub)}</strong>
        </div>
        <h3 className="item-name">{item.name}</h3>
        <div className="item-meta muted small">
          {item.fit ? <span>{item.fit}</span> : null}
          {isListing ? (
            <span className="item-meta-dot">
              {feed === 'snapshot' && snapshotAt ? `снимок ${shortDate(snapshotAt)}` : 'объявление'}
            </span>
          ) : (
            <span className="item-meta-dot item-meta-warn">подборка Авито</span>
          )}
        </div>

        {item.reasons?.length ? (
          <p className="item-why muted">{item.reasons[0]}</p>
        ) : null}

        <div className="item-actions-grid item-actions-v2">
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => {
              playClick()
              openExternal(item.url)
            }}
          >
            <ExternalIcon size={12} />
            <span>
              {isAvitoUrl(item.url) || item.source === 'avito'
                ? isListing
                  ? 'Открыть'
                  : 'На Авито'
                : 'В магазин'}
            </span>
          </button>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => {
              playClick()
              onSwap(item.slot)
            }}
            disabled={swapping}
          >
            <SwapIcon size={12} />
            <span>{swapping ? '…' : 'Заменить'}</span>
          </button>
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={() => {
              playTick()
              setOpen((v) => !v)
            }}
          >
            {open ? 'Скрыть' : 'Ещё'}
          </button>
        </div>

        {open ? (
          <div className="item-extra stack" style={{ gap: 10 }}>
            {item.reasons && item.reasons.length > 1 ? (
              <ul className="reasons">
                {item.reasons.slice(1).map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
            {item.breakdown ? (
              <div className="breakdown">
                {Object.entries(item.breakdown)
                  .filter(([, value]) => typeof value === 'number')
                  .map(([key, value]) => (
                    <div className="breakdown-row" key={key}>
                      <span style={{ width: 84, flex: '0 0 auto' }}>{BREAKDOWN_LABELS[key] ?? key}</span>
                      <span className="bar">
                        <span style={{ width: `${Math.round(Number(value) * 100)}%` }} />
                      </span>
                      <span style={{ width: 28, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                        {Math.round(Number(value) * 100)}
                      </span>
                    </div>
                  ))}
              </div>
            ) : null}
            {item.color_hexes?.length ? (
              <div className="wrap" style={{ gap: 6 }}>
                {item.color_hexes.map((hex) => (
                  <span key={hex} className="palette-dot" style={{ background: hex }} title={hex} />
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  )
}
