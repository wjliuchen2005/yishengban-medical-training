/** MiMo-only TTS gateway. No browser or meSpeak fallback is permitted. */
let activeAudio = null
let activeUrl = ''
const activeControllers = new Set()
let stopActive = null
let reusableAudio = null
const audioCache = new Map()
const CACHE_LIMIT = 48

const PREGENERATED_AUDIO_BY_TEXT = new Map([
  ['我是“易”生伴，有什么需要帮助的吗？请选择你想要训练的场景。', '/audio/tts/guide-intro.wav'],
  ['温故而知新，欢迎来到历史记录。', '/audio/tts/guide-history.wav'],
  ['欢迎来到训练场景，请选择你想要进行的训练。', '/audio/tts/guide-home.wav'],
  ['在这里你可以修改个人信息。', '/audio/tts/guide-profile.wav'],
  ['训练完成了，我们一起看看本次复盘。', '/audio/tts/guide-result.wav'],
  ['嗨，我是易心。今天感觉怎么样？不管是开心的、烦心的还是心里堵着说不出口的，都可以慢慢告诉我，我会认真听。', '/audio/tts/psych-opening.wav']
])

export function isMiMoTTSSupported() { return typeof window !== 'undefined' && typeof Audio !== 'undefined' }

function getAudioElement() {
  if (!reusableAudio) {
    reusableAudio = new Audio()
    reusableAudio.preload = 'auto'
    reusableAudio.playsInline = true
  }
  return reusableAudio
}

// Mobile browsers only allow later programmatic playback after an audio element
// has been activated by a user gesture. Login and voice buttons call this once.
export function unlockMiMoAudio() {
  if (!isMiMoTTSSupported() || activeAudio) return
  const audio = getAudioElement()
  const previousVolume = audio.volume
  audio.volume = 0
  audio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='
  const promise = audio.play()
  promise?.then(() => {
    audio.pause()
    audio.currentTime = 0
    audio.volume = previousVolume
  }).catch(() => { audio.volume = previousVolume })
}

function remember(key, blob) {
  if (audioCache.has(key)) audioCache.delete(key)
  audioCache.set(key, blob)
  while (audioCache.size > CACHE_LIMIT) audioCache.delete(audioCache.keys().next().value)
}

function play(url, options = {}, revoke = false) {
  return new Promise((resolve, reject) => {
    activeUrl = url
    const audio = getAudioElement()
    activeAudio = audio
    audio.src = url
    audio.volume = options.volume ?? 1
    const cleanup = () => {
      audio.onended = null
      audio.onerror = null
      if (revoke && activeUrl) URL.revokeObjectURL(activeUrl)
      activeUrl = ''
      if (activeAudio === audio) activeAudio = null
      stopActive = null
    }
    stopActive = () => { audio.pause(); cleanup(); resolve({ started: false, interrupted: true }) }
    audio.onended = () => { cleanup(); resolve({ started: true }) }
    audio.onerror = () => { cleanup(); reject(new Error('MiMo audio playback failed')) }
    audio.play().then(() => options.onReady?.()).catch((error) => { cleanup(); reject(error) })
  })
}

async function fetchMiMoBlob(text, options) {
  const token = localStorage.getItem('yishengban_token') || ''
  if (!token) throw new Error('MiMo requires sign-in')
  const payload = { text, role: options.role || 'patient', gender: options.gender || '', emotion: options.emotion || 'neutral' }
  if (options.mimoVoice) payload.voice = options.mimoVoice
  const key = JSON.stringify(payload)
  if (audioCache.has(key)) return audioCache.get(key)
  const controller = new AbortController()
  activeControllers.add(controller)
  const timeout = window.setTimeout(() => controller.abort(), 32000)
  try {
    const response = await fetch('/api/tts/synthesize', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: controller.signal })
    if (!response.ok) throw new Error(`MiMo HTTP ${response.status}`)
    const blob = await response.blob()
    if (blob.size < 44 || !/^audio\//i.test(blob.type)) throw new Error('Invalid MiMo audio')
    remember(key, blob)
    return blob
  } finally {
    window.clearTimeout(timeout)
    activeControllers.delete(controller)
  }
}

// Download may run concurrently for several speakers. Playback remains single-track.
export async function prepareMiMoSpeech(text, options = {}) {
  if (!text || !isMiMoTTSSupported()) return null
  const prepared = PREGENERATED_AUDIO_BY_TEXT.get(text)
  if (prepared) return { url: prepared, revoke: false }
  return { blob: await fetchMiMoBlob(text, options), revoke: true }
}

export function playPreparedMiMoSpeech(prepared, options = {}) {
  if (!prepared || !isMiMoTTSSupported()) return Promise.resolve({ started: false })
  // Starting the next utterance should stop only the current audio, not other
  // speakers whose audio is still downloading in the background.
  stopActive?.()
  const url = prepared.url || URL.createObjectURL(prepared.blob)
  return play(url, options, prepared.revoke)
}

export async function unifiedSpeak(text, options = {}) {
  if (!text || !isMiMoTTSSupported()) return { started: false }
  stopUnifiedSpeaking()
  return playPreparedMiMoSpeech(await prepareMiMoSpeech(text, options), options)
}

export function stopUnifiedSpeaking() {
  activeControllers.forEach((controller) => controller.abort())
  activeControllers.clear()
  stopActive?.()
}
