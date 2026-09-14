import { useEffect, useMemo, useState } from 'react'
import type { OccasionKey, Outfit, SeasonKey, WardrobeItem } from '../types'
import { useAppState } from '../state/AppState'
import { OCCASIONS, OCCASION_MAP, SEASON_LABEL } from '../lib/catalog'
import { readableText } from '../lib/color'
import { addDays, buildWeekPlan, formatDate, isoDate, weekdayLabel } from '../lib/stylist'
import { ScoreRing } from './OutfitCard'

type Season = Exclude<SeasonKey, 'all'>

const seasonDefaults: Record<Season, number> = { winter: -4, spring: 13, summer: 25, autumn: 9 }

const SEASONS: Season[] = ['winter', 'spring', 'summer', 'autumn']

function currentSeason(): Season {
  const month = new Date().getMonth()
  if (month <= 1 || month === 11) return 'winter'
  if (month <= 4) return 'spring'
  if (month <= 7) return 'summer'
  return 'autumn'
}

const defaultOccasions: OccasionKey[] = ['work', 'work', 'work', 'work', 'work', 'walk', 'home']

export function WeekView() {
  const { items, profile, itemById, markWorn, saveOutfit } = useAppState()
  const [startDate, setStartDate] = useState(isoDate())
  const [season, setSeason] = useState<Season>(currentSeason())
  const [temperature, setTemperature] = useState<number>(seasonDefaults[currentSeason()])
  const [plan, setPlan] = useState<ReturnType<typeof buildWeekPlan>>([])

  const dates = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(startDate, i)), [startDate])
  const [occasions, setOccasions] = useState<Record<string, OccasionKey>>(() =>
    Object.fromEntries(dates.map((d, i) => [d, defaultOccasions[i]])),
  )

  useEffect(() => {
    const next = Object.fromEntries(dates.map((d, i) => [d, occasions[d] ?? defaultOccasions[i]]))
    setOccasions(next)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate])

  useEffect(() => {
    if (items.length === 0) {
      setPlan([])
      return
    }
    setPlan(buildWeekPlan({ items, profile, season, temperature, startDate, occasionsByDate: occasions }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, profile, season, temperature, startDate, JSON.stringify(occasions)])

  const resolve = (ids: string[]): WardrobeItem[] =>
    ids.map((id) => itemById(id)).filter((i): i is WardrobeItem => Boolean(i))

  const applyPlan = () => {
    for (const day of plan) {
      if (day.outfit) markWorn(day.outfit.itemIds, day.date)
    }
  }

  return (
    <section className="view">
      <div className="view-head">
        <div>
          <h2>План на неделю</h2>
          <p className="muted">
            Семь образов подряд: надетые вещи учитываются в следующие дни, поэтому гардероб
            равномерно прокручивается, а образы не повторяются
          </p>
        </div>
        <div className="view-actions">
          <button type="button" className="btn ghost" onClick={applyPlan} disabled={plan.length === 0}>
            Отметить неделю надетой
          </button>
        </div>
      </div>

      <div className="control-row">
        <label className="field">
          <span className="field-label">Начало недели</span>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </label>
        <div className="field">
          <span className="field-label">Сезон</span>
          <div className="chip-select">
            {SEASONS.map((s) => (
              <button
                key={s}
                type="button"
                className={`chip ${season === s ? 'is-active' : ''}`}
                onClick={() => {
                  setSeason(s)
                  setTemperature(seasonDefaults[s])
                }}
              >
                {SEASON_LABEL[s]}
              </button>
            ))}
          </div>
        </div>
        <div className="field grow">
          <span className="field-label">
            Температура: <b>{temperature > 0 ? '+' : ''}{temperature} °C</b>
          </span>
          <input
            type="range"
            min={-25}
            max={35}
            step={1}
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
          />
        </div>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>Неделю собирать не из чего</h3>
          <p>Добавьте вещи в гардероб — и план на семь дней соберётся автоматически.</p>
        </div>
      ) : (
        <div className="week-grid">
          {plan.map((day) => (
            <article className="day-card" key={day.date}>
              <header>
                <div>
                  <b>{weekdayLabel(day.date)}</b>
                  <small>{formatDate(day.date)}</small>
                </div>
                {day.outfit ? (
                  <ScoreRing score={day.outfit.score} />
                ) : (
                  <span className="no-outfit">нет вариантов</span>
                )}
              </header>

              <select
                className="day-occasion"
                value={occasions[day.date]}
                onChange={(e) =>
                  setOccasions((prev) => ({ ...prev, [day.date]: e.target.value as OccasionKey }))
                }
              >
                {OCCASIONS.map((o) => (
                  <option key={o.key} value={o.key}>
                    {o.icon} {o.label}
                  </option>
                ))}
              </select>

              {day.outfit && (
                <>
                  <div className="day-items">
                    {resolve(day.outfit.itemIds).map((item) => (
                      <span key={item.id} className="day-item" title={item.name}>
                        {item.image ? (
                          <img src={item.image} alt={item.name} loading="lazy" />
                        ) : (
                          <i
                            className="day-swatch"
                            style={{ background: item.colorHex, color: readableText(item.colorHex) }}
                          >
                            {item.name.slice(0, 1)}
                          </i>
                        )}
                      </span>
                    ))}
                  </div>
                  <ul className="day-names">
                    {resolve(day.outfit.itemIds).map((item) => (
                      <li key={item.id}>{item.name}</li>
                    ))}
                  </ul>
                  <p className="day-tip">{day.outfit.analysis.tips[0]}</p>
                  <footer>
                    <button
                      type="button"
                      className="btn tiny"
                      onClick={() => saveOutfit({ ...day.outfit!, plannedFor: day.date } as Outfit)}
                    >
                      Сохранить
                    </button>
                    <button
                      type="button"
                      className="btn tiny ghost"
                      onClick={() => day.outfit && markWorn(day.outfit.itemIds, day.date)}
                    >
                      Надето
                    </button>
                  </footer>
                  <p className="day-occasion-label">{OCCASION_MAP[day.occasion].label}</p>
                </>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
