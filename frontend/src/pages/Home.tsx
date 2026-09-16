import { useState } from 'react'
import type { HistoryEntry, Meta } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, BrandLogo, SectionTitle, ThemeToggle } from '../components/ui'
import { playClick, playTick } from '../lib/sound'

export function Home({
  meta,
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenSearch,
  onOpenLook,
  userName,
  theme,
  onToggleTheme,
}: {
  meta: Meta | null
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenSearch: () => void
  onOpenLook: (id: number) => void
  userName: string | null
  theme: 'noir' | 'parchment'
  onToggleTheme: () => void
}) {
  const [activeStylePreview, setActiveStylePreview] = useState<string>('minimal')

  const currentStyle = meta?.styles.find((s) => s.id === activeStylePreview) ?? meta?.styles[0]

  return (
    <div className="stack page-transition" style={{ gap: 30 }}>
      {/* ---------- Hero: коротко, крупно, по делу ---------- */}
      <header className="hero">
        <div className="hero-top">
          <BrandLogo
            big
            tagline
            onHome={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          />
          <div className="hero-top-controls">
            {meta?.demo_mode ? <Badge tone="warn">демо-режим</Badge> : <Badge tone="ok">telegram</Badge>}
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          </div>
        </div>

        <h1>
          {userName ? `${userName}, ` : ''}соберём образ, <em>который вам идёт</em>
        </h1>

        <p className="hero-sub">Пять коротких шагов — и гардероб под вашу фигуру, цвета и бюджет готов.</p>

        {meta ? (
          <div className="wrap" style={{ gap: 8 }}>
            <Badge>{meta.styles.length} стилей</Badge>
            <Badge>{meta.moods.length} настроений</Badge>
            <Badge>{meta.colors.length} оттенков</Badge>
            <Badge>до {formatRub(meta.budget.max_rub)}</Badge>
            <Badge tone="ok">вещи — с Авито</Badge>
          </div>
        ) : null}
      </header>

      {/* ---------- Одно главное действие + тихие вторичные ---------- */}
      <section className="stack" style={{ gap: 16 }}>
        <button
          type="button"
          className="btn btn-primary btn-block btn-xl"
          onClick={() => {
            playClick()
            onStart()
          }}
        >
          Собрать образ
        </button>

        <button
          type="button"
          className="link-btn cta-link"
          onClick={() => {
            playClick()
            onOpenSearch()
          }}
        >
          Найти вещи словами
        </button>

        <div className="home-actions-grid">
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => {
              playClick()
              onOpenHistory()
            }}
          >
            Мои образы
          </button>

          <button
            type="button"
            className="btn btn-outline"
            onClick={() => {
              playClick()
              onOpenVerification()
            }}
          >
            Проверка товаров
          </button>
        </div>
      </section>

      {/* ---------- Направления стиля: табы + короткая подсказка ---------- */}
      {meta?.styles?.length ? (
        <section className="style-showcase-container">
          <SectionTitle hint={`${meta.styles.length}`}>Направления стиля</SectionTitle>

          <div className="style-pills-row">
            {meta.styles.map((style) => (
              <button
                key={style.id}
                type="button"
                className="style-pill-btn"
                data-active={activeStylePreview === style.id}
                onClick={() => {
                  playTick()
                  setActiveStylePreview(style.id)
                }}
              >
                {style.label}
              </button>
            ))}
          </div>

          {currentStyle ? (
            <div className="style-preview-card">
              <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ fontSize: 17, fontFamily: 'var(--font-display)' }}>{currentStyle.label}</strong>
                <div className="small muted" style={{ marginTop: 4 }}>
                  {currentStyle.description}
                </div>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* ---------- Последние образы ---------- */}
      {history.length ? (
        <section className="stack" style={{ gap: 12 }}>
          <SectionTitle hint={`${history.length}`}>Последние образы</SectionTitle>
          <div className="card index-list">
            {history.slice(0, 3).map((entry, index) => (
              <button
                key={entry.id}
                type="button"
                className="index-row"
                onClick={() => {
                  playClick()
                  onOpenLook(entry.id)
                }}
              >
                <span className="index-num">{String(index + 1).padStart(2, '0')}</span>
                <span className="stack" style={{ flex: 1, minWidth: 0, gap: 3 }}>
                  <span className="row-between" style={{ gap: 10 }}>
                    <strong style={{ fontSize: 16 }}>{entry.style}</strong>
                    <span className="muted small" style={{ fontVariantNumeric: 'tabular-nums' }}>
                      {formatRub(entry.total_rub)}
                    </span>
                  </span>
                  <span className="muted small">
                    {itemsWord(entry.items_count)} · индекс {Math.round(entry.score)} · {relativeTime(entry.created_at)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <div className="page-mark">ASStylist · 2026</div>
    </div>
  )
}
