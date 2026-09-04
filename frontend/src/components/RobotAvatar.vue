<template>
  <div ref="hostRef" class="robot-host" :style="hostStyle">
    <svg
      class="robot-svg"
      viewBox="0 0 200 260"
      xmlns="http://www.w3.org/2000/svg"
      :class="svgClass"
      :style="svgVars"
      aria-label="医疗急救机器人"
    >
      <defs>
        <!-- 卡通柔光阴影：让小熊有柔和体积感 -->
        <filter id="softShadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#3a2412" flood-opacity="0.18" />
        </filter>
      </defs>

      <!-- 机器人整体组：呼吸/下沉/颤抖都挂在这里 -->
      <g class="robot-body-group">
        <!-- ============ 腿部（小熊胖短腿） ============ -->
        <g class="legs">
          <ellipse class="leg leg-left" cx="78" cy="232" rx="11" ry="16"
                   fill="#f7d99a" stroke="#8b6f3a" stroke-width="2" />
          <ellipse class="leg leg-right" cx="122" cy="232" rx="11" ry="16"
                   fill="#f7d99a" stroke="#8b6f3a" stroke-width="2" />
          <!-- 鞋底浅奶油边（小熊胖脚） -->
          <ellipse cx="78"  cy="247" rx="13" ry="5" fill="#fffaf0" stroke="#8b6f3a" stroke-width="1.4" />
          <ellipse cx="122" cy="247" rx="13" ry="5" fill="#fffaf0" stroke="#8b6f3a" stroke-width="1.4" />
        </g>

        <!-- ============ 躯干（小熊身体 + 白大褂） ============ -->
        <g class="torso-group">
          <!-- 小熊身体（圆胖体，浅黄奶油色） -->
          <rect
            x="56"
            y="106"
            width="88"
            height="108"
            rx="22"
            fill="#f7d99a"
            stroke="#8b6f3a"
            stroke-width="2"
            filter="url(#softShadow)"
          />

          <!-- 白大褂：覆盖躯干大部分的白色外套 + V 领露出原色 + 中央对襟粗线 + 大纽扣 + 左右胸袋 + 衣摆下沿，强化医护形象 -->
          <g class="coat" aria-hidden="true">
            <!-- 大褂主体：覆盖躯干除 V 领外的全部区域，圆角下摆 -->
            <path
              class="coat-body"
              d="M58 122
                 C 58 116, 62 112, 68 112
                 L 80 112
                 L 100 138
                 L 120 112
                 L 132 112
                 C 138 112, 142 116, 142 122
                 L 142 208
                 C 142 212, 138 214, 134 214
                 L 66 214
                 C 62 214, 58 212, 58 208
                 Z"
              fill="#ffffff"
              stroke="#b6cbd9"
              stroke-width="1.4"
            />
            <!-- V 领内边：领口加深一圈描边 -->
            <path
              class="coat-collar-edge"
              d="M80 112 L100 138 L120 112"
              fill="none"
              stroke="#9aa9b8"
              stroke-width="0.8"
            />
            <!-- 衣领白边（领口内壁高光，让 V 领更立体） -->
            <path
              class="coat-collar-rim"
              d="M82 113.5 L100 137 L118 113.5"
              fill="none"
              stroke="#ffffff"
              stroke-width="1.4"
              stroke-linecap="round"
            />
            <!-- 中央对襟粗线（白大褂前襟） -->
            <line class="coat-seam" x1="100" y1="138" x2="100" y2="212" stroke="#9aa9b8" stroke-width="1" />
            <!-- 4 颗大纽扣（中央对襟，醒目） -->
            <circle class="coat-button" cx="100" cy="148" r="2.6" fill="#5b6a7a" stroke="#3a4655" stroke-width="0.5" />
            <circle class="coat-button" cx="100" cy="162" r="2.6" fill="#5b6a7a" stroke="#3a4655" stroke-width="0.5" />
            <circle class="coat-button" cx="100" cy="176" r="2.6" fill="#5b6a7a" stroke="#3a4655" stroke-width="0.5" />
            <circle class="coat-button" cx="100" cy="190" r="2.6" fill="#5b6a7a" stroke="#3a4655" stroke-width="0.5" />
            <!-- 左侧胸袋（白大褂典型口袋） -->
            <rect class="coat-pocket" x="65" y="141" width="16" height="20" rx="2.5" fill="#ffffff" stroke="#9aa9b8" stroke-width="0.9" />
            <!-- 口袋内一支笔 -->
            <rect x="73" y="141" width="1.6" height="9" fill="#3a4655" />
            <rect x="75" y="141" width="1.6" height="11" fill="#4a9bd1" />
            <!-- 右侧胸袋 -->
            <rect class="coat-pocket" x="119" y="141" width="16" height="20" rx="2.5" fill="#ffffff" stroke="#9aa9b8" stroke-width="0.9" />
            <!-- 衣摆下沿阴影线（立体感） -->
            <line class="coat-hem" x1="60" y1="211" x2="140" y2="211" stroke="#9aa9b8" stroke-width="0.7" />
          </g>

          <!-- 医疗盾形徽章（按图：小熊左胸口袋位置 + 盾形 + 红色十字） -->
          <g class="medical-shield">
            <path d="M84 134 L84 152 L93 156 L93 137 Z"
                  fill="#ffd35a" stroke="#8b6f3a" stroke-width="1.2" />
            <rect x="87" y="138" width="1.8" height="6.2" rx="0.5" fill="#d64545" />
            <rect x="85.4" y="139.6" width="5" height="1.8" rx="0.5" fill="#d64545" />
          </g>
        </g>

        <!-- ============ 头部（小熊：耳朵 + 圆脸 + 大黑眼 + 嘴周白圈 + 月牙嘴） ============ -->
        <g class="head-group">
          <!-- 耳朵（在头后面先画，让头圆下边覆盖） -->
          <g class="ears">
            <circle cx="46"  cy="32" r="20" fill="#f7d99a" stroke="#8b6f3a" stroke-width="2" />
            <circle cx="46"  cy="34" r="11" fill="#ffe2a3" stroke="#8b6f3a" stroke-width="1" />
            <circle cx="154" cy="32" r="20" fill="#f7d99a" stroke="#8b6f3a" stroke-width="2" />
            <circle cx="154" cy="34" r="11" fill="#ffe2a3" stroke="#8b6f3a" stroke-width="1" />
          </g>

          <!-- 头壳（face：脸色随 choking 压迫 奶油→紫青发绀） -->
          <ellipse
            class="head-face"
            cx="100"
            cy="80"
            rx="62"
            ry="58"
            :fill="headSkinColor"
            stroke="#8b6f3a"
            stroke-width="2"
            filter="url(#softShadow)"
          />

          <!-- 眉骨：图中两道短弧（默认显示，浅棕） -->
          <path d="M68 56 Q78 50 90 56"
                fill="none" stroke="#8b6f3a" stroke-width="2.4" stroke-linecap="round" />
          <path d="M110 56 Q122 50 132 56"
                fill="none" stroke="#8b6f3a" stroke-width="2.4" stroke-linecap="round" />

          <!-- 担忧眉（仅 concerned 表情亮起，stroke 颜色走 CSS 变量） -->
          <path class="brow brow-left"  d="M72 52 Q80 47 88 52" />
          <path class="brow brow-right" d="M112 52 Q120 47 128 52" />

          <!-- 大黑眼（黑眼圈 + 白色高光，让眼神可爱） -->
          <g class="eyes">
            <circle class="eye-ring eye-left"  cx="78"  cy="82" r="13" fill="#1f1a14" />
            <circle class="eye-dot eye-left"   cx="82"  cy="78" r="3.2" fill="#ffffff" />
            <circle class="eye-ring eye-right" cx="122" cy="82" r="13" fill="#1f1a14" />
            <circle class="eye-dot eye-right"  cx="126" cy="78" r="3.2" fill="#ffffff" />
            <!-- 泪滴（仅 crying 表情显示） -->
            <path class="tear tear-left"  d="M78  100 C82  108 84  112 78  116 C72  112 74  108 78  100 Z" />
            <path class="tear tear-right" d="M122 100 C126 108 128 112 122 116 C116 112 118 108 122 100 Z" />
          </g>

          <!-- 腮红 -->
          <ellipse class="cheek cheek-left"  cx="55"  cy="100" rx="11" ry="6.5" fill="#ff9eb5" opacity="0.82" />
          <ellipse class="cheek cheek-right" cx="145" cy="100" rx="11" ry="6.5" fill="#ff9eb5" opacity="0.82" />

          <!-- 嘴周白圈（图中嘴周围的奶油色弧，中心与嘴缝一致 y≈106） -->
          <ellipse cx="100" cy="106" rx="23" ry="14"
                   fill="#fffaf0" stroke="#8b6f3a" stroke-width="1.6" />

          <!-- 鼻子（嘴缝正上方，紧贴白圈上沿内侧） -->
          <ellipse cx="100" cy="92.5" rx="3.6" ry="2.6" fill="#1f1a14" />

          <!-- 嘴：静态表情用 path（笑/哭/痛苦…），说话时切到 ellipse 做粉舌头开合 -->
          <path class="mouth-shape" :d="mouthPath" fill="none" stroke-width="3" stroke-linecap="round" />
          <ellipse class="mouth-talk" cx="100" cy="106" rx="10" ry="1.5" />
        </g>

        <!-- ============ 手臂（小熊胖短手，颜色由 CSS 强制身体色 #f7d99a） ============ -->
        <!-- 左臂：肩 → 上臂 → 肘 → 前臂 → 手 -->
        <g class="arm arm-left">
          <rect class="upper-arm" x="42" y="128" width="20" height="34" rx="10" />
          <circle class="elbow" cx="52" cy="162" r="7" />
          <g class="forearm-group forearm-left">
            <rect class="fore-arm" x="42" y="156" width="20" height="30" rx="10" />
            <circle class="hand" cx="52" cy="190" r="10" />
          </g>
        </g>

        <!-- 右臂 -->
        <g class="arm arm-right">
          <rect class="upper-arm" x="138" y="128" width="20" height="34" rx="10" />
          <circle class="elbow" cx="148" cy="162" r="7" />
          <g class="forearm-group forearm-right">
            <rect class="fore-arm" x="138" y="156" width="20" height="30" rx="10" />
            <circle class="hand" cx="148" cy="190" r="10" />
          </g>
        </g>
      </g>
    </svg>

    <!-- 时间压迫提示条 -->
    <transition name="fade">
      <div v-if="showPressureBar" class="pressure-bar" :style="{ '--p': pressureValue }">
        <span class="p-stage">{{ pressureMeta.emoji }} {{ pressureMeta.text }}</span>
        <span class="p-track"><i /></span>
      </div>
    </transition>

    <div v-if="status === 'loading'" class="mask">
      <div class="spinner" />
      <p>正在启动机器人…</p>
    </div>

    <div v-else-if="status === 'error'" class="mask is-error">
      <p class="err-title">机器人启动失败</p>
      <p class="err-detail">{{ errorMsg }}</p>
    </div>

    <transition name="fade">
      <span v-if="speaking" class="speaking-badge" aria-label="正在说话">
        <span class="wave"><i /><i /><i /></span>
        说话中
      </span>
    </transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { IDLE_CYCLE, IDLE_CYCLE_CHOKING, IDLE_CYCLE_PSYCH, ROLE_PROFILE, moodColor, pressureStage } from '@/utils/live2dMap'

