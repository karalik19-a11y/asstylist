import { useState } from 'react'
import type { Look } from '../lib/types'
import { formatRub, itemsWord } from '../lib/format'
import { Badge, BudgetBar, ScoreRing, SectionTitle } from './ui'
import { ItemCard } from './ItemCard'

const COLOR_NAMES: Record<string, string> = {}

export function colorLabel(id: string, colors: { id: string; label: string }[]): string {
  if (COLOR_NAMES[id]) return COLOR_NAMES[id]
  const found = colors.find((entry) => entry.id === id)
  return found?.label ?? id
}

export function LookResult({
  look,
  colors,
  swappingSlot,
  onSwap,
  onNewLook,
  onFavorite,
}: {
  look: Look
  colors: { id: string; label: string; hex: string }[]
  swappingSlot: string | null
  onSwap: (slot: string) => void
  onNewLook: () => void
  onFavorite: () => void
}) {
  const [showDiagnostics, setShowDiagnostics] = useState(false)
  const diagnostics = look.diagnostics as {
    candidates_total?: number
    rejected_total?: number
    warnings?: string[]
    dropped_slots?: string[]
    plan_description?: string
  }
  const hexById = new Map(colors.map((entry) => [entry.id, entry.hex]))

  return (
    <div className="stack">
      {/* ---------- обложка выпуска ---------- */}
      <section className="card stack" style={{ gap: 14 }}>
        <div className="kicker-rule">
          <span className="kicker">Ваш образ · {look.plan}</span>
        </div>
        <div className="row" style={{ gap: 14, alignItems: 'center' }}>
          <ScoreRing score={look.score} />
          <div style={{ minWidth: 0, flex: 1 }}>
            <h2 style={{ fontSize: 26 }}>{look.verdict.title || 'Ваш образ'}</h2>
            <div className="muted small">{look.verdict.note}</div>
          </div>
          <span className="stamp" aria-hidden="true">
            оценка {look.verdict.grade}
          </span>
        </div>

        <p className="small" style={{ margin: 0, color: 'var(--ink)' }}>
          {look.summary}
        </p>

        <div className="wrap" style={{ gap: 6 }}>
          <Badge>
            {itemsWord(look.items.length)} · {formatRub(look.total_rub)}
          </Badge>
          {look.is_favorite ? <Badge tone="ok">в избранном</Badge> : null}
        </div>

        <BudgetBar total={look.total_rub} budget={look.budget_rub} />

        <div className="row" style={{ gap: 10 }}>
          <button type="button" className="btn btn-primary btn-sm" onClick={onNewLook}>
            Новый образ
          </button>
          <button type="button" className="btn btn-sm" onClick={onFavorite} disabled={look.id === null}>
            {look.is_favorite ? '★ В избранном' : '☆ В избранное'}
          </button>
        </div>
      </section>

      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle index="01" hint={`уверенность ${Math.round(look.body.confidence * 100)}%`}>
          Силуэт
        </SectionTitle>
        <div className="row-between">
          <div>
            <strong>{look.body.silhouette_ru}</strong>
            <div className="muted small">
              ИМТ {look.body.bmi} ({look.body.bmi_label}) · рост {look.body.height_cm} см · вес {look.body.weight_kg} кг
            </div>
          </div>
        </div>
        {look.body.signals?.length ? (
          <ul className="reasons">
            {look.body.signals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle index="02" hint={`уверенность ${Math.round(look.palette.confidence * 100)}%`}>
          Палитра · {look.palette.season_label}
        </SectionTitle>
        <div className="palette-dots">
          {look.palette.recommended.slice(0, 12).map((id) => (
            <span
              key={id}
              className="palette-dot"
              title={colorLabel(id, colors)}
              style={{ background: hexById.get(id) ?? '#888' }}
            />
          ))}
        </div>
        {look.palette.avoid.length ? (
          <div className="muted small">Лучше избегать: {look.palette.avoid.map((id) => colorLabel(id, colors)).join(', ')}</div>
        ) : null}
        {look.palette.dominant_colors.length ? (
          <div className="muted small">На фото: {look.palette.dominant_colors.map((id) => colorLabel(id, colors)).join(', ')}</div>
        ) : null}
      </section>

      <section className="stack" style={{ gap: 10 }}>
        <SectionTitle index="03" hint={`план: ${look.plan}`}>
          Образ
        </SectionTitle>
        {look.items.map((item) => (
          <ItemCard key={`${item.slot}-${item.sku}`} item={item} onSwap={onSwap} swapping={swappingSlot === item.slot} />
        ))}
      </section>

      <section className="card stack" style={{ gap: 8 }}>
        <SectionTitle index="04">Советы стилиста</SectionTitle>
        <ul className="reasons">
          {look.tips.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      </section>

      <section className="card stack" style={{ gap: 8 }}>
        <button type="button" className="link-btn" onClick={() => setShowDiagnostics((value) => !value)}>
          {showDiagnostics ? 'Скрыть диагностику движка' : 'Как это посчитано'}
        </button>
        {showDiagnostics ? (
          <div className="small muted stack" style={{ gap: 6 }}>
            <div>Версия движка: {look.engine_version}</div>
            <div>Проанализировано товаров: {diagnostics.candidates_total ?? 0}</div>
            <div>Отклонено фильтром: {diagnostics.rejected_total ?? 0}</div>
            <div>План образа: {diagnostics.plan_description ?? look.plan}</div>
            {diagnostics.dropped_slots?.length ? <div>Убрано из-за бюджета: {diagnostics.dropped_slots.join(', ')}</div> : null}
            {diagnostics.warnings?.length ? (
              <ul className="reasons">
                {diagnostics.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
            <div>Итог: {formatRub(look.total_rub)} при бюджете {formatRub(look.budget_rub)}</div>
          </div>
        ) : null}
      </section>
    </div>
  )
}
