import { useEffect, useState } from 'react'
import type { EngineSearchItem, EngineSearchResult, Meta, WizardState } from '../lib/types'
import { api } from '../lib/api'
import { formatRub } from '../lib/format'
import { Badge, Chip, RangeField, SectionTitle, Spinner } from '../components/ui'
import { playClick, playSuccess, playTick } from '../lib/sound'

const PRESETS: { label: string; query: string; style: string; niche: number }[] = [
  { label: 'Индустриальная романтика', query: 'индустриальный образ с прозрачным верхом и кожаной курткой', style: 'grunge', niche: 82 },
  { label: 'Архив 90-х', query: 'архивный образ девяностых, джинса и потертый трикотаж', style: 'streetwear', niche: 76 },
  { label: 'Тихая роскошь', query: 'спокойный образ: кашемир, шерсть, прямые силуэты', style: 'old_money', niche: 58 },
  { label: 'Техно-утилитаризм', query: 'техничный образ: нейлон, мембрана, многослойность', style: 'techwear', niche: 80 },
  { label: 'Романтика', query: 'романтичный образ: кружево, шифон, мягкие линии', style: 'romantic', niche: 64 },
  { label: 'Оверсайз-объём', query: 'объёмный образ оверсайз, крупные формы', style: 'avantgarde', niche: 84 },
]

