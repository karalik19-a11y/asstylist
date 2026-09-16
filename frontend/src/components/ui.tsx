import { useState, type ReactNode } from 'react'
import { formatRub } from '../lib/format'
import { isSoundEnabled, playClick, playTick, toggleSound } from '../lib/sound'
import { SoundIcon } from '../lib/graphics'
import { DevilA } from './DevilA'
export { DevilA } from './DevilA'

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
    <button type="button" className={big ? 'brand-logo brand-logo-big' : 'brand-logo'} onClick={() => { playClick(); onHome() }} aria-label="ASStylist — на главную" title="На главную">
      <span className="brand-logo-text">
        <span className="brand-logo-word" aria-hidden="true">
          <span className="brand-logo-ass"><DevilA /><span>SS</span></span>
          <em>tylist</em>
        </span>
        <span className="brand-logo-rule" aria-hidden="true" />
        {tagline ? <span className="brand-logo-tagline" aria-hidden="true">персональный стилист из настоящих вещей</span> : null}
      </span>
    </button>
  )
}

export function Header({
  title, subtitle, onBack, onHome, right, compact = false,
}: {
  title: string
  subtitle?: string
  onBack?: () => void
  onHome?: () => void
  right?: ReactNode
  compact?: boolean
}) {
  return (
    <header className={`stack app-header${compact ? ' compact' : ''}`} style={{ gap: compact ? 0 : 10 }}>
      <div className="row-between header-main-row" style={{ alignItems: 'center' }}>
        <div className="row header-main-left" style={{ gap: 8, minWidth: 0, flex: 1 }}>
          {onBack ? <button type="button" className="btn btn-sm btn-outline header-back" onClick={() => { playClick(); onBack() }} aria-label="Назад">←</button> : null}
          {onHome ? <BrandLogo onHome={onHome} /> : <div className="kicker header-kicker">ASStylist</div>}
        </div>
        <div className="row header-controls"><SoundToggle />{right}</div>
      </div>
      {!compact ? <div className="app-header-title-block" style={{ paddingBottom: 2, minWidth: 0 }}><h2 className="app-header-title">{title}</h2>{subtitle ? <div className="muted small" style={{ marginTop: 4 }}>{subtitle}</div> : null}</div> : null}
    </header>
  )
}

export function SoundToggle() {
  const [soundOn, setSoundOn] = useState(() => isSoundEnabled())
  return <button type="button" className="header-control header-control-icon" onClick={() => setSoundOn(toggleSound())} aria-label={soundOn ? 'Выключить звук' : 'Включить звук'} title={soundOn ? 'Звук: включён' : 'Звук: выключен'}><SoundIcon enabled={soundOn} size={16} /></button>
}

export function ProgressBar({ value }: { value: number }) {
  return <div className="progress" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${Math.max(4, Math.round(value * 100))}%` }} /></div>
}

export function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return <button type="button" className="chip" data-active={active} onClick={() => { playTick(); onClick() }} aria-pressed={active}>{children}</button>
}

export function Tile({ active, onClick, badgeKanji, badgeNum, title, description }: { active: boolean; onClick: () => void; badgeKanji?: string; badgeNum?: string; title: string; description?: string }) {
  return <button type="button" className="stamp-tile" data-active={active} onClick={() => { playClick(); onClick() }} aria-pressed={active}><div className="stamp-tile-top">{badgeKanji ? <span className="stamp-tile-kanji">{badgeKanji}</span> : <span />}{badgeNum ? <span className="stamp-tile-badge">№ {badgeNum}</span> : null}</div><strong className="stamp-tile-title">{title}</strong>{description ? <span className="stamp-tile-desc">{description}</span> : null}</button>
}

export function RangeField({ label, value, min, max, step = 1, suffix, onChange, hint }: { label: string; value: number; min: number; max: number; step?: number; suffix: string; onChange: (value: number) => void; hint?: string }) {
  return <div className="range-field"><div className="row-between"><span className="tiny">{label}</span><span className="range-value">{value} {suffix}</span></div><input type="range" min={min} max={max} step={step} value={value} aria-label={label} onChange={(e) => onChange(Number(e.target.value))} />{hint ? <span className="muted small">{hint}</span> : null}</div>
}

export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'ok' | 'warn' | 'bad'; children: ReactNode }) {
  const className = tone === 'neutral' ? 'badge' : `badge badge-${tone}`
  return <span className={className}>{children}</span>
}

export function verificationTone(status: string): 'ok' | 'warn' | 'bad' { if (status === 'verified') return 'ok'; if (status === 'review') return 'warn'; return 'bad' }

export function ScoreRing({ score }: { score: number }) {
  const value = Math.max(0, Math.min(100, Math.round(score)))
  return <div className="score-ring" aria-label={`Оценка ${value} из 100`}><strong>{value}</strong><span>/100</span></div>
}

export function BudgetBar({ spent, budget }: { spent: number; budget: number }) {
  const pct = budget > 0 ? Math.min(100, Math.round((spent / budget) * 100)) : 0
  return <div className="budget-bar" aria-label={`Потрачено ${formatRub(spent)} из ${formatRub(budget)}`}><span style={{ width: `${pct}%` }} /></div>
}

export function SectionTitle({ children, action, index, hint }: { children: ReactNode; action?: ReactNode; index?: string; hint?: string }) {
  return <div className="row-between section-title"><div style={{ minWidth: 0 }}><h3>{children}</h3>{index || hint ? <div className="muted small section-title-meta">{index ? `${index}${hint ? ' · ' : ''}` : ''}{hint ?? ''}</div> : null}</div>{action}</div>
}

export function Spinner() { return <span className="spinner" aria-label="Загрузка" /> }

export function isAvitoUrl(url: string): boolean {
  try { return new URL(url).hostname.toLowerCase().endsWith('avito.ru') } catch { return url.toLowerCase().includes('avito.ru') }
}

export function ThemeToggle({ theme, onToggle }: { theme: 'noir' | 'parchment'; onToggle: () => void }) {
  return <button type="button" className="header-control header-control-icon" onClick={onToggle} aria-label={theme === 'noir' ? 'Включить светлую тему' : 'Включить тёмную тему'} title={theme === 'noir' ? 'Светлая тема' : 'Тёмная тема'}>{theme === 'noir' ? '☼' : '☾'}</button>
}
