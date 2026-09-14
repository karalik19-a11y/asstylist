import { useCallback, useEffect, useMemo, useState } from 'react'
import type { OccasionKey, Outfit, SeasonKey, WardrobeItem } from '../types'
import { useAppState } from '../state/AppState'
import { OCCASIONS, OCCASION_MAP, SEASON_LABEL } from '../lib/catalog'
import { analyzeOutfit, generateOutfits, isoDate, missingSlots, suitsSeason } from '../lib/stylist'
import { OutfitCard } from './OutfitCard'

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

interface StudioViewProps {
  onGoWardrobe: () => void
}

export function StudioView({ onGoWardrobe }: StudioViewProps) {
  const { items, profile, itemById, saveOutfit, markWorn, loadDemo } = useAppState()
  const [occasion, setOccasion] = useState<OccasionKey>('work')
  const [season, setSeason] = useState<Season>(currentSeason())
  const [temperature, setTemperature] = useState<number>(seasonDefaults[currentSeason()])
  const [seed, setSeed] = useState(1)
  const [favOnly, setFavOnly] = useState(false)
  const [outfits, setOutfits] = useState<Outfit[]>([])

  const pool = useMemo(
    () => (favOnly ? items.filter((i) => i.favorite) : items),
    [items, favOnly],
  )

  const missing = useMemo(() => missingSlots(pool, occasion, season), [pool, occasion, season])

  const regenerate = useCallback(() => {
    if (pool.length === 0) {
      setOutfits([])
      return
    }
    setOutfits(
      generateOutfits({
        items: pool,
        profile,
        occasion,
        season,
        temperature,
        limit: 6,
        seed,
      }),
    )
  }, [pool, profile, occasion, season, temperature, seed])

  useEffect(() => {
    regenerate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [regenerate])

  const resolve = useCallback(
    (ids: string[]): WardrobeItem[] => ids.map((id) => itemById(id)).filter((i): i is WardrobeItem => Boolean(i)),
    [itemById],
  )

  const alternativesFor = useCallback(
    (outfit: Outfit) => (item: WardrobeItem): WardrobeItem[] =>
      pool.filter(
        (candidate) =>
          candidate.id !== item.id &&
          candidate.category === item.category &&
          suitsSeason(candidate, season) &&
          !outfit.itemIds.includes(candidate.id),
      ),
    [pool, season],
  )

  const handleSwap = (outfit: Outfit, fromId: string, toId: string) => {
    setOutfits((prev) =>
      prev.map((o) => {
        if (o.id !== outfit.id) return o
        const itemIds = o.itemIds.map((id) => (id === fromId ? toId : id))
        const resolved = resolve(itemIds)
        const analysis = analyzeOutfit(resolved, profile, o.occasion, o.temperature)
        return { ...o, itemIds, analysis, score: analysis.total }
      }),
    )
  }

  const handleWear = (outfit: Outfit) => {
    markWorn(outfit.itemIds, isoDate())
    setSeed((s) => s + 1)
  }

  return (
    <section className="view">
      <div className="view-head">
        <div>
          <h2>Студия образов</h2>
          <p className="muted">Выберите повод, сезон и погоду — стилист соберёт варианты и объяснит решение</p>
        </div>
        <div className="view-actions">
          <button type="button" className="btn ghost" onClick={() => setSeed((s) => s + 1)}>
            Другие варианты
          </button>
        </div>
      </div>

      <div className="studio-controls">
        <div className="field">
          <span className="field-label">Повод</span>
          <div className="occasion-grid">
            {OCCASIONS.map((o) => (
              <button
                key={o.key}
                type="button"
                className={`occasion ${occasion === o.key ? 'is-active' : ''}`}
                onClick={() => setOccasion(o.key)}
              >
                <b>
                  {o.icon} {o.label}
                </b>
                <small>{o.description}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="control-row">
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
              Температура на улице: <b>{temperature > 0 ? '+' : ''}{temperature} °C</b>
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

          <label className="switch">
            <input type="checkbox" checked={favOnly} onChange={(e) => setFavOnly(e.target.checked)} />
            Только избранное
          </label>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>Сначала нужен гардероб</h3>
          <p>Добавьте вещи или загрузите демо-гардероб — дальше я соберу образы под любой повод.</p>
          <div className="empty-actions">
            <button type="button" className="btn primary" onClick={onGoWardrobe}>
              Перейти в гардероб
            </button>
            <button type="button" className="btn ghost" onClick={loadDemo}>
              Демо-гардероб
            </button>
          </div>
        </div>
      ) : outfits.length === 0 ? (
        <div className="empty-state">
          <h3>Не хватает вещей для этого повода</h3>
          <p>
            {missing.length > 0
              ? `Для повода «${OCCASION_MAP[occasion].label}» в сезоне «${SEASON_LABEL[season].toLowerCase()}» нет вещей в категориях: ${missing.join(', ')}.`
              : occasion === 'sport'
                ? 'Для спортивного образа нужны вещи со стилем «Спорт» — добавьте их в гардероб.'
                : 'Под этот сезон и повод подходящих вещей нет.'}
          </p>
          <p className="muted small">
            Попробуйте другой сезон, снимите фильтр «только избранное» или добавьте вещи в гардероб.
          </p>
          <div className="empty-actions">
            <button type="button" className="btn ghost" onClick={onGoWardrobe}>
              В гардероб
            </button>
            {favOnly && (
              <button type="button" className="btn primary" onClick={() => setFavOnly(false)}>
                Показать все вещи
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          <p className="muted pad">
            Показано {outfits.length} вариантов из {pool.length} вещ. — оценка учитывает гармонию
            цвета, формальность, стиль, ваш цветотип, погоду и ротацию вещей.
          </p>
          <div className="outfit-grid">
            {outfits.map((outfit) => (
              <OutfitCard
                key={outfit.id}
                outfit={outfit}
                items={resolve(outfit.itemIds)}
                alternativesFor={alternativesFor(outfit)}
                onSwap={(fromId, toId) => handleSwap(outfit, fromId, toId)}
                onSave={() => saveOutfit(outfit)}
                onWear={() => handleWear(outfit)}
              />
            ))}
          </div>
        </>
      )}
    </section>
  )
}
