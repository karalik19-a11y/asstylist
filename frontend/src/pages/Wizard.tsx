import type { Meta } from '../lib/types'
import type { WizardModel, WizardStep } from '../state/wizard'
import { LIMITS, STEP_ORDER, STEP_TITLES, validateStep } from '../state/wizard'
import { formatRub } from '../lib/format'
import { Chip, Header, ProgressBar, RangeField, SectionTitle, Spinner, Tile } from '../components/ui'
import { PhotoUploader } from '../components/PhotoUploader'

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
    <div className="stack">
      <Header title={STEP_TITLES[step]} subtitle={`Шаг ${STEP_ORDER.indexOf(step) + 1} из ${STEP_ORDER.length}`} onBack={step === 'photo' ? onExit : onBack} />
      <ProgressBar value={(STEP_ORDER.indexOf(step) + 1) / STEP_ORDER.length} />

      {step === 'photo' ? (
        <div className="stack">
          <p className="muted small" style={{ margin: 0 }}>
            Фото не обязательно, но с ним движок определит подтон кожи и пропорции. Изображение обрабатывается на
            сервере и по умолчанию не сохраняется.
          </p>
          <PhotoUploader dataUrl={state.photoDataUrl} onSelect={onPhoto} onClear={onClearPhoto} />
          {state.photoDataUrl ? (
            <div className="card small muted">Фото добавлено — анализ запустится при генерации образа.</div>
          ) : null}
        </div>
      ) : null}

      {step === 'body' ? (
        <div className="stack">
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
              hint={`ИМТ ${bmi.toFixed(1)}`}
            />
          </div>
          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Посадка</SectionTitle>
            <div className="wrap">
              {(meta?.presentations ?? [{ id: 'unisex', label: 'Унисекс' }]).map((option) => (
                <Chip key={option.id} active={state.presentation === option.id} onClick={() => onPatch({ presentation: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
            <div className="muted small">
              Параметры нужны только для подбора силуэта. Мы не ставим диагнозы и не оцениваем тело.
            </div>
          </div>
        </div>
      ) : null}

      {step === 'style' ? (
        <div className="grid-2">
          {(meta?.styles ?? []).map((style) => (
            <Tile
              key={style.id}
              active={state.style === style.id}
              emoji={style.emoji}
              title={style.label}
              description={style.description}
              onClick={() => onPatch({ style: style.id })}
            />
          ))}
        </div>
      ) : null}

      {step === 'mood' ? (
        <div className="grid-2">
          {(meta?.moods ?? []).map((mood) => (
            <Tile
              key={mood.id}
              active={state.mood === mood.id}
              emoji={mood.emoji}
              title={mood.label}
              description={mood.description}
              onClick={() => onPatch({ mood: mood.id })}
            />
          ))}
        </div>
      ) : null}

      {step === 'tune' ? (
        <div className="stack">
          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Повод</SectionTitle>
            <div className="wrap">
              {(meta?.occasions ?? []).map((option) => (
                <Chip key={option.id} active={state.occasion === option.id} onClick={() => onPatch({ occasion: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
          </div>

          <div className="card stack" style={{ gap: 10 }}>
            <SectionTitle>Сезон</SectionTitle>
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
              label="Бюджет"
              suffix="₽"
              value={state.budget_rub}
              min={LIMITS.budget.min}
              max={LIMITS.budget.max}
              step={LIMITS.budget.step}
              onChange={(value) => onPatch({ budget_rub: value })}
              hint={`Движок соберёт образ не дороже ${formatRub(state.budget_rub)}`}
            />
          </div>

          {meta?.colors?.length ? (
            <div className="card stack" style={{ gap: 10 }}>
              <SectionTitle hint="до 5">Любимые цвета</SectionTitle>
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
              <SectionTitle hint="до 5">Не надевать</SectionTitle>
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
        <div className="stack">
          <div className="card stack" style={{ gap: 8 }}>
            <SectionTitle>Проверьте ввод</SectionTitle>
            <ReviewRow label="Стиль" value={meta?.styles.find((s) => s.id === state.style)?.label ?? state.style} />
            <ReviewRow label="Настроение" value={meta?.moods.find((m) => m.id === state.mood)?.label ?? state.mood} />
            <ReviewRow label="Повод" value={meta?.occasions.find((o) => o.id === state.occasion)?.label ?? state.occasion} />
            <ReviewRow label="Сезон" value={meta?.seasons.find((s) => s.id === state.season)?.label ?? state.season} />
            <ReviewRow label="Рост / вес" value={`${state.height_cm} см / ${state.weight_kg} кг`} />
            <ReviewRow label="Бюджет" value={formatRub(state.budget_rub)} />
            <ReviewRow label="Фото" value={state.photoDataUrl ? 'добавлено' : 'без фото'} />
            <ReviewRow
              label="Любимые цвета"
              value={
                state.preferred_colors.length
                  ? state.preferred_colors.map((id) => meta?.colors.find((c) => c.id === id)?.label ?? id).join(', ')
                  : '—'
              }
            />
            <ReviewRow
              label="Не надевать"
              value={
                state.avoid_colors.length
                  ? state.avoid_colors.map((id) => meta?.colors.find((c) => c.id === id)?.label ?? id).join(', ')
                  : '—'
              }
            />
          </div>
          {state.photoDataUrl ? (
            <div className="photo-preview">
              <img src={state.photoDataUrl} alt="Ваше фото" />
            </div>
          ) : null}
          {error ? <div className="error-box">{error}</div> : null}
        </div>
      ) : null}

      <div className="action-bar">
        {blocker ? <div className="muted small">{blocker}</div> : null}
        <div className="action-bar-inner">
          {step !== 'photo' ? (
            <button type="button" className="btn" onClick={onBack}>
              Назад
            </button>
          ) : null}
          {isLast ? (
            <button type="button" className="btn btn-primary" style={{ flex: 1 }} onClick={onGenerate} disabled={generating}>
              {generating ? (
                <>
                  <Spinner /> Собираем образ
                </>
              ) : (
                'Сгенерировать'
              )}
            </button>
          ) : (
            <button type="button" className="btn btn-primary" style={{ flex: 1 }} onClick={onNext} disabled={Boolean(blocker)}>
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
    <div className="row-between small">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export type { WizardStep }
