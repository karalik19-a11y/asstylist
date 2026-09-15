import { useEffect, useId, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { formatRub } from '../lib/format'

export type IconName = 'spark' | 'star' | 'heart' | 'shield' | 'camera' | 'bolt'

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const box = { width: size, height: size, viewBox: '0 0 24 24' }
  switch (name) {
    case 'spark':
      return (
        <svg {...box} fill="currentColor" aria-hidden="true">
          <path d="M12 3l1.7 5 5 1.7-5 1.7-1.7 5-1.7-5-5-1.7 5-1.7z" />
          <path d="M19 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
        </svg>
      )
    case 'star':
      return (
        <svg {...box} fill="currentColor" aria-hidden="true">
          <path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8L3.5 9.7l5.9-.8z" />
        </svg>
      )
    case 'heart':
      return (
        <svg {...box} fill="currentColor" aria-hidden="true">
          <path d="M12 20.2C7.6 16.7 3.6 13.3 3.6 9.5c0-2.4 1.8-4.2 4.1-4.2 1.6 0 3.1.9 4.3 2.3 1.1-1.4 2.6-2.3 4.3-2.3 2.3 0 4.1 1.8 4.1 4.2 0 3.8-4 7.2-8.4 10.7z" />
        </svg>
      )
    case 'shield':
      return (
        <svg {...box} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 3.5l6.5 2.6v4.6c0 4.2-2.8 7.9-6.5 9.3-3.7-1.4-6.5-5.1-6.5-9.3V6.1z" />
          <path d="M9.2 11.8l2.1 2.1 3.6-3.9" />
        </svg>
      )
    case 'camera':
      return (
        <svg {...box} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3.5" y="7.5" width="17" height="11.5" rx="3" />
          <circle cx="12" cy="13.2" r="3.2" />
          <path d="M9 7.5L10.3 5h3.4L15 7.5" />
        </svg>
      )
    case 'bolt':
      return (
        <svg {...box} fill="currentColor" aria-hidden="true">
          <path d="M13 2L4.5 13.5H11L9.5 22 19 10h-6.5L13 2z" />
        </svg>
      )
  }
}

/** Круговой почтовый штемпель с медленно вращающейся надписью (декор). */
export function Postmark({ size = 84, text = 'ASSTYLIST • FIRST CLASS • ' }: { size?: number; text?: string }) {
  const id = useId()
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className="postmark-spin" aria-hidden="true">
      <defs>
        <path id={id} d="M50,50 m-35,0 a35,35 0 1,1 70,0 a35,35 0 1,1 -70,0" />
      </defs>
      <circle cx="50" cy="50" r="47" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3" />
      <text fontSize="11" letterSpacing="2.2" fill="currentColor" fontFamily="'Special Elite', monospace">
        <textPath href={`#${id}`}>{text}</textPath>
      </text>
      <text x="50" y="56" textAnchor="middle" fontSize="17" fill="currentColor">
        ★
      </text>
    </svg>
  )
}

function useCountUp(target: number, duration = 900): number {
  const [value, setValue] = useState(0)
  useEffect(() => {
    let raf = 0
    const started = performance.now()
    const tick = (now: number) => {
      const progress = Math.min(1, (now - started) / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(target * eased))
      if (progress < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  return value
}

export function Reveal({
  children,
  delay = 0,
  className = '',
  style,
}: {
  children: ReactNode
  delay?: number
  className?: string
  style?: CSSProperties
}) {
  return (
    <div className={`reveal ${className}`} style={{ ...style, ['--d' as string]: `${delay}s` }}>
      {children}
    </div>
  )
}

export function Header({ title, subtitle, onBack, right }: { title: string; subtitle?: string; onBack?: () => void; right?: ReactNode }) {
  return (
    <header className="stack" style={{ gap: 10 }}>
      <div className="topbar">
        {onBack ? (
          <button className="back-btn" onClick={onBack} aria-label="Назад">
            ←
          </button>
        ) : null}
        <div className="topbar-logo">
          <span className="dot" aria-hidden="true" />
          <span><span style={{ color: 'var(--red)' }}>ASS</span>tylist</span>
        </div>
        <div style={{ marginLeft: 'auto' }}>{right}</div>
      </div>
      <div className="stack" style={{ gap: 4, paddingTop: 2 }}>
        <h2>{title}</h2>
        {subtitle ? <div className="muted small">{subtitle}</div> : null}
      </div>
    </header>
  )
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="progress" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${Math.max(6, Math.round(value * 100))}%` }} />
    </div>
  )
}

export function StepDots({ total, current }: { total: number; current: number }) {
  return (
    <div className="step-dots" aria-hidden="true">
      {Array.from({ length: total }, (_, i) => (
        <span key={i} className={`step-dot${i < current ? ' done' : i === current ? ' now' : ''}`} />
      ))}
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
  title,
  description,
  index = 0,
}: {
  active: boolean
  onClick: () => void
  title: string
  description?: string
  index?: number
}) {
  return (
    <button
      type="button"
      className="tile"
      data-active={active}
      onClick={onClick}
      aria-pressed={active}
      style={{ ['--d' as string]: `${Math.min(index, 8) * 0.06}s` }}
    >
      <span className="tile-num">{String(index + 1).padStart(2, '0')}</span>
      <strong>{title}</strong>
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
  const fill = max > min ? ((value - min) / (max - min)) * 100 : 0
  return (
    <div className="range-field">
      <div className="row-between">
        <span className="tiny">{label}</span>
        <span className="range-value">
          {value} <span style={{ fontSize: 16, color: 'var(--muted)' }}>{suffix}</span>
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-label={label}
        style={{ ['--fill' as string]: `${fill}%` }}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      {hint ? <span className="muted small">{hint}</span> : null}
    </div>
  )
}

export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'ok' | 'warn' | 'bad' | 'pop'; children: ReactNode }) {
  const className = tone === 'neutral' ? 'badge' : tone === 'pop' ? 'badge badge-pop' : `badge badge-${tone}`
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

export function ScoreRing({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score))
  const shown = useCountUp(clamped)
  return (
    <div className="score-ring" aria-label={`Оценка образа ${Math.round(clamped)} из 100`}>
      <b>{shown}</b>
      <span>из 100</span>
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

export function SectionTitle({ children, hint, index }: { children: ReactNode; hint?: string; index?: string }) {
  return (
    <div className="section-head">
      <h3>
        {index ? <span className="sec-num">{index}</span> : null}
        {children}
      </h3>
      {hint ? <span className="muted small" style={{ whiteSpace: 'nowrap' }}>{hint}</span> : null}
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

export function Loader({ text }: { text?: string }) {
  return (
    <div className="loading-center">
      <div className="ring-loader" aria-hidden="true" />
      {text ? <div className="small">{text}</div> : null}
    </div>
  )
}
