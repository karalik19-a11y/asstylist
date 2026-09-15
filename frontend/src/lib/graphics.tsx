/**
 * High-fashion vector graphics, authentic leopard textures,
 * linocut illustrations, and postal cancellation stamps inspired by references.
 */

export function LeopardPatternDef() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
      <defs>
        <pattern id="leopard-rosette-pattern" width="60" height="60" patternUnits="userSpaceOnUse">
          {/* Base warm fur ochre */}
          <rect width="60" height="60" fill="#c48a43" />
          {/* Rosette 1 */}
          <path
            d="M12 10c-3 1-5 4-4 8 1 3 4 5 7 4 3-1 5-4 4-7-1-3-4-5-7-5z"
            fill="#8e531e"
          />
          <path
            d="M9 8c2-2 6-1 7 1m-9 7c1 4 5 5 7 3m1-8c3 2 3 6 1 8"
            stroke="#16120e"
            strokeWidth="2.8"
            strokeLinecap="round"
            fill="none"
          />
          {/* Rosette 2 */}
          <path
            d="M42 38c-3 1-4 4-3 7 1 3 4 4 7 3 3-1 4-4 3-7-1-3-4-4-7-3z"
            fill="#8e531e"
          />
          <path
            d="M39 36c2-2 6-1 7 1m-9 7c1 4 5 4 7 2m1-8c3 2 3 6 1 7"
            stroke="#16120e"
            strokeWidth="2.8"
            strokeLinecap="round"
            fill="none"
          />
          {/* Smaller rosettes and spots */}
          <path
            d="M45 12c-2 0-4 2-3 4 1 2 3 2 5 1 2-1 2-3 1-4-1-1-2-1-3-1z"
            fill="#9b5e24"
          />
          <path
            d="M43 11c1-1 4 0 4 2m-5 4c2 2 4 1 4-1"
            stroke="#16120e"
            strokeWidth="2.2"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M16 44c-2 0-3 2-3 4 1 2 3 2 4 1 2-1 2-3 1-4-1-1-1-1-2-1z"
            fill="#9b5e24"
          />
          <circle cx="28" cy="24" r="3.2" fill="#16120e" />
          <circle cx="34" cy="52" r="2.8" fill="#16120e" />
          <circle cx="2" cy="30" r="2.5" fill="#16120e" />
          <circle cx="58" cy="28" r="2.5" fill="#16120e" />
          <circle cx="24" cy="6" r="2.2" fill="#16120e" />
        </pattern>
      </defs>
    </svg>
  )
}

/** Horizontal leopard texture ribbon inspired by Reference 3 and Reference 1 */
export function LeopardRibbon({ height = 12, className = '' }: { height?: number; className?: string }) {
  return (
    <div
      className={`leopard-ribbon ${className}`}
      style={{
        height: `${height}px`,
        width: '100%',
        backgroundImage: `radial-gradient(#1c1610 2px, transparent 2px), radial-gradient(#1c1610 2px, #bf813a 2px)`,
        backgroundSize: '16px 16px',
        backgroundPosition: '0 0, 8px 8px',
        borderTop: '1px solid #000',
        borderBottom: '1px solid #000',
      }}
      aria-hidden="true"
    />
  )
}

/**
 * Cheetah linocut portrait inspired by Reference 1 ("POSITIVE POISON").
 * High contrast screenprint aesthetic.
 */
