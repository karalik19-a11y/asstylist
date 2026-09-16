/**
 * Фото объявления и кольцо оценки.
 *
 * Раньше при недоступном снимке в карточке оставался чёрный прямоугольник, а
 * цифра в кольце оценки красилась в цвет самой дуги и пропадала. Оба случая
 * закрываем: фото идёт через наш сервер и в крайнем случае даёт понятную
 * заглушку, цифра — контрастная.
 */

import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { ItemPhoto } from '../src/components/ItemPhoto'
import { ScoreRing } from '../src/components/ui'

const AVITO_PHOTO = 'https://90.img.avito.st/image/1/1.example.jpg'

describe('фото вещи', () => {
  it('сначала пробует прямую ссылку объявления без Referer', () => {
    render(<ItemPhoto src={AVITO_PHOTO} alt="свитер" swatch="#111" chips={['#111114']} />)
    const img = screen.getByAltText('свитер') as HTMLImageElement
    expect(img.getAttribute('src')).toBe(AVITO_PHOTO)
    expect(img.getAttribute('referrerpolicy')).toBe('no-referrer')
  })

  it('если прямая ссылка не открылась — берёт фото через наш сервер', () => {
    render(<ItemPhoto src={AVITO_PHOTO} alt="свитер" swatch="#111" />)
    fireEvent.error(screen.getByAltText('свитер'))
    const img = screen.getByAltText('свитер') as HTMLImageElement
    expect(img.getAttribute('src')).toBe(`/api/media/photo?u=${encodeURIComponent(AVITO_PHOTO)}`)
  })

  it('когда и сервер не смог — показывает заглушку с оттенками, а не чёрный экран', () => {
    const { container } = render(
      <ItemPhoto src={AVITO_PHOTO} alt="свитер" swatch="#111" chips={['#111114', '#f2f2f2']} fallbackLabel="Фото объявления" />,
    )
    const img = screen.getByAltText('свитер')
    fireEvent.error(img)
    fireEvent.error(screen.getByAltText('свитер'))

    expect(screen.queryByAltText('свитер')).toBeNull()
    expect(screen.getByText('Фото объявления недоступно')).toBeTruthy()
    expect(screen.getByText('Откройте объявление по кнопке ниже')).toBeTruthy()
    expect(container.querySelectorAll('.item-photo-chip')).toHaveLength(2)
    expect(container.querySelector('.item-photo')?.className).toContain('item-photo-fallback')
  })

  it('не тянет фото через сервер, если вещь не из Авито', () => {
    render(<ItemPhoto src="https://shop.example.com/item.jpg" alt="вещь" swatch="#111" />)
    fireEvent.error(screen.getByAltText('вещь'))
    expect(screen.queryByAltText('вещь')).toBeNull()
    expect(screen.getByText('Фото вещи недоступно')).toBeTruthy()
  })
})

describe('кольцо оценки', () => {
  it('цифра не окрашена в цвет дуги — текст читается', () => {
    const { container } = render(<ScoreRing score={88} />)
    const ring = container.querySelector('.score-ring') as HTMLElement
    expect(ring.textContent).toBe('88')
    expect(ring.style.color).toBe('')
    expect(ring.style.background).toContain('radial-gradient')
    expect(ring.style.background).toContain('conic-gradient')
  })

  it('ограничивает оценку диапазоном 0–100', () => {
    const { container } = render(<ScoreRing score={142} />)
    expect(container.querySelector('.score-ring')?.textContent).toBe('100')
    expect(container.querySelector('.score-ring')?.getAttribute('aria-label')).toContain('100')
  })
})
