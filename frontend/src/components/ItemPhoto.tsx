import { useState } from 'react'

/**
 * Фото вещи рядом с карточкой. Если снимок недоступен (битая ссылка внешнего
 * источника), показываем цветовой свотч — карточка никогда не остаётся «дыркой».
 */
export function ItemPhoto({
  src,
  alt,
  swatch,
  className = '',
}: {
  src?: string
  alt: string
  swatch: string
  className?: string
}) {
  const [failed, setFailed] = useState(false)
  const showImage = Boolean(src) && !failed
  return (
    <div className={`item-photo ${className}`} style={{ background: swatch }} aria-hidden={!showImage}>
      {showImage ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : null}
    </div>
  )
}
