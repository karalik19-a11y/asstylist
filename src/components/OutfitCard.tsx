import { useState } from 'react'
import type { Outfit, WardrobeItem } from '../types'
import { OCCASION_MAP, SEASON_LABEL } from '../lib/catalog'
import { readableText } from '../lib/color'
import { gradeOf } from '../lib/stylist'

interface OutfitCardProps {
  outfit: Outfit
  items: WardrobeItem[]
  saved?: boolean
  alternativesFor?: (item: WardrobeItem) => WardrobeItem[]
  onSave?: () => void
  onRemove?: () => void
  onWear?: () => void
  onSwap?: (fromId: string, toId: string) => void
  title?: string
}

export function ScoreRing({ score }: { score: number }) {
  const r = 26
  const c = 2 * Math.PI * r
  const dash = (Math.max(0, Math.min(100, score)) / 100) * c
  const tone = score >= 85 ? 'good' : score >= 72 ? 'ok' : score >= 58 ? 'mid' : 'low'
  return (
    <div className={`score-ring ${tone}`}>
      <svg viewBox="0 0 64 64" width="64" height="64" aria-hidden>
        <circle className="ring-bg" cx="32" cy="32" r={r} />
        <circle
          className="ring-fg"
          cx="32"
          cy="32"
          r={r}
          strokeDasharray={`${dash} ${c - dash}`}
        />
      </svg>
      <span>
        {score}
        <small>/100</small>
      </span>
    </div>
  )
}

export function OutfitCard({
  outfit,
  items,
  saved = false,
  alternativesFor,
  onSave,
  onRemove,
  onWear,
  onSwap,
  title,
}: OutfitCardProps) {
  const [swapFor, setSwapFor] = useState<string | null>(null)
  const [broken, setBroken] = useState<Record<string, boolean>>({})
  const cfg = OCCASION_MAP[outfit.occasion]

  return (
    <article className="outfit-card">
      <header className="outfit-head">
        <div>
          <h3>
            {title ?? (
              <>
                {cfg.icon} {cfg.label}
              </>
            )}
          </h3>
          <p className="muted">
            {SEASON_LABEL[outfit.season]} · {outfit.temperature > 0 ? '+' : ''}
            {outfit.temperature} °C · оценка: {gradeOf(outfit.score)}
          </p>
        </div>
        <ScoreRing score={outfit.score} />
      </header>

      <div className="outfit-items">
        {items.map((item) => {
          const alts = alternativesFor ? alternativesFor(item) : []
          const isOpen = swapFor === item.id
          return (
            <div className="outfit-item" key={item.id}>
              <div className="outfit-thumb">
                {item.image && !broken[item.id] ? (
                  <img
                    src={item.image}
                    alt={item.name}
                    loading="lazy"
                    onError={() => setBroken((b) => ({ ...b, [item.id]: true }))}
                  />
                ) : (
                  <div
                    className="outfit-swatch"
                    style={{ background: item.colorHex, color: readableText(item.colorHex) }}
                  >
                    {item.name.slice(0, 1)}
                  </div>
                )}
              </div>
              <span className="outfit-item-name">{item.name}</span>
              {alternativesFor && onSwap && alts.length > 0 && (
                <div className="swap">
                  <button
                    type="button"
                    className="swap-toggle"
                    onClick={() => setSwapFor(isOpen ? null : item.id)}
                    aria-expanded={isOpen}
                    title="Заменить вещь"
                  >
                    ⇄
                  </button>
                  {isOpen && (
                    <div className="swap-menu">
                      <p className="swap-title">Заменить на:</p>
                      {alts.slice(0, 8).map((alt) => (
                        <button
                          key={alt.id}
                          type="button"
                          className="swap-option"
                          onClick={() => {
                            onSwap(item.id, alt.id)
                            setSwapFor(null)
                          }}
                        >
                          <span className="dot" style={{ background: alt.colorHex }} />
                          {alt.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="breakdown">
        {outfit.analysis.parts.map((part) => (
          <div className="breakdown-row" key={part.key}>
            <span className="breakdown-label">{part.label}</span>
            <span className="bar">
              <i style={{ width: `${Math.round(part.value * 100)}%` }} />
            </span>
            <span className="breakdown-value">{Math.round(part.value * 100)}%</span>
            <span className="breakdown-hint">{part.hint}</span>
          </div>
        ))}
      </div>

      <ul className="tips">
        {outfit.analysis.tips.map((tip, i) => (
          <li key={i}>{tip}</li>
        ))}
      </ul>

      <footer className="outfit-foot">
        {onWear && (
          <button type="button" className="btn tiny" onClick={onWear}>
            Надел(а) сегодня
          </button>
        )}
        {saved ? (
          onRemove && (
            <button type="button" className="btn tiny ghost danger" onClick={onRemove}>
              Убрать из сохранённых
            </button>
          )
        ) : (
          onSave && (
            <button type="button" className="btn tiny primary" onClick={onSave}>
              Сохранить образ
            </button>
          )
        )}
      </footer>
    </article>
  )
}
