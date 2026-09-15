/**
 * Web Audio API synthesized tactile sound engine.
 * No external audio files needed — zero network latency, 100% reliable, zero lag.
 */

let audioCtx: AudioContext | null = null
let soundEnabled = true

// Initialize sound preference from localStorage if available
if (typeof window !== 'undefined') {
  try {
    const saved = localStorage.getItem('asstylist_sound')
    if (saved !== null) {
      soundEnabled = saved === 'true'
    }
  } catch {
    soundEnabled = true
  }
}

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (AudioContextClass) {
      audioCtx = new AudioContextClass()
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    void audioCtx.resume()
  }
  return audioCtx
}

export function isSoundEnabled(): boolean {
  return soundEnabled
}

export function toggleSound(): boolean {
  soundEnabled = !soundEnabled
  try {
    localStorage.setItem('asstylist_sound', String(soundEnabled))
  } catch {
    /* ignore */
  }
  if (soundEnabled) {
    playClick()
  }
  return soundEnabled
}

/** Crisp tactile micro-click for buttons & interactive elements (Leica shutter click) */
export function playClick(): void {
  if (!soundEnabled) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return
    const now = ctx.currentTime

    // High subtle click
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(1400, now)
    osc.frequency.exponentialRampToValueAtTime(320, now + 0.028)

    gain.gain.setValueAtTime(0.08, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.028)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.03)
  } catch {
    /* ignore */
  }
}

/** Deep tactile rubber stamp imprint sound */
export function playStamp(): void {
  if (!soundEnabled) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return
    const now = ctx.currentTime

    // Low resonant thud
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(160, now)
    osc.frequency.exponentialRampToValueAtTime(45, now + 0.12)

    gain.gain.setValueAtTime(0.25, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12)

    osc.connect(gain)
    gain.connect(ctx.destination)

    // Second layer: paper rustle/impact
    const noiseBuffer = ctx.createBuffer(1, ctx.sampleRate * 0.04, ctx.sampleRate)
    const output = noiseBuffer.getChannelData(0)
    for (let i = 0; i < noiseBuffer.length; i++) {
      output[i] = Math.random() * 2 - 1
    }
    const noise = ctx.createBufferSource()
    noise.buffer = noiseBuffer

    const filter = ctx.createBiquadFilter()
    filter.type = 'bandpass'
    filter.frequency.value = 800

    const noiseGain = ctx.createGain()
    noiseGain.gain.setValueAtTime(0.06, now)
    noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.04)

    noise.connect(filter)
    filter.connect(noiseGain)
    noiseGain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.13)
    noise.start(now)
    noise.stop(now + 0.05)
  } catch {
    /* ignore */
  }
}

/** Subtle soft tick for hover or chip selection */
export function playTick(): void {
  if (!soundEnabled) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return
    const now = ctx.currentTime

    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(980, now)
    osc.frequency.exponentialRampToValueAtTime(600, now + 0.015)

    gain.gain.setValueAtTime(0.04, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.015)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.018)
  } catch {
    /* ignore */
  }
}

/** Elegant harmonic chime on generation complete */
export function playSuccess(): void {
  if (!soundEnabled) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return
    const now = ctx.currentTime

    const notes = [523.25, 659.25, 783.99] // C5, E5, G5
    notes.forEach((freq, index) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, now + index * 0.06)

      gain.gain.setValueAtTime(0.07, now + index * 0.06)
      gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.06 + 0.22)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now + index * 0.06)
      osc.stop(now + index * 0.06 + 0.24)
    })
  } catch {
    /* ignore */
  }
}
