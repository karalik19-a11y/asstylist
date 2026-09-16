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
  const engine = look.engine
  const engineActive = engine?.pipeline === 'asstylist-fashion-engine'
  const tasteMix = Object.entries(engine?.taste_mix ?? {})
  const hexById = new Map(colors.map((entry) => [entry.id, entry.hex]))

  // Что именно открывается по кнопке у каждой вещи: конкретное объявление или
  // (в крайнем случае) подборка Авито. Пользователь должен видеть разницу.
  const listingKinds = look.items.map((item) => item.link_kind ?? item.listing?.kind ?? 'listing')
  const concreteListings = listingKinds.filter((kind) => kind !== 'search').length
  const searchFallbacks = listingKinds.length - concreteListings
  const snapshotAt =
    look.items.find((item) => item.snapshot_captured_at)?.snapshot_captured_at ??
    engine?.snapshot_captured_at ??
    null
  const fromSnapshot = look.items.filter((item) => (item.feed ?? item.listing?.feed) === 'snapshot').length
  const feedNotes = engine?.feed_notes ?? []

  const handleSealStamp = () => {
    playStamp()
    setStampActive(true)
    setTimeout(() => setStampActive(false), 400)
  }

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      {/* ---------- Итог селекции ---------- */}
      <section className="stamp-card stack" style={{ gap: 18 }}>
        <div className="stamp-strip">
          <div className="stamp-strip-title">
            <span>Готовый образ</span>
            <span className="tiny">· {look.plan}</span>
          </div>
          <div className="stamp-strip-num">№ {look.id ?? '01'}</div>
        </div>

        <div className="result-head">
          <ScoreRing score={look.score} />

          <div className="result-head-main">
            <h2>{look.verdict.title || 'Персональный образ'}</h2>
            <div className="small muted" style={{ marginTop: 4 }}>
              {look.verdict.note}
            </div>
          </div>

          <PostalCancellationStamp
            text="ASStylist · 2026"
            sub="VERIFIED SELECTION"
            active={stampActive}
            onClick={handleSealStamp}
          />
        </div>

        <p style={{ margin: 0, fontSize: 15.5, lineHeight: 1.55 }}>{look.summary}</p>

        {look.personal_note ? (
          <div className="personal-note">
            <span className="tiny">Почему это ваш образ</span>
            <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.55 }}>{look.personal_note}</p>
          </div>
        ) : null}

        <div className="wrap" style={{ gap: 8 }}>
          <Badge>
            {itemsWord(look.items.length)} · {formatRub(look.total_rub)}
          </Badge>
          {look.items.length > 0 && look.items.every((entry) => entry.url.includes('avito.ru')) ? (
            <Badge tone="ok">все вещи — с Авито</Badge>
          ) : null}
          {look.is_favorite ? <Badge tone="ok">в избранном</Badge> : null}
          <span className="stamp-badge">Сертификат · {look.verdict.grade}</span>
        </div>

        <BudgetBar total={look.total_rub} budget={look.budget_rub} />

        {engineActive ? (
          <div className="engine-thesis stack" style={{ gap: 12 }}>
            <div className="row-between" style={{ gap: 10, alignItems: 'center' }}>
              <span className="tiny">Тезис образа</span>
              <span className="tiny">{engine?.styling_thesis}</span>
            </div>
            <div className="row" style={{ gap: 14, alignItems: 'center' }}>
              <div className="engine-score">
                <strong>{Math.round(engine?.outfit_score ?? 0)}</strong>
                <span className="tiny">fit score</span>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ fontSize: 16 }}>{engine?.styling_thesis_ru || engine?.styling_thesis}</strong>
                <div className="muted small" style={{ marginTop: 3 }}>
                  {engine?.score_formula}
                  {engine?.aesthetic_ru || engine?.aesthetic ? ` · ${engine.aesthetic_ru ?? engine.aesthetic}` : ''}
                </div>
              </div>
            </div>
            <div className="wrap" style={{ gap: 8 }}>
              <Badge tone={engine?.critic_decision === 'APPROVE' ? 'ok' : 'warn'}>
                критик: {engine?.critic_decision === 'APPROVE' ? 'одобрено' : 'нужно усилить'}
              </Badge>
              {engine?.niche_level !== undefined ? <Badge>ниша {engine.niche_level}/100</Badge> : null}
              {engine?.queries_total ? <Badge>запросов: {engine.queries_total}</Badge> : null}
              {engine?.candidates?.validated ? <Badge>прошли отбор: {engine.candidates.validated}</Badge> : null}
              {engine?.repair ? <Badge tone="warn">бюджетный баланс</Badge> : null}
            </div>
            {engine?.critic_feedback?.length ? (
              <ul className="reasons">
                {engine.critic_feedback.slice(0, 2).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        {/* Действия — сетка с широкими промежутками */}
        <div className="home-actions-grid">
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

      {/* ---------- Силуэт и пропорции ---------- */}
      <section className="card stack" style={{ gap: 14 }}>
        <SectionTitle index="01" hint={`точность ${Math.round(look.body.confidence * 100)}%`}>
          Силуэт и посадка
        </SectionTitle>

        <div className="row" style={{ gap: 18, alignItems: 'center' }}>
          <div style={{ width: 60, flexShrink: 0 }}>
            <DobermanStamp />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <strong style={{ fontSize: 16 }}>{look.body.silhouette_ru}</strong>
            <div className="muted small" style={{ marginTop: 4 }}>
              ИМТ {look.body.bmi} ({look.body.bmi_label}) · рост {look.body.height_cm} см · вес {look.body.weight_kg} кг
            </div>
            {look.body.recommended_fits.length ? (
              <div className="wrap" style={{ marginTop: 10, gap: 8 }}>
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
          {look.palette.source !== 'defaults' && look.palette.color_type_ru
            ? `Цветотип · ${look.palette.color_type_ru}`
            : `Цветовая гамма · ${look.palette.season_label}`}
        </SectionTitle>

        {look.palette.source !== 'defaults' ? (
          <div className="appearance-row">
            {look.palette.skin_hex ? (
              <span className="appearance-swatch" style={{ background: look.palette.skin_hex }} title="Тон кожи по фото" />
            ) : null}
            {look.palette.hair_hex ? (
              <span className="appearance-swatch" style={{ background: look.palette.hair_hex }} title="Оттенок волос по фото" />
            ) : null}
            {look.palette.undertone_ru ? <Badge>подтон: {look.palette.undertone_ru}</Badge> : null}
            {look.palette.contrast_ru ? <Badge>контраст: {look.palette.contrast_ru}</Badge> : null}
            {look.palette.metal_ru ? <Badge>металл: {look.palette.metal_ru}</Badge> : null}
          </div>
        ) : null}

        {look.palette.signals?.length ? (
          <ul className="reasons">
            {look.palette.signals.slice(0, 3).map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        ) : null}

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

        <div className={`listing-summary ${searchFallbacks > 0 ? 'listing-summary-warn' : ''}`}>
          <strong>
            {concreteListings} из {look.items.length} вещей — конкретные объявления Авито
          </strong>
          <div className="muted small" style={{ marginTop: 4 }}>
            {fromSnapshot > 0 && snapshotAt
              ? `Фото, цена и ссылка — из снимка выдачи от ${snapshotAt}. Открывается страница самого объявления, а не поиск по словам.`
              : 'Фото, цена и ссылка ведут на страницу самого объявления Авито.'}
          </div>
          {searchFallbacks > 0 ? (
            <div className="small" style={{ marginTop: 6 }}>
              {searchFallbacks} вещ. — без доступа к объявлению: кнопка ведёт на подборку Авито и помечена предупреждением.
            </div>
          ) : null}
          {feedNotes.length ? (
            <div className="muted small" style={{ marginTop: 4 }}>{feedNotes.join(' · ')}</div>
          ) : null}
        </div>
        {look.items.map((item) => (
          <ItemCard key={`${item.slot}-${item.sku}`} item={item} onSwap={onSwap} swapping={swappingSlot === item.slot} />
        ))}
      </section>

      {/* ---------- Советы стилиста ---------- */}
      <section className="card stack" style={{ gap: 8 }}>
        <SectionTitle index="04">Советы стилиста</SectionTitle>
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
            <div>Версия платформы: v{look.engine_version}</div>
            {engineActive ? (
              <>
                <div>Метод подбора: {engine?.pipeline} v{engine?.engine_version}</div>
                <div>Тезис: {engine?.styling_thesis_ru} ({engine?.styling_thesis})</div>
                <div>
                  Оценка образа: {Math.round(engine?.outfit_score ?? 0)}/100 · оценка приложения:{' '}
                  {Math.round(engine?.app_score ?? 0)}/100
                </div>
                <div>Критик: {engine?.critic_decision === 'APPROVE' ? 'одобрено' : 'рекомендованы правки'}</div>
                {tasteMix.length ? (
                  <div>Состав по вкусу: {tasteMix.map(([category, count]) => `${category} — ${count}`).join(', ')}</div>
                ) : null}
                {engine?.queries_used?.length ? <div>Запросы: {engine.queries_used.slice(0, 3).join(' · ')}</div> : null}
              </>
            ) : null}
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
