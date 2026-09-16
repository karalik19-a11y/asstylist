import type { CSSProperties } from 'react'

/**
 * Devil A — буква «A» брендовой антиквой (Bodoni Moda) с рогами над вершиной
 * и хвостом-стрелкой под ней. Буква наследует цвет текста (currentColor),
 * рога и хвост — вишнёвый акцент айдентики.
 *
 * Координаты SVG — в единицах шрифта (1em = 2000): базовая линия буквы лежит
 * на y=0, поэтому vertical-align: -0.4em ставит её на базовую линию текста.
 */
const HORN =
  'M 570 -1420 C 460 -1500, 395 -1610, 380 -1730 C 368 -1850, 405 -1965, 520 -2025 ' +
  'C 520 -1940, 515 -1850, 530 -1750 C 570 -1620, 660 -1545, 810 -1500 ' +
  'C 725 -1455, 640 -1425, 570 -1420 Z'

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
        <path d={HORN} />
        <path d={HORN} transform="matrix(-1 0 0 1 1544 0)" />
        <path d="M 940 465 L 1215 705 L 870 785 Z" />
      </g>
      <path
        className="devil-a-tail"
        d="M 500 -60 C 440 160, 470 350, 610 430 C 750 510, 900 470, 990 560"
        strokeWidth="105"
        strokeLinecap="round"
      />
    </svg>
  )
}
