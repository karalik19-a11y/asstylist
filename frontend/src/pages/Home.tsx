import { useState } from 'react'
import type { Meta } from '../lib/types'
import { formatRub } from '../lib/format'
import { Badge, BrandLogo, SectionTitle, ThemeToggle } from '../components/ui'
import { playClick, playTick } from '../lib/sound'

export function Home({
  meta,
  onStart,
  onOpenHistory,
  onOpenSearch,
  userName,
  theme,
  onToggleTheme,
}: {
  meta: Meta | null
  onStart: () => void
  onOpenHistory: () => void
  onOpenSearch: () => void
  userName: string | null
  theme: 'noir' | 'parchment'
  onToggleTheme: () => void
}) {
  const [activeStylePreview, setActiveStylePreview] = useState<string>('minimal')
  const currentStyle =
    meta?.styles.find((s) => s.id === activeStylePreview) ?? meta?.styles[0]

  return (
    <div className="stack page-transition" style={{ gap: 30 }}>
      <header className="hero">
        <div className="hero-top">
          <BrandLogo big tagline onHome={() => window.scrollTo({ top: 0, behavior: 'smooth' })} />
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

      <section className="stack" style={{ gap: 16 }}>
        <button type="button" className="btn btn-primary btn-block btn-xl" onClick={() => { playClick(); onStart() }}>
          Собрать образ
        </button>
        <div className="home-actions-grid">
          <button type="button" className="btn btn-outline" onClick={() => { playClick(); onOpenHistory() }}>
            Архив образов
          </button>
          <button type="button" className="btn btn-outline" onClick={() => { playClick(); onOpenSearch() }}>
            Поиск вещей
          </button>
        </div>
      </section>

      {meta?.styles?.length ? (
        <section className="card stack" style={{ gap: 14 }}>
          <SectionTitle hint="листайте">Направления стиля</SectionTitle>
          <div className="style-pills-row">
            {meta.styles.map((style) => (
              <button
                key={style.id}
                type="button"
                className="style-pill-btn chip"
                data-active={activeStylePreview === style.id}
                onClick={() => { playTick(); setActiveStylePreview(style.id) }}
              >
                {style.label}
              </button>
            ))}
          </div>
          {currentStyle ? (
            <p className="muted" style={{ margin: 0, fontSize: 15, lineHeight: 1.5 }}>
              {currentStyle.description}
            </p>
          ) : null}
        </section>
      ) : null}

      <div className="page-mark">ASStylist · 2026</div>
    </div>
  )
}
