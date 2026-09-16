import { useId } from 'react'

export function DevilA({ className = '' }: { className?: string }) {
  const rawId = useId().replace(/:/g, '')
  const hornGrad = `hornGrad-${rawId}`
  const hornSheen = `hornSheen-${rawId}`
  const tailGrad = `tailGrad-${rawId}`
  const staffGrad = `staffGrad-${rawId}`
  return (
    <span className={`devil-a ${className}`.trim()} aria-hidden="true">
      <svg className="devil-a-horns" viewBox="0 0 64 28" fill="none">
        <defs>
          <linearGradient id={hornGrad} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff6b7a" />
            <stop offset="55%" stopColor="#e82045" />
            <stop offset="100%" stopColor="#8b1028" />
          </linearGradient>
          <linearGradient id={hornSheen} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M18 26 C14 18 6 10 4 3 C3 0.5 6.5 0.2 9 3 C12 7 14 14 16 22 C16.5 24 17.5 26 18 26 Z"
          fill={`url(#${hornGrad})`}
        />
        <path d="M7.5 4.5 C10 8 12.5 14 14.5 21" stroke={`url(#${hornSheen})`} strokeWidth="1.4" strokeLinecap="round" />
        <path
          d="M46 26 C50 18 58 10 60 3 C61 0.5 57.5 0.2 55 3 C52 7 50 14 48 22 C47.5 24 46.5 26 46 26 Z"
          fill={`url(#${hornGrad})`}
        />
        <path d="M56.5 4.5 C54 8 51.5 14 49.5 21" stroke={`url(#${hornSheen})`} strokeWidth="1.4" strokeLinecap="round" />
        <path d="M16 24 C24 22 40 22 48 24" stroke="#8b1028" strokeWidth="1.2" strokeLinecap="round" opacity="0.5" />
      </svg>

      <span className="devil-a-letter">A</span>

      <svg className="devil-a-tail" viewBox="0 0 48 36" fill="none">
        <defs>
          <linearGradient id={tailGrad} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#ff4a66" />
            <stop offset="100%" stopColor="#b81432" />
          </linearGradient>
        </defs>
        <path
          d="M4 4 C12 6 18 14 16 22 C15 28 20 30 28 26 C34 23 40 24 44 30"
          stroke={`url(#${tailGrad})`}
          strokeWidth="3.2"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M4 4 C12 6 18 14 16 22 C15 28 20 30 28 26 C34 23 40 24 44 30"
          stroke="#ff8a9a"
          strokeWidth="1.1"
          strokeLinecap="round"
          fill="none"
          opacity="0.45"
        />
        <path d="M38 26 L47 32 L39 34 L41 30 Z" fill={`url(#${tailGrad})`} />
        <path d="M40 28.5 L45.5 31.5 L41 32.5 Z" fill="#ff8a9a" opacity="0.35" />
      </svg>

      <svg className="devil-a-staff" viewBox="0 0 24 48" fill="none">
        <defs>
          <linearGradient id={staffGrad} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5d060" />
            <stop offset="40%" stopColor="#e8b020" />
            <stop offset="100%" stopColor="#9a7010" />
          </linearGradient>
        </defs>
        <path d="M12 46 V16" stroke={`url(#${staffGrad})`} strokeWidth="2.4" strokeLinecap="round" />
        <path d="M12 46 V16" stroke="#fff3c0" strokeWidth="0.7" strokeLinecap="round" opacity="0.35" />
        <path
          d="M5 18 C5 12 8 8 12 5 C16 8 19 12 19 18"
          stroke={`url(#${staffGrad})`}
          strokeWidth="2.2"
          strokeLinecap="round"
          fill="none"
        />
        <path d="M12 5 V14" stroke={`url(#${staffGrad})`} strokeWidth="2.2" strokeLinecap="round" />
        <circle cx="5" cy="18" r="1.5" fill="#f5d060" />
        <circle cx="12" cy="5" r="1.7" fill="#f5d060" />
        <circle cx="19" cy="18" r="1.5" fill="#f5d060" />
        <ellipse cx="12" cy="34" rx="3.2" ry="1.4" fill="#c4920a" opacity="0.85" />
      </svg>
    </span>
  )
}