const props = defineProps({
  role: { type: String, default: 'patient' },
  speaking: { type: Boolean, default: false },
  expression: { type: String, default: 'neutral' },
  // 肢体动作：deepBreath / waveHigh / clutchThroat / chestPat / slump / reachOut / nod / shakeHead / explain / idle / idleChoke
  action: { type: String, default: 'idle' },
  // 时间压迫强度 0（平稳）→ 1（濒危）：驱动眼睛蓝→黄→红、屏幕黑→红
  pressure: { type: Number, default: 0 },
  // 场景：choking（异物梗阻）/ firstVisit（第一次独立看病）/ other
  scene: { type: String, default: 'other' },
  persona: { type: Object, default: null }
})

const hostRef = ref(null)
const status = ref('loading')
const errorMsg = ref('')

const profile = computed(() => ROLE_PROFILE[props.role] || ROLE_PROFILE.patient)
const hostStyle = computed(() => ({ background: profile.value.bg }))

const svgClass = computed(() => ({
  'is-speaking': props.speaking,
  'is-idle-loop': isIdle.value,
  [`is-scene-${props.scene}`]: true,
  [`is-mood-${effectiveExpression.value}`]: true,
  [`is-action-${effectiveAction.value}`]: true,
  [`is-micro-${speakMicro.value}`]: true,
  'has-pressure': pressureValue.value > 0.02
}))

const pressureValue = computed(() => Math.max(0, Math.min(1, Number(props.pressure) || 0)))
const pressureMeta = computed(() => pressureStage(pressureValue.value))
const showPressureBar = computed(() => pressureValue.value > 0.02)

// ---------------------------------------------------------------
// 挂机动作轮换：无对话 + 无指定动作 + 无时间压迫时，
// 在「待机 → 拍手 → 待机 → 外展双臂」之间循环，避免数字人僵住
// ---------------------------------------------------------------
const IDLE_INTERVAL = 4200 // 每个挂机动作持续约 4.2 秒
const idleVariant = ref('idle')
let idleTimer = null
let idleIdx = 0

