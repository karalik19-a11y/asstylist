import type { CSSProperties } from 'react'
import { useState } from 'react'
import type { LookItem } from '../lib/types'
import { formatRub } from '../lib/format'
import { openExternal } from '../lib/telegram'
import { Badge, verificationLabel, verificationTone } from './ui'

const BREAKDOWN_LABELS: Record<string, string> = {
  style: 'стиль',
  mood: 'настроение',
  silhouette: 'силуэт',
  color: 'цвет',
  formality: 'формальность',
  season: 'сезон',
  value: 'цена/кач-во',
  verification: 'проверка',
}

export function ItemCard({
  item,
  onSwap,
  swapping,
  index = 0,
}: {
  item: LookItem
  onSwap: (slot: string) => void
  swapping: boolean
  index?: number
}) {
  const [open, setOpen] = useState(false)
  const swatch =
    item.color_hexes.length > 0
      ? `linear-gradient(150deg, ${item.color_hexes.map((hex, i) => `${hex} ${i * 45}%`).join(', ')})`
      : 'rgba(255,255,255,0.06)'

  return (
    <article className="item-card" style={{ ['--d' as string]: `${index * 0.07}s` } as CSSProperties}>
      <div className="item-head">
        <div className="item-swatch" style={{ background: swatch }} aria-hidden="true" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="row-between">
            <span className="tiny">{item.slot_label}</span>
            <strong style={{ fontVariantNumeric: 'tabular-nums', color: 'var(--blue-deep)' }}>{formatRub(item.price_rub)}</strong>
          </div>
          <div style={{ fontWeight: 700, marginTop: 3 }}>{item.name}</div>
          <div className="muted small">
            {item.brand} · {item.fit}
          </div>
          <div className="wrap" style={{ marginTop: 9 }}>
            <Badge tone={verificationTone(item.verification_status)}>
              {verificationLabel(item.verification_status)} · {Math.round(item.verification_score * 100)}%
            </Badge>
            <Badge tone="pop">матч {Math.round(item.score * 100)}%</Badge>
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
          {swapping ? 'Меняем…' : '⇄ Заменить'}
        </button>
        <button type="button" className="btn btn-sm btn-ghost" onClick={() => openExternal(item.url)}>
          Открыть товар ↗
        </button>
        <button type="button" className="link-btn" style={{ marginLeft: 'auto' }} onClick={() => setOpen((v) => !v)}>
          {open ? 'скрыть оценки ↑' : 'почему эта вещь ↓'}
        </button>
      </div>

      {open ? (
        <div className="breakdown">
          {Object.entries(item.breakdown).map(([key, value]) => (
            <div className="breakdown-row" key={key}>
              <span style={{ width: 82, flex: '0 0 auto' }}>{BREAKDOWN_LABELS[key] ?? key}</span>
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
