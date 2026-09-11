<template>
  <div ref="host" class="robot-host" :style="{ background: profile.bg }">
    <svg class="robot-svg" viewBox="0 0 320 360" preserveAspectRatio="xMidYMid meet" role="img" aria-label="易生伴动态角色">
      <defs>
        <radialGradient :id="skinId" cx="50%" cy="38%" r="75%"><stop stop-color="#f9da8c"/><stop offset="1" stop-color="#f5d17e"/></radialGradient>
      </defs>
      <ellipse cx="160" cy="332" rx="66" ry="9" fill="#b2dcd0" opacity=".38"/>
      <g class="float">
        <g class="body" stroke="#816327" stroke-width="3" stroke-linejoin="round" stroke-linecap="round">
          <path d="M133 300 C127 315 131 331 141 330 C153 329 153 315 152 302 M171 302 C167 320 174 332 183 329 C192 325 190 311 187 301" :fill="skin"/>
          <path d="M130 222 Q158 210 190 224 Q201 252 201 302 Q162 315 119 301 Q120 252 130 222Z" :fill="casual ? shirt : '#fffdf6'"/>
          <template v-if="!casual">
            <path d="M132 222 L160 245 L186 222 L190 241 L176 245 L173 260 L160 248 L147 258 L144 244 L130 240Z" fill="#fffef9"/>
            <path d="M160 250 L160 304" fill="none" stroke-width="1.6"/>
            <path d="M130 272 L145 272 L145 288 Q137 295 130 288Z M176 272 L191 272 L190 289 Q183 294 176 289Z" fill="none" stroke-width="2"/>
            <circle cx="163" cy="265" r="2.6" fill="#e9c774"/><circle cx="163" cy="286" r="2.6" fill="#e9c774"/>
            <image :href="universityEmblem" x="178" y="253" width="12" height="16" preserveAspectRatio="xMidYMid meet"><title>南京医科大学校徽</title></image>
          </template>
          <template v-else><path d="M136 227 Q160 245 184 227" fill="none" stroke="#fff7e5" stroke-width="5"/><path d="M138 277 Q160 287 184 277" fill="none" opacity=".4"/></template>
        </g>
        <!-- Organic continuous silhouette, not a scaled ellipse or assembled circles. -->
        <g class="head" stroke="#816327" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M57 91 C32 79 35 47 51 35 C68 22 91 30 106 47 C138 35 182 35 214 47 C229 30 252 22 269 35 C285 47 288 79 263 91 C278 118 279 157 265 184 C248 220 207 239 160 239 C113 239 72 220 55 184 C41 157 42 118 57 91Z" :fill="skin"/>
          <g class="brows" fill="none" stroke-width="3">
            <path :d="worried ? 'M93 101 Q109 104 121 94' : 'M93 97 Q107 83 121 97'"/>
            <path :d="worried ? 'M227 101 Q211 104 199 94' : 'M199 97 Q213 83 227 97'"/>
          </g>
          <g v-for="(x, i) in [107, 213]" :key="i">
            <g :class="['eye', `eye-${i}`]">
              <ellipse :cx="x" cy="139" rx="27" ry="28" fill="#fffdf6" stroke-width="3.5"/>
              <ellipse :cx="x" cy="139" rx="21" ry="22" fill="#121313" stroke="none"/>
              <circle :cx="x - 7" cy="130" r="7.5" fill="white" stroke="none"/>
              <circle :cx="x + 8" cy="149" r="3.4" fill="white" stroke="none"/>
            </g>
            <path v-if="joyful && !speaking" :d="`M${x - 17} 138 Q${x} 116 ${x + 17} 138`" fill="none" stroke-width="4"/>
          </g>
          <ellipse cx="78" cy="175" rx="17" ry="8" fill="#ec7e98" stroke="none"/>
          <ellipse cx="242" cy="175" rx="17" ry="8" fill="#ec7e98" stroke="none"/>
          <path d="M108 189 C115 176 142 171 160 171 C178 171 205 176 212 189 C232 220 192 233 160 233 C128 233 88 220 108 189Z" fill="#fffdf6" stroke="none"/>
          <ellipse cx="160" cy="171" rx="11" ry="9" fill="#121313" stroke="none"/>
          <ellipse cx="163" cy="168" rx="3" ry="1.8" fill="white" stroke="none"/>
          <g v-show="speaking && !blocked" class="talk-mouth"><path d="M139 197 Q160 203 181 197 C181 234 139 234 139 197Z" fill="#e98297" stroke-width="2.3"/><path d="M148 221 Q160 215 172 221" stroke="#f3a0ae" fill="none" stroke-width="3"/></g>
          <path v-if="!speaking && !blocked && action === 'waveHigh'" d="M139 198 Q160 205 181 198 C181 233 139 233 139 198Z" fill="#e98297" stroke-width="2.5"/>
          <path v-if="(!speaking || blocked) && action !== 'waveHigh'" :d="mouthPath" :fill="surprised || blocked ? '#b8756c' : 'none'" stroke-width="2.8"/>
          <path v-if="['crying', 'sad'].includes(expression)" d="M82 158 Q70 177 80 180 Q91 181 82 158Z" fill="#a8d9e2" stroke="none"/>
        </g>
        <!-- Short seamless paws; rotate as rigid shapes around the shoulders. -->
        <g class="arm-left" stroke="#816327" stroke-width="3" stroke-linejoin="round">
          <path d="M129 235 Q119 232 111 245 L102 265 C98 276 103 285 110 282 Q115 285 118 279 Q125 268 132 248Z" :fill="skin"/>
          <path d="M126 232 C119 230 112 237 109 245 Q107 249 111 252 Q117 256 123 256 C126 256 126 251 129 248 C134 243 136 235 126 232Z" :fill="casual ? shirt : '#fffdf6'" stroke-width="2.6"/>
        </g>
        <g class="arm-right" stroke="#816327" stroke-width="3" stroke-linejoin="round">
          <path d="M190 237 Q201 233 207 248 L216 270 Q220 282 212 284 Q206 287 202 278 L189 253Z" :fill="skin"/>
          <path d="M193 233 C200 231 207 238 210 246 Q212 250 208 253 Q202 257 196 257 C193 257 193 252 190 249 C185 244 183 236 193 233Z" :fill="casual ? shirt : '#fffdf6'" stroke-width="2.6"/>
        </g>
      </g>
    </svg>
    <span v-if="speaking" class="speaking-badge"><i/> 说话中</span>
    <div v-if="pressureValue > .02" class="pressure-bar"><span><i class="pressure-dot" :class="pressureMeta.key"/>{{ pressureMeta.text }}</span><div><i :style="{ width: `${pressureValue * 100}%` }"/></div></div>
  </div>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { gsap } from 'gsap'
