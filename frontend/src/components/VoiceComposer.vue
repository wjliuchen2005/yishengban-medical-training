<template>
  <div class="voice-composer" :class="{ psych: target === 'psych' }">
    <VoiceFeedback :items="clips.map(c => c.assessment)" :psych="target === 'psych'" editable @remove="i => clips.splice(i, 1)" />
    <div v-if="busy" class="record-status" role="status">
      <span :class="{ pulse: recording }" />
      {{ starting ? '正在启动麦克风…' : recording ? `正在聆听 · ${elapsed} 秒` : `${pending.length} 段语音处理中，可继续录音` }}
      <button v-if="recording" type="button" @click="stop">停止</button>
      <button v-else-if="starting" type="button" @click="cancelCapture">取消启动</button>
      <button v-else type="button" @click="cancelPending">取消等待</button>
    </div>
    <p v-if="error" class="voice-error" role="alert">{{ error }}</p>
    <div class="composer-row">
      <el-input ref="inputRef" :model-value="modelValue" @update:model-value="value => $emit('update:modelValue', value)"
        type="textarea" :autosize="{ minRows: 2, maxRows: 5 }" :maxlength="maxlength" show-word-limit
        :placeholder="placeholder" :disabled="disabled" @keydown.ctrl.enter="send" @keydown.meta.enter="send"
        @select="rememberCaret" @keyup="rememberCaret" @click="rememberCaret" @input="rememberCaret" />
      <div class="composer-buttons">
        <button type="button" class="microphone" :class="{ active: recording || (isMobile && holdVisible) }"
          :aria-label="recording ? '停止语音输入' : '语音输入'" :aria-pressed="recording || (isMobile && holdVisible)"
          :disabled="disabled" @pointerdown.prevent="rememberCaret" @click="toggle">
          <el-icon><Microphone /></el-icon><span>{{ recording ? '停止' : '语音输入' }}</span>
        </button>
        <el-button :type="target === 'psych' ? 'warning' : 'primary'" :loading="sending"
          :disabled="disabled || busy || !modelValue.trim()" @click="send"><el-icon><Promotion /></el-icon>{{ sendLabel }}</el-button>
      </div>
    </div>
    <button v-if="isMobile && holdVisible" type="button" class="hold-talk" :class="{ recording }"
      :disabled="disabled" @pointerdown.prevent="holdStart" @pointerup.prevent="holdEnd"
      @pointercancel="holdEnd" @lostpointercapture="holdEnd" @contextmenu.prevent
      @keydown.space.prevent="start" @keyup.space.prevent="stop">
      {{ starting ? '正在启动 · 松开取消' : recording ? '正在录音 · 松开停止' : '按住说话 · 松开停止' }}
    </button>
    <small v-if="holdVisible || busy" class="voice-note">每次最多90秒 · 松开后不采集 · 关闭或闲置20秒后释放麦克风</small>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Microphone, Promotion } from '@element-plus/icons-vue'
import { useMobileViewport } from '@/utils/useMobileViewport'
import { stopUnifiedSpeaking } from '@/utils/ttsService'
import { audioBase64, encodeWav, insertTranscript, readTranscript, voiceRequest } from '@/utils/voiceInput'
import VoiceFeedback from './VoiceFeedback.vue'

const props = defineProps({
  modelValue: { type: String, default: '' }, sessionId: Number, target: { type: String, default: 'patient' },
  context: { type: Array, default: () => [] }, disabled: Boolean, sending: Boolean,
  maxlength: { type: Number, default: 2000 }, placeholder: String, sendLabel: { type: String, default: '发送' }
})
const emit = defineEmits(['update:modelValue', 'send', 'recording'])
const isMobile = useMobileViewport()
const inputRef = ref(null), clips = ref([]), starting = ref(false), recording = ref(false)
const holdVisible = ref(false), elapsed = ref(0), error = ref(''), pending = shallowRef([])
const capturing = computed(() => starting.value || recording.value)
// Sending waits for this draft's metadata; capturing the next clip does not.
const busy = computed(() => capturing.value || pending.value.length > 0)
let consent = false, disposed = false, sequence = 0, cursor = null, activeRun = null, activePointer = null
let audioEngine = null, workletLoad = null, pooledStream = null, poolIdleTimer = null
let transcriptQueue = Promise.resolve(), insertionQueue = Promise.resolve()

