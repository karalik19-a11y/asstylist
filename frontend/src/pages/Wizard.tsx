import type { Meta } from '../lib/types'
import type { WizardModel, WizardStep } from '../state/wizard'
import { LIMITS, STEP_ORDER, STEP_TITLES, validateStep } from '../state/wizard'
import type { BodyMemory } from '../lib/profile'
import { bodyLabel, bodyUpdatedLabel } from '../lib/profile'
import { formatRub } from '../lib/format'
import { Chip, Header, ProgressBar, RangeField, SectionTitle, Spinner, Tile } from '../components/ui'
import { PhotoUploader } from '../components/PhotoUploader'
import { MOOD_BADGES, STYLE_BADGES } from '../lib/graphics'
import { isTelegram } from '../lib/telegram'
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
  savedBody = null,
  onUseSavedBody,
  onNewBody,
  onRestartAll,
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
  /** Сохранённые рост и вес: предлагаем выбор «сохранённые или новые». */
  savedBody?: BodyMemory | null
  onUseSavedBody?: () => void
  onNewBody?: () => void
  onRestartAll?: () => void
}) {
  const { step, state } = model
  const blocker = validateStep(step, state)
  const isLast = step === STEP_ORDER[STEP_ORDER.length - 1]
  const bmi = state.weight_kg / Math.pow(state.height_cm / 100, 2)

  return (
    <div className="stack page-transition" style={{ gap: 16 }}>
      <Header
        title={STEP_TITLES[step]}
        subtitle={
          step === 'memory' ? 'рост и вес уже сохранены' : `Шаг ${STEP_ORDER.indexOf(step) + 1} из ${STEP_ORDER.length}`
        }
        onBack={isTelegram() || step === 'photo' || step === 'memory' ? undefined : onBack}
        onHome={onExit}
      />
      {step === 'memory' ? null : <ProgressBar value={(STEP_ORDER.indexOf(step) + 1) / STEP_ORDER.length} />}

      {step === 'memory' ? (
        <div className="stack" style={{ gap: 16 }}>
          <p className="muted" style={{ margin: 0, fontSize: 15.5 }}>
            Вы уже называли рост и вес — сервис помнит их и предлагает выбор. Данные хранятся только для
            подбора посадки: рост и вес, ничего лишнего.
          </p>
          <div className="card stack memory-card" style={{ gap: 14 }}>
            <div>
              <div className="tiny muted">Сохранённые параметры</div>
              <div className="memory-value">{bodyLabel(savedBody)}</div>
              {bodyUpdatedLabel(savedBody) ? (
                <div className="muted small">обновлено {bodyUpdatedLabel(savedBody)}</div>
              ) : null}
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                playClick()
                onUseSavedBody?.()
              }}
            >
              Собрать по сохранённым данным
            </button>
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => {
                playClick()
                onNewBody?.()
              }}
            >
              Ввести новые рост и вес
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                playClick()
                onRestartAll?.()
              }}
            >
              Пройти настройку полностью заново
            </button>
          </div>
        </div>
      ) : null}

      {step === 'photo' ? (
        <div className="stack" style={{ gap: 16 }}>
          <p className="muted" style={{ margin: 0, fontSize: 15.5 }}>
            По фото определим цветотип, подтон кожи, контраст внешности и пропорции — и подберём оттенки и
            крой под вас, а не «в среднем». Снимок анализируется при формировании образа и не сохраняется.
          </p>
          <PhotoUploader dataUrl={state.photoDataUrl} onSelect={onPhoto} onClear={onClearPhoto} />
          <div className="muted small" style={{ textAlign: 'center' }}>
            Вещи подберём только на Авито — с живыми фото, ценами и ссылками.
          </div>
          {state.photoDataUrl ? (
            <div className="card small muted" style={{ borderLeft: '4px solid var(--accent-leopard)' }}>
              Снимок прикреплён — разбор внешности (цветотип, подтон, контраст) запустится при формировании гардероба.
            </div>
          ) : null}
        </div>
      ) : null}

      {step === 'body' ? (
        <div className="stack" style={{ gap: 16 }}>
          {savedBody ? (
            <div className="card small muted" style={{ borderLeft: '4px solid var(--accent-leopard)' }}>
              Сохранено: {bodyLabel(savedBody)}. Меняйте, если что-то изменилось — новые значения запомним
              снова.
            </div>
          ) : null}
          <div className="card stack" style={{ gap: 22 }}>
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

          <div className="card stack" style={{ gap: 14 }}>
            <SectionTitle>Линия посадки</SectionTitle>
            <div className="wrap">
              {(meta?.presentations ?? [{ id: 'unisex', label: 'Унисекс' }]).map((option) => (
                <Chip key={option.id} active={state.presentation === option.id} onClick={() => onPatch({ presentation: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
            <div className="muted small">Нужно только для подбора пропорций и лекал.</div>
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
        <div className="stack" style={{ gap: 16 }}>
          <div className="card stack" style={{ gap: 14 }}>
            <SectionTitle>Контекст и повод</SectionTitle>
            <div className="wrap">
              {(meta?.occasions ?? []).map((option) => (
                <Chip key={option.id} active={state.occasion === option.id} onClick={() => onPatch({ occasion: option.id })}>
                  {option.label}
                </Chip>
              ))}
            </div>
          </div>

          <div className="card stack" style={{ gap: 14 }}>
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
            <div className="card stack" style={{ gap: 16 }}>
              <SectionTitle hint="до 5">Предпочтительные оттенки</SectionTitle>
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

              <SectionTitle hint="до 5">Исключить из подбора</SectionTitle>
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
        <div className="stack" style={{ gap: 16 }}>
          <div className="stamp-card stack" style={{ gap: 12 }}>
            <div className="stamp-strip">
              <span className="stamp-strip-title">Ваш запрос</span>
              <span className="stamp-strip-num">проверьте детали</span>
            </div>
            <ReviewRow label="Направление стиля" value={meta?.styles.find((s) => s.id === state.style)?.label ?? state.style} />
            <ReviewRow label="Тональность настроения" value={meta?.moods.find((m) => m.id === state.mood)?.label ?? state.mood} />
            <ReviewRow label="Контекст" value={meta?.occasions.find((o) => o.id === state.occasion)?.label ?? state.occasion} />
            <ReviewRow label="Сезон" value={meta?.seasons.find((s) => s.id === state.season)?.label ?? state.season} />
            <ReviewRow label="Параметры фигуры" value={`${state.height_cm} см / ${state.weight_kg} кг`} />
            <ReviewRow label="Предел бюджета" value={formatRub(state.budget_rub)} />
            <ReviewRow label="Снимок" value={state.photoDataUrl ? 'прикреплён' : 'без фото'} />
            <ReviewRow
              label="Свободный запрос"
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

          <div className="stamp-card stack" style={{ gap: 12 }}>
            <div className="stamp-strip">
              <span className="stamp-strip-title">Своя формулировка</span>
              <span className="stamp-strip-num">необязательно</span>
            </div>
            <p className="muted small" style={{ margin: 0 }}>
              Опишите образ словами — соберём вещи под ваш текст. Оставьте пустым — возьмём стиль и настроение.
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
