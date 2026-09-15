import { useState } from 'react'
import type { HistoryEntry, Meta } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, SectionTitle } from '../components/ui'
import { CheetahArtwork, DiamondIcon, LeopardRibbon, STYLE_BADGES } from '../lib/graphics'
import { playClick, playTick } from '../lib/sound'

const STEPS = [
  { num: '01', kanji: '写', title: 'Фото и пропорции', text: 'Анализ силуэта, пропорций и природного колорита.' },
  { num: '02', kanji: '格', title: 'Стиль и тональность', text: '10 гардеробных эстетик и 8 настроений.' },
  { num: '03', kanji: '金', title: 'Бюджетный лимит', text: 'Строгий баланс стоимости без превышения лимита.' },
  { num: '04', kanji: '証', title: 'Проверенные бренды', text: 'Верификация цен, ссылок и подлинности позиций.' },
]

const TICKER_ITEMS = [
  'ATELIER 2026',
  'ПЕРСОНАЛЬНЫЙ СТИЛЬ',
  'СИЛУЭТ И ПОСАДКА',
  'ЦВЕТОВАЯ ГАММА',
  'ВЕРИФИЦИРОВАННЫЙ КАТАЛОГ',
  'КАЧЕСТВЕННЫЙ КРОЙ',
  'ВЫПУСК 01',
]

function Ticker() {
  const sequence = (
    <>
      {TICKER_ITEMS.map((item) => (
        <span key={item}>
          <i>
            <DiamondIcon size={8} />
          </i>
          {item}
        </span>
      ))}
    </>
  )
  return (
    <div className="ticker" aria-hidden="true">
      <div className="ticker-track">
        <span>{sequence}</span>
        <span>{sequence}</span>
      </div>
    </div>
  )
}

