import { useEffect, useState } from 'react'

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
              {i === 0 ? (
                <span className="devil-a devil-a--intro">
                  <svg className="devil-a-horns" viewBox="0 0 40 18" width="1em" height="0.45em" fill="none">
                    <path d="M6 16 C4 8 2 2 8 1 C10 4 11 10 12 16" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
                    <path d="M34 16 C36 8 38 2 32 1 C30 4 29 10 28 16" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
                    <circle cx="8" cy="1.5" r="1.6" fill="currentColor" />
                    <circle cx="32" cy="1.5" r="1.6" fill="currentColor" />
                  </svg>
                  <span className="devil-a-letter">A</span>
                  <svg className="devil-a-tail" viewBox="0 0 28 22" width="0.7em" height="0.55em" fill="none">
                    <path d="M2 2 C10 4 14 12 12 18 C16 14 22 12 26 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    <path d="M22 14 L27 18 L21 19 Z" fill="currentColor" />
                  </svg>
                  <svg className="devil-a-staff" viewBox="0 0 16 28" width="0.35em" height="0.7em" fill="none">
                    <path d="M8 26 V8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                    <path d="M3 9 L8 3 L13 9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M5 11 L8 7 L11 11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              ) : (
                ch
              )}
            </span>
          ))}
        </span>
        <span className="boot-intro-rule" />
      </div>
    </div>
  )
}
