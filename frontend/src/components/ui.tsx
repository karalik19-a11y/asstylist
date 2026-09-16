import { useState, type ReactNode } from 'react'
import { formatRub } from '../lib/format'
import { isSoundEnabled, playClick, playTick, toggleSound } from '../lib/sound'
import { SoundIcon } from '../lib/graphics'

export function BrandLogo({
  onHome,
  big = false,
  tagline = false,
}: {
  onHome: () => void
  big?: boolean
  tagline?: boolean
}) {
  return (
    <button
      type="button"
      className={big ? 'brand-logo brand-logo-big' : 'brand-logo'}
      onClick={() => {
        playClick()
        onHome()
      }}
      aria-label="ASStylist — на главную"
      title="На главную"
    >
      <span className="brand-logo-text">
        <span className="brand-logo-word" aria-hidden="true">
          AS<em>Stylist</em>
        </span>
        <span className="brand-logo-rule" aria-hidden="true" />
        {tagline ? (
          <span className="brand-logo-tagline" aria-hidden="true">
            персональный стилист из настоящих вещей
          </span>
        ) : null}
      </span>
    </button>
  )
}

export function Header({
  title,
  subtitle,
  onBack,
  onHome,
  right,
  compact = false,
}: {
  title: string
  subtitle?: string
  onBack?: () => void
  onHome?: () => void
  right?: ReactNode
  compact?: boolean
}) {
  const [soundOn, setSoundOn] = useState(() => isSoundEnabled())

  const handleSoundToggle = () => {
    const next = toggleSound()
    setSoundOn(next)
  }

  return (
    <header className={`stack app-header${compact ? ' compact' : ''}`} style={{ gap: compact ? 0 : 10 }}>
      <div className="row-between" style={{ alignItems: 'center' }}>
        <div className="row" style={{ gap: 10, minWidth: 0, flex: 1 }}>
          {onBack ? (
            <button
              type="button"
              className="btn btn-sm btn-outline"
              onClick={() => {
                playClick()
                onBack()
              }}
              aria-label="Назад"
              style={{ minHeight: 42, minWidth: 46, padding: '8px 14px', fontSize: 16 }}
            >
              ←
            </button>
          ) : null}
          {onHome ? (
            <BrandLogo onHome={onHome} />
          ) : (
            <div className="kicker" style={{ flexShrink: 0 }}>
              ASStylist
            </div>
          )}
        </div>

        <div className="row" style={{ gap: 10, flexShrink: 0 }}>
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={handleSoundToggle}
            aria-label={soundOn ? 'Выключить звук' : 'Включить звук'}
            title={soundOn ? 'Звук: включён' : 'Звук: выключен'}
            style={{ padding: '8px 10px', minHeight: 42, minWidth: 44 }}
          >
            <SoundIcon enabled={soundOn} size={18} />
          </button>
          {right}
        </div>
      </div>

      {!compact ? (
        <div className="app-header-title-block" style={{ paddingBottom: 2, minWidth: 0 }}>
          <h2 className="app-header-title">{title}</h2>
          {subtitle ? <div className="muted small" style={{ marginTop: 4 }}>{subtitle}</div> : null}
        </div>
      ) : null}
    </header>
  )
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="progress" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${Math.max(4, Math.round(value * 100))}%` }} />
    </div>
  )
}

export function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" className="chip" data-active={active} onClick={() => { playTick(); onClick() }} aria-pressed={active}>
      {children}
    </button>
  )
}

export function Tile({
  active, onClick, badgeKanji, badgeNum, title, description,
}: {
  active: boolean; onClick: () => void; badgeKanji?: string; badgeNum?: string; title: string; description?: string
}) {
  return (
    <button type="button" className="stamp-tile" data-active={active} onClick={() => { playClick(); onClick() }} aria-pressed={active}>
      <div className="stamp-tile-top">
        {badgeKanji ? <span className="stamp-tile-kanji">{badgeKanji}</span> : <span />}
        {badgeNum ? <span className="stamp-tile-badge">№ {badgeNum}</span> : null}
      </div>
      <strong className="stamp-tile-title">{title}</strong>
      {description ? <span className="stamp-tile-desc">{description}</span> : null}
    </button>
  )
}

export function RangeField({
  label, value, min, max, step = 1, suffix, onChange, hint,
}: {
  label: string; value: number; min: number; max: number; step?: number; suffix: string; onChange: (value: number) => void; hint?: string
}) {
  return (
    <div className="range-field">
      <div className="row-between">
        <span className="tiny">{label}</span>
        <span className="range-value">{value} {suffix}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} aria-label={label} onChange={(e) => onChange(Number(e.target.value))} />
      {hint ? <span className="muted small">{hint}</span> : null}
    </div>
  )
}

export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'ok' | 'warn' | 'bad'; children: ReactNode }) {
  const className = tone === 'neutral' ? 'badge' : `badge badge-${tone}`
  return <span className={className}>{children}</span>
}

export function verificationTone(status: string): 'ok' | 'warn' | 'bad' {
  if (status === 'verified') return 'ok'
  if (status === 'warning' || status === 'external') return 'warn'
  return 'bad'
}

export function verificationLabel(status: string): string {
  if (status === 'verified') return 'проверено'
  if (status === 'warning') return 'внимание'
  if (status === 'failed') return 'не проверено'
  if (status === 'external') return 'Авито'
  return status
}

export function isAvitoUrl(url: string | undefined): boolean {
  if (!url) return false
  try {
    const host = new URL(url, 'https://asstylist.local').hostname.toLowerCase()
    return host === 'avito.ru' || host.endsWith('.avito.ru')
  } catch {
    return url.includes('avito.ru')
  }
}

function scoreColor(score: number): string {
  if (score >= 88) return 'var(--ok)'
  if (score >= 70) return 'var(--accent-leopard)'
  return 'var(--warn)'
}

export function ScoreRing({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score))
  const color = scoreColor(clamped)
  return (
    <div
      className="score-ring"
      style={{
        background:
          `radial-gradient(circle at 50% 50%, rgba(8, 20, 31, 0.62) 0 57%, rgba(8, 20, 31, 0) 59%), ` +
          `conic-gradient(${color} ${clamped * 3.6}deg, var(--surface-2) 0deg)`,
        boxShadow: 'inset 0 0 0 6px var(--surface), 0 10px 24px rgba(23, 68, 99, 0.18)',
      }}
      aria-label={`Оценка ${Math.round(clamped)} из 100`}
    >
      {Math.round(clamped)}
    </div>
  )
}

export function BudgetBar({ total, budget }: { total: number; budget: number }) {
  const share = budget > 0 ? Math.min(1, total / budget) : 0
  const left = Math.max(0, budget - total)
  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="budget-bar">
        <span style={{ width: `${share * 100}%` }} />
      </div>
      <div className="row-between small muted">
        <span>{formatRub(total)} из {formatRub(budget)}</span>
        <span>{left > 0 ? `остаток ${formatRub(left)}` : 'полный бюджет'}</span>
      </div>
    </div>
  )
}

export function SectionTitle({ children, hint, index }: { children: ReactNode; hint?: string; index?: string }) {
  return (
    <div className="section-head">
      <h3>
        {index ? (<><span className="sec-num">№ {index}</span>{children}</>) : children}
      </h3>
      {hint ? <span className="section-head-hint muted small">{hint}</span> : null}
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

export function ThemeToggle({ theme, onToggle }: { theme: 'noir' | 'parchment'; onToggle: () => void }) {
  return (
    <button type="button" className="btn btn-sm btn-ghost" onClick={onToggle} style={{ padding: '8px 14px', minHeight: 42, fontSize: 13 }} title="Переключить тему">
      {theme === 'noir' ? 'Светлая' : 'Тёмная'}
    </button>
  )
}
