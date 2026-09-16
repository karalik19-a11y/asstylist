import { useState } from 'react'
import type { Meta } from '../lib/types'
import { formatRub } from '../lib/format'
import { Badge, BrandLogo, ThemeToggle } from '../components/ui'
import { playClick, playTick } from '../lib/sound'

export function Home({
  meta,
  onStart,
  onOpenSearch,
  userName,
  theme,
  onToggleTheme,
}: {
  meta: Meta | null
  onStart: () => void
  onOpenSearch?: () => void
  userName: string | null
  theme: 'noir' | 'parchment'
  onToggleTheme: () => void
}) {
  const [activeStylePreview, setActiveStylePreview] = useState<string>('minimal')
  const currentStyle = meta?.styles.find((s) => s.id === activeStylePreview) ?? meta?.styles[0]

  return (
    <div className="stack page-transition home-editorial" style={{ gap: 24 }}>
      <header className="hero home-hero">
        <div className="hero-top home-hero-top">
          <BrandLogo big tagline onHome={() => window.scrollTo({ top: 0, behavior: 'smooth' })} />
          <div className="hero-top-controls">
            {meta?.demo_mode ? <Badge tone="warn">демо</Badge> : <Badge tone="ok">online</Badge>}
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          </div>
        </div>

        <div className="home-hero-kicker">
          <span>PERSONAL STYLING ENGINE</span>
          <span>{meta ? `${meta.styles.length} направлений` : 'ASStylist'}</span>
        </div>

        <h1>
          {userName ? `${userName}, ` : ''}соберём образ, <em>который работает на вас</em>
        </h1>
        <p className="hero-sub">
          Стиль, посадка, цвет и реальные вещи — в одной персональной селекции.
        </p>

        {meta ? (
          <div className="home-stat-line">
            <span><b>{meta.styles.length}</b> стилей</span>
            <span><b>{meta.moods.length}</b> настроений</span>
            <span><b>{formatRub(meta.budget.max_rub)}</b> верхний бюджет</span>
            <span><b>AVITO</b> реальные вещи</span>
          </div>
        ) : null}
      </header>

      <section className="home-actions-editorial" aria-label="Основные действия">
        <button
          type="button"
          className="btn btn-primary btn-block btn-xl home-main-cta"
          onClick={() => { playClick(); onStart() }}
        >
          <span>Собрать мой образ</span><span aria-hidden="true">↗</span>
        </button>
        <button
          type="button"
          className="btn btn-outline btn-block home-secondary-cta"
          onClick={() => { playClick(); onOpenSearch?.() }}
        >
          Найти конкретную вещь <span aria-hidden="true">→</span>
        </button>
      </section>

      {meta?.styles?.length ? (
        <section className="home-style-panel" aria-labelledby="style-directions-title">
          <div className="home-section-topline">
            <div>
              <span className="home-section-index">01 / STYLE</span>
              <h2 id="style-directions-title">Направления стиля</h2>
            </div>
            <span className="home-scroll-hint">свайпайте →</span>
          </div>

          <div className="style-pills-row" role="tablist" aria-label="Направления стиля">
            {meta.styles.map((style, index) => (
              <button
                key={style.id}
                type="button"
                className="style-pill-btn"
                data-active={activeStylePreview === style.id}
                role="tab"
                aria-selected={activeStylePreview === style.id}
                onClick={() => { playTick(); setActiveStylePreview(style.id) }}
              >
                <span className="style-pill-index">{String(index + 1).padStart(2, '0')}</span>
                <span className="style-pill-label">{style.label}</span>
                <span className="style-pill-arrow" aria-hidden="true">↗</span>
              </button>
            ))}
          </div>

          {currentStyle ? (
            <div className="style-preview-editorial">
              <span className="style-preview-label">SELECTED DIRECTION</span>
              <strong>{currentStyle.label}</strong>
              <p>{currentStyle.description}</p>
            </div>
          ) : null}
        </section>
      ) : null}

      <div className="page-mark">ASStylist · 2026</div>
    </div>
  )
}