// 是否处于挂机态：窒息/时间压迫中不应出现拍手这类轻松动作
const isIdle = computed(
  () => !props.speaking && props.action === 'idle' && pressureValue.value < 0.02
)

function stopIdleCycle() {
  if (idleTimer) {
    clearInterval(idleTimer)
    idleTimer = null
  }
}

function startIdleCycle() {
  stopIdleCycle()
  idleIdx = 0
  // 按场景选挂机池：梗阻=捂喉干呕；心理陪伴=待机/温柔摊手/点头（等待输入时也不呆立）；普通=拍手/外展双臂
  let cycle = IDLE_CYCLE
  if (props.scene === 'choking') cycle = IDLE_CYCLE_CHOKING
  else if (props.scene === 'psych') cycle = IDLE_CYCLE_PSYCH
  // 心理陪伴等待节奏稍快一点（约 3.4s 换一个动作），让“等你开口”有更多生命感
  const interval = props.scene === 'psych' ? 3400 : IDLE_INTERVAL
  idleVariant.value = cycle[0]
  idleTimer = window.setInterval(() => {
    idleIdx = (idleIdx + 1) % cycle.length
    idleVariant.value = cycle[idleIdx]
  }, interval)
}

// 实际渲染的动作：
// - 异物梗阻场景：从进场第一帧起「无脑钳制」为捂喉——任何说话 / 表情线索都不覆盖，
//   直到离开该场景才恢复外部动作，保证进入场景的第一秒就是痛苦捂喉。
// - 其他场景：挂机走轮换池，否则用外部指定的动作
const effectiveAction = computed(() => {
  if (props.scene === 'choking') return 'clutchThroat'
  if (isIdle.value) return idleVariant.value
  // 说话时的点头/摇头交给「说话微动作」节奏接管（每 5s 一次左右交替摆头），
  // 避免 head-nod 高频循环（0.62s infinite）把摆头动画盖掉、看起来像一直右下点头
  if (props.speaking && (props.action === 'nod' || props.action === 'shakeHead')) return 'idle'
  return props.action
})

// 实际渲染的表情：梗阻场景同样无脑钳制为「窒息难受」
const effectiveExpression = computed(() => {
  if (props.scene === 'choking') return 'choking'
  return props.expression
})

watch(
  isIdle,
  (v) => {
    if (v) startIdleCycle()
    else stopIdleCycle()
  },
  { immediate: true }
)

// ---------------------------------------------------------------
// 说话微动作：说话中且没有明确动作指令（action 为 idle/空）时，
// 每 4~5 秒做一次动作（约 2 秒）：左右交替摆头、点头、摆手或温柔摊手，
// 让「只张嘴说话」也有自然的节奏。梗阻场景除外 —— 那里恒定捂喉挣扎。
// 心理场景节拍约 4 秒一次，且每段话开口先做一次「打招呼」。
// ---------------------------------------------------------------
// 状态：none | greet | tilt-left | tilt-right | nod | wave | open（greet/open=心理场景）
const speakMicro = ref('none')
const MICRO_INTERVAL = 5000
const MICRO_HOLD = 2000
let microTimer = null
let microHoldTimer = null
let lastMicroWave = false
let lastTiltDir = 'left' // 第一次摆向 left，下一次自动切到 right，交替进行

function stopSpeakMicro() {
  if (microTimer) {
    clearInterval(microTimer)
    microTimer = null
  }
  if (microHoldTimer) {
    clearTimeout(microHoldTimer)
    microHoldTimer = null
  }
  speakMicro.value = 'none'
}

function pickMicro() {
  // 心理陪伴：说话时手势更丰富 —— 摆头 45% / 点头 15% / 双手温柔摊开 25% / 单手轻摆 15%。
  // 相比急救/看病场景，心理场景多一只手部动作选项（open 摊手），让易心说话更有「在倾听、
  // 在安抚」的手势，而不只是头部小动作。
  if (props.scene === 'psych') {
    const r = Math.random()
    if (r < 0.45) {
      const dir = lastTiltDir === 'left' ? 'right' : 'left'
      lastTiltDir = dir
      return 'tilt-' + dir
    }
    if (r < 0.6) return 'nod'
    if (r < 0.85) return 'open'
    return 'wave'
  }

  // 非心理场景（急救 / 看病）：摆手是「偶尔」，摆手后至少隔一个完整周期才可能再摆
  if (!lastMicroWave && Math.random() < 0.2) {
    lastMicroWave = true
    return 'wave'
  }
  lastMicroWave = false
  // 70% 概率左右摆头（方向交替），20% 点头，10% 还是摆头（兜底）
  const r = Math.random()
  if (r < 0.7) {
    const dir = lastTiltDir === 'left' ? 'right' : 'left'
    lastTiltDir = dir
    return 'tilt-' + dir
  }
  if (r < 0.9) return 'nod'
  // 兜底也走摆头
  const dir = lastTiltDir === 'left' ? 'right' : 'left'
  lastTiltDir = dir
  return 'tilt-' + dir
}

function fireMicro() {
  if (props.scene === 'choking') return
  // 外部已给了明确动作（点头/摇头/摆手说明/伸手等）时不叠加，避免动画打架
  const a = props.action
  if (a && a !== 'idle' && a !== 'nod' && a !== 'shakeHead') return
  speakMicro.value = pickMicro()
  if (microHoldTimer) clearTimeout(microHoldTimer)
  microHoldTimer = setTimeout(() => {
    speakMicro.value = 'none'
  }, MICRO_HOLD)
}

function startSpeakMicro() {
  stopSpeakMicro()
  // 心理场景：开口第一拍固定做「打招呼」（抬手轻摆两三下，约 2.2s），
  // 让易心每段话的起点都像先挥手说“嗨，我在”，之后才进入 ~4s 的随机手势节拍
  if (props.scene === 'psych') {
    const a = props.action
    if (!a || a === 'idle' || a === 'nod' || a === 'shakeHead') {
      speakMicro.value = 'greet'
      microHoldTimer = setTimeout(() => {
        speakMicro.value = 'none'
      }, 2300)
    }
  } else {
    // 其他场景：立即做一次随机微动作（说话一开始就有头部节奏，不用干等 5 秒）
    fireMicro()
  }
  // 手势节拍：心理场景约 4 秒一次（更活络），急救/看病保持 5 秒一次
  const interval = props.scene === 'psych' ? 4000 : MICRO_INTERVAL
  microTimer = window.setInterval(fireMicro, interval)
}