export function Home({
  meta,
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenSearch,
  onOpenLook,
  userName,
}: {
  meta: Meta | null
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenSearch: () => void
  onOpenLook: (id: number) => void
  userName: string | null
}) {
  const [activeStylePreview, setActiveStylePreview] = useState<string>('minimal')

  const currentStyle = meta?.styles.find((s) => s.id === activeStylePreview) ?? meta?.styles[0]
  const currentBadge = STYLE_BADGES[activeStylePreview] ?? { kanji: '簡', num: '01', code: 'MINIMAL' }

  return (
    <div className="stack page-transition" style={{ gap: 18 }}>
      {/* ---------- Leopard Ribbon Accent (Ref 3 & 1) ---------- */}
      <LeopardRibbon height={10} />

      {/* ---------- Atelier Masthead (Ref 1 & 2) ---------- */}
      <header className="atelier-masthead">
        <div className="masthead-meta">
          <div className="masthead-meta-left">
            <span className="tiny">ЖУРНАЛ СТИЛЯ</span>
            <span className="tiny">·</span>
            <span className="tiny">АРХИВ 2026</span>
          </div>
          <div className="tiny">EDITION № 01</div>
        </div>

        <div className="masthead-center">
          <div className="masthead-logo-group">
            <div className="masthead-title">
              AS<span>STYLIST</span>
            </div>
            <div className="masthead-subline">СТУДИЯ ПЕРСОНАЛЬНОЙ ГАРДЕРОБНОЙ СЕЛЕКЦИИ</div>
          </div>

          <div className="masthead-stamp-badge">
            <span className="masthead-stamp-kanji">東京</span>
            <span className="masthead-stamp-code">ED.26</span>
          </div>
        </div>
      </header>

      {/* ---------- Running Ticker (No emojis, crisp diamonds) ---------- */}
      <Ticker />

      {/* ---------- Hero Editorial Screenprint Section (Ref 1) ---------- */}
      <section className="stamp-card stack" style={{ gap: 14 }}>
        <div className="row-between">
          <span className="kicker">
            <DiamondIcon size={7} /> СТУДИЙНЫЙ НОМЕР
          </span>
          {meta?.demo_mode ? <Badge tone="warn">демо-режим</Badge> : <Badge tone="ok">telegram</Badge>}
        </div>

        <div className="row" style={{ gap: 14, alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 style={{ fontSize: 28, color: 'var(--stamp-ink)', lineHeight: 1.1 }}>
              {userName ? `${userName}, ` : ''}
              соберём образ, <em>который вам идёт</em>
            </h1>
            <p className="small" style={{ margin: '8px 0 0', color: 'var(--stamp-ink-muted)' }}>
              Персональный гардеробный директор: по пропорциям, росту, весу, эстетике и бюджету составляет выверенный лук
              из проверенных каталогов. Подбор вещей выполняет движок ASSTYLIST Fashion Engine —
              он же отвечает на свободный поиск. Стоимость сервиса — 0 ₽.
            </p>
          </div>

          {/* Risograph Linocut Artwork from Ref 1 */}
          <div
            style={{
              width: 90,
              height: 105,
              flexShrink: 0,
              color: 'var(--stamp-ink)',
              border: '1.5px solid var(--stamp-ink)',
              padding: 4,
              background: '#fff',
              boxShadow: '3px 3px 0 var(--accent-blue)',
            }}
          >
            <CheetahArtwork />
          </div>
        </div>

        {/* Action Buttons: Guaranteed NEVER to overlap */}
        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={() => {
            playClick()
            onStart()
          }}
          style={{ padding: '16px 20px', minHeight: 52, fontSize: 13.5 }}
        >
          Собрать образ
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
              onOpenSearch()
            }}
          >
            Поиск по движку
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

      {/* ---------- Interactive Style Lookbook Matrix ---------- */}
      {meta?.styles?.length ? (
        <section className="style-showcase-container">
          <SectionTitle hint="интерактивный каталог">Направления стиля</SectionTitle>

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
              <div className="style-preview-stamp">
                <span className="stamp-kanji" style={{ fontSize: 22, color: 'var(--accent-crimson)' }}>
                  {currentBadge.kanji}
                </span>
                <span className="tiny" style={{ fontSize: 9, marginTop: 2 }}>
                  № {currentBadge.num}
                </span>
                <span className="tiny" style={{ fontSize: 8, color: 'var(--text-sub)' }}>
                  {currentBadge.code}
                </span>
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ fontSize: 16, color: 'var(--stamp-ink)' }}>{currentStyle.label}</strong>
                <div className="small" style={{ color: 'var(--stamp-ink-muted)', marginTop: 2 }}>
                  {currentStyle.description}
                </div>
                {currentStyle.palette_hint?.length ? (
                  <div className="wrap" style={{ marginTop: 6, gap: 4 }}>
                    {currentStyle.palette_hint.map((colorId) => (
                      <span
                        key={colorId}
                        className="badge"
                        style={{
                          background: 'rgba(0,0,0,0.06)',
                          borderColor: 'rgba(0,0,0,0.15)',
                          color: 'var(--stamp-ink)',
                          fontSize: 9.5,
                        }}
                      >
                        {colorId}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* ---------- Архитектура гардероба ---------- */}
      <section className="card stack" style={{ gap: 12 }}>
        <SectionTitle hint={meta ? `система v${meta.version}` : undefined}>Содержание</SectionTitle>
        <div className="grid-2" style={{ gap: 10 }}>
          {STEPS.map((step) => (
            <div
              key={step.num}
              className="stack"
              style={{
                gap: 4,
                padding: '12px',
                background: 'var(--surface-2)',
                border: '1px solid var(--border)',
              }}
            >
              <div className="row-between">
                <span className="index-num" style={{ fontSize: 20 }}>
                  {step.num}
                </span>
                <span className="stamp-kanji" style={{ fontSize: 13, color: 'var(--accent-crimson)' }}>
                  {step.kanji}
                </span>
              </div>
              <strong style={{ fontSize: 13.5 }}>{step.title}</strong>
              <div className="muted small" style={{ lineHeight: 1.35 }}>
                {step.text}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Характеристики каталога ---------- */}
      {meta ? (
        <section className="card stack" style={{ gap: 10 }}>
          <SectionTitle hint="до 100 000 ₽">Параметры селекции</SectionTitle>
          <div className="wrap">
            <Badge>{meta.styles.length} стилей</Badge>
            <Badge>{meta.moods.length} настроений</Badge>
            <Badge>{meta.colors.length} оттенков в палитре</Badge>
            <Badge>бюджет {formatRub(meta.budget.max_rub)}</Badge>
          </div>
          <div className="muted small">
            Каждая единица в образе оценивается по 8 критериям: посадка, стилевой вектор, сочетаемость оттенков,
            сезонность, баланс цены и статус верификации.
          </div>
        </section>
      ) : null}

      {/* ---------- Последние образы ---------- */}
      {history.length ? (
        <section className="stack" style={{ gap: 10 }}>
          <SectionTitle hint={`${history.length} ${history.length === 1 ? 'образ' : 'образов'}`}>
            Последние селекции
          </SectionTitle>
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
                <span className="stack" style={{ flex: 1, minWidth: 0, gap: 2 }}>
                  <span className="row-between" style={{ gap: 8 }}>
                    <strong>{entry.style}</strong>
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

      <hr className="rule-double" />
      <div className="page-mark">— 01 · ASSTYLIST ATELIER —</div>
    </div>
  )
}
