import { useState } from 'react'
import type { Look } from '../lib/types'
import { formatRub, itemsWord } from '../lib/format'
import { playClick, playTick } from '../lib/sound'
import { StarIcon } from '../lib/graphics'
import { Badge, ScoreRing, SectionTitle } from './ui'
import { ItemCard } from './ItemCard'

export function colorLabel(id: string, colors: { id: string; label: string }[]): string {
  const found = colors.find((entry) => entry.id === id)
  return found?.label ?? id
}

export function LookResult({ look, colors, swappingSlot, onSwap, onNewLook, onFavorite }: {
  look: Look
  colors: { id: string; label: string; hex: string }[]
  swappingSlot: string | null
  onSwap: (slot: string) => void
  onNewLook: () => void
  onFavorite: () => void
}) {
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [showDiagnostics, setShowDiagnostics] = useState(false)
  const [activeColorInfo, setActiveColorInfo] = useState<string | null>(null)
  const diagnostics = look.diagnostics as { candidates_total?: number; rejected_total?: number; warnings?: string[]; dropped_slots?: string[]; plan_description?: string }
  const engine = look.engine
  const engineActive = engine?.pipeline === 'asstylist-fashion-engine'
  const tasteMix = Object.entries(engine?.taste_mix ?? {})
  const hexById = new Map(colors.map((entry) => [entry.id, entry.hex]))
  const unifiedScore = Math.round(look.score)
  const thesisRu = engine?.styling_thesis_ru || engine?.styling_thesis
  const fitHint = engineActive && engine?.outfit_score != null ? `посадка ${Math.round(engine.outfit_score)}/100` : null
  const total = look.items.reduce((sum, item) => sum + (item.price_rub || 0), 0)

  return (
    <div className="stack page-transition result-page" style={{ gap: 18 }}>
      <section className="card stack result-hero" style={{ gap: 16 }}>
        <div className="row-between" style={{ gap: 10, alignItems: 'flex-start' }}>
          <div><div className="tiny" style={{ marginBottom: 4 }}>Готовый образ</div><div className="result-title">{look.plan || 'Подборка'}</div></div>
          <span className="tiny muted">№ {look.id ?? '—'}</span>
        </div>
        <div className="unified-score">
          <ScoreRing score={unifiedScore} />
          <div className="unified-score-main">
            <strong style={{ fontSize: 22 }}>Оценка образа</strong>
            <div className="small muted" style={{ marginTop: 4 }}>{fitHint ? `${fitHint} · ` : ''}{itemsWord(look.items.length)} · {formatRub(total)}</div>
            {thesisRu ? <p className="result-thesis" style={{ margin: '10px 0 0', fontSize: 15.5, lineHeight: 1.5 }}>{thesisRu}</p> : null}
          </div>
        </div>
        {look.summary ? <p className="result-summary" style={{ margin: 0, fontSize: 16, lineHeight: 1.55 }}>{look.summary}</p> : null}
        <div className="result-actions">
          <button type="button" className={`btn btn-block favorite-action ${look.is_favorite ? 'is-favorite' : ''}`} aria-pressed={look.is_favorite} onClick={() => { playClick(); onFavorite() }}>
            <StarIcon filled={look.is_favorite} size={16} /> {look.is_favorite ? 'В избранном' : 'В избранное'}
          </button>
          <button type="button" className="btn btn-outline btn-block" onClick={() => { playClick(); onNewLook() }}>Новый образ</button>
        </div>
      </section>

      <section className="stack" style={{ gap: 14 }}>
        <SectionTitle hint={`${look.items.length}`}>Вещи в образе</SectionTitle>
        {look.items.map((item) => <ItemCard key={`${item.slot}-${item.sku}`} item={item} swapping={swappingSlot === item.slot} onSwap={onSwap} />)}
      </section>

      <section className="card stack" style={{ gap: 12 }}>
        <button type="button" className="details-toggle" onClick={() => { playTick(); setDetailsOpen((v) => !v) }} aria-expanded={detailsOpen}>
          <span>{detailsOpen ? 'Скрыть подробности' : 'Подробнее об образе'}</span><span className="details-chevron" data-open={detailsOpen}>▾</span>
        </button>
        {detailsOpen ? (
          <div className="stack details-panel" style={{ gap: 16 }}>
            {look.personal_note ? <p className="muted" style={{ margin: 0, fontSize: 15, lineHeight: 1.5 }}>{look.personal_note}</p> : null}
            {look.body ? <div className="stack" style={{ gap: 8 }}><SectionTitle index="01">Фигура и посадка</SectionTitle>{look.body.recommended_fits?.length ? <div className="wrap" style={{ gap: 8 }}>{look.body.recommended_fits.map((fit) => <Badge key={fit}>посадка: {fit}</Badge>)}</div> : null}{look.body.signals?.length ? <ul className="reasons">{look.body.signals.map((signal) => <li key={signal}>{signal}</li>)}</ul> : null}</div> : null}
            {look.palette ? <div className="stack" style={{ gap: 8 }}><SectionTitle index="02" hint={`точность ${Math.round((look.palette.confidence ?? 0) * 100)}%`}>{look.palette.source !== 'defaults' && look.palette.color_type_ru ? `Цветотип · ${look.palette.color_type_ru}` : `Цветовая гамма · ${look.palette.season_label ?? ''}`}</SectionTitle>{look.palette.source !== 'defaults' ? <div className="appearance-row">{look.palette.skin_hex ? <span className="appearance-swatch" style={{ background: look.palette.skin_hex }} title="Тон кожи" /> : null}{look.palette.hair_hex ? <span className="appearance-swatch" style={{ background: look.palette.hair_hex }} title="Волосы" /> : null}{look.palette.undertone_ru ? <Badge>подтон: {look.palette.undertone_ru}</Badge> : null}{look.palette.contrast_ru ? <Badge>контраст: {look.palette.contrast_ru}</Badge> : null}</div> : null}<div className="palette-dots">{(look.palette.recommended ?? []).slice(0, 12).map((id) => <span key={id} className="palette-dot" title={colorLabel(id, colors)} style={{ background: hexById.get(id) ?? '#888' }} onClick={() => { playTick(); setActiveColorInfo(colorLabel(id, colors)) }} />)}</div>{activeColorInfo ? <div className="small muted">{activeColorInfo}</div> : null}</div> : null}
            {tasteMix.length ? <div className="stack" style={{ gap: 6 }}><SectionTitle index="03">Вкусовой микс</SectionTitle><div className="wrap" style={{ gap: 8 }}>{tasteMix.map(([key, value]) => <Badge key={key}>{key}: {Math.round(Number(value) * 100)}%</Badge>)}</div></div> : null}
            <button type="button" className="link-btn" onClick={() => { playTick(); setShowDiagnostics((v) => !v) }}>{showDiagnostics ? 'Скрыть диагностику' : 'Диагностика подбора'}</button>
            {showDiagnostics ? <ul className="reasons small">{diagnostics.plan_description ? <li>{diagnostics.plan_description}</li> : null}{diagnostics.candidates_total != null ? <li>Кандидатов: {diagnostics.candidates_total}</li> : null}{diagnostics.rejected_total != null ? <li>Отклонено: {diagnostics.rejected_total}</li> : null}{(diagnostics.warnings ?? []).map((w) => <li key={w}>{w}</li>)}</ul> : null}
          </div>
        ) : null}
      </section>
    </div>
  )
}
