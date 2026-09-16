import { useEffect, useState } from 'react'
import { DevilA } from './ui'

const LETTERS = ['A', 'S', 'S', 't', 'y', 'l', 'i', 's', 't'] as const

export function BootIntro({ onDone }: { onDone: () => void }) {
  const [phase, setPhase] = useState<'letters' | 'hold' | 'shrink' | 'out'>('letters')

  useEffect(() => {
    const t1 = window.setTimeout(() => setPhase('hold'), 1400)
    const t2 = window.setTimeout(() => setPhase('shrink'), 1900)
    const t3 = window.setTimeout(() => setPhase('out'), 2600)
    const t4 = window.setTimeout(() => onDone(), 3100)
    return () => {
      window.clearTimeout(t1)
      window.clearTimeout(t2)
      window.clearTimeout(t3)
      window.clearTimeout(t4)
    }
  }, [onDone])

  return (
    <div className={`boot-intro boot-intro--${phase}`} aria-hidden="true">
      <div className="boot-intro-logo">
        <span className="boot-intro-word">
          {LETTERS.map((ch, i) => (
            <span
              key={`${ch}-${i}`}
              className={`boot-intro-letter${i === 0 ? ' boot-intro-letter--devil' : ''}${i < 3 ? ' boot-intro-letter--ass' : ' boot-intro-letter--tyl'}`}
              style={{ animationDelay: `${i * 0.11}s` }}
            >
              {i === 0 ? <DevilA className="devil-a--intro" /> : ch}
            </span>
          ))}
        </span>
        <span className="boot-intro-rule" />
      </div>
    </div>
  )
}
