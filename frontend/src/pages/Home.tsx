import type { HistoryEntry, Meta } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, SectionTitle } from '../components/ui'
import { TelegramSetup } from '../components/TelegramSetup'

const STEPS = [
  { num: '01', title: 'Фото и параметры', text: 'Рост, вес и фото — для силуэта и палитры.' },
  { num: '02', title: 'Стиль и настроение', text: '10 стилей и 8 настроений на выбор.' },
  { num: '03', title: 'Бюджет до 100 000 ₽', text: 'Движок собирает образ строго в рамках суммы.' },
  { num: '04', title: 'Проверенные товары', text: 'Каждая позиция проходит верификацию цены и ссылки.' },
]

const TICKER_ITEMS = ['стиль', 'палитра', 'силуэт', 'бюджет', 'проверенные товары', 'личный стилист', 'выпуск 0 ₽']

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
  meta,
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenLook,
  userName,
  onBotConnected,
}: {
  meta: Meta | null
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenLook: (id: number) => void
  userName: string | null
  onBotConnected: () => void
}) {
  return (
    <div className="stack">
      {/* ---------- обложка ---------- */}
      <header className="masthead">
        <div className="masthead-top">
          <span className="tiny">Журнал образов</span>
          <span className="tiny">N° 01 · 2026</span>
        </div>
        <div className="masthead-word">
          as<span>Stylist</span>
        </div>
        <div className="masthead-sub">личный стилист · каждый день новый выпуск</div>
      </header>

      <Ticker />

      <section className="stack" style={{ gap: 14, paddingTop: 6 }}>
        <div className="row-between">
          <span className="kicker">Свежий номер</span>
          {meta?.demo_mode ? <Badge tone="warn">демо-режим</Badge> : <Badge tone="ok">telegram</Badge>}
        </div>
        <div className="kicker-rule" />
        <h1 className="hero-title">
          {userName ? `${userName}, ` : ''}
          соберём образ, <em>который вам идёт</em>
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          Личный стилист: по фото, росту, весу, стилю, настроению и бюджету собирает персональный лук из проверенных
          товаров. Некоммерческий проект — стоимость 0 ₽.
        </p>
        <button type="button" className="btn btn-primary btn-block" onClick={onStart} style={{ marginTop: 4, padding: '16px 18px' }}>
          Собрать образ
        </button>
        <div className="row" style={{ gap: 18 }}>
          <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenHistory}>
            Мои образы
          </button>
          <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenVerification}>
            Проверка товаров
          </button>
        </div>
      </section>

      <TelegramSetup status={meta?.telegram} onConnected={onBotConnected} />

      {/* ---------- содержание ---------- */}
      <section className="card stack" style={{ gap: 12 }}>
        <SectionTitle hint={meta ? `движок v${meta.version}` : undefined}>Содержание</SectionTitle>
        <div className="grid-2" style={{ gap: 0 }}>
          {STEPS.map((step) => (
            <div key={step.num} className="stack" style={{ gap: 4, padding: '10px 12px', borderLeft: '1px solid var(--line-soft)' }}>
              <div className="index-num" style={{ fontSize: 22 }}>
                {step.num}
              </div>
              <strong style={{ fontSize: 13.5 }}>{step.title}</strong>
              <div className="muted small" style={{ lineHeight: 1.35 }}>
                {step.text}
              </div>
            </div>
          ))}
        </div>
      </section>

      {meta ? (
        <section className="card stack" style={{ gap: 10 }}>
          <SectionTitle hint="до 100 000 ₽">Что умеет движок</SectionTitle>
          <div className="wrap">
            <Badge>{meta.styles.length} стилей</Badge>
            <Badge>{meta.moods.length} настроений</Badge>
            <Badge>{meta.colors.length} оттенков в палитре</Badge>
            <Badge>бюджет {formatRub(meta.budget.max_rub)}</Badge>
          </div>
          <div className="muted small">
            Каждый товар в образе получает оценку по 8 параметрам: стиль, настроение, силуэт, цвет, формальность,
            сезон, цена/качество и статус проверки.
          </div>
        </section>
      ) : null}

      {history.length ? (
        <section className="stack" style={{ gap: 10 }}>
          <SectionTitle hint={`${history.length} ${history.length === 1 ? 'образ' : 'образов'}`}>Последние выпуски</SectionTitle>
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
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <hr className="rule-double" />
      <div className="page-mark">— 01 —</div>
    </div>
  )
}
