import type { CSSProperties } from 'react'

/**
 * Devil A — обычная буква A тем же шрифтом, что и остальной логотип,
 * с однотонными рогами и хвостом как декоративными элементами.
 */
export function DevilA({ className = '', style }: { className?: string; style?: CSSProperties }) {
  return (
    <span className={`devil-a ${className}`.trim()} style={style} aria-hidden="true">
      <span className="devil-a-horn devil-a-horn-left" />
      <span className="devil-a-horn devil-a-horn-right" />
      <span className="devil-a-letter">A</span>
      <span className="devil-a-tail" />
    </span>
  )
}
