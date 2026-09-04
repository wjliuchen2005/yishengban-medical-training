/**
 * 统一 TTS 服务：系统语音优先，meSpeak.js 兜底
 *
 * 策略链：
 * 1. 系统有匹配性别的中文语音 → 用系统语音（音质最好）
 * 2. 系统没有男声 → 自动切到 meSpeak.js（纯 JS 引擎，不依赖系统安装）
 * 3. meSpeak 也没加载好 → 退回系统女声降调
 *
 * meSpeak 的中文语音数据放在 public/voices/zh.json，打包后无需下载。
 */

// meSpeak 是通过 npm 安装的，但它的模块导出方式比较特殊
// 我们用动态 import 来加载，避免影响首屏性能
// mespeak 的 loadConfig 需要引擎配置（mespeak_config.json），loadVoice 才是加载语言数据
import mespeakConfig from 'mespeak/src/mespeak_config.json'

let meSpeakLoaded = false
let meSpeakLoading = false
let meSpeakInstance = null

async function loadMeSpeak() {
  if (meSpeakLoaded) return meSpeakInstance
  if (meSpeakLoading) {
    // 等待正在进行的加载
    while (meSpeakLoading) {
      await new Promise((r) => setTimeout(r, 100))
    }
    return meSpeakInstance
  }
  meSpeakLoading = true
  try {
    const meSpeak = (await import('mespeak')).default || (await import('mespeak'))
    // 1. 加载引擎配置（内置的 mespeak_config.json，随包打包）
    meSpeak.loadConfig(mespeakConfig)
    // 2. 加载中文语音数据（public/voices/zh.json，打包后无需下载）
    const resp = await fetch('/voices/zh.json')
    if (!resp.ok) throw new Error('zh.json fetch failed: ' + resp.status)
    const voiceData = await resp.json()
    meSpeak.loadVoice(voiceData)
    meSpeakLoaded = true
    meSpeakInstance = meSpeak
    console.log('[TTS] meSpeak.js 已加载，中文语音就绪')
  } catch (e) {
    console.error('[TTS] meSpeak.js 加载失败:', e)
  } finally {
    meSpeakLoading = false
  }
  return meSpeakInstance
}

// 检测系统是否有指定性别的中文语音
export function hasSystemChineseVoice(gender = '') {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return false
  const voices = window.speechSynthesis.getVoices() || []
  const zhVoices = voices.filter((v) => /^zh/i.test(v.lang))
  if (gender === 'male') {
    return zhVoices.some((v) => /kang|zhiwei|yunjian|yunyang|male|男/i.test(v.name))
  }
  if (gender === 'female') {
    return zhVoices.some((v) => /huihui|yaoyao|xiaoxiao|xiaoyi|female|女/i.test(v.name))
  }
  return zhVoices.length > 0
}

// 获取系统中文语音
function getSystemChineseVoice(gender = '') {
  const voices = window.speechSynthesis?.getVoices() || []
  if (gender === 'male') {
    // 优先 Edge 在线自然男声（Yunxi 云希=年轻男声 / Yunyang 云扬=播音男声 / Yunjian 云健），
    // 其次桌面男声（Kangkang/Zhiwei），最后任意非女声的中文语音
    return (
      voices.find((v) => /^zh/i.test(v.lang) && /online|natural/i.test(v.name) && /yunxi|yunyang|yunjian/i.test(v.name)) ||
      voices.find((v) => /^zh/i.test(v.lang) && /kang|zhiwei|yunxi|yunyang|yunjian|male|男/i.test(v.name)) ||
      null
    )
  }
  if (gender === 'female') {
    return (
      voices.find((v) => /^zh/i.test(v.lang) && /huihui|yaoyao|xiaoxiao|xiaoyi|female|女/i.test(v.name)) ||
      voices.find((v) => /^zh/i.test(v.lang)) ||
      null
    )
  }
  return voices.find((v) => /^zh/i.test(v.lang)) || null
}

// 预热：在页面加载后尽早把 meSpeak 加载好（后台静默执行）
let preheated = false
export async function preheatMeSpeak() {
  if (preheated) return
  preheated = true
  // 延迟 2 秒加载，不抢首屏资源
  setTimeout(() => loadMeSpeak(), 2000)
}

/**
 * 统一朗读接口
 * @param {string} text 要朗读的文本
 * @param {object} opts { gender, pitch, rate, volume, voice }
 * @returns {Promise<void>}
 */