watch(
  () => props.speaking,
  (v) => {
    if (v) startSpeakMicro()
    else stopSpeakMicro()
  }
)

// ---------------------------------------------------------------
// 颜色计算：表情主色 × 时间压迫色
// 眼睛：表情主色（如平静=淡蓝、着急=琥珀、窒息=淡紫）
//      开启时间压迫后被压向 蓝→黄→红 的危急色阶
// 屏幕（脸色）：紫(#5b21b6) → 紫红(#a31251) → 亮红(#e02b2b)，表示紧张程度
// ---------------------------------------------------------------
function hexToRgb(hex) {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function lerpColor(c1, c2, t) {
  const a = hexToRgb(c1)
  const b = hexToRgb(c2)
  const k = Math.max(0, Math.min(1, t))
  const mix = a.map((v, i) => Math.round(v + (b[i] - v) * k))
  return `rgb(${mix[0]}, ${mix[1]}, ${mix[2]})`
}

// 压迫色阶：0 → 0.5 → 1
function pressureEye(p) {
  return p <= 0.5 ? lerpColor('#00d4ff', '#ffc830', p / 0.5) : lerpColor('#ffc830', '#ff3b30', (p - 0.5) / 0.5)
}
// 梗阻脸色：紫（缺氧发绀）→ 紫红 → 红（危急），随时间压迫加深
function pressureScreen(p) {
  return p <= 0.5 ? lerpColor('#5b21b6', '#a31251', p / 0.5) : lerpColor('#a31251', '#e02b2b', (p - 0.5) / 0.5)
}

// 小熊皮肤发绀色阶（仅哽咽场景）：奶油 #f7d99a → 中段紫青 → 濒危深紫青
// 模拟缺氧时脸色逐渐变紫发青，越接近失败越明显
function chokeSkin(p) {
  return p <= 0.5
    ? lerpColor('#f7d99a', '#8f70d8', p / 0.5)
    : lerpColor('#8f70d8', '#5c47a8', (p - 0.5) / 0.5)
}

// 屏幕底色：仅异物梗阻场景用紫色脸（缺氧发绀），其他场景（看病/心理陪伴）保持深空屏
const SCREEN_BASE = '#15181d'
const SCREEN_BASE_CHOKING = '#5b21b6'

// 眼睛色 = 表情主色（moodColor）；开启时间压迫后被压向 蓝→黄→红 危急色阶
const eyeColor = computed(() => {
  const base = moodColor(props.expression) || '#7ec8e3'
  const p = pressureValue.value
  if (p <= 0.02) return base
  // 压迫越强，越盖过表情色（1.4 倍权重让中段就明显偏黄）
  return lerpColor(base, pressureEye(p), Math.min(1, p * 1.4))
})

const screenColor = computed(() => {
  const p = pressureValue.value
  const base = props.scene === 'choking' ? SCREEN_BASE_CHOKING : SCREEN_BASE
  return p <= 0.02 ? base : lerpColor(base, pressureScreen(p), Math.min(1, p * 1.25))
})

// 脸部皮肤底色：正常时奶油 #f7d99a；仅异物哽咽场景随时间压迫越大越偏紫青（发绀）
const headSkinColor = computed(() => {
  const p = pressureValue.value
  if (props.scene !== 'choking' || p <= 0.02) return '#f7d99a'
  return chokeSkin(p)
})

const svgVars = computed(() => ({
  '--eye-color': eyeColor.value,
  '--screen-color': screenColor.value,
  '--mood-color': moodColor(effectiveExpression.value) || '#7ec8e3',
  '--pressure': String(pressureValue.value)
}))

// ---------------------------------------------------------------
// 嘴型：静态表情用 path，说话时由 ellipse 接管开合
// ---------------------------------------------------------------
const MOUTH_PATHS = {
  // 嘴缝视觉中心统一在 y≈106（与说话粉舌椭圆 .mouth-talk cy=106 同高，切换不跳位）
  // 平静 / 从容：几乎水平的微弧
  neutral: 'M89 105 Q100 108.5 111 105',
  calm: 'M89 105.5 Q100 108.5 111 105.5',
  // 微笑 / 开心 / 松口气：咧嘴月牙（∪ 两端上扬，中段下弯像笑开的嘴缝）
  smile: 'M86 100 Q100 112 114 100',
  happy: 'M84 99 Q100 114.5 116 99',
  relieved: 'M87 101.5 Q100 111.5 113 101.5',
  // 流泪：倒弧（嘴角下撇，中段上拱）
  crying: 'M90 109 Q100 99.5 110 109',
  // 着急 / 疑惑：紧绷的小弧
  anxious: 'M91 107.5 Q100 102.5 109 107.5',
  confused: 'M90 106.5 Q94.5 108.8 100 105.5 Q105.5 102.8 110 106.8',
  concerned: 'M90 108.5 Q100 103.5 110 108.5',
  // 窒息 / 哽咽 / 支撑不住：痛苦波浪
  suffering: 'M85 105.5 Q92 99 100 105.5 Q108 112 115 105.5',
  choking: 'M85 105.5 Q92 99 100 105.5 Q108 112 115 105.5',
  collapsed: 'M87 107 Q93 111.5 100 107 Q107 102.5 113 107',
  // 精神萎靡：无力下垂
  listless: 'M90 107 Q100 110 110 107',
  // 说明 / 观察 / 惊讶：小圆口（惊讶更大）
  explaining: 'M91 106 Q100 109 109 106',
  observing: 'M92 106.5 Q100 109 108 106.5',
  surprised: 'M92 103.5 Q100 111 108 103.5',
  // 难过 / 疲倦：嘴角略下撇 / 平缓无力
  sad: 'M90 108 Q100 100.5 110 108',
  tired: 'M91 106.5 Q100 102.5 109 106.5',
  angry: 'M89 108.5 Q100 100.5 111 108.5'
}

const mouthPath = computed(() => MOUTH_PATHS[props.expression] || MOUTH_PATHS.neutral)

// ---------------------------------------------------------------
// 嘴型同步：说话时按波形开合，并把静态 path 淡出让位
// ---------------------------------------------------------------
let mouthTarget = 0
let mouthCurrent = 0
let talkStart = 0
let rafId = null

function mouthWave(elapsed) {
  const t = elapsed
  // 说话嘴型频率系数：原 2/3，按需求再降低 1/3 → 4/9（两个场景都生效）
  const k = 4 / 9
  const primary = Math.abs(Math.sin(t * 0.026 * k))
  const harmonic = Math.abs(Math.sin(t * 0.026 * 2.37 * k)) * 0.32
  const envelope = 0.62 + 0.38 * (0.5 + 0.5 * Math.sin(t * 0.0042 * k))
  return Math.min(1, (primary * 0.72 + harmonic) * envelope)
}

function onFrame() {
  if (props.speaking) {
    mouthTarget = mouthWave(performance.now() - talkStart)
  } else {
    mouthTarget = 0
  }
  mouthCurrent += (mouthTarget - mouthCurrent) * 0.35

  const host = hostRef.value
  if (host) {
    const talk = host.querySelector('.mouth-talk')
    const shape = host.querySelector('.mouth-shape')
    if (talk) {
      // 闭合 ry=1.2，张开最大 ry=8.5，开合更明显
      talk.setAttribute('ry', (1.2 + mouthCurrent * 7.3).toFixed(2))
      talk.style.opacity = mouthCurrent.toFixed(3)
    }
    if (shape) shape.style.opacity = (1 - mouthCurrent).toFixed(3)
  }

  rafId = requestAnimationFrame(onFrame)
}

onMounted(() => {
  try {
    status.value = 'ready'
    rafId = requestAnimationFrame(onFrame)
  } catch (e) {
    console.error('[RobotAvatar] 启动失败', e)
    errorMsg.value = e?.message || '未知错误'
    status.value = 'error'
  }
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  stopIdleCycle()
  stopSpeakMicro()
})

watch(
  () => props.speaking,
  (v) => {
    if (v) talkStart = performance.now()
  }
)

defineExpose({
  startTalk: () => {
    talkStart = performance.now()
  }
})
</script>

<style scoped lang="scss">
.robot-host {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.robot-svg {
  width: 100%;
  height: 100%;
  max-width: 320px;
  max-height: 420px;
  display: block;
  // 颜色由 JS 按「表情 × 时间压迫 × 场景」计算后注入
  --eye-color: #7ec8e3;
  --screen-color: #15181d;
  --mood-color: #7ec8e3;
  --pressure: 0;
}

/* 所有 SVG 组的变换原点统一用 viewBox 坐标系 */
.robot-body-group,
.head-group,
.arm,
.forearm-group,
.torso-group {
  transform-box: view-box;
}

/* ===== 躯干：深呼吸时横向起伏 ===== */
.torso-group {
  transform-origin: 100px 160px;
}

/* ===== 待机呼吸 ===== */
.robot-body-group {
  transform-origin: 100px 180px;
  animation: robot-breathe 2.6s ease-in-out infinite;
}

@keyframes robot-breathe {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-3px) scale(1.01); }
}