function rememberCaret() {
  const el = inputRef.value?.textarea
  if (el) cursor = { start: el.selectionStart ?? props.modelValue.length, end: el.selectionEnd ?? props.modelValue.length }
}
async function insert(text) {
  if (disposed) return
  const el = inputRef.value?.textarea
  if (el && document.activeElement === el) rememberCaret()
  const at = cursor || { start: props.modelValue.length, end: props.modelValue.length }
  const result = insertTranscript(props.modelValue, text, at.start, at.end, props.maxlength)
  emit('update:modelValue', result.value)
  cursor = { start: result.caret, end: result.caret }
  if (result.truncated) error.value = '输入已达字数上限，部分识别文字未插入。请精简或分条发送。'
  await nextTick()
  el?.setSelectionRange(result.caret, result.caret)
}
async function ensureConsent() {
  if (consent) return true
  try {
    await ElMessageBox.confirm('开启后，录音会上传给小米 MiMo 进行文字识别，并连同当前对话语境分析声音表达。服务器不保存原始录音；发送后表达反馈随消息保存，易心则在你确认保存历史后加密保存。声音反馈仅供练习参考，不是心理诊断。你也可以取消并继续打字。', '语音输入与表达反馈', { confirmButtonText: '同意并启用', cancelButtonText: '继续打字', distinguishCancelAndClose: true })
    consent = true
    return true
  } catch { return false }
}
async function toggle() {
  rememberCaret()
  if (capturing.value) return stop()
  if (!consent && !(await ensureConsent())) return
  if (isMobile.value) {
    holdVisible.value = !holdVisible.value
    if (!holdVisible.value) closeEngine()
    return
  }
  start()
}
function holdStart(event) {
  if (capturing.value || props.disabled || (event.button != null && event.button > 0)) return
  activePointer = event.pointerId
  try { event.currentTarget.setPointerCapture?.(event.pointerId) } catch { /* Synthetic/older pointer implementations. */ }
  start()
}
function holdEnd(event) {
  if (event?.pointerId != null && event.pointerId !== activePointer) return
  activePointer = null
  stop()
}
function closeEngine() {
  clearTimeout(poolIdleTimer)
  poolIdleTimer = null
  pooledStream?.getTracks().forEach(track => track.stop())
  pooledStream = null
  const old = audioEngine
  audioEngine = null; workletLoad = null
  if (old && old.state !== 'closed') old.close().catch(() => {})
}
function releaseCapture(run) {
  clearInterval(run.timer); clearTimeout(run.startTimeout)
  if (run.node) {
    if (run.node.port) run.node.port.onmessage = null
    run.node.onaudioprocess = null
    run.node.disconnect()
  }
  run.source?.disconnect(); run.gain?.disconnect()
  // iPhone Safari and WeChat can leave the next getUserMedia call pending for
  // many seconds after a just-stopped track.  Between presses, keep the
  // already-authorized track but disable it and disconnect every audio node.
  // No samples are collected or uploaded while it is parked.
  if (run.stream !== pooledStream) run.stream?.getTracks().forEach(track => track.stop())
  run.node = run.source = run.gain = run.stream = null
}
function parkMicrophone() {
  if (!pooledStream) return
  pooledStream.getAudioTracks().forEach(track => { track.enabled = false })
  clearTimeout(poolIdleTimer)
  // A brief pool covers repeated long-presses; it is not a background mic.
  poolIdleTimer = window.setTimeout(closeEngine, 20000)
}
function cancelCapture() {
  const run = activeRun
  if (!run) return
  run.cancelled = true; run.controller.abort(); releaseCapture(run)
  run.chunks = []; run.segment = []
  activeRun = null; activePointer = null; starting.value = recording.value = false
  emit('recording', false)
}
async function start() {
  if (capturing.value || props.disabled || disposed) return
  if (clips.value.length + pending.value.length >= 8) { error.value = '每条消息最多8次录音，可先发送或移除不用的反馈。'; return }
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) { error.value = '语音输入需要HTTPS和麦克风权限，请使用系统浏览器打开。'; return }
  if (!consent && !(await ensureConsent())) return
  const run = {
    id: ++sequence, cancelled: false, controller: new AbortController(), chunks: [], segment: [],
    samples: 0, segmentSamples: 0, silence: 0, segmentSpeech: false, transcript: Promise.resolve(),
    request: { session_id: props.sessionId || null, target: props.target, draft: props.modelValue,
      messages: props.target === 'psych' ? props.context.map(m => ({ role: m.role, content: m.content })) : [] }
  }
  activeRun = run; starting.value = true; error.value = ''; elapsed.value = 0
  stopUnifiedSpeaking(); emit('recording', true)
  run.startTimeout = window.setTimeout(() => {
    if (activeRun !== run) return
    cancelCapture(); closeEngine()
    error.value = '麦克风启动超时，请松开后重新按住说话。已识别文字不会丢失。'
  }, 8000)
  try {
    // Reuse the unlocked engine instead of closing/recreating it on every press.
    // Tracks still stop on EVERY release; keeping an engine does not keep a mic.
    if (!audioEngine || audioEngine.state === 'closed') {
      audioEngine = new (window.AudioContext || window.webkitAudioContext)()
      workletLoad = null
    }
    const engine = audioEngine
    const resumed = engine.resume().then(() => null, e => e)
    let acquired = pooledStream
    if (!acquired || !acquired.getAudioTracks().some(track => track.readyState === 'live')) {
      pooledStream?.getTracks().forEach(track => track.stop())
      pooledStream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }, video: false })
      acquired = pooledStream
    }
    if (run.cancelled || disposed || activeRun !== run) { acquired.getTracks().forEach(t => t.stop()); return }
    clearTimeout(poolIdleTimer)
    pooledStream.getAudioTracks().forEach(track => { track.enabled = true })
    run.stream = acquired
    const resumeError = await resumed
    if (run.cancelled || disposed || activeRun !== run) return
    if (resumeError) throw resumeError
    const useWorklet = !!engine.audioWorklet && typeof AudioWorkletNode !== 'undefined'
    if (useWorklet) {
      if (!workletLoad) workletLoad = engine.audioWorklet.addModule('/audio/voice-capture-worklet.js')
      await workletLoad
    }
    if (run.cancelled || disposed || activeRun !== run) return
    run.rate = engine.sampleRate
    run.source = engine.createMediaStreamSource(acquired)
    run.node = useWorklet ? new AudioWorkletNode(engine, 'voice-capture') : engine.createScriptProcessor(2048, 1, 1)
    run.gain = engine.createGain(); run.gain.gain.value = 0
    run.lastFrame = performance.now()
    const onAudio = data => {
      if (activeRun !== run || !recording.value) return
      run.lastFrame = performance.now()
      const chunk = data.slice(0, Math.max(0, run.rate * 90 - run.samples))
      if (!chunk.length) { stop(); return }
      run.chunks.push(chunk); run.segment.push(chunk); run.samples += chunk.length; run.segmentSamples += chunk.length
      const rms = Math.sqrt(chunk.reduce((n, v) => n + v * v, 0) / chunk.length)
      if (rms > .003) { run.silence = 0; run.segmentSpeech = true } else run.silence += chunk.length / run.rate
      if ((run.silence > .7 && run.segmentSamples / run.rate >= 2) || run.segmentSamples / run.rate >= 12) flush(run)
      if (run.samples >= run.rate * 90) stop()
    }
    if (useWorklet) run.node.port.onmessage = ({ data }) => onAudio(data)
    else run.node.onaudioprocess = event => onAudio(new Float32Array(event.inputBuffer.getChannelData(0)))
    run.source.connect(run.node); run.node.connect(run.gain); run.gain.connect(engine.destination)
    acquired.getAudioTracks().forEach(track => track.addEventListener('ended', () => { if (activeRun === run) stop() }, { once: true }))
    clearTimeout(run.startTimeout)
    recording.value = true; starting.value = false
    run.timer = window.setInterval(() => {
      elapsed.value = Math.floor(run.samples / run.rate)
      if (performance.now() - run.lastFrame > 4000) {
        stop(); closeEngine()
        error.value = '麦克风声音中断，请重新按住说话。已录内容仍会处理。'
      }
    }, 250)
  } catch (e) {
    if (activeRun !== run) return
    cancelCapture(); closeEngine()
    error.value = e.name === 'NotAllowedError' ? '麦克风未获授权，可在浏览器设置中开启；文字输入不受影响。' : '无法启动录音，请松开后重试，并确认麦克风可用。'
  }
}
function flush(run) {
  const chunks = run.segment, meaningful = run.segmentSpeech
  run.segment = []; run.segmentSamples = 0; run.silence = 0; run.segmentSpeech = false
  if (!meaningful || !chunks.length) return
  const wav = encodeWav(chunks, run.rate)
  // One transcription queue across clips preserves their order even if later
  // recordings finish while earlier HTTP responses are still in flight.
  transcriptQueue = transcriptQueue.then(async () => {
    if (run.cancelled || disposed) return
    const timeout = window.setTimeout(() => run.controller.abort(), 60000)
    try {
      const audio = await audioBase64(wav)
      if (run.cancelled || disposed) return
      const response = await voiceRequest('transcribe', { ...run.request, messages: [], audio }, run.controller.signal)
      await readTranscript(response, text => {
        insertionQueue = insertionQueue.then(() => { if (!run.cancelled && !disposed) return insert(text) })
      })
      await insertionQueue
    } finally { clearTimeout(timeout) }
  }).catch(e => {
    if (!run.cancelled && !disposed) error.value = e.name === 'AbortError' ? '这段语音处理超时，已识别文字保留，可继续录音。' : e.message
  })
  run.transcript = transcriptQueue
}
function stop() {
  if (starting.value) { cancelCapture(); return }
  const run = activeRun
  if (!run || !recording.value) return
  recording.value = false; activeRun = null; activePointer = null
  releaseCapture(run); parkMicrophone(); emit('recording', false)
  flush(run)
  const wav = run.samples / run.rate >= .15 ? encodeWav(run.chunks, run.rate) : null
  run.chunks = []
  pending.value = [...pending.value, run]
  finish(run, wav)
}
async function finish(run, wav) {
  run.finishTimeout = window.setTimeout(() => {
    if (run.cancelled) return
    run.cancelled = true; run.controller.abort()
    pending.value = pending.value.filter(item => item !== run)
    error.value = '这段语音处理超时，已识别文字保留，请检查后发送。'
  }, 120000)
  try {
    const result = await (wav ? audioBase64(wav).then(audio => voiceRequest('assess', { ...run.request, audio }, run.controller.signal)).then(res => res.json()).catch(e => ({ error: e })) : Promise.resolve(null))
    await run.transcript
    if (run.cancelled || disposed) return
    if (result?.receipt) {
      clips.value.push({ ...result, order: run.id })
      clips.value.sort((a, b) => a.order - b.order)
    } else error.value = result?.error?.name === 'AbortError' ? '本段表达反馈未完成，已识别文字仍可使用。' : result?.error?.message || '录音太短，未进行识别或评价。'
  } finally {
    clearTimeout(run.finishTimeout)
    pending.value = pending.value.filter(item => item !== run)
  }
}
function cancelPending() {
  for (const run of pending.value) { run.cancelled = true; run.controller.abort(); clearTimeout(run.finishTimeout) }
  pending.value = []
}
function send() { if (!props.disabled && !busy.value && props.modelValue.trim()) emit('send') }
function takeClips() { const result = clips.value.splice(0); cursor = null; return result }
function clear() { cancelCapture(); cancelPending(); clips.value = []; cursor = null; error.value = ''; closeEngine() }
function onVisibility() { if (document.hidden) { holdEnd(); closeEngine() } }
onMounted(() => {
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('pointerup', holdEnd)
  window.addEventListener('pointercancel', holdEnd)
})
onBeforeUnmount(() => {
  disposed = true; clear()
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('pointerup', holdEnd)
  window.removeEventListener('pointercancel', holdEnd)
})
defineExpose({ takeClips, clear, busy })
</script>