export function CheetahArtwork({ className = '' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 240 280"
      className={`cheetah-svg ${className}`}
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Cheetah linocut print"
    >
      <rect width="240" height="280" fill="none" />
      {/* Head silhouette */}
      <path
        d="M60 270 L60 220 Q65 170 75 140 Q65 110 50 60 Q70 65 95 85 Q120 78 145 85 Q170 65 190 60 Q175 110 165 140 Q175 170 180 220 L180 270 Z"
        fill="currentColor"
      />
      {/* Inner negative space highlights */}
      <path
        d="M72 265 L72 225 Q76 185 85 155 Q95 125 105 100 Q120 95 135 100 Q145 125 155 155 Q164 185 168 225 L168 265 Z"
        fill="var(--stamp-paper, #F5F2EC)"
      />
      {/* Brow and nose bridge */}
      <path
        d="M102 105 Q120 102 138 105 L132 165 Q120 170 108 165 Z"
        fill="currentColor"
      />
      {/* Piercing eyes */}
      <polygon points="86,130 108,126 102,136 88,138" fill="currentColor" />
      <polygon points="154,130 132,126 138,136 152,138" fill="currentColor" />
      <circle cx="98" cy="132" r="2.8" fill="var(--stamp-paper, #F5F2EC)" />
      <circle cx="142" cy="132" r="2.8" fill="var(--stamp-paper, #F5F2EC)" />
      {/* Cheetah characteristic black tear stripes */}
      <path
        d="M100 137 Q95 160 98 185 Q99 205 102 220 L94 220 Q90 200 90 180 Q87 155 93 136 Z"
        fill="currentColor"
      />
      <path
        d="M140 137 Q145 160 142 185 Q141 205 138 220 L146 220 Q150 200 150 180 Q153 155 147 136 Z"
        fill="currentColor"
      />
      {/* Muzzle & Nose */}
      <path
        d="M110 168 L130 168 L125 182 L115 182 Z"
        fill="currentColor"
      />
      <path
        d="M120 182 L120 196 Q112 198 106 208 M120 196 Q128 198 134 208"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Spots on cheeks and neck */}
      <circle cx="82" cy="165" r="4" fill="currentColor" />
      <circle cx="76" cy="185" r="5" fill="currentColor" />
      <circle cx="82" cy="205" r="4.5" fill="currentColor" />
      <circle cx="88" cy="235" r="5.5" fill="currentColor" />
      <circle cx="158" cy="165" r="4" fill="currentColor" />
      <circle cx="164" cy="185" r="5" fill="currentColor" />
      <circle cx="158" cy="205" r="4.5" fill="currentColor" />
      <circle cx="152" cy="235" r="5.5" fill="currentColor" />
      <circle cx="112" cy="225" r="3.5" fill="currentColor" />
      <circle cx="128" cy="225" r="3.5" fill="currentColor" />
      <circle cx="120" cy="245" r="4" fill="currentColor" />
      {/* Ears details */}
      <polygon points="56,70 66,110 82,90" fill="var(--stamp-paper, #F5F2EC)" />
      <polygon points="184,70 174,110 158,90" fill="var(--stamp-paper, #F5F2EC)" />
    </svg>
  )
}

/**
 * Doberman Postage Stamp graphic inspired by Reference 2 ("日本 JAPAN").
 */
export function DobermanStamp({ className = '' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 160 210"
      className={`doberman-stamp-svg ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Japanese Doberman postage stamp"
    >
      {/* Stamp backing */}
      <rect x="4" y="4" width="152" height="202" fill="var(--stamp-paper, #F7F4EB)" stroke="currentColor" strokeWidth="1.5" />
      <rect x="8" y="8" width="144" height="194" fill="none" stroke="currentColor" strokeWidth="0.8" strokeDasharray="3 2" />
      {/* Header: 日本 JAPAN */}
      <text x="18" y="32" fontFamily="var(--font-display)" fontSize="18" fontWeight="bold" fill="currentColor">
        日本
      </text>
      <text x="64" y="32" fontFamily="var(--font-display)" fontSize="16" letterSpacing="0.1em" fontWeight="bold" fill="currentColor">
        JAPAN
      </text>
      {/* Denomination */}
      <text x="116" y="32" fontFamily="var(--font-label)" fontSize="13" fontWeight="bold" fill="currentColor">
        ¥350
      </text>
      {/* Inner illustration frame */}
      <rect x="14" y="42" width="132" height="150" fill="var(--stamp-dark, #151518)" />
      {/* Doberman profile silhouette */}
      <path
        d="M26 192 L45 140 Q55 115 62 95 Q68 75 72 48 L80 48 Q82 72 86 86 L118 100 Q124 103 126 109 Q126 115 116 118 L96 116 L108 126 Q112 130 106 134 L92 128 Q78 145 68 192 Z"
        fill="#C98B48"
      />
      <path
        d="M32 192 L50 144 Q58 120 64 100 Q70 82 74 54 L78 54 Q80 76 84 89 L114 102 Q118 104 116 108 L94 112 Q82 135 72 192 Z"
        fill="#101012"
      />
      {/* Eye and snout details */}
      <polygon points="86,96 92,93 90,98" fill="#C98B48" />
      <circle cx="120" cy="106" r="2.5" fill="#101012" />
      {/* Collar */}
      <path d="M52 144 L78 152" stroke="#D32F2F" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

/**
 * Clickable, interactive rubber cancellation postmark seal.
 * "日本 TOKYO · ASSTYLIST ATELIER · DAR ES SALAAM"
 */
export function PostalCancellationStamp({
  text = 'TOKYO · ATELIER 2026',
  sub = 'DAR ES SALAAM K 350A',
  onClick,
  active = false,
}: {
  text?: string
  sub?: string
  onClick?: () => void
  active?: boolean
}) {
  return (
    <div
      className={`cancellation-seal ${active ? 'cancellation-seal-active' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      title={onClick ? 'Нажмите для тактильного оттиска штампа' : undefined}
      aria-label="Почтовый штемпель"
    >
      <svg viewBox="0 0 130 130" width="100%" height="100%">
        {/* Outer dotted / dashed stamp ring */}
        <circle cx="65" cy="65" r="58" fill="none" stroke="currentColor" strokeWidth="1.8" strokeDasharray="4 2" />
        <circle cx="65" cy="65" r="52" fill="none" stroke="currentColor" strokeWidth="1" />
        {/* Curved text along path */}
        <defs>
          <path id="seal-curve-top" d="M 22,65 A 43,43 0 0,1 108,65" fill="none" />
          <path id="seal-curve-bot" d="M 108,65 A 43,43 0 0,1 22,65" fill="none" />
        </defs>
        <text fontSize="8.5" fontFamily="var(--font-label)" letterSpacing="0.22em" fill="currentColor">
          <textPath href="#seal-curve-top" startOffset="50%" textAnchor="middle">
            {text}
          </textPath>
        </text>
        <text fontSize="7" fontFamily="var(--font-label)" letterSpacing="0.18em" fill="currentColor">
          <textPath href="#seal-curve-bot" startOffset="50%" textAnchor="middle">
            {sub}
          </textPath>
        </text>
        {/* Center postal mark */}
        <circle cx="65" cy="65" r="22" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <text x="65" y="62" textAnchor="middle" fontFamily="var(--font-display)" fontSize="13" fontWeight="bold" fill="currentColor">
          日本
        </text>
        <text x="65" y="74" textAnchor="middle" fontFamily="var(--font-label)" fontSize="7" letterSpacing="0.15em" fill="currentColor">
          SPEC
        </text>
        {/* Postal wavy cancellation lines extending to the right */}
        <path d="M102 52 Q114 48 126 52 M102 65 Q114 61 126 65 M102 78 Q114 74 126 78" stroke="currentColor" strokeWidth="1.2" fill="none" />
      </svg>
    </div>
  )
}

/** Clean SVG Icons (replacing emojis) */

export function CameraViewfinder({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.8">
      {/* Corner crop marks */}
      <path d="M4 10V5H9 M23 5H28V10 M28 22V27H23 M9 27H4V22" strokeLinecap="square" />
      {/* Aperture / Lens */}
      <circle cx="16" cy="16" r="6.5" strokeWidth="1.6" />
      <circle cx="16" cy="16" r="2.5" fill="currentColor" />
      {/* Top flash mark */}
      <line x1="16" y1="3" x2="16" y2="5" strokeLinecap="square" />
    </svg>
  )
}

export function StarIcon({ filled = false, size = 16 }: { filled?: boolean; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  )
}

export function SoundIcon({ enabled, size = 18 }: { enabled: boolean; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill={enabled ? 'currentColor' : 'none'} />
      {enabled ? (
        <>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
        </>
      ) : (
        <line x1="23" y1="9" x2="17" y2="15" />
      )}
    </svg>
  )
}

export function SwapIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 16V4M7 4L3 8M7 4L11 8" />
      <path d="M17 8V20M17 20L21 16M17 20L13 16" />
    </svg>
  )
}

