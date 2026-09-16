import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import type { HistoryEntry, Look, Meta, WizardState } from './lib/types'
import { api, ApiError } from './lib/api'
import { haptic, initTelegram, isTelegram, onBackButton, onTelegramEvent, setBackButtonVisible, setClosingConfirmation, syncTelegramChrome, telegramColorScheme, telegramUserName } from './lib/telegram'
import { initialModel, wizardReducer } from './state/wizard'
import { Home } from './pages/Home'
import { Wizard } from './pages/Wizard'
import type { BodyMemory } from './lib/profile'
import { loadBodyMemory, markBodyUsed, saveBodyMemory } from './lib/profile'
import { History } from './pages/History'
import { Profile } from './pages/Profile'
import { Search } from './pages/Search'
import { Journal } from './pages/Journal'
import { LookResult } from './components/LookResult'
import { Header, ThemeToggle } from './components/ui'
import { TabBar } from './components/TabBar'
import { playClick, playSuccess } from './lib/sound'
import { LeopardPatternDef } from './lib/graphics'
import { BootIntro } from './components/BootIntro'
import { BUILD_STAMP, formatBuildLabel } from './lib/build'

type Screen = 'home' | 'wizard' | 'result' | 'history' | 'profile' | 'search' | 'journal'

const SCREEN_TITLES: Record<Screen, string> = {
  home: 'ASStylist', wizard: 'Новый гардероб', result: 'Персональная селекция', history: 'Архив образов', profile: 'Личный кабинет', search: 'Поиск вещей', journal: 'Журнал',
}