/* ===== 头部：点头 / 摇头的旋转中心在颈部 ===== */
.head-group {
  transform-origin: 100px 118px;
}

/* ===== 天线 & 胸前面板灯 ===== */
.antenna-bulb {
  fill: var(--eye-color);
  opacity: 0.85;
  animation: antenna-pulse 1.8s ease-in-out infinite;
  transition: fill 0.4s ease;
}

.panel-light {
  fill: var(--eye-color);
  animation: panel-blink 2.2s ease-in-out infinite;
  transition: fill 0.4s ease;
}
.panel-light:nth-child(2) { animation-delay: 0.3s; }
.panel-light:nth-child(3) { animation-delay: 0.6s; }
.panel-light:nth-child(4) { animation-delay: 0.9s; }

@keyframes panel-blink {
  0%, 100% { opacity: 0.45; }
  50% { opacity: 1; }
}
@keyframes antenna-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* ===== 眼睛 / 眼色：小熊大黑眼 fill 走 SVG 属性（黑 + 高光），stroke 走眼色变量仅作描边 ===== */
.eye-ring {
  stroke: var(--eye-color);
  transition: stroke 0.45s ease, opacity 0.35s ease;
}
.eye-dot {
  fill: var(--eye-color);
  transition: fill 0.45s ease, opacity 0.35s ease;
}
.face-screen { transition: fill 0.6s ease; }

/* ===== 白大褂（医护形象）：肩披 / 对襟 / 纽扣 / 口袋 / 白色长袖 ===== */
.coat-shoulder {
  fill: #ffffff;
  stroke: #cfdde8;
  stroke-width: 1.2;
}
.coat-seam {
  stroke: #b6cbd9;
  stroke-width: 1.2;
  stroke-dasharray: 3 3;
}
.coat-button {
  fill: #eef5fa;
  stroke: #8fb4cf;
  stroke-width: 1.1;
}
.coat-pocket {
  fill: #ffffff;
  stroke: #b6cbd9;
  stroke-width: 1.1;
}
/* ===== 卡通小熊手臂：小熊身体色（浅黄奶油）+ 棕色描边，整体一段，不要白大褂长袖盖住 ===== */
.arm .upper-arm,
.arm .fore-arm {
  fill: #f7d99a;
  stroke: #8b6f3a;
  stroke-width: 2;
}
/* 肘关节 + 圆胖短手：小熊肤色 + 棕描边 */
.arm .elbow,
.arm .hand {
  fill: #f7d99a;
  stroke: #8b6f3a;
  stroke-width: 2;
}

/* ===== 担忧眉：仅 concerned（担忧）表情亮起，内端微蹙上挑 ===== */
.brow {
  fill: none;
  stroke: var(--eye-color);
  stroke-width: 2.2;
  stroke-linecap: round;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.is-mood-concerned .brow {
  opacity: 0.95;
}

/* 压迫越高，屏幕辉光越明显、脉动越快 */
.screen-glow {
  opacity: calc(var(--pressure) * 0.55);
  transition: opacity 0.6s ease, fill 0.6s ease;
}
.has-pressure .screen-glow {
  animation: screen-pulse 1.4s ease-in-out infinite;
}
@keyframes screen-pulse {
  0%, 100% { opacity: calc(var(--pressure) * 0.3); }
  50% { opacity: calc(var(--pressure) * 0.7); }
}

/* ===== 头壳脸色：随 choking 压迫平滑渐变紫青（发绀） ===== */
.head-face {
  transition: fill 0.6s ease;
}

/* ===== 嘴（按小熊改：mouth-shape 固定红色弧线贴近原版；mouth-talk 说话时是同色系红嘴开合） ===== */
.mouth-shape {
  stroke: #e05252;
  opacity: 1;
  transition: opacity 0.1s linear;
}
.mouth-talk {
  fill: #f27878;
  opacity: 0;
}

/* 说话时：彻底隐藏原弧线嘴（避免两个嘴同时出现），
   强制显示椭圆开合嘴（不受 mouthCurrent 起始值影响） */
.is-speaking .mouth-shape {
  opacity: 0 !important;
}
.is-speaking .mouth-talk {
  opacity: 1 !important;
}

/* ===== 泪滴：默认隐藏，crying 时下落 ===== */
.tear {
  fill: #6fc8ff;
  opacity: 0;
}
.is-mood-crying .tear {
  animation: tear-fall 1.6s ease-in infinite;
}
.is-mood-crying .tear-right {
  animation-delay: 0.45s;
}
@keyframes tear-fall {
  0% { opacity: 0; transform: translateY(0) scale(0.6); }
  25% { opacity: 0.95; transform: translateY(4px) scale(1); }
  75% { opacity: 0.8; transform: translateY(14px) scale(0.9); }
  100% { opacity: 0; transform: translateY(20px) scale(0.6); }
}

/* ===== 手臂：肩部旋转 ===== */
.arm {
  transition: transform 0.45s cubic-bezier(0.34, 1.3, 0.64, 1);
}
.arm-left { transform-origin: 52px 132px; }
.arm-right { transform-origin: 148px 132px; }

/* ===== 前臂：肘部旋转 ===== */
.forearm-group {
  transition: transform 0.45s cubic-bezier(0.34, 1.3, 0.64, 1);
}
.forearm-left { transform-origin: 52px 160px; }
.forearm-right { transform-origin: 148px 160px; }

/* 说话时的手臂动作统一交给「说话微动作」节奏（每 5s 偶发一次摆手），
   不再无限循环摆动，避免碎动盖住头部摆头观感 */

@keyframes wave-left {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(8deg); }
}
@keyframes wave-right {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(-8deg); }
}

