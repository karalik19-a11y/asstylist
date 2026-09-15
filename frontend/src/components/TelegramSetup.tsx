import { useState } from 'react'
import { api } from '../lib/api'
import { haptic, openTelegramLink } from '../lib/telegram'
import { Badge, SectionTitle, Spinner } from './ui'
import type { SetupResponse } from '../lib/types'

/**
 * Self-service Telegram wiring: paste a token from @BotFather, press the button,
 * and the backend attaches the Mini App to the bot (menu button + commands).
 */
export function TelegramSetup({ onConnected }: { onConnected?: (bot: SetupResponse['bot']) => void }) {
  const defaultUrl = typeof window === 'undefined' ? '' : window.location.origin
  const [token, setToken] = useState('')
  const [url, setUrl] = useState(defaultUrl)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState<SetupResponse | null>(null)

  const submit = async () => {
    setBusy(true)
    setError(null)
    try {
      const result = await api.connectBot(token.trim(), url.trim())
      setDone(result)
      haptic('success')
      onConnected?.(result.bot)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Не удалось подключить бота')
      haptic('error')
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <section className="card stack" style={{ gap: 10 }}>
        <SectionTitle hint="готово">Бот подключён</SectionTitle>
        <div className="row" style={{ gap: 8 }}>
          <Badge tone="ok">@{done.bot.username}</Badge>
          {done.demo_mode ? <Badge>демо-доступ в браузере сохранён</Badge> : null}
        </div>
        <div className="small">{done.next_step}</div>
        <ul className="reasons">
          {done.actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
        <div className="row" style={{ gap: 8 }}>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => openTelegramLink(`https://t.me/${done.bot.username}`)}>
            Открыть @{done.bot.username}
          </button>
        </div>
        <div className="muted tiny">
          Токен сохранён в .env на сервере (файл в .gitignore) и не показывается в интерфейсе.
        </div>
      </section>
    )
  }

  return (
    <section className="card stack" style={{ gap: 10 }}>
      <SectionTitle hint="1 минута">Подключить своего Telegram-бота</SectionTitle>
      <ol className="reasons" style={{ paddingLeft: 18 }}>
        <li>
          Откройте{' '}
          <button type="button" className="link-btn" onClick={() => openTelegramLink('https://t.me/BotFather')}>
            @BotFather
          </button>{' '}
          → /newbot → скопируйте токен.
        </li>
        <li>Вставьте токен и публичный https-адрес этого приложения.</li>
        <li>Нажмите «Подключить» — бот сам получит кнопку-приложение и команды.</li>
      </ol>

      <input
        className="btn"
        style={{ textAlign: 'left', fontWeight: 400 }}
        type="password"
        value={token}
        placeholder="123456:ABC-DEF..."
        aria-label="Токен бота"
        onChange={(event) => setToken(event.target.value)}
      />
      <input
        className="btn"
        style={{ textAlign: 'left', fontWeight: 400 }}
        type="url"
        value={url}
        placeholder="https://your-domain.example"
        aria-label="Web App URL"
        onChange={(event) => setUrl(event.target.value)}
      />

      {error ? <div className="error-box">{error}</div> : null}

      <button type="button" className="btn btn-primary" onClick={() => void submit()} disabled={busy || token.length < 10}>
        {busy ? (
          <>
            <Spinner /> Подключаем
          </>
        ) : (
          'Подключить'
        )}
      </button>
      <div className="muted tiny">
        Telegram принимает только публичные https-адреса: localhost не подойдёт.
      </div>
    </section>
  )
}
