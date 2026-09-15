import type { Meta } from '../lib/types'
import type { WizardModel, WizardStep } from '../state/wizard'
import { LIMITS, STEP_ORDER, STEP_TITLES, validateStep } from '../state/wizard'
import { formatRub } from '../lib/format'
import { Chip, Header, ProgressBar, RangeField, SectionTitle, Spinner, Tile } from '../components/ui'
import { PhotoUploader } from '../components/PhotoUploader'
import { MOOD_BADGES, STYLE_BADGES } from '../lib/graphics'
import { playClick } from '../lib/sound'

export function Wizard({
  model,
  meta,
  onPatch,
  onToggleColor,
  onPhoto,
  onClearPhoto,
  onBack,
  onNext,
  onGenerate,
  onExit,
  generating,
  error,
}: {
  model: WizardModel
  meta: Meta | null
  onPatch: (patch: Partial<WizardModel['state']>) => void
  onToggleColor: (id: string, field: 'preferred_colors' | 'avoid_colors') => void
  onPhoto: (dataUrl: string, file: File) => void
  onClearPhoto: () => void
  onBack: () => void
  onNext: () => void
  onGenerate: () => void
  onExit: () => void
  generating: boolean
  error: string | null
}) {
  const { step, state } = model
  const blocker = validateStep(step, state)
  const isLast = step === STEP_ORDER[STEP_ORDER.length - 1]
  const bmi = state.weight_kg / Math.pow(state.height_cm / 100, 2)

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      <Header
        title={STEP_TITLES[step]}
        subtitle={`Шаг ${STEP_ORDER.indexOf(step) + 1} из ${STEP_ORDER.length} · Студия подбора`}
        onBack={step === 'photo' ? onExit : onBack}
      />
      <ProgressBar value={(STEP_ORDER.indexOf(step) + 1) / STEP_ORDER.length} />

      {step === 'photo' ? (
        <div className="stack" style={{ gap: 14 }}>
          <p className="muted small" style={{ margin: 0 }}>
            Фотоснимок позволяет точно рассчитать пропорции силуэта и определить колорит внешности. Изображение
            обрабатывается локально и не сохраняется в постоянную базу.
          </p>
          <PhotoUploader dataUrl={state.photoDataUrl} onSelect={onPhoto} onClear={onClearPhoto} />
          {state.photoDataUrl ? (
            <div className="card small muted" style={{ borderLeft: '3px solid var(--accent-leopard)' }}>
              Снимок прикреплён — расчёт цветотипа и силуэта запустится при формировании гардероба.
            </div>
          ) : null}
        </div>
      ) : null}

      {step === 'body' ? (
        <div className="stack" style={{ gap: 14 }}>
          <div className="card stack">
            <RangeField
              label="Рост"
              suffix="см"
              value={state.height_cm}
              min={LIMITS.height.min}
              max={LIMITS.height.max}
              onChange={(value) => onPatch({ height_cm: value })}
            />
            <RangeField
              label="Вес"
              suffix="кг"
              value={state.weight_kg}
              min={LIMITS.weight.min}
              max={LIMITS.weight.max}
              onChange={(value) => onPatch({ weight_kg: value })}
              hint={`Индекс массы тела: ${bmi.toFixed(1)}`}
            />
          </div>

          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Линия посадки</SectionTitle>
            <div className="wrap">
              {(meta?.presentations ?? [{ id: 'unisex', label: 'Унисекс' }]).map((option) => (
                <Chip key={option.id} active={state.presentation === option.id} onClick={() => onPatch({ presentation: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
            <div className="muted small">
              Метрики необходимы исключительно для корректного подбора пропорций и лекал.
            </div>
          </div>
        </div>
      ) : null}

      {step === 'style' ? (
        <div className="grid-2">
          {(meta?.styles ?? []).map((style) => {
            const badge = STYLE_BADGES[style.id] ?? { kanji: '格', num: '00' }
            return (
              <Tile
                key={style.id}
                active={state.style === style.id}
                badgeKanji={badge.kanji}
                badgeNum={badge.num}
                title={style.label}
                description={style.description}
                onClick={() => onPatch({ style: style.id })}
              />
            )
          })}
        </div>
      ) : null}

      {step === 'mood' ? (
        <div className="grid-2">
          {(meta?.moods ?? []).map((mood) => {
            const badge = MOOD_BADGES[mood.id] ?? { kanji: '気', num: '00' }
            return (
              <Tile
                key={mood.id}
                active={state.mood === mood.id}
                badgeKanji={badge.kanji}
                badgeNum={badge.num}
                title={mood.label}
                description={mood.description}
                onClick={() => onPatch({ mood: mood.id })}
              />
            )
          })}
        </div>
      ) : null}

      {step === 'tune' ? (
        <div className="stack" style={{ gap: 14 }}>
          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Контекст и повод</SectionTitle>
            <div className="wrap">
              {(meta?.occasions ?? []).map((option) => (
                <Chip key={option.id} active={state.occasion === option.id} onClick={() => onPatch({ occasion: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
          </div>

          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Сезонность</SectionTitle>
            <div className="wrap">
              {(meta?.seasons ?? []).map((option) => (
                <Chip key={option.id} active={state.season === option.id} onClick={() => onPatch({ season: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
          </div>

          <div className="card stack">
            <RangeField
              label="Бюджет гардероба"
              suffix="₽"
              value={state.budget_rub}
              min={LIMITS.budget.min}
              max={LIMITS.budget.max}
              step={LIMITS.budget.step}
              onChange={(value) => onPatch({ budget_rub: value })}
              hint={`Селекция составляется строго в пределах ${formatRub(state.budget_rub)}`}
            />
          </div>

          {meta?.colors?.length ? (
            <div className="card stack" style={{ gap: 10 }}>
              <SectionTitle hint="до 5 оттенков">Предпочтительные оттенки</SectionTitle>
              <div className="wrap">
                {meta.colors.map((color) => (
                  <Chip
                    key={color.id}
                    active={state.preferred_colors.includes(color.id)}
                    onClick={() => onToggleColor(color.id, 'preferred_colors')}
                  >
                    {color.label}
                  </Chip>
                ))}
              </div>

              <SectionTitle hint="до 5 оттенков">Исключить из подбора</SectionTitle>
              <div className="wrap">
                {meta.colors.map((color) => (
                  <Chip
                    key={color.id}
                    active={state.avoid_colors.includes(color.id)}
                    onClick={() => onToggleColor(color.id, 'avoid_colors')}
                  >
                    {color.label}
                  </Chip>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {step === 'review' ? (
        <div className="stack" style={{ gap: 14 }}>
          <div className="stamp-card stack" style={{ gap: 10 }}>
            <div className="stamp-strip">
              <span className="stamp-strip-title">СПЕЦИФИКАЦИЯ ЗАКАЗА</span>
              <span className="stamp-strip-num">CHECK № 01</span>
            </div>
            <ReviewRow label="Направление стиля" value={meta?.styles.find((s) => s.id === state.style)?.label ?? state.style} />
            <ReviewRow label="Тональность настроения" value={meta?.moods.find((m) => m.id === state.mood)?.label ?? state.mood} />
            <ReviewRow label="Контекст" value={meta?.occasions.find((o) => o.id === state.occasion)?.label ?? state.occasion} />
            <ReviewRow label="Сезон" value={meta?.seasons.find((s) => s.id === state.season)?.label ?? state.season} />
            <ReviewRow label="Параметры фигуры" value={`${state.height_cm} см / ${state.weight_kg} кг`} />
            <ReviewRow label="Предел бюджета" value={formatRub(state.budget_rub)} />
            <ReviewRow label="Снимок" value={state.photoDataUrl ? 'прикреплён' : 'без фото'} />
            <ReviewRow
              label="Запрос к движку"
              value={state.query.trim() ? state.query.trim() : 'собирается из стиля и настроения'}
            />
            <ReviewRow
              label="Выбранные оттенки"
              value={
                state.preferred_colors.length
                  ? state.preferred_colors.map((id) => meta?.colors.find((c) => c.id === id)?.label ?? id).join(', ')
                  : 'по усмотрению стилиста'
              }
            />
            <ReviewRow
              label="Исключённые оттенки"
              value={
                state.avoid_colors.length
                  ? state.avoid_colors.map((id) => meta?.colors.find((c) => c.id === id)?.label ?? id).join(', ')
                  : 'нет ограничений'
              }
            />
          </div>

          <div className="stamp-card stack" style={{ gap: 8 }}>
            <div className="stamp-strip">
              <span className="stamp-strip-title">СВОЯ ФОРМУЛИРОВКА</span>
              <span className="stamp-strip-num">ДВИЖОК</span>
            </div>
            <p className="muted small" style={{ margin: 0 }}>
              Опишите образ словами — движок ASSTYLIST Fashion Engine расширит запрос, отберёт вещи и соберёт
              стилистический тезис. Если оставить поле пустым, запрос соберётся из стиля и настроения.
            </p>
            <textarea
              className="engine-query"
              rows={3}
              value={state.query}
              placeholder="Например: грязный индустриальный образ с прозрачным верхом"
              aria-label="Своя формулировка образа"
              onChange={(event) => onPatch({ query: event.target.value })}
            />
          </div>

          {state.photoDataUrl ? (
            <div className="photo-preview-container">
              <img src={state.photoDataUrl} alt="Кадр для анализа" />
            </div>
          ) : null}

          {error ? <div className="error-box">{error}</div> : null}
        </div>
      ) : null}

      {/* Sticky Bottom Action Bar: Buttons CANNOT overlap */}
      <div className="action-bar">
        {blocker ? (
          <div className="muted small" style={{ textAlign: 'center', color: 'var(--accent-crimson)' }}>
            {blocker}
          </div>
        ) : null}
        <div className="action-bar-inner">
          {step !== 'photo' ? (
            <button
              type="button"
              className="btn action-bar-btn-back"
              onClick={() => {
                playClick()
                onBack()
              }}
            >
              Назад
            </button>
          ) : null}

          {isLast ? (
            <button
              type="button"
              className="btn btn-primary action-bar-btn-main"
              onClick={() => {
                playClick()
                onGenerate()
              }}
              disabled={generating}
            >
              {generating ? (
                <>
                  <Spinner /> Формируем гардероб
                </>
              ) : (
                'Сгенерировать'
              )}
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-primary action-bar-btn-main"
              onClick={() => {
                playClick()
                onNext()
              }}
              disabled={Boolean(blocker)}
            >
              Далее
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="row-between small" style={{ borderBottom: '1px dashed var(--stamp-line-soft)', paddingBottom: 4 }}>
      <span className="muted" style={{ color: 'var(--stamp-ink-muted)' }}>
        {label}
      </span>
      <strong style={{ color: 'var(--stamp-ink)', textAlign: 'right' }}>{value}</strong>
    </div>
  )
}

export type { WizardStep }
