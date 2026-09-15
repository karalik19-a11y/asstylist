import { useState } from 'react'
import type { Look } from '../lib/types'
import { formatRub, itemsWord } from '../lib/format'
import { playClick, playStamp, playTick } from '../lib/sound'
import { DobermanStamp, PostalCancellationStamp, StarIcon } from '../lib/graphics'
import { Badge, BudgetBar, ScoreRing, SectionTitle } from './ui'
import { ItemCard } from './ItemCard'

export function colorLabel(id: string, colors: { id: string; label: string }[]): string {
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
  const [stampActive, setStampActive] = useState(false)
  const [activeColorInfo, setActiveColorInfo] = useState<string | null>(null)

  const diagnostics = look.diagnostics as {
    candidates_total?: number
    rejected_total?: number
    warnings?: string[]
    dropped_slots?: string[]
    plan_description?: string
  }
  const hexById = new Map(colors.map((entry) => [entry.id, entry.hex]))

  const handleSealStamp = () => {
    playStamp()
    setStampActive(true)
    setTimeout(() => setStampActive(false), 400)
  }

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      {/* ---------- Обложка выпуска (Postage Stamp Aesthetic) ---------- */}
      <section className="stamp-card stack" style={{ gap: 14 }}>
        <div className="stamp-strip">
          <div className="stamp-strip-title">
            <span>ATELIER ARCHIVE</span>
            <span className="tiny" style={{ color: 'var(--stamp-ink-muted)' }}>
              · {look.plan.toUpperCase()}
            </span>
          </div>
          <div className="stamp-strip-num">EDITION № {look.id ?? '01'}</div>
        </div>

        <div className="row-between" style={{ alignItems: 'center', gap: 12 }}>
          <ScoreRing score={look.score} />

          <div style={{ minWidth: 0, flex: 1 }}>
            <h2 style={{ fontSize: 24, color: 'var(--stamp-ink)' }}>{look.verdict.title || 'Персональный образ'}</h2>
            <div className="small" style={{ color: 'var(--stamp-ink-muted)', marginTop: 2 }}>
              {look.verdict.note}
            </div>
          </div>

          <PostalCancellationStamp
            text="ATELIER · VERIFIED 2026"
            sub="TOKYO / LONDON SPEC"
            active={stampActive}
            onClick={handleSealStamp}
          />
        </div>

        <p className="small" style={{ margin: 0, color: 'var(--stamp-ink)', lineHeight: 1.45 }}>
          {look.summary}
        </p>

        <div className="wrap" style={{ gap: 6 }}>
          <Badge>
            {itemsWord(look.items.length)} · {formatRub(look.total_rub)}
          </Badge>
          {look.is_favorite ? <Badge tone="ok">в избранном</Badge> : null}
          <span className="stamp-badge">СТУДИЙНЫЙ СЕРТИФИКАТ {look.verdict.grade}</span>
        </div>

        <BudgetBar total={look.total_rub} budget={look.budget_rub} />

        {/* Action Buttons: 2-column grid guaranteed NEVER to overlap */}
        <div className="home-actions-grid" style={{ marginTop: 4 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              playClick()
              onNewLook()
            }}
          >
            Новый образ
          </button>

          <button
            type="button"
            className="btn btn-outline"
            onClick={() => {
              playClick()
              onFavorite()
            }}
            disabled={look.id === null}
          >
            <StarIcon filled={look.is_favorite} size={14} />
            <span>{look.is_favorite ? 'В избранном' : 'В избранное'}</span>
          </button>
        </div>
      </section>

      {/* ---------- Силуэт и пропорции (Ref 2 Doberman stamp motif) ---------- */}
      <section className="card stack" style={{ gap: 12 }}>
        <SectionTitle index="01" hint={`точность ${Math.round(look.body.confidence * 100)}%`}>
          Силуэт и посадка
        </SectionTitle>

        <div className="row" style={{ gap: 14, alignItems: 'center' }}>
          <div style={{ width: 72, flexShrink: 0 }}>
            <DobermanStamp />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <strong style={{ fontSize: 16 }}>{look.body.silhouette_ru}</strong>
            <div className="muted small" style={{ marginTop: 4 }}>
              ИМТ {look.body.bmi} ({look.body.bmi_label}) · рост {look.body.height_cm} см · вес {look.body.weight_kg} кг
            </div>
            {look.body.recommended_fits.length ? (
              <div className="wrap" style={{ marginTop: 6, gap: 4 }}>
                {look.body.recommended_fits.map((fit) => (
                  <Badge key={fit}>посадка: {fit}</Badge>
                ))}
              </div>
            ) : null}
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

      {/* ---------- Палитра оттенков ---------- */}
      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle index="02" hint={`точность ${Math.round(look.palette.confidence * 100)}%`}>
          Цветовая гамма · {look.palette.season_label}
        </SectionTitle>

        <div className="palette-dots">
          {look.palette.recommended.slice(0, 14).map((id) => (
            <span
              key={id}
              className="palette-dot"
              title={colorLabel(id, colors)}
              style={{ background: hexById.get(id) ?? '#888' }}
              onClick={() => {
                playTick()
                setActiveColorInfo(colorLabel(id, colors))
              }}
            />
          ))}
        </div>

        {activeColorInfo ? (
          <div className="small muted">Выбран оттенок: <strong>{activeColorInfo}</strong></div>
        ) : null}

        {look.palette.avoid.length ? (
          <div className="muted small">
            Рекомендуется ограничить: {look.palette.avoid.map((id) => colorLabel(id, colors)).join(', ')}
          </div>
        ) : null}
        {look.palette.dominant_colors.length ? (
          <div className="muted small">
            Определено по снимку: {look.palette.dominant_colors.map((id) => colorLabel(id, colors)).join(', ')}
          </div>
        ) : null}
      </section>

      {/* ---------- Предметы гардероба ---------- */}
      <section className="stack" style={{ gap: 12 }}>
        <SectionTitle index="03" hint={`структура: ${look.plan}`}>
          Предметы селекции
        </SectionTitle>
        {look.items.map((item) => (
          <ItemCard key={`${item.slot}-${item.sku}`} item={item} onSwap={onSwap} swapping={swappingSlot === item.slot} />
        ))}
      </section>

      {/* ---------- Советы стилиста ---------- */}
      <section className="card stack" style={{ gap: 8 }}>
        <SectionTitle index="04">Студийные рекомендации</SectionTitle>
        <ul className="reasons">
          {look.tips.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      </section>

      {/* ---------- Параметры селекции ---------- */}
      <section className="card stack" style={{ gap: 8 }}>
        <button
          type="button"
          className="link-btn"
          onClick={() => {
            playTick()
            setShowDiagnostics((value) => !value)
          }}
        >
          {showDiagnostics ? 'Скрыть параметры селекции' : 'Технические параметры селекции'}
        </button>

        {showDiagnostics ? (
          <div className="small muted stack" style={{ gap: 6, paddingTop: 6 }}>
            <div>Студийный движок: v{look.engine_version}</div>
            <div>Оценено позиций в каталоге: {diagnostics.candidates_total ?? 0}</div>
            <div>Отфильтровано позиций: {diagnostics.rejected_total ?? 0}</div>
            <div>План гардероба: {diagnostics.plan_description ?? look.plan}</div>
            {diagnostics.dropped_slots?.length ? <div>Исключено по бюджету: {diagnostics.dropped_slots.join(', ')}</div> : null}
            {diagnostics.warnings?.length ? (
              <ul className="reasons">
                {diagnostics.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
            <div>Итог: {formatRub(look.total_rub)} из бюджета {formatRub(look.budget_rub)}</div>
          </div>
        ) : null}
      </section>
    </div>
  )
}
