import { useMemo, useState } from 'react'
import type { Category, StyleKey, WardrobeItem } from '../types'
import { useAppState } from '../state/AppState'
import { CATEGORY_LABEL, CATEGORY_ORDER, STYLE_LABEL, STYLE_ORDER } from '../lib/catalog'
import { hexToHsl } from '../lib/color'
import { wardrobeAudit } from '../lib/stylist'
import { ItemCard } from './ItemCard'
import { ItemEditor } from './ItemEditor'

export function WardrobeView() {
  const { items, profile, addItem, updateItem, removeItem, toggleFavorite, loadDemo } = useAppState()
  const [editing, setEditing] = useState<WardrobeItem | null>(null)
  const [creating, setCreating] = useState(false)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<Category | 'all'>('all')
  const [style, setStyle] = useState<StyleKey | 'all'>('all')
  const [favOnly, setFavOnly] = useState(false)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items.filter((item) => {
      if (category !== 'all' && item.category !== category) return false
      if (style !== 'all' && !item.styles.includes(style)) return false
      if (favOnly && !item.favorite) return false
      if (q && !item.name.toLowerCase().includes(q)) return false
      return true
    })
  }, [items, category, style, favOnly, query])

  const audit = useMemo(() => wardrobeAudit(items, profile), [items, profile])

  const stats = useMemo(() => {
    const neutral = items.filter((i) => {
      const hsl = hexToHsl(i.colorHex)
      return hsl.s < 0.15 || hsl.l > 0.9 || hsl.l < 0.12
    }).length
    return {
      total: items.length,
      neutral: items.length ? Math.round((neutral / items.length) * 100) : 0,
      favorites: items.filter((i) => i.favorite).length,
      byCategory: CATEGORY_ORDER.map((c) => ({
        category: c,
        count: items.filter((i) => i.category === c).length,
      })),
    }
  }, [items])

  const closeEditor = () => {
    setEditing(null)
    setCreating(false)
  }

  return (
    <section className="view">
      <div className="view-head">
        <div>
          <h2>Гардероб</h2>
          <p className="muted">
            {stats.total} вещ. · {stats.neutral}% нейтральной базы · {stats.favorites} в избранном
          </p>
        </div>
        <div className="view-actions">
          {items.length === 0 && (
            <button type="button" className="btn ghost" onClick={loadDemo}>
              Загрузить демо-гардероб
            </button>
          )}
          <button type="button" className="btn primary" onClick={() => setCreating(true)}>
            + Добавить вещь
          </button>
        </div>
      </div>

      <div className="filters">
        <input
          className="search"
          type="search"
          placeholder="Поиск по названию"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="chip-select">
          <button
            type="button"
            className={`chip ${category === 'all' ? 'is-active' : ''}`}
            onClick={() => setCategory('all')}
          >
            Все категории
          </button>
          {CATEGORY_ORDER.map((c) => (
            <button
              key={c}
              type="button"
              className={`chip ${category === c ? 'is-active' : ''}`}
              onClick={() => setCategory(c)}
            >
              {CATEGORY_LABEL[c].icon} {CATEGORY_LABEL[c].one}
            </button>
          ))}
        </div>
        <div className="chip-select">
          <button
            type="button"
            className={`chip ${style === 'all' ? 'is-active' : ''}`}
            onClick={() => setStyle('all')}
          >
            Любой стиль
          </button>
          {STYLE_ORDER.map((s) => (
            <button
              key={s}
              type="button"
              className={`chip ${style === s ? 'is-active' : ''}`}
              onClick={() => setStyle(s)}
            >
              {STYLE_LABEL[s]}
            </button>
          ))}
        </div>
        <label className="switch">
          <input type="checkbox" checked={favOnly} onChange={(e) => setFavOnly(e.target.checked)} />
          Только избранное
        </label>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>Гардероб пока пуст</h3>
          <p>
            Добавьте 5–7 вещей — или загрузите демо-гардероб из 10 базовых предметов, чтобы сразу
            посмотреть, как стилист собирает образы.
          </p>
          <div className="empty-actions">
            <button type="button" className="btn primary" onClick={() => setCreating(true)}>
              Добавить первую вещь
            </button>
            <button type="button" className="btn ghost" onClick={loadDemo}>
              Демо-гардероб
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="stat-strip">
            {stats.byCategory.map((s) => (
              <div key={s.category} className="stat">
                <span className="stat-value">{s.count}</span>
                <span className="stat-label">{CATEGORY_LABEL[s.category].many}</span>
              </div>
            ))}
          </div>

          {filtered.length === 0 ? (
            <p className="muted pad">Под фильтры ничего не подошло — сбросьте условия поиска.</p>
          ) : (
            <div className="item-grid">
              {filtered.map((item) => (
                <ItemCard
                  key={item.id}
                  item={item}
                  onEdit={(i) => setEditing(i)}
                  onDelete={(i) => removeItem(i.id)}
                  onToggleFavorite={toggleFavorite}
                />
              ))}
            </div>
          )}
        </>
      )}

      <div className="panel">
        <h3>Что говорит стилист</h3>
        <ul className="audit">
          {audit.map((note, idx) => (
            <li key={idx} className={`audit-item ${note.level}`}>
              <b>{note.title}</b>
              <span>{note.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {(creating || editing) && (
        <ItemEditor
          item={editing}
          onClose={closeEditor}
          onSubmit={(data) => {
            if (editing) updateItem(editing.id, data)
            else addItem(data)
            closeEditor()
          }}
          onDelete={
            editing
              ? () => {
                  removeItem(editing.id)
                  closeEditor()
                }
              : undefined
          }
        />
      )}
    </section>
  )
}
