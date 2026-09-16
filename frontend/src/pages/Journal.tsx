import { useEffect, useMemo, useState } from 'react'

type JournalCategory = 'world' | 'russian-streetwear' | 'runway' | 'merch' | 'social-trends'

interface JournalArticle {
  id: string
  title: string
  summary: string
  editorial?: string
  url: string
  source: string
  published_at: string
  category: JournalCategory
  image_url?: string | null
  tags?: string[]
}

interface JournalIssue {
  issue: number
  week_start: string
  week_end: string
  generated_at: string
  lead: string
  trend_note: string
  articles: JournalArticle[]
  source_count: number
}

const CATEGORY_LABELS: Record<JournalCategory, string> = {
  world: 'Мир моды',
  'russian-streetwear': 'Русский streetwear',
  runway: 'Показы',
  merch: 'Мерчи',
  'social-trends': 'Соцсети & тренды',
}

const CATEGORY_ORDER: JournalCategory[] = ['world', 'russian-streetwear', 'runway', 'merch', 'social-trends']

function formatDate(value: string) {
  try {
    return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(new Date(value))
  } catch {
    return value
  }
}

function shortText(value: string, max = 190) {
  const clean = value.replace(/<[^>]+>/g, '').trim()
  return clean.length > max ? `${clean.slice(0, max).trim()}…` : clean
}

