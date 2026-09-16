import { useState } from 'react'
import type { LookItem } from '../lib/types'
import { formatRub } from '../lib/format'
import { openExternal } from '../lib/telegram'
import { playClick, playTick } from '../lib/sound'
import { ExternalIcon, SwapIcon } from '../lib/graphics'
import { Badge, verificationLabel, verificationTone } from './ui'
import { ItemPhoto } from './ItemPhoto'

const BREAKDOWN_LABELS: Record<string, string> = {
  style: 'стиль',
  mood: 'настроение',
  silhouette: 'силуэт',
  color: 'цвет',
  formality: 'формальность',
  season: 'сезон',
  value: 'цена/качество',
  verification: 'проверка',
  // метрики движка ASSTYLIST Fashion Engine
  engine: 'fashion score',
  trend: 'тренд',
  uniqueness: 'уникальность',
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
      ? `linear-gradient(135deg, ${item.color_hexes.map((hex, index) => `${hex} ${index * 45}%`).join(', ')})`
      : 'var(--surface-2)'

  return (
    <article className="item-card">
      {item.image_url ? (
        <ItemPhoto
          src={item.image_url}
          alt={`${item.brand} — ${item.name}`}
          swatch={swatch}
          className="item-photo-card"
        />
      ) : null}
      <div className="item-head">
        <div className="item-swatch" style={{ background: swatch }} aria-hidden="true">
          <span
            style={{
              position: 'absolute',
              bottom: 2,
              right: 4,
              fontSize: 9,
              fontFamily: 'var(--font-mono)',
              color: '#fff',
              textShadow: '0 1px 2px #000',
            }}
          >
            {item.slot.slice(0, 3).toUpperCase()}
          </span>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="row-between">
            <span className="tiny">{item.slot_label}</span>
            <strong style={{ fontVariantNumeric: 'tabular-nums', fontSize: 17 }}>{formatRub(item.price_rub)}</strong>
          </div>
          <div style={{ fontWeight: 600, fontSize: 17, marginTop: 4, lineHeight: 1.3 }}>{item.name}</div>
          <div className="muted small" style={{ marginTop: 3 }}>
            {item.brand} · {item.fit}
          </div>
          <div className="wrap" style={{ marginTop: 12, gap: 8 }}>
            <Badge tone={verificationTone(item.verification_status)}>
              {verificationLabel(item.verification_status)} · {Math.round(item.verification_score * 100)}%
            </Badge>
            <Badge>селекция {Math.round(item.score * 100)}%</Badge>
            {item.engine?.role_label ? <Badge>{item.engine.role_label}</Badge> : null}
            {item.engine?.taste_label ? (
              <Badge tone={item.engine.in_engine_outfit ? 'ok' : 'neutral'}>{item.engine.taste_label}</Badge>
            ) : null}
            {item.engine?.fashion_score ? <Badge>fashion {item.engine.fashion_score}/100</Badge> : null}
          </div>
        </div>
      </div>

      <ul className="reasons">
        {item.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>

      {/* Action buttons: Responsive Grid guaranteed NEVER to overlap */}
      <div className="item-actions-grid">
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
          <span>{swapping ? 'Подбор…' : 'Заменить'}</span>
        </button>

        <button
          type="button"
          className="btn btn-sm btn-outline"
          onClick={() => {
            playClick()
            openExternal(item.url)
          }}
        >
          <ExternalIcon size={12} />
          <span>В магазин</span>
        </button>

        <button
          type="button"
          className="btn btn-sm btn-ghost"
          onClick={() => {
            playTick()
            setOpen((v) => !v)
          }}
        >
          <span>{open ? 'Скрыть параметры' : 'Параметры вещи'}</span>
        </button>
      </div>

      {open ? (
        <div className="breakdown">
          {Object.entries(item.breakdown)
            .filter(([, value]) => typeof value === 'number')
            .map(([key, value]) => (
            <div className="breakdown-row" key={key}>
              <span style={{ width: 84, flex: '0 0 auto' }}>{BREAKDOWN_LABELS[key] ?? key}</span>
              <span className="bar">
                <span style={{ width: `${Math.round(value * 100)}%` }} />
              </span>
              <span style={{ width: 28, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {Math.round(value * 100)}
              </span>
            </div>
          ))}
          {item.engine?.engine_category ? (
            <div className="muted small">
              Категория: {item.engine.engine_category}
              {item.engine.material && item.engine.material !== 'unknown' ? ` · фактура: ${item.engine.material}` : ''}
              {item.engine.silhouette?.length ? ` · силуэт: ${item.engine.silhouette.join(', ')}` : ''}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}
