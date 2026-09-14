import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { AppData, Outfit, Profile, WardrobeItem } from '../types'
import { randomId } from '../lib/color'
import {
  createDemoData,
  emptyData,
  exportJson,
  loadData,
  normalize,
  saveData,
} from '../lib/storage'

export type NewItemInput = Omit<WardrobeItem, 'id' | 'wornDates'>

interface AppStateValue {
  data: AppData
  profile: Profile
  items: WardrobeItem[]
  outfits: Outfit[]
  itemById: (id: string) => WardrobeItem | undefined
  updateProfile: (patch: Partial<Profile>) => void
  addItem: (input: NewItemInput) => WardrobeItem
  updateItem: (id: string, patch: Partial<WardrobeItem>) => void
  removeItem: (id: string) => void
  toggleFavorite: (id: string) => void
  saveOutfit: (outfit: Outfit) => void
  removeOutfit: (id: string) => void
  markWorn: (itemIds: string[], date: string) => void
  clearWorn: () => void
  loadDemo: () => void
  resetAll: () => void
  importJson: (text: string) => { ok: boolean; error?: string }
  downloadBackup: () => void
}

const AppStateContext = createContext<AppStateValue | null>(null)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AppData>(() => loadData())
  const firstRun = useRef(true)

  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false
      return
    }
    saveData(data)
  }, [data])

  const updateProfile = useCallback((patch: Partial<Profile>) => {
    setData((prev) => ({ ...prev, profile: { ...prev.profile, ...patch } }))
  }, [])

  const addItem = useCallback((input: NewItemInput) => {
    const item: WardrobeItem = { ...input, id: randomId('item'), wornDates: [] }
    setData((prev) => ({ ...prev, items: [...prev.items, item] }))
    return item
  }, [])

  const updateItem = useCallback((id: string, patch: Partial<WardrobeItem>) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.map((i) => (i.id === id ? { ...i, ...patch } : i)),
    }))
  }, [])

  const removeItem = useCallback((id: string) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.filter((i) => i.id !== id),
      outfits: prev.outfits.filter((o) => !o.itemIds.includes(id)),
    }))
  }, [])

  const toggleFavorite = useCallback((id: string) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.map((i) => (i.id === id ? { ...i, favorite: !i.favorite } : i)),
    }))
  }, [])

  const saveOutfit = useCallback((outfit: Outfit) => {
    setData((prev) => {
      if (prev.outfits.some((o) => o.id === outfit.id)) return prev
      return { ...prev, outfits: [{ ...outfit, saved: true }, ...prev.outfits].slice(0, 60) }
    })
  }, [])

  const removeOutfit = useCallback((id: string) => {
    setData((prev) => ({ ...prev, outfits: prev.outfits.filter((o) => o.id !== id) }))
  }, [])

  const markWorn = useCallback((itemIds: string[], date: string) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.map((i) =>
        itemIds.includes(i.id) && !i.wornDates.includes(date)
          ? { ...i, wornDates: [...i.wornDates, date] }
          : i,
      ),
    }))
  }, [])

  const clearWorn = useCallback(() => {
    setData((prev) => ({ ...prev, items: prev.items.map((i) => ({ ...i, wornDates: [] })) }))
  }, [])

  const loadDemo = useCallback(() => {
    setData(createDemoData())
  }, [])

  const resetAll = useCallback(() => {
    setData(emptyData())
  }, [])

  const importJson = useCallback((text: string) => {
    try {
      const parsed = normalize(JSON.parse(text))
      setData(parsed)
      return { ok: true }
    } catch (error) {
      return { ok: false, error: error instanceof Error ? error.message : 'Не удалось прочитать JSON' }
    }
  }, [])

  const downloadBackup = useCallback(() => {
    const blob = new Blob([exportJson(data)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `asstylist-backup-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [data])

  const itemById = useCallback(
    (id: string) => data.items.find((i) => i.id === id),
    [data.items],
  )

  const value = useMemo<AppStateValue>(
    () => ({
      data,
      profile: data.profile,
      items: data.items,
      outfits: data.outfits,
      itemById,
      updateProfile,
      addItem,
      updateItem,
      removeItem,
      toggleFavorite,
      saveOutfit,
      removeOutfit,
      markWorn,
      clearWorn,
      loadDemo,
      resetAll,
      importJson,
      downloadBackup,
    }),
    [
      data,
      itemById,
      updateProfile,
      addItem,
      updateItem,
      removeItem,
      toggleFavorite,
      saveOutfit,
      removeOutfit,
      markWorn,
      clearWorn,
      loadDemo,
      resetAll,
      importJson,
      downloadBackup,
    ],
  )

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
}

export function useAppState(): AppStateValue {
  const ctx = useContext(AppStateContext)
  if (!ctx) throw new Error('useAppState должен использоваться внутри AppStateProvider')
  return ctx
}
