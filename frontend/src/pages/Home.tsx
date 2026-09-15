import type { HistoryEntry } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Reveal, SectionTitle } from '../components/ui'

const STEPS = [
  { num: '01', title: 'Покажи себя', text: 'Фото и пара цифр — дальше мы сами.' },
  { num: '02', title: 'Выбери вайб', text: 'Хоть дерзкий, хоть нежный.' },
  { num: '03', title: 'Забери лук', text: 'Готовый образ со ссылками.' },
  { num: '04', title: 'Блистай', text: 'Носи. Сияй. Повторяй.' },
]

const COVER_LINES = [
  'палитра, от которой мурчат',
  'бюджет выжил и процветает',
  'комплименты почти гарантированы',
  'ass-approved · печать внизу',
]

const TICKER_ITEMS = ['fresh looks', 'zero stress', "from 'meh' to 'wow'", 'ass & class', 'cover star: ты']

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

export function Home({
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenLook,
  userName,
}: {
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenLook: (id: number) => void
  userName: string | null
}) {
  const star = userName && userName !== 'Гость' ? userName : 'ты'

  return (
    <div className="stack">
      {/* ---------- обложка ---------- */}
      <Reveal delay={0}>
        <section className="cover">
          <div className="issue-row">
            <span>выпуск № 001</span>
            <b>ass &amp; class</b>
            <span>2026</span>
          </div>

          <h1 className="masthead" aria-label="ASStylist">
            <span className="m-ass">ASS</span><span className="m-sty">tylist</span>
          </h1>
          <div className="mast-sub">
            звучит дерзко · <em>одевает дерзче</em>
          </div>
          <div className="star-line">
            <span className="sp" aria-hidden="true">★</span>
            cover star: <b>{star}</b>
            <span className="sp" aria-hidden="true">★</span>
          </div>

          <div className="checker" aria-hidden="true" />

          <div className="cover-head">
            <div className="cover-over">— the ballad of —</div>
            <div className="cover-giant">
              LOOKING <span className="hot">HOT</span>
            </div>
            <div className="cover-stars">★&nbsp;&nbsp;from&nbsp;&nbsp;★</div>
            <div className="cover-meh">
              <span className="meh">'meh'</span>
              <span className="arr" aria-hidden="true">→</span>
              <span className="wow">'wow!'</span>
            </div>
          </div>

          <div className="cover-lines">
            {COVER_LINES.map((line) => (
              <div key={line} className="cover-line">
                <i aria-hidden="true">✦</i>
                {line}
              </div>
            ))}
          </div>

          <div className="sticker-row">
            <span className="sticker st-sun">new!</span>
            <span className="sticker st-black">ass-approved ✓</span>
            <span className="sticker st-white">лук за минуту</span>
          </div>

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

          <div className="barcode-row">
            <span className="barcode" aria-hidden="true" />
            <span className="price">
              цена: твоя улыбка
              <br />
              0% занудства
            </span>
          </div>
        </section>
      </Reveal>

      <Reveal delay={0.1}>
        <Ticker />
      </Reveal>

      {/* ---------- в этом выпуске ---------- */}
      <Reveal delay={0.15}>
        <section className="card stack" style={{ gap: 14 }}>
          <SectionTitle hint="inside">В этом выпуске</SectionTitle>
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
            <SectionTitle hint="fresh">Недавние выходы</SectionTitle>
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
                      <span className="muted small" style={{ fontVariantNumeric: 'tabular-nums' }}>
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
      <div className="page-mark">ass &amp; class · made to slay</div>
    </div>
  )
}
