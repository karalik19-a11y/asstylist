import { useEffect, useState } from 'react'
import { isAvitoPhotoUrl, photoProxyUrl } from '../lib/api'

/**
 * Фото вещи рядом с карточкой.
 *
 * Снимки объявлений лежат на CDN Авито, который браузеру отвечает не всегда
 * (hotlink-защита, регион, Referer). Поэтому пробуем по очереди:
 *
 * 1. прямую ссылку объявления (без Referer — так шансов больше);
 * 2. наш сервер ``/api/media/photo`` — он ходит на Авито сам и отдаёт файл
 *    со своего домена;
 * 3. если не вышло и это — показываем **понятную заглушку**: оттенки вещи,
 *    подпись «фото объявления» и подсказку, где смотреть. Чёрного
 *    прямоугольника без объяснений не бывает.
 */
export function ItemPhoto({
  src,
  alt,
  swatch,
  className = '',
  chips = [],
  fallbackLabel = 'Фото вещи',
}: {
  src?: string
  alt: string
  swatch: string
  className?: string
  /** Оттенки вещи — показываем их, если фото не приехало. */
  chips?: string[]
  fallbackLabel?: string
}) {
  const [stage, setStage] = useState<'direct' | 'proxy' | 'failed'>('direct')

  useEffect(() => {
    setStage('direct')
  }, [src])

  const direct = src ?? ''
  const proxied = src && isAvitoPhotoUrl(src) ? photoProxyUrl(src) : ''
  const current = stage === 'direct' ? direct : stage === 'proxy' ? proxied : ''
  const showImage = Boolean(current)

  return (
    <div
      className={`item-photo ${className}${showImage ? '' : ' item-photo-fallback'}`}
      style={{ background: swatch }}
      aria-hidden={!showImage}
    >
      {showImage ? (
        <img
          src={current}
          alt={alt}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          onError={() => setStage((value) => (value === 'direct' && proxied ? 'proxy' : 'failed'))}
        />
      ) : (
        <div className="item-photo-note">
          <span className="item-photo-note-title">{fallbackLabel} недоступно</span>
          {chips.length ? (
            <span className="item-photo-chips">
              {chips.map((hex) => (
                <span key={hex} className="item-photo-chip" style={{ background: hex }} />
              ))}
            </span>
          ) : null}
          <span className="item-photo-note-hint">Откройте объявление по кнопке ниже</span>
        </div>
      )}
    </div>
  )
}
