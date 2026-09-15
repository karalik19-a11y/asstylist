import type { CSSProperties } from 'react'
import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Postmark, Reveal, SectionTitle } from '../components/ui'

const STEPS = [
  { num: '01', title: 'Фото и мерки', text: 'Загрузи фото, укажи рост и вес.' },
  { num: '02', title: 'Стиль и настроение', text: 'Выбери, что ближе сегодня.' },
  { num: '03', title: 'Детали', text: 'Повод, сезон и бюджет.' },
  { num: '04', title: 'Готовый образ', text: 'Вещи, палитра и советы.' },
]

const COVER_LINES = [
  'палитра под твой тип внешности',
  'силуэт по твоим меркам',
  'вещи с проверенными ссылками',
  'строго в рамках бюджета',
]

const TICKER_ITEMS = ['новый образ за минуту', 'палитра', 'силуэт', 'проверенные вещи', 'твой стиль']

function Ticker() {
  const sequence = (
    <>
      {TICKER_ITEMS.map((item) => (
        <span key={item}>
          <i aria-hidden="true">✦</i>
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

function Masthead() {
  return (
    <h1 className="masthead" aria-label="ASStylist">
      {'ASStylist'.split('').map((ch, i) => (
        <span
          key={`${ch}-${i}`}
          aria-hidden="true"
          className={i < 3 ? 'm-letter red' : 'm-letter'}
          style={{ '--i': i } as CSSProperties}
        >
          {ch}
        </span>
      ))}
    </h1>
  )
}

export function Home({
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenLook,
}: {
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenLook: (id: number) => void
}) {
  return (
    <div className="stack">
      {/* ---------- марка ---------- */}
      <Reveal delay={0}>
        <section className="cover">
          <div className="issue-row">
            <span>est. 2026</span>
            <b>asstylist post</b>
            <span>№ 001</span>
          </div>

          <Masthead />

          <div className="first-class">
            <Postmark size={78} />
            <span className="fc-label">first class · par avion</span>
          </div>

          <div className="perfo" aria-hidden="true" />

          <div className="cover-head">
            <div className="cover-title">
              Твой новый <em>образ</em>
            </div>
            <div className="cover-sub">
              Под фигуру, настроение и бюджет — за минуту.
            </div>
          </div>

          <div className="wild-strip" aria-hidden="true" />

          <div className="cover-lines">
            {COVER_LINES.map((line) => (
              <div key={line} className="cover-line">
                <i aria-hidden="true">✦</i>
                {line}
              </div>
            ))}
          </div>

          <div className="airmail" aria-hidden="true" />

          <button type="button" className="btn btn-primary btn-lg btn-block" onClick={onStart} aria-label="Собрать образ">
            Собрать образ →
          </button>
          <div className="ghost-row">
            <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenHistory}>
              Мои образы
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenVerification}>
              Проверка товаров
            </button>
          </div>

          <div className="perfo" aria-hidden="true" />

          <div className="barcode-row">
            <span className="barcode" aria-hidden="true" />
            <span className="price">
              asstylist · выпуск 001
              <br />
              новый образ каждую неделю
            </span>
          </div>
        </section>
      </Reveal>

      <Reveal delay={0.1}>
        <Ticker />
      </Reveal>

      {/* ---------- как это работает ---------- */}
      <Reveal delay={0.15}>
        <section className="card stack" style={{ gap: 14 }}>
          <SectionTitle hint="4 шага">Как это работает</SectionTitle>
          <div className="step-grid">
            {STEPS.map((step) => (
              <div key={step.num} className="step-card">
                <div className="num">{step.num}</div>
                <strong>{step.title}</strong>
                <p>{step.text}</p>
              </div>
            ))}
          </div>
        </section>
      </Reveal>

      {history.length ? (
        <Reveal delay={0.2}>
          <section className="stack" style={{ gap: 10 }}>
            <SectionTitle hint="недавнее">Недавние образы</SectionTitle>
            <div className="card index-list">
              {history.slice(0, 3).map((entry, index) => (
                <button
                  key={entry.id}
                  type="button"
                  className="index-row"
                  onClick={() => onOpenLook(entry.id)}
                >
                  <span className="index-num">{String(index + 1).padStart(2, '0')}</span>
                  <span className="stack" style={{ flex: 1, minWidth: 0, gap: 2 }}>
                    <span className="row-between" style={{ gap: 8 }}>
                      <strong>{entry.style}</strong>
                      <span className="muted small" style={{ fontVariantNumeric: 'tabular-nums', flex: '0 0 auto' }}>
                        {formatRub(entry.total_rub)}
                      </span>
                    </span>
                    <span className="muted small">
                      {itemsWord(entry.items_count)} · оценка {Math.round(entry.score)} · {relativeTime(entry.created_at)}
                    </span>
                  </span>
                  <span className="index-arrow" aria-hidden="true">→</span>
                </button>
              ))}
            </div>
          </section>
        </Reveal>
      ) : null}

      <hr className="rule-double" />
      <div className="page-mark">ASStylist · 2026</div>
    </div>
  )
}
