import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { isTelegram, telegramUserName, telegramUserPhoto, telegramUsername } from '../lib/telegram'
import { playClick, playSuccess } from '../lib/sound'

type UserCard = {
  id: number
  telegram_id: string
  username: string | null
  first_name: string | null
  is_demo: boolean
  signature_color: string | null
  registered: boolean
}

export function Profile() {
  const [user, setUser] = useState<UserCard | null>(null)
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const tgName = telegramUserName()
  const tgUser = telegramUsername()
  const photo = telegramUserPhoto()

  const displayName =
    tgName ||
    user?.first_name ||
    (user?.username && user.username !== 'demo_user' ? user.username : null) ||
    tgUser ||
    (isTelegram() ? 'Telegram' : 'Гость')

  const handle =
    tgUser ||
    (user?.username && user.username !== 'demo_user' ? user.username : null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .profile()
      .then((res) => {
        if (!cancelled && res.user) setUser(res.user)
      })
      .catch(() => {
        if (!cancelled)
          setUser({
            id: 0,
            telegram_id: '',
            username: tgUser,
            first_name: tgName,
            is_demo: !isTelegram(),
            signature_color: null,
            registered: false,
          })
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [tgName, tgUser])

  const onRegister = async () => {
    playClick()
    setRegistering(true)
    setError(null)
    try {
      const res = await api.registerProfile()
      setUser(res.user)
      playSuccess()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось зарегистрироваться')
    } finally {
      setRegistering(false)
    }
  }

  const color = user?.signature_color

  return (
    <div className="stack page-transition" style={{ gap: 22 }}>
      <div className="step-heading">
        <h2>Личный кабинет</h2>
        <div className="muted small">профиль и персональный цвет-ID</div>
      </div>

      <section className="card stack profile-card" style={{ gap: 20 }}>
        <div className="profile-identity">
          <div
            className={`profile-avatar${color ? ' profile-avatar-glow' : ''}`}
            style={
              color
                ? {
                    ['--sig-color' as string]: color,
                    boxShadow: `0 0 0 3px ${color}, 0 0 18px color-mix(in srgb, ${color} 55%, transparent), 0 10px 24px rgba(0,0,0,0.25)`,
                  }
                : undefined
            }
          >
            {photo ? (
              <img src={photo} alt="" />
            ) : (
              <span className="profile-avatar-fallback">{(displayName || '?').slice(0, 1).toUpperCase()}</span>
            )}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <strong className="profile-name">{loading ? '…' : displayName}</strong>
            {handle ? (
              <div className="profile-handle">@{handle}</div>
            ) : (
              <div className="muted small">{isTelegram() ? 'Telegram' : 'браузерная сессия'}</div>
            )}
          </div>
        </div>

        {user?.registered && color ? (
          <div className="profile-color-block">
            <div className="tiny">Ваш персональный цвет</div>
            <div className="profile-color-row">
              <span className="profile-color-swatch" style={{ background: color }} />
              <code className="profile-color-hex">{color.toUpperCase()}</code>
            </div>
            <p className="muted small" style={{ margin: 0 }}>
              Неизменяемый цвет-ID: выдаётся один раз при регистрации.
            </p>
          </div>
        ) : (
          <div className="stack" style={{ gap: 12 }}>
            <p className="muted" style={{ margin: 0, fontSize: 15.5, lineHeight: 1.55 }}>
              Зарегистрируйтесь, чтобы получить уникальный персональный цвет — постоянный
              идентификатор в сервисе.
            </p>
            <button
              type="button"
              className="btn btn-primary btn-block"
              disabled={registering || loading}
              onClick={() => void onRegister()}
            >
              {registering ? 'Регистрируем…' : 'Регистрация'}
            </button>
          </div>
        )}

        {error ? <div className="error-box">{error}</div> : null}
      </section>
    </div>
  )
}