export async function unifiedSpeak(text, opts = {}) {
  if (!text) return
  // 任何新朗读先打断正在播的旧语音（系统语音 + meSpeak 一起停），
  // 保证「重播 / 切换话题 / 新一轮回复」永远不会和上一句叠音
  stopUnifiedSpeaking()
  const gender = opts.gender || ''
  const pitch = opts.pitch ?? 1
  const rate = opts.rate ?? 1
  const volume = opts.volume ?? 1

  // 男声特殊处理：meSpeak 优先。
  // 原因：部分机器（如本机 Edge）语音列表里能枚举到 Kangkang，但合成时静默回退默认女声，
  // 导致「男身份女声音」。meSpeak 是纯 JS 引擎，variant 'm' 必定是男声，最可靠。
  if (gender === 'male') {
    // 第一优先：Edge 在线自然男声（Yunxi 云希 / Yunyang 云扬 / Yunjian 云健），
    // 音质最好且真实可用；桌面 Kangkang 在部分机器上会枚举到但合成时静默回退女声
    const sysMale = getSystemChineseVoice('male')
    if (sysMale) {
      console.log('[TTS] 男声 → 系统语音:', sysMale.name)
      return speakWithSystem(text, sysMale, pitch, rate, volume, false, gender)
    }
    // 第二优先：meSpeak 纯 JS 引擎（必定男声）
    const ms = await loadMeSpeak()
    if (ms) {
      console.log('[TTS] 男声 → meSpeak.js 引擎')
      return speakWithMeSpeak(text, pitch, rate, volume)
    }
    // 都没有 → 系统女声降调模拟
    const fb = getSystemChineseVoice('female') || getSystemChineseVoice('')
    console.warn('[TTS] 男声 → 无可用男声引擎，女声降调模拟')
    return speakWithSystem(text, fb, Math.min(pitch, 0.45), rate, volume, true, gender)
  }

  // 策略 1：如果调用方传了明确的 voice，用它（系统语音匹配成功的情况）
  if (opts.voice && typeof opts.voice === 'object' && opts.voice.voice) {
    return speakWithSystem(text, opts.voice.voice, pitch, rate, volume, opts.voice.isFallbackFemale, gender)
  }

  // 策略 2：系统有匹配性别的语音 → 用系统语音
  const sysVoice = getSystemChineseVoice(gender)
  if (sysVoice) {
    return speakWithSystem(text, sysVoice, pitch, rate, volume, false, gender)
  }

  // 策略 3：兜底系统女声
  const fallbackVoice = getSystemChineseVoice('female') || getSystemChineseVoice('')
  return speakWithSystem(text, fallbackVoice, pitch, rate, volume, true, gender)
}

function speakWithSystem(text, voice, pitch, rate, volume, isFallback, gender) {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      resolve()
      return
    }
    const synth = window.speechSynthesis
    synth.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    const actualPitch = isFallback && gender === 'male' ? Math.min(pitch, 0.45) : pitch
    if (voice) utterance.voice = voice
    utterance.lang = 'zh-CN'
    utterance.pitch = actualPitch
    utterance.rate = rate
    utterance.volume = volume

    let settled = false
    const finish = () => {
      if (settled) return
      settled = true
      resolve()
    }
    utterance.onend = finish
    utterance.onerror = finish
    const estimated = Math.max(1500, (text.length / 4.5) * 1000 + 1200)
    window.setTimeout(finish, estimated * 2)
    synth.speak(utterance)
  })
}

function speakWithMeSpeak(text, pitch, rate, volume) {
  return new Promise((resolve) => {
    try {
      // meSpeak 的 pitch 范围 0-100（默认 50），系统 pitch 通常 0-2
      // 把人物设定 pitch 真实映射进去，让不同男声有区分：
      //   胖叔 0.74 → 28（低沉）、中年男性 0.82 → 31、路人 0.9 → 33
      // 极端兜底（女声降调 0.45）→ 18
      const msPitch = Math.max(14, Math.min(Math.round((pitch || 1) * 38), 45))
      // meSpeak 的 speed 范围 0-450，默认 175；人物 rate 慢 → 语速慢（胖叔 0.9 → 158）
      const msSpeed = Math.round(175 * (rate || 1))
      // meSpeak 的 amplitude 范围 0-200，默认 100
      const msAmp = Math.round(100 * (volume || 1))

      // variant 'm' = 男声基础变体；显式指定 voice:'zh' 确保中文；wordgap 0 保持连贯
      meSpeakInstance.speak(text, {
        voice: 'zh',
        pitch: msPitch,
        speed: msSpeed,
        amplitude: msAmp,
        wordgap: 0,
        variant: 'm',
        raw: false
      })
      console.log(`[TTS] meSpeak 参数: pitch=${msPitch} speed=${msSpeed}`)

      // meSpeak 播放是内部触发的，给一个估算的 resolve 时间
      const estimated = Math.max(1500, (text.length / 4) * 1000 + 1000)
      setTimeout(resolve, estimated)
    } catch (e) {
      console.error('[TTS] meSpeak 朗读失败:', e)
      resolve()
    }
  })
}

export function stopUnifiedSpeaking() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
  // 同时停掉 meSpeak 正在播放的音频（否则旧声音会压着新声音）
  if (meSpeakInstance) {
    try {
      meSpeakInstance.stop()
    } catch (e) {
      /* 忽略停止异常 */
    }
  }
}
