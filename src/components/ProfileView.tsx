import { useMemo, useRef, useState } from 'react'
import type { ColorSeason, StyleKey, WardrobeItem } from '../types'
import { useAppState } from '../state/AppState'
import { STYLE_LABEL, STYLE_ORDER } from '../lib/catalog'
import { SEASON_PALETTES, normalizeHex } from '../lib/color'
import { formatDate, isoDate } from '../lib/stylist'
import { OutfitCard } from './OutfitCard'

const SEASON_KEYS: ColorSeason[] = ['winter', 'summer', 'spring', 'autumn']

export function ProfileView() {
  const {
    profile,
    outfits,
    items,
    itemById,
    updateProfile,
    removeOutfit,
    clearWorn,
    resetAll,
    importJson,
    downloadBackup,
  } = useAppState()
  const [avoidDraft, setAvoidDraft] = useState('#b5561f')
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const toggleStyle = (style: StyleKey) => {
    const next = profile.preferredStyles.includes(style)
      ? profile.preferredStyles.filter((s) => s !== style)
      : [...profile.preferredStyles, style]
    updateProfile({ preferredStyles: next })
  }

  const sortedOutfits = useMemo(
    () => [...outfits].sort((a, b) => b.score - a.score),
    [outfits],
  )

  const handleImport = async (file: File | undefined) => {
    if (!file) return
    const text = await file.text()
    const res = importJson(text)
    setMessage(
      res.ok
        ? { type: 'ok', text: 'Гардероб импортирован' }
        : { type: 'err', text: `Ошибка импорта: ${res.error}` },
    )
  }

  return (
    <section className="view">
      <div className="view-head">
        <div>
          <h2>Профиль и данные</h2>
          <p className="muted">Настройки влияют на подбор: цветотип задаёт палитру, стили — характер образов</p>
        </div>
      </div>

      <div className="profile-grid">
        <div className="panel">
          <h3>Цветотип</h3>
          <p className="muted small">
            Выберите сезон — стилист будет повышать оценку образам в вашей палитре и предлагать
            замены для «чужих» оттенков.
          </p>
          <div className="season-grid">
            {SEASON_KEYS.map((key) => (
              <button
                key={key}
                type="button"
                className={`season-card ${profile.colorSeason === key ? 'is-active' : ''}`}
                onClick={() => updateProfile({ colorSeason: key })}
              >
                <div className="season-swatches">
                  {SEASON_PALETTES[key].swatches.map((c) => (
                    <i key={c} style={{ background: c }} />
                  ))}
                </div>
                <b>{SEASON_PALETTES[key].label}</b>
                <small>{SEASON_PALETTES[key].tagline}</small>
              </button>
            ))}
          </div>

          <h3 className="mt">Любимые стили</h3>
          <div className="chip-select">
            {STYLE_ORDER.map((s) => (
              <button
                key={s}
                type="button"
                className={`chip ${profile.preferredStyles.includes(s) ? 'is-active' : ''}`}
                onClick={() => toggleStyle(s)}
              >
                {STYLE_LABEL[s]}
              </button>
            ))}
          </div>

          <h3 className="mt">Цвета, которых избегаю</h3>
          <div className="avoid-row">
            <input
              type="color"
              value={avoidDraft}
              onChange={(e) => setAvoidDraft(e.target.value)}
              aria-label="Выбрать цвет"
            />
            <button
              type="button"
              className="btn tiny"
              onClick={() =>
                updateProfile({
                  avoidColors: Array.from(new Set([...profile.avoidColors, normalizeHex(avoidDraft)])),
                })
              }
            >
              Добавить
            </button>
            <div className="swatches">
              {profile.avoidColors.map((c) => (
                <button
                  key={c}
                  type="button"
                  className="swatch removable"
                  style={{ background: c }}
                  onClick={() =>
                    updateProfile({ avoidColors: profile.avoidColors.filter((x) => x !== c) })
                  }
                  title={`Убрать ${c}`}
                />
              ))}
            </div>
          </div>

          <h3 className="mt">Заметки о себе</h3>
          <textarea
            className="textarea"
            rows={3}
            placeholder="Например: не ношу каблуки выше 5 см, предпочитаю свободный силуэт"
            value={profile.notes}
            onChange={(e) => updateProfile({ notes: e.target.value })}
          />
        </div>

        <div className="panel">
          <h3>Сохранённые образы</h3>
          {sortedOutfits.length === 0 ? (
            <p className="muted">
              Пока пусто. В «Студии образов» нажмите «Сохранить образ» — он появится здесь.
            </p>
          ) : (
            <div className="saved-grid">
              {sortedOutfits.map((outfit) => (
                <OutfitCard
                  key={outfit.id}
                  outfit={outfit}
                  saved
                  items={outfit.itemIds
                    .map((id) => itemById(id))
                    .filter((i): i is WardrobeItem => Boolean(i))}
                  onRemove={() => removeOutfit(outfit.id)}
                  title={outfit.plannedFor ? `План на ${formatDate(outfit.plannedFor)}` : undefined}
                />
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <h3>Данные</h3>
          <p className="muted small">
            Все данные хранятся локально в браузере (localStorage) — сервер не используется.
            Сделайте резервную копию перед очисткой.
          </p>
          <div className="data-actions">
            <button type="button" className="btn" onClick={downloadBackup}>
              Скачать JSON
            </button>
            <button type="button" className="btn" onClick={() => fileRef.current?.click()}>
              Импортировать JSON
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="application/json"
              hidden
              onChange={(e) => handleImport(e.target.files?.[0])}
            />
            <button type="button" className="btn ghost" onClick={clearWorn} disabled={items.length === 0}>
              Очистить историю носки
            </button>
            <button
              type="button"
              className="btn ghost danger"
              onClick={() => {
                if (window.confirm('Удалить весь гардероб и сохранённые образы?')) resetAll()
              }}
            >
              Очистить всё
            </button>
          </div>
          {message && <p className={`message ${message.type}`}>{message.text}</p>}
          <p className="muted small mt">
            Вещей: {items.length} · сохранённых образов: {outfits.length} · сегодня: {formatDate(isoDate())}
          </p>
        </div>
      </div>
    </section>
  )
}
