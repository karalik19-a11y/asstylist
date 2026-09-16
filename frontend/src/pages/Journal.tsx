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

export function Journal() {
  const [issue, setIssue] = useState<JournalIssue | null>(null)
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState<JournalCategory | 'all'>('all')
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
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
    return () => {
      cancelled = true
    }
  }, [])

  const articles = useMemo(
    () => issue?.articles.filter((article) => category === 'all' || article.category === category) ?? [],
    [issue, category],
  )

  return (
    <main className="journal page-transition">
      <section className="journal-hero">
        <div className="journal-masthead">
          <span className="kicker">ASSTYLIST EDITORIAL</span>
          <span className="journal-issue">{issue ? `ВЫПУСК №${issue.issue}` : 'ЕЖЕНЕДЕЛЬНИК'}</span>
        </div>
        <div className="journal-title-row">
          <div>
            <h1>Журнал</h1>
            <p className="journal-deck">Мода, streetwear и то, что будет носиться завтра.</p>
          </div>
          {issue ? <div className="journal-dates">{formatDate(issue.week_start)} — {formatDate(issue.week_end)}</div> : null}
        </div>
        {issue?.lead ? <p className="journal-lead">{issue.lead}</p> : null}
        {issue?.trend_note ? (
          <div className="journal-note"><span>ТРЕНД-РАДАР</span><strong>{issue.trend_note}</strong></div>
        ) : null}
      </section>

      <div className="journal-tabs" role="tablist" aria-label="Разделы журнала">
        <button className={category === 'all' ? 'is-active' : ''} onClick={() => setCategory('all')}>Все</button>
        {CATEGORY_ORDER.map((id) => (
          <button key={id} className={category === id ? 'is-active' : ''} onClick={() => setCategory(id)}>
            {CATEGORY_LABELS[id]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="journal-loading"><span /> <span /> <span /></div>
      ) : error || !issue ? (
        <section className="journal-empty">
          <span className="kicker">EDITORIAL OFFLINE</span>
          <h2>Выпуск ещё собирается</h2>
          <p>Редакционный сборщик обновляет журнал раз в неделю. Попробуйте открыть раздел чуть позже.</p>
        </section>
      ) : (
        <section className="journal-feed">
          {articles.map((article, index) => (
            <article className={`journal-card ${index === 0 && category === 'all' ? 'journal-card-featured' : ''}`} key={article.id}>
              {article.image_url ? (
                <a className="journal-image" href={article.url} target="_blank" rel="noreferrer">
                  <img src={article.image_url} alt="" loading={index < 3 ? 'eager' : 'lazy'} />
                </a>
              ) : null}
              <div className="journal-card-body">
                <div className="journal-meta"><span>{CATEGORY_LABELS[article.category]}</span><time>{formatDate(article.published_at)}</time></div>
                <h2><a href={article.url} target="_blank" rel="noreferrer">{article.title}</a></h2>
                <p>{article.summary}</p>
                <div className="journal-footer"><span>{article.source}</span><a href={article.url} target="_blank" rel="noreferrer" aria-label="Открыть материал">↗</a></div>
              </div>
            </article>
          ))}
          {!articles.length ? <div className="journal-empty"><h2>В этом разделе пока тихо</h2><p>Следующий выпуск добавит новые материалы автоматически.</p></div> : null}
        </section>
      )}

      {issue ? <footer className="journal-footnote">Обновлено {new Date(issue.generated_at).toLocaleString('ru-RU')} · {issue.source_count} открытых источников</footer> : null}
    </main>
  )
}
