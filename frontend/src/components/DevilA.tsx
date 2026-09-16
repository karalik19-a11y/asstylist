import type { CSSProperties } from 'react'

/**
 * Devil A — буква «A» брендовой антиквой (Bodoni Moda) с рогами над вершиной
 * и хвостом-стрелкой под ней. Буква наследует цвет текста (currentColor),
 * рога и хвост — вишнёвый акцент айдентики.
 *
 * Координаты SVG — в единицах шрифта (1em = 2000): базовая линия буквы лежит
 * на y=0, поэтому vertical-align: -0.4em ставит её на базовую линию текста.
 */
export function DevilA({ className = '', style }: { className?: string; style?: CSSProperties }) {
  return (
    <svg
      className={`devil-a ${className}`.trim()}
      style={style}
      viewBox="0 -2300 1544 3100"
      aria-hidden="true"
      focusable="false"
    >
      <text className="devil-a-letter" x="0" y="0" fontSize="2000">
        A
      </text>
      <g className="devil-a-accent">
        <path d="M 570 -1440 C 470 -1530, 405 -1650, 385 -1780 C 370 -1900, 365 -1960, 370 -2020 C 450 -1910, 550 -1770, 630 -1650 C 680 -1570, 720 -1500, 755 -1450 C 690 -1440, 630 -1438, 570 -1440 Z" />
        <path
          d="M 570 -1440 C 470 -1530, 405 -1650, 385 -1780 C 370 -1900, 365 -1960, 370 -2020 C 450 -1910, 550 -1770, 630 -1650 C 680 -1570, 720 -1500, 755 -1450 C 690 -1440, 630 -1438, 570 -1440 Z"
          transform="matrix(-1 0 0 1 1544 0)"
        />
        <path d="M 930 470 L 1200 700 L 870 780 Z" />
      </g>
      <path
        className="devil-a-tail"
        d="M 500 -60 C 440 160, 470 350, 610 430 C 750 510, 900 470, 990 560"
        strokeWidth="100"
        strokeLinecap="round"
      />
    </svg>
  )
}