export function ExternalIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  )
}

export function DiamondIcon({ size = 10, fill = true }: { size?: number; fill?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill={fill ? 'currentColor' : 'none'} stroke="currentColor">
      <polygon points="6,0 12,6 6,12 0,6" />
    </svg>
  )
}

/** Roman / Japanese Stamp Badges for the 10 styles */
export const STYLE_BADGES: Record<string, { kanji: string; num: string; code: string }> = {
  minimal: { kanji: '簡', num: '01', code: 'MINIMAL' },
  old_money: { kanji: '貴', num: '02', code: 'LUXURY' },
  streetwear: { kanji: '街', num: '03', code: 'STREET' },
  business_casual: { kanji: '職', num: '04', code: 'CASUAL' },
  techwear: { kanji: '機', num: '05', code: 'TECH' },
  romantic: { kanji: '華', num: '06', code: 'ROMANCE' },
  athleisure: { kanji: '動', num: '07', code: 'SPORT' },
  grunge: { kanji: '破', num: '08', code: 'GRUNGE' },
  boho: { kanji: '風', num: '09', code: 'BOHO' },
  avantgarde: { kanji: '前', num: '10', code: 'AVANT' },
}

/** Roman / Japanese Stamp Badges for the 8 moods */
export const MOOD_BADGES: Record<string, { kanji: string; num: string; code: string }> = {
  confident: { kanji: '力', num: '01', code: 'FORCE' },
  calm: { kanji: '静', num: '02', code: 'CALM' },
  playful: { kanji: '遊', num: '03', code: 'PLAY' },
  bold: { kanji: '激', num: '04', code: 'BOLD' },
  cozy: { kanji: '温', num: '05', code: 'COZY' },
  elegant: { kanji: '雅', num: '06', code: 'NOBLE' },
  energetic: { kanji: '速', num: '07', code: 'SPEED' },
  mysterious: { kanji: '幽', num: '08', code: 'NOIR' },
}
