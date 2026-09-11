import { useUserStore } from '@/stores/user'

// Cursor insertion only changes the selected range, never replaces the draft.
export function insertTranscript(value, text, start, end, maxLength) {
  start = Math.min(value.length, Math.max(0, start))
  end = Math.min(value.length, Math.max(start, end))
  const available = Math.max(0, maxLength - value.length + end - start)
  const inserted = text.slice(0, available)
  return { value: value.slice(0, start) + inserted + value.slice(end), caret: start + inserted.length, truncated: inserted.length !== text.length }
}

export function encodeWav(chunks, sourceRate) {
  const length = chunks.reduce((n, v) => n + v.length, 0)
  const input = new Float32Array(length)
  let offset = 0
  for (const c of chunks) { input.set(c, offset); offset += c.length }
  const count = Math.floor(length * 16000 / sourceRate)
  const bytes = new ArrayBuffer(44 + count * 2)
  const view = new DataView(bytes)
  const str = (at, s) => [...s].forEach((ch, i) => view.setUint8(at + i, ch.charCodeAt(0)))
  str(0, 'RIFF'); view.setUint32(4, bytes.byteLength - 8, true); str(8, 'WAVE'); str(12, 'fmt ')
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true)
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true)
  str(36, 'data'); view.setUint32(40, count * 2, true)
  // Average downsampling instead of dropping samples (48kHz/44.1kHz devices).
  for (let i = 0; i < count; i++) {
    const left = Math.floor(i * sourceRate / 16000)
    const right = Math.max(left + 1, Math.floor((i + 1) * sourceRate / 16000))
    let sum = 0
    for (let j = left; j < right; j++) sum += input[j] || 0
    const v = Math.max(-1, Math.min(1, sum / (right - left)))
    view.setInt16(44 + i * 2, v * (v < 0 ? 32768 : 32767), true)
  }
  return new Blob([bytes], { type: 'audio/wav' })
}

export function audioBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export async function voiceRequest(path, payload, signal) {
  const response = await fetch('/api/voice/' + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + useUserStore().token },
    body: JSON.stringify(payload), signal
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(typeof error.detail === 'string' ? error.detail : '语音服务暂不可用，请检查登录或网络')
  }
  return response
}

export async function readTranscript(response, onText) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = '', done = false
  try {
    while (true) {
      const part = await reader.read()
      pending += decoder.decode(part.value || new Uint8Array(), { stream: !part.done })
      let end
      while ((end = pending.indexOf('\n\n')) >= 0) {
        const event = pending.slice(0, end); pending = pending.slice(end + 2)
        for (const line of event.split('\n')) {
          if (!line.startsWith('data:')) continue
          const data = JSON.parse(line.slice(5))
          if (data.type === 'error') throw new Error(data.message)
          if (data.type === 'text') onText(data.text)
          if (data.type === 'done') done = true
        }
      }
      if (part.done) break
    }
    if (!done) throw new Error('语音识别中断，已识别文字保留，请检查后补写。')
  } finally { reader.releaseLock() }
}