/* =========================================================
   说话微动作：每 ~5s 一次「左右交替」的轻微摆头（单次约 2s），
   偶尔穿插轻微点头或摆手。只作用于说话中且无明确动作指令时
   ========================================================= */
.is-micro-tilt-left .head-group {
  animation: micro-tilt-left 2s ease-in-out 1;
}
.is-micro-tilt-right .head-group {
  animation: micro-tilt-right 2s ease-in-out 1;
}
.is-micro-nod .head-group {
  animation: micro-nod 2s ease-in-out 1;
}
.is-micro-wave .arm-right {
  animation: micro-wave-arm 2s ease-in-out 1;
}

/* 轻摆头向左：±5° 左右小角度，绕颈部左右歪头（不低头） */
@keyframes micro-tilt-left {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-5deg); }
  55% { transform: rotate(1.2deg); }
  80% { transform: rotate(-2deg); }
}
/* 轻摆头向右：与向左镜像 */
@keyframes micro-tilt-right {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(5deg); }
  55% { transform: rotate(-1.2deg); }
  80% { transform: rotate(2deg); }
}
/* 轻微点头：纯上下移动（不向左右倾），更像真人点头 */
@keyframes micro-nod {
  0%, 100% { transform: translateY(0); }
  20% { transform: translateY(2.4px); }
  45% { transform: translateY(0.3px); }
  68% { transform: translateY(1.8px); }
  86% { transform: translateY(0.1px); }
}
/* 偶发摆手：右臂小幅抬起摆动（区别于呼救的高臂大动作） */
@keyframes micro-wave-arm {
  0%, 100% { transform: rotate(-14deg); }
  26% { transform: rotate(-30deg); }
  52% { transform: rotate(-20deg); }
  78% { transform: rotate(-32deg); }
}

/* 心理场景专用「打招呼」：每段话开口第一拍，右臂抬起在身侧轻摆两三下（像挥手说“嗨”），
   左臂微抬保持平衡，约 2.2s 内完成并收回 */
.is-micro-greet .arm-left {
  transform: rotate(4deg);
}
.is-micro-greet .arm-right {
  animation: micro-greet 2.2s ease-in-out 1;
}
@keyframes micro-greet {
  0%, 100% { transform: rotate(-16deg); }
  14% { transform: rotate(-60deg); }
  30% { transform: rotate(-42deg); }
  46% { transform: rotate(-66deg); }
  62% { transform: rotate(-46deg); }
  80% { transform: rotate(-56deg); }
}

/* 心理场景专用说话手势：双臂温柔摊开（像“敞开怀抱、慢慢说”），持续约 2s 后收回 */
.is-micro-open .arm-left {
  animation: micro-open-left 2s ease-in-out 1;
}
.is-micro-open .arm-right {
  animation: micro-open-right 2s ease-in-out 1;
}
@keyframes micro-open-left {
  0%, 100% { transform: rotate(0deg); }
  28% { transform: rotate(-21deg); }
  62% { transform: rotate(-9deg); }
}
@keyframes micro-open-right {
  0%, 100% { transform: rotate(0deg); }
  28% { transform: rotate(21deg); }
  62% { transform: rotate(9deg); }
}

/* =========================================================
   心理陪伴「等待开口」：用户在打字/沉默时，易心也不呆立 ——
   身体保持呼吸，头部以约 9s 一个周期缓慢左右轻转，像在安静地看着你、等你继续说
   ========================================================= */
.is-scene-psych.is-idle-loop.is-action-idle .head-group {
  animation: psych-wait-look 9s ease-in-out infinite;
}
@keyframes psych-wait-look {
  0%, 100% { transform: rotate(0deg) translateY(0); }
  18% { transform: rotate(-2.4deg) translateY(0.3px); }
  42% { transform: rotate(2deg) translateY(0.6px); }
  66% { transform: rotate(-1.2deg) translateY(0.2px); }
  84% { transform: rotate(0.8deg) translateY(0.5px); }
}

/* =========================================================
   心理陪伴「温柔摊手」挂机动作：双臂缓慢地向两侧摊开一点再收回（约 3.4s 一个周期，
   跟挂机轮换窗口同步，能完整看到一次张开），幅度比说话摊手小，安静不打扰 ——
   像咨询师轻声说“你可以继续说”
   ========================================================= */
.is-action-psychOpen .arm-left {
  animation: psych-open-left 3.4s ease-in-out infinite;
}
.is-action-psychOpen .arm-right {
  animation: psych-open-right 3.4s ease-in-out infinite;
}
.is-action-psychOpen .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, psych-open-sway 3.4s ease-in-out infinite;
}
@keyframes psych-open-left {
  0%, 100% { transform: rotate(-3deg); }
  30% { transform: rotate(-19deg); }
  72% { transform: rotate(-8deg); }
}
@keyframes psych-open-right {
  0%, 100% { transform: rotate(3deg); }
  30% { transform: rotate(19deg); }
  72% { transform: rotate(8deg); }
}
@keyframes psych-open-sway {
  0%, 100% { transform: translateY(0) scale(1); }
  30% { transform: translateY(-2px) scale(1.012); }
}

/* =========================================================
   动作 1：深呼吸 —— 躯干起伏加大 + 双臂外展再收回
   ========================================================= */