function ItemRow({ item }: { item: EngineSearchItem }) {
  const swatch =
    item.color_hexes.length > 0
      ? `linear-gradient(135deg, ${item.color_hexes.map((hex, index) => `${hex} ${index * 50}%`).join(', ')})`
      : 'var(--surface-2)'
  return (
    <div className="engine-item">
      <span className="engine-item-swatch" style={{ background: swatch }} aria-hidden="true" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="row-between" style={{ gap: 8 }}>
          <span className="tiny">{item.slot_label}</span>
          <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{formatRub(item.price_rub)}</strong>
        </div>
        <div style={{ fontWeight: 700, fontSize: 14, marginTop: 2, lineHeight: 1.25 }}>{item.name}</div>
        <div className="muted small" style={{ marginTop: 2 }}>
          {item.brand}
        </div>
        <div className="wrap" style={{ gap: 5, marginTop: 6 }}>
          {item.engine.taste_label ? <Badge>{item.engine.taste_label}</Badge> : null}
          {item.engine.fashion_score ? <Badge tone="ok">fashion {item.engine.fashion_score}/100</Badge> : null}
          {item.engine.role_label ? <Badge>{item.engine.role_label}</Badge> : null}
          <Badge>селекция {Math.round(item.score * 100)}%</Badge>
        </div>
        {item.reasons.length ? (
          <ul className="reasons" style={{ marginTop: 6 }}>
            {item.reasons.slice(0, 2).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  )
}

export function Search({
  meta,
  onGenerate,
  generating,
  error,
}: {
  meta: Meta | null
  onGenerate: (patch: Partial<WizardState>) => void
  generating: boolean
  error: string | null
}) {
  const [query, setQuery] = useState('')
  const [style, setStyle] = useState('minimal')
  const [season, setSeason] = useState('all')
  const [occasion, setOccasion] = useState('everyday')
  const [presentation, setPresentation] = useState('unisex')
  const [budget, setBudget] = useState(50_000)
  const [niche, setNiche] = useState<number | null>(null)
  const [result, setResult] = useState<EngineSearchResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    if (meta?.styles.length) setStyle((current) => (meta.styles.some((s) => s.id === current) ? current : meta.styles[0].id))
  }, [meta])

  const runSearch = async (overrides?: Partial<{ query: string; style: string; niche: number }>) => {
    const text = (overrides?.query ?? query).trim()
    if (text.length < 2) {
      setLocalError('Опишите образ словами — например, «индустриальный образ с прозрачным верхом».')
      return
    }
    setBusy(true)
    setLocalError(null)
    try {
      const response = await api.engineSearch({
        query: text,
        style: overrides?.style ?? style,
        occasion,
        season,
        presentation,
        budget_rub: budget,
        niche_level: overrides?.niche ?? niche,
        limit: 8,
      })
      setResult(response)
      playSuccess()
    } catch (caught) {
      setResult(null)
      setLocalError(caught instanceof Error ? caught.message : 'Поиск не удался, попробуйте ещё раз.')
    } finally {
      setBusy(false)
    }
  }

  const applyPreset = (preset: (typeof PRESETS)[number]) => {
    playTick()
    setQuery(preset.query)
    setStyle(preset.style)
    setNiche(preset.niche)
    void runSearch({ query: preset.query, style: preset.style, niche: preset.niche })
  }

  const engine = result?.engine
  const tasteMix = Object.entries(engine?.taste_mix ?? {})

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle index="01" hint="свободный запрос">
          Что ищем
        </SectionTitle>
        <textarea
          className="engine-query"
          value={query}
          rows={3}
          placeholder="Например: грязный индустриальный образ с прозрачным верхом и кожаной курткой"
          aria-label="Запрос к движку"
          onChange={(event) => setQuery(event.target.value)}
        />

        <div className="wrap" style={{ gap: 6 }}>
          {PRESETS.map((preset) => (
            <Chip key={preset.label} active={false} onClick={() => applyPreset(preset)}>
              {preset.label}
            </Chip>
          ))}
        </div>

        <div className="stack" style={{ gap: 6 }}>
          <span className="tiny">Направление стиля</span>
          <div className="wrap" style={{ gap: 6 }}>
            {(meta?.styles ?? []).map((option) => (
              <Chip key={option.id} active={style === option.id} onClick={() => setStyle(option.id)}>
                {option.label}
              </Chip>
            ))}
          </div>
        </div>

        <div className="stack" style={{ gap: 6 }}>
          <span className="tiny">Сезон</span>
          <div className="wrap" style={{ gap: 6 }}>
            {(meta?.seasons ?? []).map((option) => (
              <Chip key={option.id} active={season === option.id} onClick={() => setSeason(option.id)}>
                {option.label}
              </Chip>
            ))}
          </div>
        </div>

        <div className="stack" style={{ gap: 6 }}>
          <span className="tiny">Повод</span>
          <div className="wrap" style={{ gap: 6 }}>
            {(meta?.occasions ?? []).map((option) => (
              <Chip key={option.id} active={occasion === option.id} onClick={() => setOccasion(option.id)}>
                {option.label}
              </Chip>
            ))}
          </div>
        </div>

        <div className="stack" style={{ gap: 6 }}>
          <span className="tiny">Подача</span>
          <div className="wrap" style={{ gap: 6 }}>
            {(meta?.presentations ?? []).map((option) => (
              <Chip key={option.id} active={presentation === option.id} onClick={() => setPresentation(option.id)}>
                {option.label}
              </Chip>
            ))}
          </div>
        </div>

        <RangeField
          label="Бюджет"
          value={budget}
          min={meta?.budget.min_rub ?? 10_000}
          max={meta?.budget.max_rub ?? 100_000}
          step={1_000}
          suffix="₽"
          onChange={setBudget}
          hint="Бюджет удерживает приложение: движок подбирает, оптимизатор доводит до лимита."
        />

        <div className="stack" style={{ gap: 6 }}>
          <RangeField
            label="Уровень ниши (движок)"
            value={niche ?? 60}
            min={0}
            max={100}
            step={2}
            suffix="/100"
            onChange={setNiche}
            hint="Выше — больше редких и нишевых вещей, ниже — больше базовых."
          />
          <button type="button" className="link-btn" onClick={() => setNiche(null)}>
            {niche === null ? 'Сейчас: ниша выводится из стиля' : 'Сбросить и выводить из стиля'}
          </button>
        </div>

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={() => {
            playClick()
            void runSearch()
          }}
          disabled={busy}
        >
          {busy ? (
            <>
              <Spinner /> Движок ищет
            </>
          ) : (
            'Найти вещи'
          )}
        </button>

        {localError ? <div className="error-box">{localError}</div> : null}
      </section>

      {result && engine ? (
        <>
          <section className="card stack" style={{ gap: 10 }}>
            <SectionTitle index="02" hint={`движок v${engine.engine_version ?? '1.0.0'}`}>
              Тезис образа
            </SectionTitle>

            <div className="row" style={{ gap: 12, alignItems: 'center' }}>
              <div className="engine-score">
                <strong>{Math.round(engine.outfit_score ?? 0)}</strong>
                <span className="tiny">из 100</span>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ fontSize: 16 }}>{engine.styling_thesis_ru || engine.styling_thesis}</strong>
                <div className="muted small" style={{ marginTop: 2 }}>
                  {engine.styling_thesis} · {engine.aesthetic_ru ?? engine.aesthetic}
                </div>
              </div>
            </div>

            <div className="wrap" style={{ gap: 6 }}>
              <Badge tone={engine.critic_decision === 'APPROVE' ? 'ok' : 'warn'}>
                критик: {engine.critic_decision === 'APPROVE' ? 'одобрено' : 'нужно усилить'}
              </Badge>
              <Badge>ниша {engine.niche_level}/100</Badge>
              {engine.aesthetics?.map((aesthetic) => (
                <Badge key={aesthetic}>{aesthetic}</Badge>
              ))}
              {(engine.queries_used ?? []).length ? <Badge>запросов: {engine.queries_total}</Badge> : null}
            </div>

            {engine.critic_feedback?.length ? (
              <ul className="reasons">
                {engine.critic_feedback.slice(0, 3).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            ) : null}

            {engine.candidates ? (
              <div className="muted small">
                Найдено позиций: {engine.candidates.raw_items ?? 0} · прошли отбор: {engine.candidates.validated ?? 0} ·
                собрано образов: {engine.candidates.outfits_built ?? 0}
              </div>
            ) : null}

            {tasteMix.length ? (
              <div className="wrap" style={{ gap: 6 }}>
                {tasteMix.map(([category, count]) => (
                  <Badge key={category}>
                    {category}: {count}
                  </Badge>
                ))}
              </div>
            ) : null}
          </section>

          <section className="card stack" style={{ gap: 10 }}>
            <SectionTitle index="03" hint={`${result.items.length} позиций`}>
              Подбор движка
            </SectionTitle>
            {result.items.map((item) => (
              <ItemRow key={item.sku} item={item} />
            ))}
            <div className="muted small">
              Сумма отобранного: {formatRub(result.total_rub)} из бюджета {formatRub(result.budget_rub)}
            </div>
          </section>

          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled={generating}
            onClick={() => {
              playClick()
              onGenerate({
                query: result.query,
                style,
                mood: result.suggested_request.mood,
                occasion,
                season,
                presentation,
                budget_rub: budget,
                niche_level: result.suggested_request.niche_level,
              })
            }}
          >
            {generating ? (
              <>
                <Spinner /> Собираем образ
              </>
            ) : (
              'Собрать образ по этому запросу'
            )}
          </button>
        </>
      ) : null}

      {error ? <div className="error-box">{error}</div> : null}
    </div>
  )
}
