import { useRef } from 'react'
import { CameraViewfinder } from '../lib/graphics'
import { playClick } from '../lib/sound'

const MAX_BYTES = 10 * 1024 * 1024
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']

export function PhotoUploader({
  dataUrl,
  onSelect,
  onClear,
  error,
}: {
  dataUrl: string | null
  onSelect: (dataUrl: string, file: File) => void
  onClear: () => void
  error?: string | null
}) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    if (!ACCEPTED.includes(file.type)) {
      onClear()
      window.alert('Поддерживаются форматы JPEG, PNG и WebP')
      return
    }
    if (file.size > MAX_BYTES) {
      onClear()
      window.alert('Размер файла превышает 10 МБ — выберите фото поменьше')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      onSelect(String(reader.result), file)
      playClick()
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="stack" style={{ gap: 12 }}>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(',')}
        style={{ display: 'none' }}
        onChange={(event) => handleFiles(event.target.files)}
      />

      {dataUrl ? (
        <div className="photo-preview-container">
          <img src={dataUrl} alt="Кадр для анализа пропорций" />
        </div>
      ) : (
        <button
          type="button"
          className="photo-drop-box"
          onClick={() => {
            playClick()
            inputRef.current?.click()
          }}
        >
          <CameraViewfinder size={36} />
          <strong className="condensed-title" style={{ fontSize: 14 }}>
            Загрузить снимок
          </strong>
          <div className="muted small" style={{ maxWidth: 360, margin: '0 auto' }}>
            Портрет в полный рост или по пояс. Изображение используется только для определения пропорций и палитры.
          </div>
        </button>
      )}

      {error ? <div className="error-box">{error}</div> : null}

      <div className="grid-2" style={{ gap: 14 }}>
        {dataUrl ? (
          <>
            <button
              type="button"
              className="btn btn-sm"
              onClick={() => {
                playClick()
                inputRef.current?.click()
              }}
            >
              Заменить снимок
            </button>
            <button
              type="button"
              className="btn btn-sm btn-outline"
              onClick={() => {
                playClick()
                onClear()
              }}
            >
              Удалить снимок
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn btn-sm"
            style={{ gridColumn: '1 / -1' }}
            onClick={() => {
              playClick()
              inputRef.current?.click()
            }}
          >
            Выбрать файл
          </button>
        )}
      </div>
    </div>
  )
}