.is-action-deepBreath .torso-group {
  animation: breathe-expand 3.4s ease-in-out infinite;
}
.is-action-deepBreath .arm-left {
  animation: breathe-arm-left 3.4s ease-in-out infinite;
}
.is-action-deepBreath .arm-right {
  animation: breathe-arm-right 3.4s ease-in-out infinite;
}
.is-action-deepBreath .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, breathe-rise 3.4s ease-in-out infinite;
}

@keyframes breathe-expand {
  0%, 100% { transform: scale(1, 1); }
  45% { transform: scale(1.09, 1.045); }
  70% { transform: scale(0.97, 1); }
}
@keyframes breathe-arm-left {
  0%, 100% { transform: rotate(6deg); }
  45% { transform: rotate(26deg); }
  70% { transform: rotate(2deg); }
}
@keyframes breathe-arm-right {
  0%, 100% { transform: rotate(-6deg); }
  45% { transform: rotate(-26deg); }
  70% { transform: rotate(-2deg); }
}
@keyframes breathe-rise {
  0%, 100% { transform: translateY(0) scale(1); }
  45% { transform: translateY(-5px) scale(1.02); }
}

/* =========================================================
   动作 2：高臂挥手 —— 右臂高举过头左右摆动（呼救）
   ========================================================= */
.is-action-waveHigh .arm-right {
  animation: high-wave 0.85s ease-in-out infinite;
}
.is-action-waveHigh .arm-left {
  transform: rotate(10deg);
}
.is-action-waveHigh .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, wave-bounce 0.85s ease-in-out infinite;
}

/* 右臂抬起约 165° 举过肩，再左右摆动手掌 */
@keyframes high-wave {
  0%, 100% { transform: rotate(-168deg); }
  50% { transform: rotate(-150deg); }
}
@keyframes wave-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* =========================================================
   动作 3：双手捂住脖子 —— 异物梗阻的经典窒息姿势
   双臂向内上折，双手贴到喉咙两侧，配合身体颤抖
   ========================================================= */
.is-action-clutchThroat .arm-left {
  animation: clutch-left 0.55s ease-in-out infinite alternate;
}
.is-action-clutchThroat .arm-right {
  animation: clutch-right 0.55s ease-in-out infinite alternate;
}
.is-action-clutchThroat .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, choke-shake 0.42s ease-in-out infinite;
}
.is-action-clutchThroat .head-group {
  /* 痛苦摆头：1.8s 一个大周期，左右 4~7° 挣扎摆动（身体仍保留高频微颤） */
  animation: agony-head 1.8s ease-in-out infinite;
}

/* 负角度 = 向身体内侧（右）折起，双手够到喉咙 */
@keyframes clutch-left {
  0% { transform: rotate(-118deg); }
  100% { transform: rotate(-126deg); }
}
@keyframes clutch-right {
  0% { transform: rotate(118deg); }
  100% { transform: rotate(126deg); }
}
@keyframes choke-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-1.8px); }
  75% { transform: translateX(1.8px); }
}
@keyframes agony-head {
  0%, 100% { transform: rotate(0deg) translateY(0); }
  16% { transform: rotate(-7deg) translateX(-1.6px) translateY(-0.6px); }
  38% { transform: rotate(5.5deg) translateX(1.4px) translateY(0.4px); }
  58% { transform: rotate(-4deg) translateX(-1px) translateY(1px); }
  78% { transform: rotate(3deg) translateX(0.8px) translateY(0.3px); }
}

/* =========================================================
   动作 4：劫后余生拍胸脯 —— 双手交替轻拍胸口
   ========================================================= */
.is-action-chestPat .arm-left {
  animation: chest-pat-left 0.62s ease-in-out infinite;
}
.is-action-chestPat .arm-right {
  animation: chest-pat-right 0.62s ease-in-out infinite;
}
.is-action-chestPat .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, relief-sway 1.5s ease-in-out infinite;
}

/* 手臂折到胸前，前臂回勾让手掌贴胸，再小幅拍动 */
@keyframes chest-pat-left {
  0%, 100% { transform: rotate(-78deg); }
  50% { transform: rotate(-88deg); }
}
@keyframes chest-pat-right {
  0%, 100% { transform: rotate(78deg); }
  50% { transform: rotate(88deg); }
}
@keyframes relief-sway {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-2px) rotate(1.2deg); }
}

/* 拍胸时前臂回勾，手掌朝内贴住胸口 */
.is-action-chestPat .forearm-left { transform: rotate(-52deg); }
.is-action-chestPat .forearm-right { transform: rotate(52deg); }

/* =========================================================
   动作 5：精神萎靡 —— 身体下沉、头低垂、动作迟缓
   ========================================================= */
.is-action-slump .robot-body-group {
  animation: slump-sink 3.6s ease-in-out infinite;
}
.is-action-slump .head-group {
  animation: slump-head 3.6s ease-in-out infinite;
}
.is-action-slump .arm-left { transform: rotate(14deg); }
.is-action-slump .arm-right { transform: rotate(-14deg); }
.is-action-slump .eye-ring,
.is-action-slump .eye-dot { opacity: 0.55; }

@keyframes slump-sink {
  0%, 100% { transform: translateY(6px) scaleY(0.955); }
  50% { transform: translateY(9px) scaleY(0.94); }
}
@keyframes slump-head {
  0%, 100% { transform: rotate(7deg) translateY(3px); }
  50% { transform: rotate(9deg) translateY(4.5px); }
}

/* =========================================================
   动作 6：伸手 —— 右臂向前下方递出（递单据 / 递卡）
   ========================================================= */
.is-action-reachOut .arm-right {
  animation: reach-out 1.5s ease-in-out infinite;
}
.is-action-reachOut .arm-left { transform: rotate(5deg); }
.is-action-reachOut .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, reach-lean 1.5s ease-in-out infinite;
}

/* 手臂略向外下伸出，前臂回勾让手掌朝上（像托着东西递出去） */
@keyframes reach-out {
  0%, 100% { transform: rotate(-18deg); }
  45% { transform: rotate(-34deg); }
}
@keyframes reach-lean {
  0%, 100% { transform: translateY(0); }
  45% { transform: translateY(-2px); }
}
.is-action-reachOut .forearm-right {
  animation: reach-forearm 1.5s ease-in-out infinite;
}
@keyframes reach-forearm {
  0%, 100% { transform: rotate(-30deg); }
  45% { transform: rotate(-62deg); }
}

/* =========================================================
   动作 7：点头 —— 点 3 下后回到正常
   ========================================================= */
.is-action-nod .head-group {
  animation: head-nod 0.62s ease-in-out infinite;
}
/* 点头 = 纯上下（不做 rotate，避免绕颈部原点产生「向右下点」的观感） */
@keyframes head-nod {
  0%, 100% { transform: translateY(0); }
  30% { transform: translateY(5px); }
  62% { transform: translateY(1.2px); }
}

