import { useRef } from 'react'
import { Icon } from './ui'

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
      window.alert('Поддерживаются JPEG, PNG и WebP')
      return
    }
    if (file.size > MAX_BYTES) {
      onClear()
      window.alert('Файл больше 10 МБ — выберите фото поменьше')
      return
    }
    const reader = new FileReader()
    reader.onload = () => onSelect(String(reader.result), file)
    reader.readAsDataURL(file)
  }

  return (
    <div className="stack">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(',')}
        style={{ display: 'none' }}
        onChange={(event) => handleFiles(event.target.files)}
      />
      {dataUrl ? (
        <div className="photo-preview">
          <img src={dataUrl} alt="Загруженное фото" />
        </div>
      ) : (
        <button type="button" className="photo-drop" onClick={() => inputRef.current?.click()}>
          <span className="cam-badge" aria-hidden="true">
            <Icon name="camera" size={30} />
          </span>
          <strong style={{ fontSize: 16 }}>Добавить фото</strong>
          <span className="muted small">
            Анфас или в полный рост. Ничего не храним — честно.
          </span>
        </button>
      )}
      {error ? <div className="error-box">{error}</div> : null}
      <div className="row" style={{ gap: 10 }}>
        {dataUrl ? (
          <>
            <button type="button" className="btn btn-sm" style={{ flex: 1 }} onClick={() => inputRef.current?.click()}>
              Заменить
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={onClear}>
              Убрать фото
            </button>
          </>
        ) : (
          <button type="button" className="btn btn-sm btn-block" onClick={() => inputRef.current?.click()}>
            Выбрать файл
          </button>
        )}
      </div>
    </div>
  )
}
