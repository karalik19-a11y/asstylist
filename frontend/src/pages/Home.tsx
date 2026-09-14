import type { HistoryEntry, Meta } from '../lib/types'
import { formatRub, itemsWord, relativeTime } from '../lib/format'
import { Badge, SectionTitle } from '../components/ui'

const STEPS = [
  { emoji: '📷', title: 'Фото и параметры', text: 'Рост, вес и фото — для силуэта и палитры.' },
  { emoji: '🎛️', title: 'Стиль и настроение', text: '10 стилей и 8 настроений на выбор.' },
  { emoji: '💸', title: 'Бюджет до 100 000 ₽', text: 'Движок собирает образ строго в рамках суммы.' },
  { emoji: '✅', title: 'Проверенные товары', text: 'Каждая позиция проходит верификацию цены и ссылки.' },
]

export function Home({
  meta,
  history,
  onStart,
  onOpenHistory,
  onOpenVerification,
  onOpenLook,
  userName,
}: {
  meta: Meta | null
  history: HistoryEntry[]
  onStart: () => void
  onOpenHistory: () => void
  onOpenVerification: () => void
  onOpenLook: (id: number) => void
  userName: string | null
}) {
  return (
    <div className="stack">
      <section className="stack" style={{ gap: 10, paddingTop: 8 }}>
        <div className="row" style={{ gap: 8 }}>
          <strong className="accent" style={{ letterSpacing: '0.14em', fontSize: 13 }}>
            ASSTYLIST
          </strong>
          {meta?.demo_mode ? <Badge tone="warn">демо-режим</Badge> : <Badge tone="ok">telegram</Badge>}
        </div>
        <h1 className="hero-title">
          {userName ? `${userName}, ` : ''}соберём образ, который вам идёт
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          AI fashion director: по фото, росту, весу, стилю, настроению и бюджету собирает персональный лук из
          проверенных товаров. Некоммерческий проект — стоимость 0 ₽.
        </p>
        <button type="button" className="btn btn-primary btn-block" onClick={onStart} style={{ marginTop: 6 }}>
          Собрать образ
        </button>
        <div className="row" style={{ gap: 8 }}>
          <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenHistory}>
            Мои образы
          </button>
          <button type="button" className="btn btn-sm btn-ghost" onClick={onOpenVerification}>
            Проверка товаров
          </button>
        </div>
      </section>

      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle hint={meta ? `движок v${meta.version}` : undefined}>Как это работает</SectionTitle>
        <div className="grid-2">
          {STEPS.map((step) => (
            <div key={step.title} className="card" style={{ background: 'var(--surface-2)', padding: 12 }}>
              <div style={{ fontSize: 20 }}>{step.emoji}</div>
              <strong style={{ fontSize: 13.5 }}>{step.title}</strong>
              <div className="muted small" style={{ marginTop: 2 }}>
                {step.text}
              </div>
            </div>
          ))}
        </div>
      </section>

      {meta ? (
        <section className="card stack" style={{ gap: 8 }}>
          <SectionTitle hint="до 100 000 ₽">Что умеет движок</SectionTitle>
          <div className="wrap">
            <Badge>{meta.styles.length} стилей</Badge>
            <Badge>{meta.moods.length} настроений</Badge>
            <Badge>{meta.colors.length} оттенков в палитре</Badge>
            <Badge>бюджет {formatRub(meta.budget.max_rub)}</Badge>
            <Badge tone="ok">AI: {meta.ai_provider}</Badge>
          </div>
          <div className="muted small">
            Каждый товар в образе получает оценку по 8 параметрам: стиль, настроение, силуэт, цвет, формальность,
            сезон, цена/качество и статус проверки.
          </div>
        </section>
      ) : null}

      {history.length ? (
        <section className="stack" style={{ gap: 10 }}>
          <SectionTitle hint={`${history.length} ${history.length === 1 ? 'образ' : 'образов'}`}>Последние образы</SectionTitle>
          {history.slice(0, 3).map((entry) => (
            <button key={entry.id} type="button" className="card stack" style={{ gap: 4, textAlign: 'left' }} onClick={() => onOpenLook(entry.id)}>
              <div className="row-between">
                <strong>{entry.style}</strong>
                <span className="muted small">{formatRub(entry.total_rub)}</span>
              </div>
              <div className="muted small">
                {itemsWord(entry.items_count)} · оценка {Math.round(entry.score)} · {relativeTime(entry.created_at)}
              </div>
            </button>
          ))}
        </section>
      ) : null}
    </div>
  )
}
