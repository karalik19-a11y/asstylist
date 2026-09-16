import { useEffect, useState } from 'react'

const LOGO_SRC = '/asstylist-logo.svg?brand=20260916-v3'

export function BootIntro({ onDone }: { onDone: () => void }) {
  const [phase, setPhase] = useState<'hold' | 'shrink' | 'out'>('hold')
  useEffect(() => {
    const t1 = window.setTimeout(() => setPhase('shrink'), 1300)
    const t2 = window.setTimeout(() => setPhase('out'), 2050)
    const t3 = window.setTimeout(() => onDone(), 2500)
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); window.clearTimeout(t3) }
  }, [onDone])
  return <div className={`boot-intro boot-intro--${phase}`} aria-hidden="true"><div className="boot-intro-logo"><div className="boot-intro-word"><img className="boot-intro-image" src={LOGO_SRC} alt="" /></div><span className="boot-intro-rule" /></div></div>
}