<style scoped>
.voice-composer { width: 100%; min-width: 0; --accent:#247bd7; }
.psych { --accent:#ba7e49; }
.composer-row { display:flex; align-items:stretch; gap:10px; }
.composer-row > :first-child { flex:1; min-width:0; }
.composer-buttons { display:flex; flex-direction:column; gap:6px; width:100px; flex-shrink:0; }
.composer-buttons .el-button { margin:0; min-height:36px; }
.microphone { display:flex; justify-content:center; align-items:center; gap:5px; border:1px solid #d5e5ed; border-radius:9px; background:#f3f8fb; color:var(--accent); cursor:pointer; min-height:34px; font:inherit; font-size:12px; }
.microphone.active { background:#e5f2f7; border-color:var(--accent); }
button:disabled { opacity:.5; cursor:not-allowed; }
.hold-talk { width:100%; border:1px solid #cfe1e9; border-radius:12px; background:linear-gradient(110deg,#edf5fb,#ecf7f3); color:#386b7a; font-size:14px; font-weight:600; min-height:46px; margin-top:8px; touch-action:none; user-select:none; -webkit-user-select:none; -webkit-touch-callout:none; }
.hold-talk.recording { background:#dcefe9; color:#25795f; }
.voice-note { display:block; text-align:center; color:#7d929f; font-size:10px; margin-top:5px; }
.record-status { display:flex; gap:7px; align-items:center; color:var(--accent); font-size:12px; margin-bottom:8px; }
.record-status > span { width:6px; height:6px; border-radius:50%; background:currentColor; }
.record-status button { border:0; background:none; color:inherit; padding:5px 8px; margin-left:auto; cursor:pointer; }
.pulse { animation:mic-pulse 1.2s ease-in-out infinite; }
.voice-error { font-size:12px; color:#a56e37; margin:5px 0; }
:deep(textarea) { font-size:16px; line-height:1.6; border-radius:10px; padding-bottom:24px; }
@keyframes mic-pulse { 50% { opacity:.3 } }
@media(prefers-reduced-motion:reduce) { .pulse { animation:none } }
@media(max-width:980px) { .composer-buttons { width:84px; } .composer-row { gap:8px; } }
</style>