import { ROLE_PROFILE, pressureStage } from '@/utils/live2dMap'
import universityEmblem from '@/assets/images/njmu-emblem.png'

const props = defineProps({ role: { type: String, default: 'patient' }, speaking: Boolean, expression: { type: String, default: 'neutral' }, action: { type: String, default: 'idle' }, pressure: { type: Number, default: 0 }, scene: { type: String, default: 'other' }, persona: { type: Object, default: null } })
const host = ref(null)
const skinId = `bear-skin-${getCurrentInstance().uid}`
const profile = computed(() => ROLE_PROFILE[props.role] || ROLE_PROFILE.patient)
const casual = computed(() => ['patient', 'psych'].includes(props.role))
const shirt = computed(() => props.role === 'psych' ? '#dfad8c' : '#83b3be')
const pressureValue = computed(() => Math.min(1, Math.max(0, Number(props.pressure) || 0)))
const pressureMeta = computed(() => pressureStage(pressureValue.value))
const recovered = computed(() => ['startledPant', 'deepBreath', 'chestPat'].includes(props.action) || props.expression === 'relieved')
const collapsed = computed(() => props.action === 'slump' || props.expression === 'collapsed')
const blocked = computed(() => props.role === 'patient' && props.scene === 'choking' && !recovered.value)
const worried = computed(() => blocked.value || ['concerned', 'sad', 'crying', 'suffering', 'confused', 'tired', 'listless'].includes(props.expression))
const surprised = computed(() => props.expression === 'surprised' || props.action === 'startledPant')
const joyful = computed(() => ['happy', 'relieved'].includes(props.expression) && !blocked.value)
const skin = computed(() => {
  if (!blocked.value || pressureValue.value < .15) return `url(#${skinId})`
  const p = pressureValue.value
  return `rgb(${Math.round(246 - p * 91)},${Math.round(210 - p * 72)},${Math.round(139 + p * 30)})`
})
const mouthPath = computed(() => blocked.value || surprised.value ? 'M153 195 C145 209 168 217 168 202 C168 191 158 189 153 195Z' : worried.value ? 'M146 207 Q159 191 173 206' : 'M133 191 C129 205 149 207 159 194 C168 208 190 204 185 190')
let ctx, media, observer, mounted = false
const visible = ref(true)
const reduced = ref(false)
function buildMotion() {
  if (!mounted) return
  // Keep the current rigid pose during state changes, instead of snapping to rest.
  const previous = [...host.value.querySelectorAll('.arm-left, .arm-right, .head')].map(element => ({
    element, rotation: Number(gsap.getProperty(element, 'rotation')) || 0,
    y: Number(gsap.getProperty(element, 'y')) || 0
  }))
  ctx?.revert()
  ctx = gsap.context(() => {
    const q = gsap.utils.selector(host.value)
    const left = q('.arm-left'), right = q('.arm-right'), head = q('.head')
    gsap.set(left, { svgOrigin: '127 239' })
    gsap.set(right, { svgOrigin: '192 240' })
    gsap.set(head, { svgOrigin: '160 228' })
    previous.forEach(({ element, rotation, y }) => gsap.set(element, { rotation, y }))
    gsap.set(q('.eye-0'), { svgOrigin: '107 139', opacity: joyful.value && !props.speaking ? 0 : 1 })
    gsap.set(q('.eye-1'), { svgOrigin: '213 139', opacity: joyful.value && !props.speaking ? 0 : 1 })
    // Rotations/translations only for the rig: head/body ratio stays constant.
    const pose = collapsed.value ? [10, -8, 2] : blocked.value ? [133, -132, 0] : props.action === 'waveHigh' ? [78, -8, 0] : ['explain', 'reachOut', 'psychOpen', 'idleStretch'].includes(props.action) ? [48, -40, 0] : props.action === 'idleClap' ? [74, -74, 0] : props.action === 'chestPat' ? [125, -10, 0] : props.action === 'startledPant' ? [22, -24, 0] : worried.value ? [12, -16, 0] : [3, -4, 0]
    if (reduced.value) {
      gsap.set(left, { rotation: pose[0] }); gsap.set(right, { rotation: pose[1] }); gsap.set(head, { rotation: pose[2] })
      return
    }
    gsap.to(left, { rotation: pose[0], duration: .55, ease: 'power2.out' })
    gsap.to(right, { rotation: pose[1], duration: .6, ease: 'power2.out' })
    gsap.to(head, { rotation: pose[2], y: props.action === 'slump' ? 5 : 0, duration: .7, ease: 'sine.inOut' })
    if (collapsed.value) {
      gsap.to('.float', { svgOrigin: '160 190', rotation: 65, scale: .7, y: 45, duration: 1.4, ease: 'power2.inOut' })
      gsap.set('.eye', { scaleY: .08 })
      return
    }
    gsap.to('.float', { y: blocked.value ? 1.8 : props.action === 'startledPant' ? 3 : -2.5, duration: blocked.value ? .32 : props.action === 'startledPant' ? .55 : 2.2, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.timeline({ repeat: -1, repeatDelay: 3.1 }).to('.eye', { scaleY: .06, duration: .095, delay: 1.8 }).to('.eye', { scaleY: 1, duration: .14 })
    if (props.action === 'waveHigh' && !blocked.value) gsap.to(left, { rotation: pose[0] - 12, duration: .5, repeat: 3, yoyo: true, delay: .7, ease: 'sine.inOut' })
    else if (props.action === 'shakeHead') gsap.timeline({ delay: .75 }).to(head, { rotation: -1.5, duration: .35 }).to(head, { rotation: 1.5, duration: .7 }).to(head, { rotation: 0, duration: .35 })
    else if (props.action === 'nod') gsap.timeline({ delay: .75 }).to(head, { y: 2, duration: .35 }).to(head, { y: 0, duration: .5 })
    // Listening stays upright; the breathing layer supplies subtle movement.
    if (props.speaking && !blocked.value) {
      // Speech activity drives a stylized mouth rhythm, not phoneme-level lip sync.
      gsap.set('.talk-mouth', { svgOrigin: '160 197' })
      gsap.timeline({ repeat: -1 }).to('.talk-mouth', { scaleY: .28, duration: .13 }).to('.talk-mouth', { scaleY: .85, duration: .19 }).to('.talk-mouth', { scaleY: .42, duration: .1 }).to('.talk-mouth', { scaleY: 1, duration: .21 }).to('.talk-mouth', { scaleY: .18, duration: .15 }).to('.talk-mouth', { scaleY: .7, duration: .23 })
    }
    // Each explanation returns to a relaxed pose. Occasional asymmetric gestures
    // have long rests and never stretch the artwork or continuously raise both arms.
    if (!blocked.value && ['idle', 'explain', 'reachOut', 'psychOpen', 'idleStretch', 'waveHigh'].includes(props.action)) {
      const gestures = gsap.timeline({ delay: 2.5, repeat: props.speaking ? -1 : 0, repeatRefresh: true })
      gestures.to(left, { rotation: 3, duration: .9, ease: 'sine.inOut' }, 0)
        .to(right, { rotation: -4, duration: .9, ease: 'sine.inOut' }, 0)
      if (props.speaking) {
        gestures.to(right, { rotation: () => -18 - Math.random() * 12, duration: .8, ease: 'sine.inOut' }, '+=3.5')
          .to(right, { rotation: -4, duration: 1, ease: 'sine.inOut' }, '+=.5')
          .to(left, { rotation: () => 12 + Math.random() * 10, duration: .85, ease: 'sine.inOut' }, '+=4')
          .to(left, { rotation: 3, duration: 1, ease: 'sine.inOut' }, '+=.4')
      }
    }
  }, host.value)
  pauseIfHidden()
}
function pauseIfHidden() {
  // Pause parent timelines, not their individual children (which breaks sequencing).
  ctx?.data.filter(animation => animation.parent === gsap.globalTimeline && typeof animation.paused === 'function')
    .forEach(animation => animation.paused(document.hidden || !visible.value))
}
function preferenceChanged() { reduced.value = media.matches; buildMotion() }
watch(() => [props.role, props.scene, props.action, props.speaking, props.expression], async () => { await nextTick(); buildMotion() })
onMounted(() => {
  mounted = true
  media = window.matchMedia('(prefers-reduced-motion: reduce)'); reduced.value = media.matches
  media.addEventListener('change', preferenceChanged)
  document.addEventListener('visibilitychange', pauseIfHidden)
  observer = new IntersectionObserver(([entry]) => { visible.value = entry.isIntersecting; pauseIfHidden() })
  observer.observe(host.value)
  buildMotion()
})
onBeforeUnmount(() => { mounted = false; ctx?.revert(); observer?.disconnect(); media?.removeEventListener('change', preferenceChanged); document.removeEventListener('visibilitychange', pauseIfHidden) })
defineExpose({ startTalk: () => buildMotion() })
</script>

<style scoped>
.robot-host{position:relative;width:100%;height:100%;min-height:0;isolation:isolate;border-radius:inherit}
.robot-svg{display:block;width:100%;height:100%;overflow:visible}
.speaking-badge{position:absolute;top:12px;left:12px;padding:5px 9px;border-radius:20px;background:#36576ccc;color:white;font-size:11px;display:flex;align-items:center;gap:5px}
.speaking-badge i{width:6px;height:6px;border-radius:50%;background:#8ee0c1}
.pressure-bar{position:absolute;bottom:10px;left:10px;right:10px;background:#36505cdd;border-radius:12px;padding:8px 10px;color:#fff;font-size:11px}
.pressure-bar>span{display:flex;align-items:center;gap:5px;white-space:nowrap;line-height:1.2}
.pressure-dot{width:6px;height:6px;flex:0 0 6px;border-radius:50%;background:#56cba2;box-shadow:0 0 0 2px #ffffff24}
.pressure-dot.tense{background:#f1c553}.pressure-dot.critical{background:#ef6e68}
.pressure-bar>div{height:4px;margin-top:5px;background:#ffffff40;border-radius:4px;overflow:hidden}
.pressure-bar i{height:100%;display:block;background:linear-gradient(90deg,#78daca,#f2cd75,#e67c72);transition:width .5s}
</style>
