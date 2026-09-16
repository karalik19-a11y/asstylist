import { useEffect, useMemo, useState } from 'react'

type JournalCategory = 'world' | 'russian-streetwear' | 'runway' | 'merch' | 'social-trends'

interface JournalArticle {
  id: string
  title: string
  summary: string
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
    return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(new Date(value))
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

  return (
    <main className="journal page-transition">
      <header className="journal-cover">
        <div className="journal-cover-top">
          <span className="journal-brand">ASSTYLIST<span className="journal-brand-dot">.</span></span>
          <span>EDITORIAL / WEEKLY</span>
          <span>{issue ? `№ ${issue.issue}` : '№ —'}</span>
        </div>
        <div className="journal-cover-rule" />
        <div className="journal-cover-title">
          <span className="journal-kicker">МОДА · STREETWEAR · CULTURE</span>
          <h1>ЖУРНАЛ</h1>
          <p>Что происходит в моде сейчас — и что начнёт происходить дальше.</p>
        </div>
        {lead?.image_url ? (
          <a className="journal-cover-image" href={lead.url} target="_blank" rel="noreferrer">
            <img src={lead.image_url} alt="" />
            <span className="journal-cover-caption">Обложка выпуска · {lead.source}</span>
          </a>
        ) : null}
        {issue?.lead ? <div className="journal-cover-lead">{issue.lead}</div> : null}
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
                  <button onClick={() => setCategory(section.id)}>СМОТРЕТЬ ВСЕ ↗</button>
                </div>
                <div className="journal-section-rule" />
                <div className="journal-section-grid">
                  {featured ? (
                    <article className="journal-story journal-story-main">
                      {featured.image_url ? <a className="journal-story-image" href={featured.url} target="_blank" rel="noreferrer"><img src={featured.image_url} alt="" loading={sectionIndex < 2 ? 'eager' : 'lazy'} /></a> : null}
                      <div className="journal-story-copy"><div className="journal-story-meta"><span>{featured.source}</span><time>{formatDate(featured.published_at)}</time></div><h3><a href={featured.url} target="_blank" rel="noreferrer">{featured.title}</a></h3><p>{shortText(featured.summary, 250)}</p></div>
                    </article>
                  ) : null}
                  <div className="journal-story-list">
                    {rest.slice(0, 3).map((article) => (
                      <article className="journal-story journal-story-small" key={article.id}>
                        {article.image_url ? <a className="journal-story-thumb" href={article.url} target="_blank" rel="noreferrer"><img src={article.image_url} alt="" loading="lazy" /></a> : null}
                        <div className="journal-story-copy"><div className="journal-story-meta"><span>{article.source}</span><time>{formatDate(article.published_at)}</time></div><h3><a href={article.url} target="_blank" rel="noreferrer">{article.title}</a></h3></div>
                      </article>
                    ))}
                  </div>
                </div>
              </section>
            )
          })}
          {issue.trend_note ? <aside className="journal-radar"><span>ASSTYLIST TREND RADAR</span><strong>{issue.trend_note}</strong></aside> : null}
        </div>
      ) : (
        <section className="journal-category-view">
          <div className="journal-category-heading"><span className="journal-kicker">SECTION</span><h2>{CATEGORY_LABELS[category]}</h2><p>{articles.length} материалов в выпуске</p></div>
          <div className="journal-category-grid">
            {articles.map((article, index) => (
              <article className={`journal-story ${index === 0 ? 'journal-story-category-feature' : ''}`} key={article.id}>
                {article.image_url ? <a className="journal-story-image" href={article.url} target="_blank" rel="noreferrer"><img src={article.image_url} alt="" loading={index < 3 ? 'eager' : 'lazy'} /></a> : null}
                <div className="journal-story-copy"><div className="journal-story-meta"><span>{article.source}</span><time>{formatDate(article.published_at)}</time></div><h3><a href={article.url} target="_blank" rel="noreferrer">{article.title}</a></h3><p>{shortText(article.summary, 240)}</p></div>
              </article>
            ))}
          </div>
        </section>
      )}

      {issue ? <footer className="journal-footnote">Выпуск {formatDate(issue.week_start)} — {formatDate(issue.week_end)} · обновлено {new Date(issue.generated_at).toLocaleString('ru-RU')} · {issue.source_count} открытых источников</footer> : null}
    </main>
  )
}
