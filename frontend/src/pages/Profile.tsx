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

  const photo = telegramUserPhoto()
  const displayName =
    user?.first_name || telegramUserName() || user?.username || telegramUsername() || 'Гость'

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
            username: telegramUsername(),
            first_name: telegramUserName(),
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
  }, [])

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

  return (
    <div className="stack page-transition" style={{ gap: 20 }}>
      <div className="step-heading">
        <h2>Личный кабинет</h2>
        <div className="muted small">профиль и персональный цвет-ID</div>
      </div>

      <section className="card stack profile-card" style={{ gap: 18 }}>
        <div className="profile-identity">
          <div
            className="profile-avatar"
            style={{
              background: user?.signature_color
                ? `linear-gradient(145deg, ${user.signature_color}, color-mix(in srgb, ${user.signature_color} 55%, #111))`
                : 'var(--surface-2)',
              boxShadow: user?.signature_color
                ? `0 0 0 3px color-mix(in srgb, ${user.signature_color} 45%, transparent), 0 12px 28px rgba(0,0,0,0.18)`
                : undefined,
            }}
          >
            {photo ? (
              <img src={photo} alt="" />
            ) : (
              <span className="profile-avatar-fallback">{(displayName || '?').slice(0, 1).toUpperCase()}</span>
            )}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <strong style={{ fontSize: 20 }}>{loading ? '…' : displayName}</strong>
            {user?.username || telegramUsername() ? (
              <div className="muted small">@{user?.username || telegramUsername()}</div>
            ) : (
              <div className="muted small">{isTelegram() ? 'Telegram' : 'браузерный гость'}</div>
            )}
          </div>
        </div>

        {user?.registered && user.signature_color ? (
          <div className="profile-color-block">
            <div className="tiny">Ваш персональный цвет</div>
            <div className="profile-color-row">
              <span className="profile-color-swatch" style={{ background: user.signature_color }} />
              <code className="profile-color-hex">{user.signature_color.toUpperCase()}</code>
            </div>
            <p className="muted small" style={{ margin: 0 }}>
              Это ваш неизменяемый цвет-ID. Он выдаётся один раз при регистрации и больше не меняется.
            </p>
          </div>
        ) : (
          <div className="stack" style={{ gap: 12 }}>
            <p className="muted" style={{ margin: 0, fontSize: 15, lineHeight: 1.5 }}>
              Зарегистрируйтесь, чтобы получить уникальный персональный цвет — он станет вашим постоянным
              идентификатором в сервисе.
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
