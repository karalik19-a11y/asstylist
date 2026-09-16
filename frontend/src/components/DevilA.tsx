import type { CSSProperties } from 'react'

/**
 * Devil A — bold A, red crescent horns, red tail with arrow tip (reference style).
 */
export function DevilA({ className = '', style }: { className?: string; style?: CSSProperties }) {
  return (
    <span className={`devil-a ${className}`.trim()} style={style} aria-hidden="true">
      <svg
        className="devil-a-mark"
        viewBox="-12 0 128 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Tail */}
        <path
          d="M40 102
             C 16 98, 2 78, 12 58
             C 16 48, 8 40, -2 38"
          stroke="#e82045"
          strokeWidth="4.5"
          strokeLinecap="round"
          fill="none"
        />
        <path d="M-2 38 L-12 34 L-4 48 Z" fill="#e82045" />

        {/* A */}
        <path
          className="devil-a-glyph"
          fill="currentColor"
          fillRule="evenodd"
          d="
            M66 10
            L100 110
            H82
            L73 82
            H59
            L50 110
            H32
            L66 10
            Z
            M60 68
            H72
            L66 48
            L60 68
            Z
          "
        />

        {/* Horns */}
        <path
          fill="#e82045"
          d="M52 24
             C 44 14, 34 9, 28 7
             C 36 9, 46 14, 54 22
             C 53.2 23.2, 52.5 24, 52 24
             Z"
        />
        <path
          fill="#e82045"
          d="M80 24
             C 88 14, 98 9, 104 7
             C 96 9, 86 14, 78 22
             C 78.8 23.2, 79.5 24, 80 24
             Z"
        />
      </svg>
    </span>
  )
}
