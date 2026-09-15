import { useState } from 'react'
import type { Look } from '../lib/types'
import { formatRub, itemsWord } from '../lib/format'
import { Badge, BudgetBar, Reveal, ScoreRing, SectionTitle } from './ui'
import { ItemCard } from './ItemCard'

export function colorLabel(id: string, colors: { id: string; label: string }[]): string {
  const found = colors.find((entry) => entry.id === id)
  return found?.label ?? id
}

export function LookResult({
  look,
  colors,
  plans,
  swappingSlot,
  onSwap,
  onNewLook,
  onFavorite,
}: {
  look: Look
  colors: { id: string; label: string; hex: string }[]
  plans: { id: string; description: string }[]
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
  const planLabel = plans.find((p) => p.id === look.plan)?.description ?? look.plan

  return (
    <div className="stack">
      {/* ---------- cover story ---------- */}
      <Reveal delay={0}>
        <section className="card verdict-card stack" style={{ gap: 14 }}>
          <div className="kicker-rule">
            <span className="kicker">cover story · {planLabel}</span>
          </div>
          <div className="row" style={{ gap: 14, alignItems: 'center' }}>
            <ScoreRing score={look.score} />
            <div style={{ minWidth: 0, flex: 1 }}>
              <h2 style={{ fontSize: 24 }}>{look.verdict.title || 'Твой образ'}</h2>
              <div className="muted small">{look.verdict.note}</div>
            </div>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <span className="stamp" aria-hidden="true">
              ✓ ass-approved · {look.verdict.grade}
            </span>
          </div>

          <p className="small" style={{ margin: 0, fontWeight: 600 }}>
            {look.summary}
          </p>

          <div className="wrap" style={{ gap: 6 }}>
            <Badge tone="pop">
              {itemsWord(look.items.length)} · {formatRub(look.total_rub)}
            </Badge>
            {look.is_favorite ? <Badge tone="ok">в избранном</Badge> : null}
          </div>

          <BudgetBar total={look.total_rub} budget={look.budget_rub} />

          <div className="row" style={{ gap: 10 }}>
            <button type="button" className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={onNewLook}>
              Ещё лук ✦
            </button>
            <button type="button" className="btn btn-sm" onClick={onFavorite} disabled={look.id === null}>
              {look.is_favorite ? '★ В избранном' : '☆ В избранное'}
            </button>
          </div>
        </section>
      </Reveal>

      <Reveal delay={0.08}>
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
      </Reveal>

      <Reveal delay={0.14}>
        <section className="card stack" style={{ gap: 10 }}>
          <SectionTitle index="02" hint={`уверенность ${Math.round(look.palette.confidence * 100)}%`}>
            Палитра · {look.palette.season_label}
          </SectionTitle>
          <div className="palette-dots">
            {look.palette.recommended.slice(0, 12).map((id, i) => (
              <span
                key={id}
                className="palette-dot"
                title={colorLabel(id, colors)}
                style={{ background: hexById.get(id) ?? '#888', ['--d' as string]: `${i * 0.05}s` }}
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
      </Reveal>

      <section className="stack" style={{ gap: 10 }}>
        <SectionTitle index="03" hint={planLabel}>
          Образ
        </SectionTitle>
        {look.items.map((item, i) => (
          <ItemCard
            key={`${item.slot}-${item.sku}`}
            item={item}
            onSwap={onSwap}
            swapping={swappingSlot === item.slot}
            index={i}
          />
        ))}
      </section>

      <Reveal delay={0.05}>
        <section className="card stack" style={{ gap: 8 }}>
          <SectionTitle index="04">Горячие советы</SectionTitle>
          <ul className="reasons">
            {look.tips.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </section>
      </Reveal>

      <section className="card stack" style={{ gap: 8 }}>
        <button type="button" className="link-btn" onClick={() => setShowDiagnostics((value) => !value)}>
          {showDiagnostics ? 'Скрыть подробности ↑' : 'Как это посчитано ↓'}
        </button>
        {showDiagnostics ? (
          <div className="small muted stack" style={{ gap: 6 }}>
            <div>Сборка: {look.engine_version}</div>
            <div>Перебрали вещей: {diagnostics.candidates_total ?? 0}</div>
            <div>Отсеяли: {diagnostics.rejected_total ?? 0}</div>
            <div>План образа: {diagnostics.plan_description ?? planLabel}</div>
            {diagnostics.dropped_slots?.length ? <div>Убрали из-за бюджета: {diagnostics.dropped_slots.join(', ')}</div> : null}
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
