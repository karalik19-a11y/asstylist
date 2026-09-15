import { useCallback, useEffect, useRef, useState } from 'react'
import type { FeedItem } from '../lib/types'
import { api } from '../lib/api'
import { formatRub } from '../lib/format'
import { openExternal } from '../lib/telegram'
import { SectionTitle } from './ui'

const PAGE = 12

export function TrendsFeed() {
  const [items, setItems] = useState<FeedItem[]>([])
  const [cursor, setCursor] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sentinel = useRef<HTMLDivElement | null>(null)
  const busy = useRef(false)

  const loadMore = useCallback(async () => {
    if (busy.current) return
    busy.current = true
    setLoading(true)
    setError(null)
    try {
      const page = await api.feed(cursor, PAGE)
      const list = Array.isArray(page?.items) ? page.items : []
      setItems((prev) => [...prev, ...list])
      setCursor(typeof page?.next === 'number' ? page.next : cursor + list.length)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить ленту')
    } finally {
      setLoading(false)
      busy.current = false
    }
  }, [cursor])

  // first page
  useEffect(() => {
    if (items.length === 0) void loadMore()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // infinite scroll
  useEffect(() => {
    const node = sentinel.current
    if (!node || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) void loadMore()
      },
      { rootMargin: '300px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [loadMore])

  return (
    <section className="stack" style={{ gap: 10 }}>
      <SectionTitle hint="бесконечно">Сейчас в тренде</SectionTitle>
      <p className="muted small" style={{ margin: 0 }}>
        Нишевые вещи из TikTok и Pinterest — листай, открывай ссылку и забирай.
      </p>

      <div className="feed">
        {items.map((item) => (
          <button
            key={item.sku}
            type="button"
            className="feed-card"
            onClick={() => openExternal(item.url)}
          >
            <div className="feed-photo">
              <img src={item.image_url} alt={item.name} loading="lazy" />
              <span className="feed-tag">{item.style}</span>
              <span className="feed-likes">♥ {item.likes}</span>
            </div>
            <div className="feed-name">{item.name}</div>
            <div className="feed-brand">{item.brand}</div>
            <div className="row-between">
              <strong style={{ fontSize: 13 }}>{formatRub(item.price_rub)}</strong>
              <span className="link-btn">купить</span>
            </div>
          </button>
        ))}
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div ref={sentinel} style={{ minHeight: 40 }} />
      {loading ? (
        <div className="row" style={{ justifyContent: 'center' }}>
          <div className="spinner" />
        </div>
      ) : null}
    </section>
  )
}