export function Journal() {
  const [issue, setIssue] = useState<JournalIssue | null>(null)
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState<JournalCategory | 'all'>('all')
  const [selectedArticle, setSelectedArticle] = useState<JournalArticle | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetch('/journal.json', { cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error('journal unavailable')
        return response.json() as Promise<JournalIssue>
      })
      .then((data) => {
        if (!cancelled) setIssue(data)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!selectedArticle) return
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedArticle(null)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = previous
      window.removeEventListener('keydown', onKey)
    }
  }, [selectedArticle])

  const articles = useMemo(
    () => issue?.articles.filter((article) => category === 'all' || article.category === category) ?? [],
    [issue, category],
  )

  const sections = useMemo(() => {
    if (!issue) return []
    return CATEGORY_ORDER.map((id) => ({
      id,
      articles: issue.articles.filter((article) => article.category === id),
    })).filter((section) => section.articles.length > 0)
  }, [issue])

  const lead = articles[0]

  const openArticle = (article: JournalArticle) => setSelectedArticle(article)

  return (
    <main className="journal page-transition">
      <header className="journal-cover">
        <div className="journal-cover-top">
          <span className="journal-brand">ASSTYLIST<span className="journal-brand-dot">.</span></span>
          <span>THE FASHION EDIT</span>
          <span>ISSUE {issue ? issue.issue : '—'}</span>
        </div>
        <div className="journal-cover-rule" />
        <div className="journal-cover-title">
          <div>
            <span className="journal-kicker">МОДА · STREETWEAR · CULTURE</span>
            <h1>ЖУРНАЛ</h1>
          </div>
          <p>Еженедельный выпуск о вещах, людях и движениях, которые формируют стиль прямо сейчас.</p>
        </div>
        {lead?.image_url ? (
          <button className="journal-cover-image" onClick={() => openArticle(lead)} aria-label={`Открыть: ${lead.title}`}>
            <img src={lead.image_url} alt="" />
            <span className="journal-cover-image-shade" />
            <span className="journal-cover-image-label">COVER STORY / READ INSIDE ↗</span>
            <span className="journal-cover-caption">Фото: {lead.source}</span>
          </button>
        ) : null}
        <div className="journal-cover-lead">
          <span>В ЭТОМ НОМЕРЕ</span>
          <strong>{issue?.lead ?? 'Выпуск уже собирается.'}</strong>
        </div>
      </header>

      <nav className="journal-nav" aria-label="Разделы журнала">
        <button className={category === 'all' ? 'is-active' : ''} onClick={() => setCategory('all')}>ВСЕ</button>
        {CATEGORY_ORDER.map((id) => (
          <button key={id} className={category === id ? 'is-active' : ''} onClick={() => setCategory(id)}>
            {CATEGORY_LABELS[id]}
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="journal-loading"><span /><span /><span /></div>
      ) : error || !issue ? (
        <section className="journal-empty"><span className="journal-kicker">EDITORIAL OFFLINE</span><h2>Выпуск ещё собирается</h2><p>Следующий выпуск появится автоматически.</p></section>
      ) : category === 'all' ? (
        <div className="journal-sections">
          {sections.map((section, sectionIndex) => {
            const [featured, ...rest] = section.articles
            return (
              <section className="journal-section" key={section.id}>
                <div className="journal-section-head">
                  <div><span className="journal-section-index">0{sectionIndex + 1}</span><h2>{CATEGORY_LABELS[section.id]}</h2></div>
                  <button onClick={() => setCategory(section.id)}>ВСЯ РУБРИКА ↗</button>
                </div>
                <div className="journal-section-rule" />
                <div className="journal-section-grid">
                  {featured ? (
                    <article className="journal-story journal-story-main" onClick={() => openArticle(featured)} role="button" tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && openArticle(featured)}>
                      {featured.image_url ? <div className="journal-story-image"><img src={featured.image_url} alt="" loading={sectionIndex < 2 ? 'eager' : 'lazy'} /></div> : null}
                      <div className="journal-story-copy"><div className="journal-story-meta"><span>{featured.source}</span><time>{formatDate(featured.published_at)}</time></div><h3>{featured.title}</h3><p>{shortText(featured.editorial || featured.summary, 250)}</p><span className="journal-read">ЧИТАТЬ В ЖУРНАЛЕ ↗</span></div>
                    </article>
                  ) : null}
                  <div className="journal-story-list">
                    {rest.slice(0, 4).map((article, index) => (
                      <article className="journal-story journal-story-small" key={article.id} onClick={() => openArticle(article)} role="button" tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && openArticle(article)}>
                        <span className="journal-story-number">{String(index + 2).padStart(2, '0')}</span>
                        {article.image_url ? <div className="journal-story-thumb"><img src={article.image_url} alt="" loading="lazy" /></div> : <div className="journal-story-thumb journal-no-image">AS.</div>}
                        <div className="journal-story-copy"><div className="journal-story-meta"><span>{article.source}</span><time>{formatDate(article.published_at)}</time></div><h3>{article.title}</h3><span className="journal-read">ОТКРЫТЬ ↗</span></div>
                      </article>
                    ))}
                  </div>
                </div>
              </section>
            )
          })}
          {issue.trend_note ? <aside className="journal-radar"><span>ASSTYLIST / TREND RADAR</span><strong>{issue.trend_note}</strong></aside> : null}
        </div>
      ) : (
        <section className="journal-category-view">
          <div className="journal-category-heading"><span className="journal-kicker">EDITORIAL SECTION</span><h2>{CATEGORY_LABELS[category]}</h2><p>{articles.length} материалов · выпуск {issue.issue}</p></div>
          <div className="journal-category-grid">
            {articles.map((article, index) => (
              <article className={`journal-story ${index === 0 ? 'journal-story-category-feature' : ''}`} key={article.id} onClick={() => openArticle(article)} role="button" tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && openArticle(article)}>
                {article.image_url ? <div className="journal-story-image"><img src={article.image_url} alt="" loading={index < 3 ? 'eager' : 'lazy'} /></div> : <div className="journal-story-image journal-no-image">ASSTYLIST</div>}
                <div className="journal-story-copy"><div className="journal-story-meta"><span>{article.source}</span><time>{formatDate(article.published_at)}</time></div><h3>{article.title}</h3><p>{shortText(article.editorial || article.summary, 240)}</p><span className="journal-read">ЧИТАТЬ В ЖУРНАЛЕ ↗</span></div>
              </article>
            ))}
          </div>
        </section>
      )}

      {issue ? <footer className="journal-footnote">ASSTYLIST EDITORIAL · {formatDate(issue.week_start)} — {formatDate(issue.week_end)} · {issue.source_count} открытых потоков</footer> : null}

      {selectedArticle ? (
        <div className="journal-reader" role="dialog" aria-modal="true" aria-label={selectedArticle.title} onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedArticle(null) }}>
          <article className="journal-reader-sheet">
            <button className="journal-reader-close" onClick={() => setSelectedArticle(null)} aria-label="Закрыть">×</button>
            <div className="journal-reader-top"><span>{CATEGORY_LABELS[selectedArticle.category]}</span><span>{formatDate(selectedArticle.published_at)}</span><span>{selectedArticle.source}</span></div>
            {selectedArticle.image_url ? <div className="journal-reader-image"><img src={selectedArticle.image_url} alt="" /></div> : null}
            <div className="journal-reader-body">
              <span className="journal-kicker">ASSTYLIST EDITORIAL / {selectedArticle.source}</span>
              <h2>{selectedArticle.title}</h2>
              <div className="journal-reader-columns">
                <p className="journal-reader-dropcap">{(selectedArticle.editorial || selectedArticle.summary).charAt(0)}</p>
                <div>
                  <p className="journal-reader-text">{selectedArticle.editorial || selectedArticle.summary}</p>
                  <p className="journal-reader-note">Это редакционная выжимка из открытого материала. ASStylist не подменяет оригинал: факты и полный контекст доступны у первоисточника.</p>
                </div>
              </div>
              <a className="journal-source-button" href={selectedArticle.url} target="_blank" rel="noreferrer">ПЕРЕЙТИ К ПЕРВОИСТОЧНИКУ ↗</a>
            </div>
          </article>
        </div>
      ) : null}
    </main>
  )
}
