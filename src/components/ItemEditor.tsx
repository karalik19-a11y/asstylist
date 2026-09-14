import { useEffect, useState } from 'react'
import type { Category, SeasonKey, StyleKey, WardrobeItem } from '../types'
import {
  CATEGORY_LABEL,
  CATEGORY_ORDER,
  SEASON_ORDER,
  SEASON_LABEL,
  STYLE_LABEL,
  STYLE_ORDER,
} from '../lib/catalog'
import { normalizeHex } from '../lib/color'
import { fileToDataUrl } from '../lib/image'
import { Scale } from './ItemCard'

const COLOR_PRESETS = [
  '#111111',
  '#3a3a3a',
  '#8b8b8b',
  '#c9c4bb',
  '#f7f5f0',
  '#c8b191',
  '#a9713f',
  '#b5561f',
  '#d99b27',
  '#8dc63f',
  '#6e7b3c',
  '#79d1c0',
  '#3c5a86',
  '#1b3a8f',
  '#9fc4dd',
  '#5b2a86',
  '#c9b8dd',
  '#b3123f',
  '#ff9aa2',
]

interface ItemEditorProps {
  item: WardrobeItem | null
  onClose: () => void
  onSubmit: (data: Omit<WardrobeItem, 'id' | 'wornDates'>) => void
  onDelete?: () => void
}

const emptyDraft: Omit<WardrobeItem, 'id' | 'wornDates'> = {
  name: '',
  category: 'top',
  colorHex: '#8b8b8b',
  styles: ['casual'],
  seasons: ['all'],
  warmth: 3,
  formality: 3,
  image: undefined,
  favorite: false,
}

export function ItemEditor({ item, onClose, onSubmit, onDelete }: ItemEditorProps) {
  const [draft, setDraft] = useState<Omit<WardrobeItem, 'id' | 'wornDates'>>(emptyDraft)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (item) {
      const { id: _id, wornDates: _worn, ...rest } = item
      setDraft(rest)
    } else {
      setDraft(emptyDraft)
    }
  }, [item])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const toggle = <T,>(list: T[], value: T): T[] =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value]

  const handleFile = async (file: File | undefined) => {
    if (!file) return
    setUploading(true)
    try {
      const url = await fileToDataUrl(file)
      setDraft((d) => ({ ...d, image: url }))
    } catch {
      setDraft((d) => ({ ...d, image: undefined }))
    } finally {
      setUploading(false)
    }
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const name = draft.name.trim()
    if (!name) return
    onSubmit({
      ...draft,
      name,
      colorHex: normalizeHex(draft.colorHex),
      styles: draft.styles.length ? draft.styles : ['casual'],
      seasons: draft.seasons.length ? draft.seasons : ['all'],
    })
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <header className="modal-head">
          <h2>{item ? 'Редактировать вещь' : 'Новая вещь'}</h2>
          <button type="button" className="btn tiny ghost" onClick={onClose}>
            Закрыть
          </button>
        </header>

        <div className="modal-body">
          <label className="field">
            <span>Название</span>
            <input
              type="text"
              value={draft.name}
              placeholder="Например: бежевый тренч"
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              required
            />
          </label>

          <div className="field">
            <span>Категория</span>
            <div className="chip-select">
              {CATEGORY_ORDER.map((c: Category) => (
                <button
                  key={c}
                  type="button"
                  className={`chip ${draft.category === c ? 'is-active' : ''}`}
                  onClick={() => setDraft({ ...draft, category: c })}
                >
                  {CATEGORY_LABEL[c].icon} {CATEGORY_LABEL[c].one}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <span>Цвет</span>
            <div className="color-row">
              <input
                type="color"
                value={normalizeHex(draft.colorHex)}
                onChange={(e) => setDraft({ ...draft, colorHex: e.target.value })}
              />
              <div className="swatches">
                {COLOR_PRESETS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`swatch ${normalizeHex(draft.colorHex) === c ? 'is-active' : ''}`}
                    style={{ background: c }}
                    onClick={() => setDraft({ ...draft, colorHex: c })}
                    aria-label={`Цвет ${c}`}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="field">
            <span>Стиль</span>
            <div className="chip-select">
              {STYLE_ORDER.map((s: StyleKey) => (
                <button
                  key={s}
                  type="button"
                  className={`chip ${draft.styles.includes(s) ? 'is-active' : ''}`}
                  onClick={() => setDraft({ ...draft, styles: toggle(draft.styles, s) })}
                >
                  {STYLE_LABEL[s]}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <span>Сезон</span>
            <div className="chip-select">
              <button
                type="button"
                className={`chip ${draft.seasons.includes('all') ? 'is-active' : ''}`}
                onClick={() =>
                  setDraft({ ...draft, seasons: draft.seasons.includes('all') ? [] : ['all'] })
                }
              >
                Круглый год
              </button>
              {SEASON_ORDER.map((s: SeasonKey) => (
                <button
                  key={s}
                  type="button"
                  className={`chip ${draft.seasons.includes(s) ? 'is-active' : ''}`}
                  onClick={() => setDraft({ ...draft, seasons: toggle(draft.seasons, s) })}
                >
                  {SEASON_LABEL[s]}
                </button>
              ))}
            </div>
          </div>

          <div className="field two">
            <label>
              <span>
                Тепло: <b>{draft.warmth}</b>/5
              </span>
              <input
                type="range"
                min={1}
                max={5}
                step={1}
                value={draft.warmth}
                onChange={(e) => setDraft({ ...draft, warmth: Number(e.target.value) })}
              />
              <small>1 — для жары, 5 — для мороза</small>
            </label>
            <label>
              <span>
                Формальность: <b>{draft.formality}</b>/5
              </span>
              <input
                type="range"
                min={1}
                max={5}
                step={1}
                value={draft.formality}
                onChange={(e) => setDraft({ ...draft, formality: Number(e.target.value) })}
              />
              <small>1 — спорт и дом, 5 — выход в свет</small>
            </label>
          </div>

          <div className="field">
            <span>Фото</span>
            <div className="photo-row">
              <label className="file-btn">
                {uploading ? 'Обработка…' : 'Загрузить файл'}
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => handleFile(e.target.files?.[0])}
                />
              </label>
              <input
                type="url"
                placeholder="или ссылка на изображение"
                value={draft.image?.startsWith('data:') ? '' : draft.image ?? ''}
                onChange={(e) => setDraft({ ...draft, image: e.target.value || undefined })}
              />
              {draft.image && (
                <button
                  type="button"
                  className="btn tiny ghost"
                  onClick={() => setDraft({ ...draft, image: undefined })}
                >
                  Убрать
                </button>
              )}
            </div>
            {draft.image && (
              <div className="photo-preview">
                <img src={draft.image} alt="предпросмотр" />
                <Scale value={draft.warmth} />
              </div>
            )}
          </div>
        </div>

        <footer className="modal-foot">
          {item && onDelete && (
            <button type="button" className="btn ghost danger" onClick={onDelete}>
              Удалить вещь
            </button>
          )}
          <div className="spacer" />
          <button type="button" className="btn ghost" onClick={onClose}>
            Отмена
          </button>
          <button type="submit" className="btn primary">
            {item ? 'Сохранить' : 'Добавить в гардероб'}
          </button>
        </footer>
      </form>
    </div>
  )
}