/* =========================================================
   动作 8：摇头 —— 摇 3 下后回到正常
   ========================================================= */
.is-action-shakeHead .head-group {
  animation: head-shake 0.58s ease-in-out infinite;
}
@keyframes head-shake {
  0%, 100% { transform: rotate(0deg) translateX(0); }
  20% { transform: rotate(-8deg) translateX(-2px); }
  60% { transform: rotate(8deg) translateX(2px); }
  80% { transform: rotate(-4deg) translateX(-1px); }
}

/* =========================================================
   动作 9：摆手说明 —— 右臂小幅摆动（讲解流程）
   ========================================================= */
.is-action-explain .arm-right {
  animation: explain-wave 0.75s ease-in-out infinite;
}
.is-action-explain .arm-left { transform: rotate(6deg); }
@keyframes explain-wave {
  0%, 100% { transform: rotate(-14deg); }
  50% { transform: rotate(-38deg); }
}

/* =========================================================
   挂机动作 A：拍手 —— 双臂内收，双手在身前轻拍（无对话时轮换出现）
   ========================================================= */
.is-action-idleClap .arm-left {
  animation: clap-left 0.46s ease-in-out infinite alternate;
}
.is-action-idleClap .arm-right {
  animation: clap-right 0.46s ease-in-out infinite alternate;
}
.is-action-idleClap .forearm-left { transform: rotate(-72deg); }
.is-action-idleClap .forearm-right { transform: rotate(72deg); }
.is-action-idleClap .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, clap-sway 0.46s ease-in-out infinite alternate;
}

@keyframes clap-left {
  from { transform: rotate(44deg); }
  to { transform: rotate(60deg); }
}
@keyframes clap-right {
  from { transform: rotate(-44deg); }
  to { transform: rotate(-60deg); }
}
@keyframes clap-sway {
  from { transform: translateY(0); }
  to { transform: translateY(-3px); }
}

/* =========================================================
   挂机动作 B：外展双臂 —— 双臂向两侧舒展，配合呼吸（挂机放松姿态）
   ========================================================= */
.is-action-idleStretch .arm-left {
  animation: stretch-left 3.2s ease-in-out infinite;
}
.is-action-idleStretch .arm-right {
  animation: stretch-right 3.2s ease-in-out infinite;
}
.is-action-idleStretch .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, stretch-rise 3.2s ease-in-out infinite;
}

@keyframes stretch-left {
  0%, 100% { transform: rotate(-10deg); }
  50% { transform: rotate(-26deg); }
}
@keyframes stretch-right {
  0%, 100% { transform: rotate(10deg); }
  50% { transform: rotate(26deg); }
}
@keyframes stretch-rise {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-4px) scale(1.02); }
}

/* =========================================================
   挂机动作 C：捂喉干呕 —— 异物梗阻场景的挂机姿态
   双手捂住喉咙（clutch 姿势）+ 难受（窒息）表情，躯干/头部做节律性干呕抽动
   ========================================================= */
.is-action-idleChoke .arm-left {
  animation: clutch-left 0.5s ease-in-out infinite alternate;
}
.is-action-idleChoke .arm-right {
  animation: clutch-right 0.5s ease-in-out infinite alternate;
}
.is-action-idleChoke .robot-body-group {
  animation: robot-breathe 2.6s ease-in-out infinite, dry-heave 0.62s ease-in-out infinite;
}
.is-action-idleChoke .head-group {
  animation: dry-heave-head 0.62s ease-in-out infinite;
}

/* 干呕：躯干快速前顶 + 回缩的痉挛感 */
@keyframes dry-heave {
  0%, 100% { transform: translateY(0) scaleY(1); }
  35% { transform: translateY(-3px) scaleY(1.025); }
  70% { transform: translateY(1.5px) scaleY(0.985); }
}
@keyframes dry-heave-head {
  0%, 100% { transform: rotate(0deg) translateY(0); }
  35% { transform: rotate(-3.5deg) translateY(-2px); }
  70% { transform: rotate(2.5deg) translateY(1.5px); }
}

/* =========================================================
   表情颜色兜底（主要靠 JS 变量，这里处理特殊观感）
   ========================================================= */
.is-mood-suffering,
.is-mood-collapsed,
.is-mood-choking {
  .face-glow {
    fill: #a855f7;
    opacity: 0.42;
    transition: opacity 0.5s ease;
  }
  .eye-ring,
  .eye-dot {
    animation: eye-flicker 0.3s ease-in-out infinite alternate;
  }
}
.is-mood-collapsed .face-glow { opacity: 0.55; }

@keyframes eye-flicker {
  from { opacity: 0.7; }
  to { opacity: 1; }
}

.is-mood-listless .eye-ring,
.is-mood-listless .eye-dot { opacity: 0.6; }

/* =========================================================
   时间压迫提示条
   ========================================================= */
.pressure-bar {
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(18, 30, 42, 0.74);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 10px;
}

.p-stage { letter-spacing: 0.02em; }

.p-track {
  display: block;
  height: 3px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.22);
  overflow: hidden;
}

.p-track i {
  display: block;
  height: 100%;
  width: calc(var(--p) * 100%);
  border-radius: 99px;
  background: linear-gradient(90deg, #00d4ff 0%, #ffc830 55%, #ff3b30 100%);
  transition: width 0.6s ease;
}

/* ===== 统一遮罩 ===== */
.mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #5a6f80;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.9);
  p { margin: 0; }
}

.mask.is-error {
  color: #9e3927;
  padding: 12px;
  text-align: center;
}

.err-title { font-weight: 700; font-size: 13px; }
.err-detail { font-size: 11px; color: #8a6a63; line-height: 1.5; word-break: break-all; }

.spinner {
  width: 26px;
  height: 26px;
  border: 3px solid rgba(120, 150, 175, 0.25);
  border-top-color: #2c7be5;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.speaking-badge {
  position: absolute;
  left: 8px;
  top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 99px;
  background: rgba(23, 60, 90, 0.72);
  color: #fff;
  font-size: 11px;
  letter-spacing: 0.02em;
  backdrop-filter: blur(4px);
}

.wave { display: inline-flex; align-items: flex-end; gap: 2px; height: 11px; }
.wave i {
  width: 2px;
  height: 4px;
  border-radius: 1px;
  background: #7fe3c4;
  animation: wave 0.62s ease-in-out infinite;
}
.wave i:nth-child(2) { animation-delay: 0.14s; }
.wave i:nth-child(3) { animation-delay: 0.28s; }
@keyframes wave {
  0%, 100% { height: 3px; }
  50% { height: 11px; }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
