import { useState } from 'react'
import { api } from '../lib/api'
import { haptic, openTelegramLink } from '../lib/telegram'
import { Badge, SectionTitle, Spinner } from './ui'
import type { SetupResponse } from '../lib/types'

interface TelegramSetupStatus {
  configured: boolean
  web_app_url: string | null
  bot_link: string | null
}

function usernameFromLink(link: string | null): string | null {
  if (!link) return null
  const match = link.match(/t\.me\/([A-Za-z0-9_]+)/)
  return match ? match[1] : null
}

/**
 * Self-service Telegram wiring — always visible:
 *  - no bot yet  → straight to the token form;
 *  - bot attached → status card with a way to switch the bot (token form).
 */
export function TelegramSetup({
  status,
  onConnected,
}: {
  status?: TelegramSetupStatus
  onConnected?: (bot: SetupResponse['bot']) => void
}) {
  const alreadyConfigured = status?.configured ?? false
  const currentBot = usernameFromLink(status?.bot_link ?? null)
  const defaultUrl = typeof window === 'undefined' ? '' : window.location.origin
  const [view, setView] = useState<'status' | 'form'>(alreadyConfigured ? 'status' : 'form')
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
      <section className="classified">
        <SectionTitle hint="готово">Бот подключён</SectionTitle>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <Badge tone="ok">@{done.bot.username}</Badge>
          {done.demo_mode ? <Badge>демо-доступ в браузере сохранён</Badge> : null}
        </div>
        <div className="small">{done.next_step}</div>
        <ul className="reasons">
          {done.actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => openTelegramLink(`https://t.me/${done.bot.username}`)}>
            Открыть @{done.bot.username}
          </button>
        </div>
        <div className="muted tiny">
          Токен сохранён на сервере (файл в .gitignore) и не показывается в интерфейсе.
        </div>
      </section>
    )
  }

  if (view === 'status' && alreadyConfigured) {
    return (
      <section className="classified">
        <SectionTitle hint="свой телеграм">Бот уже подключён</SectionTitle>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          {currentBot ? <Badge tone="ok">@{currentBot}</Badge> : null}
          {status?.web_app_url ? <Badge>{status.web_app_url}</Badge> : null}
        </div>
        <div className="small muted">
          Кнопка-приложение уже закреплена в меню бота. Хотите переключиться на другой бот?
        </div>
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          {currentBot ? (
            <button type="button" className="btn btn-sm" onClick={() => openTelegramLink(`https://t.me/${currentBot}`)}>
              Открыть @{currentBot}
            </button>
          ) : null}
          <button type="button" className="btn btn-sm btn-primary" onClick={() => setView('form')}>
            Подключить другой бот
          </button>
        </div>
        <div className="muted tiny">
          Токен хранится на сервере и нигде не отображается.
        </div>
      </section>
    )
  }

  return (
    <section className="classified">
      <SectionTitle hint={alreadyConfigured ? 'замена бота' : '1 минута'}>
        Подключить своего Telegram-бота
      </SectionTitle>
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

      <label className="tiny" style={{ display: 'block', marginBottom: -6 }} htmlFor="bot-token">
        Токен бота
      </label>
      <input
        id="bot-token"
        className="token-input"
        type="password"
        value={token}
        placeholder="123456:ABC-DEF..."
        aria-label="Токен бота"
        autoComplete="off"
        onChange={(event) => setToken(event.target.value)}
      />
      <label className="tiny" style={{ display: 'block', marginBottom: -6 }} htmlFor="bot-url">
        Web App URL
      </label>
      <input
        id="bot-url"
        className="token-input"
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
