import type { ReactNode } from 'react'
import { formatRub } from '../lib/format'

export function Header({ title, subtitle, onBack, right }: { title: string; subtitle?: string; onBack?: () => void; right?: ReactNode }) {
  return (
    <header className="row-between">
      <div className="row" style={{ gap: 12, minWidth: 0 }}>
        {onBack ? (
          <button className="btn btn-sm btn-ghost" onClick={onBack} aria-label="Назад">
            ←
          </button>
        ) : null}
        <div style={{ minWidth: 0 }}>
          <h2 style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</h2>
          {subtitle ? <div className="muted small">{subtitle}</div> : null}
        </div>
      </div>
      {right}
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
    <button type="button" className="chip" data-active={active} onClick={onClick} aria-pressed={active}>
      {children}
    </button>
  )
}

export function Tile({
  active,
  onClick,
  emoji,
  title,
  description,
}: {
  active: boolean
  onClick: () => void
  emoji?: string
  title: string
  description?: string
}) {
  return (
    <button type="button" className="tile" data-active={active} onClick={onClick} aria-pressed={active}>
      {emoji ? <span className="tile-emoji">{emoji}</span> : null}
      <strong style={{ fontSize: 14 }}>{title}</strong>
      {description ? <span className="tile-desc">{description}</span> : null}
    </button>
  )
}

export function RangeField({
  label,
  value,
  min,
  max,
  step = 1,
  suffix,
  onChange,
  hint,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  suffix: string
  onChange: (value: number) => void
  hint?: string
}) {
  return (
    <div className="range-field">
      <div className="row-between">
        <span className="tiny">{label}</span>
        <span className="range-value">
          {value} {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-label={label}
        onChange={(event) => onChange(Number(event.target.value))}
      />
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
  if (status === 'warning') return 'warn'
  return 'bad'
}

export function verificationLabel(status: string): string {
  if (status === 'verified') return 'проверено'
  if (status === 'warning') return 'требует внимания'
  if (status === 'failed') return 'не проверено'
  return status
}

function scoreColor(score: number): string {
  if (score >= 88) return 'var(--ok)'
  if (score >= 70) return 'var(--accent)'
  return 'var(--warn)'
}

export function ScoreRing({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score))
  const color = scoreColor(clamped)
  return (
    <div
      className="score-ring"
      style={{
        background: `conic-gradient(${color} ${clamped * 3.6}deg, var(--surface-2) 0deg)`,
        boxShadow: 'inset 0 0 0 6px var(--surface)',
        color,
      }}
      aria-label={`Оценка образа ${Math.round(clamped)} из 100`}
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
        <span>
          {formatRub(total)} из {formatRub(budget)}
        </span>
        <span>{left > 0 ? `остаток ${formatRub(left)}` : 'бюджет выбран полностью'}</span>
      </div>
    </div>
  )
}

export function SectionTitle({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <div className="row-between">
      <h3>{children}</h3>
      {hint ? <span className="muted small">{hint}</span> : null}
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}