function errorMessage(error: unknown): string { if (error instanceof ApiError) return error.message; if (error instanceof Error) return error.message; return 'Произошла ошибка при формировании гардероба. Повторите попытку.' }

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [screen, setScreen] = useState<Screen>('home')
  const [model, dispatch] = useReducer(wizardReducer, initialModel)
  const [look, setLook] = useState<Look | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [generating, setGenerating] = useState(false)
  const [swappingSlot, setSwappingSlot] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(false)
  const [userName, setUserName] = useState<string | null>(null)
  const [savedBody, setSavedBody] = useState<BodyMemory | null>(null)
  const [theme, setTheme] = useState<'noir' | 'parchment'>(() => { try { const saved = localStorage.getItem('asstylist-theme'); if (saved === 'noir' || saved === 'parchment') return saved } catch {} return 'noir' })
  const [introDone, setIntroDone] = useState(() => { try { return sessionStorage.getItem('asstylist-intro-v1') === '1' } catch { return false } })
  const finishIntro = useCallback(() => { try { sessionStorage.setItem('asstylist-intro-v1', '1') } catch {} setIntroDone(true) }, [])
  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); syncTelegramChrome(theme); try { localStorage.setItem('asstylist-theme', theme) } catch {} }, [theme])
  const toggleTheme = useCallback(() => { playClick(); setTheme((value) => value === 'noir' ? 'parchment' : 'noir') }, [])
  const refreshHistory = useCallback(async () => { try { const response = await api.history(20); setHistory(response.items) } catch { setHistory([]) } }, [])
  useEffect(() => { const offTheme = onTelegramEvent('themeChanged', () => { try { if (localStorage.getItem('asstylist-theme')) return } catch {} setTheme(telegramColorScheme() === 'dark' ? 'noir' : 'parchment') }); return offTheme }, [])
  useEffect(() => { initTelegram(); setUserName(telegramUserName()); api.meta().then(setMeta).catch(() => setMeta(null)); api.auth().then((response) => setUserName(response.user.first_name ?? response.user.telegram_id)).catch(() => undefined); void loadBodyMemory().then(setSavedBody); void refreshHistory() }, [refreshHistory])
  const goHome = useCallback(() => { setScreen('home'); setError(null); void refreshHistory() }, [refreshHistory])
  const backAction = useCallback(() => { if (screen === 'wizard') { if (model.step === 'photo') goHome(); else dispatch({ type: 'back' }); return } goHome() }, [screen, model.step, goHome])
  const backActionRef = useRef(backAction)
  useEffect(() => { backActionRef.current = backAction }, [backAction])
  useEffect(() => onBackButton(() => { haptic('light'); backActionRef.current() }), [])
  useEffect(() => { setBackButtonVisible(screen !== 'home'); setClosingConfirmation(screen !== 'home') }, [screen])
  const startWizard = useCallback(() => { if (savedBody) dispatch({ type: 'reset', step: 'memory', patch: { height_cm: savedBody.height_cm, weight_kg: savedBody.weight_kg } }); else dispatch({ type: 'reset' }); setError(null); setScreen('wizard') }, [savedBody])
  const handleUseSavedBody = useCallback(() => { if (!savedBody) return; void markBodyUsed(); dispatch({ type: 'patch', patch: { height_cm: savedBody.height_cm, weight_kg: savedBody.weight_kg } }); dispatch({ type: 'goTo', step: 'photo' }) }, [savedBody])
  const handleNewBody = useCallback(() => dispatch({ type: 'goTo', step: 'photo' }), [])
  const handleRestartAll = useCallback(() => dispatch({ type: 'reset' }), [])
  const rememberBody = useCallback((height: number, weight: number) => { void saveBodyMemory(height, weight).then(setSavedBody) }, [])
  const handleGenerate = useCallback(async () => { setGenerating(true); setError(null); try { const result = await api.generateLook(model.state); setLook(result); setScreen('result'); haptic('success'); playSuccess(); rememberBody(model.state.height_cm, model.state.weight_kg); void refreshHistory() } catch (caught) { setError(errorMessage(caught)); haptic('error') } finally { setGenerating(false) } }, [model.state, refreshHistory, rememberBody])
  const handleEngineGenerate = useCallback(async (patch: Partial<WizardState>) => { const nextState = { ...model.state, ...patch }; dispatch({ type: 'patch', patch }); setGenerating(true); setError(null); try { const result = await api.generateLook(nextState); setLook(result); setScreen('result'); haptic('success'); playSuccess(); rememberBody(nextState.height_cm, nextState.weight_kg); void refreshHistory() } catch (caught) { setError(errorMessage(caught)); haptic('error') } finally { setGenerating(false) } }, [model.state, refreshHistory, rememberBody])
  const handleSwap = useCallback(async (slot: string) => { if (!look?.id) return; setSwappingSlot(slot); try { const updated = await api.swapItem(look.id, slot); setLook(updated); haptic('medium') } catch (caught) { setError(errorMessage(caught)); haptic('error') } finally { setSwappingSlot(null) } }, [look])
  const handleFavorite = useCallback(async () => { if (!look?.id) return; try { const response = await api.toggleFavorite(look.id); setLook({ ...look, is_favorite: response.is_favorite }); haptic('light') } catch (caught) { setError(errorMessage(caught)) } }, [look])
  const openLook = useCallback(async (id: number) => { setLoadingList(true); try { const result = await api.look(id); setLook(result); setScreen('result') } catch (caught) { setError(errorMessage(caught)) } finally { setLoadingList(false) } }, [])
  const openSearch = useCallback(() => { setScreen('search'); setError(null) }, [])
  const openHistory = useCallback(() => { setScreen('history'); setLoadingList(true); void refreshHistory().finally(() => setLoadingList(false)) }, [refreshHistory])
  const openJournal = useCallback(() => { setScreen('journal'); setError(null) }, [])
  useEffect(() => { const root = document.querySelector('.app'); if (!(root instanceof HTMLElement)) return; root.classList.remove('screen-flash'); void root.offsetWidth; root.classList.add('screen-flash') }, [screen])
  return (
    <div className="stage">
      <div className="ambient" aria-hidden="true"><span className="blob blob-a" /><span className="blob blob-b" /><span className="blob blob-c" /></div>
      {!introDone ? <BootIntro onDone={finishIntro} /> : null}
      <div className={`app${introDone ? ' app-ready' : ' app-booting'}`} data-screen={screen}>
        <LeopardPatternDef />
        {screen !== 'home' && screen !== 'wizard' && screen !== 'journal' ? <Header title={SCREEN_TITLES[screen]} compact onBack={isTelegram() ? undefined : backAction} onHome={goHome} right={<ThemeToggle theme={theme} onToggle={toggleTheme} />} /> : null}
        {screen === 'home' ? <Home meta={meta} userName={userName} theme={theme} onToggleTheme={toggleTheme} onStart={startWizard} onOpenHistory={openHistory} onOpenSearch={openSearch} /> : null}
        {screen === 'wizard' ? <Wizard model={model} meta={meta} generating={generating} error={error} onPatch={(patch) => dispatch({ type: 'patch', patch })} onToggleColor={(id, field) => dispatch({ type: 'toggleColor', id, field })} onPhoto={(dataUrl, file) => dispatch({ type: 'setPhoto', dataUrl, file })} onClearPhoto={() => dispatch({ type: 'setPhoto', dataUrl: null, file: null })} onBack={() => dispatch({ type: 'back' })} onNext={() => dispatch({ type: 'next' })} onGenerate={() => void handleGenerate()} onExit={goHome} savedBody={savedBody} onUseSavedBody={handleUseSavedBody} onNewBody={handleNewBody} onRestartAll={handleRestartAll} /> : null}
        {screen === 'result' && look ? <LookResult look={look} colors={meta?.colors ?? []} swappingSlot={swappingSlot} onSwap={(slot) => void handleSwap(slot)} onNewLook={startWizard} onFavorite={() => void handleFavorite()} /> : null}
        {screen === 'search' ? <Search meta={meta} onGenerate={(patch) => void handleEngineGenerate(patch)} generating={generating} error={error} /> : null}
        {screen === 'history' ? <History items={history} loading={loadingList} onOpen={(id) => void openLook(id)} /> : null}
        {screen === 'profile' ? <Profile /> : null}
        {screen === 'journal' ? <Journal /> : null}
        {screen !== 'wizard' ? <TabBar active={screen === 'history' ? 'archive' : screen === 'journal' ? 'journal' : screen === 'profile' ? 'profile' : 'home'} onHome={goHome} onArchive={openHistory} onJournal={openJournal} onProfile={() => setScreen('profile')} /> : null}
        {screen === 'home' ? <footer className="build-stamp" title="Идентификатор сборки фронтенда">{!isTelegram() ? 'ASStylist · браузер · ' : ''}<code>{formatBuildLabel(BUILD_STAMP)}</code></footer> : null}
      </div>
    </div>
  )
}
