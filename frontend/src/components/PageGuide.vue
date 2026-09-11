<template>
  <aside v-if="guideText" class="page-guide" aria-label="易生伴页面助手">
    <button v-if="bubbleVisible" type="button" class="guide-bubble" title="重新朗读" @click="speakGuide">
      <strong>“易”生伴</strong>
      <span>{{ guideText }}</span>
      <small>点击可重播</small>
    </button>
    <div class="guide-character">
      <button type="button" class="guide-avatar" title="让易生伴再说一次" :aria-expanded="bubbleVisible" @click="speakGuide">
        <RobotAvatar
          role="doctor"
          scene="other"
          :speaking="speaking"
          :expression="speaking ? 'happy' : 'smile'"
          :action="speaking ? 'waveHigh' : 'idle'"
        />
      </button>
      <button
        type="button"
        class="voice-button"
        :title="voiceEnabled ? '关闭页面助手语音' : '开启页面助手语音'"
        :aria-label="voiceEnabled ? '关闭页面助手语音' : '开启页面助手语音'"
        @click="toggleVoice"
      >{{ voiceEnabled ? '🔊' : '🔇' }}</button>
    </div>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import RobotAvatar from '@/components/RobotAvatar.vue'
import { useUserStore } from '@/stores/user'
import { isMiMoTTSSupported, stopUnifiedSpeaking, unifiedSpeak, unlockMiMoAudio } from '@/utils/ttsService'

const route = useRoute()
const userStore = useUserStore()
const speaking = ref(false)
const bubbleVisible = ref(true)
const voiceEnabled = ref(localStorage.getItem('yishengban_page_voice') !== 'off')
const resolvedText = ref('')
let speechGeneration = 0
let bubbleTimer = null
let routeTimer = null
let guidePlaybackStarted = false
const guideText = computed(() => resolvedText.value)

function resolveGuideText() {
  if (!route.meta.requiresAuth || !userStore.isLoggedIn) return ''
  const identity = userStore.user?.id || userStore.user?.username || 'current'
  const introKey = `yishengban_intro_spoken_${identity}`
  if (route.name === 'Home' && localStorage.getItem(introKey) !== 'yes') {
    localStorage.setItem(introKey, 'yes')
    return '我是“易”生伴，有什么需要帮助的吗？请选择你想要训练的场景。'
  }
  return route.meta.guideText || ''
}

async function speakGuide() {
  const text = guideText.value
  if (!text) return
  const generation = ++speechGeneration
  bubbleVisible.value = true
  if (bubbleTimer) window.clearTimeout(bubbleTimer)
  bubbleTimer = window.setTimeout(() => { bubbleVisible.value = false }, 8000)
  stopUnifiedSpeaking()
  if (!voiceEnabled.value || !isMiMoTTSSupported()) {
    speaking.value = false
    return
  }
  speaking.value = false
  try {
    await unifiedSpeak(text, {
      role: 'guide',
      emotion: 'happy',
      gender: 'female',
      rate: 1.02,
      pitch: 1.08,
      onReady: () => {
        if (generation === speechGeneration) {
          guidePlaybackStarted = true
          speaking.value = true
        }
      }
    })
  } catch (error) {
    if (error?.name !== 'AbortError') console.warn('[PageGuide] welcome audio deferred:', error?.message || error)
  } finally {
    if (generation === speechGeneration) speaking.value = false
  }
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  localStorage.setItem('yishengban_page_voice', voiceEnabled.value ? 'on' : 'off')
  if (voiceEnabled.value) speakGuide()
  else {
    speechGeneration += 1
    stopUnifiedSpeaking()
    speaking.value = false
  }
}

function refreshGuide() {
  guidePlaybackStarted = false
  resolvedText.value = resolveGuideText()
  stopUnifiedSpeaking()
  speaking.value = false
  if (routeTimer) window.clearTimeout(routeTimer)
  if (guideText.value) routeTimer = window.setTimeout(speakGuide, 180)
}

function unlockAndRetry() {
  unlockMiMoAudio()
  if (guideText.value && voiceEnabled.value && !guidePlaybackStarted) speakGuide()
}
// 首次启动时 URL 可能已是“/”，但 route.meta 与登录态稍后才完成注入；
// 同时监听这些字段，保证不切换页面也能在首页显示数字人。
watch(
  () => [route.fullPath, route.name, route.meta.guideText, route.meta.requiresAuth, userStore.isLoggedIn],
  refreshGuide,
  { immediate: true }
)

onMounted(() => document.addEventListener('pointerdown', unlockAndRetry, { once: true, passive: true }))

onBeforeUnmount(() => {
  speechGeneration += 1
  stopUnifiedSpeaking()
  if (bubbleTimer) window.clearTimeout(bubbleTimer)
  if (routeTimer) window.clearTimeout(routeTimer)
  document.removeEventListener('pointerdown', unlockAndRetry)
})
</script>

<style scoped lang="scss">
.page-guide {
  position: fixed;
  right: 22px;
  bottom: max(20px, env(safe-area-inset-bottom));
  // Keep the assistant available during the result page's loading overlay.
  z-index: 3001;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
}

.guide-avatar,
.guide-bubble {
  pointer-events: auto;
  border: 0;
  cursor: pointer;
}

.guide-avatar {
  position: relative;
  width: 116px;
  height: 142px;
  padding: 0;
  overflow: visible;
  border-radius: 48% 48% 42% 42%;
  background: transparent;
  filter: none;
}

.guide-avatar :deep(.robot-host) {
  width: 92%;
  height: 92%;
  margin: 4%;
  overflow: visible;
  border-radius: 46% 46% 42% 42%;
  background: linear-gradient(160deg, #effaff, #dff6ef);
  box-shadow: 0 12px 26px rgba(20, 67, 92, 0.16);
}
.guide-avatar :deep(.speaking-badge),
.guide-avatar :deep(.pressure-bar) {
  display: none;
}
.guide-character {
  position: relative;
  pointer-events: auto;
}
.voice-button {
  position: absolute;
  right: -2px;
  bottom: 2px;
  z-index: 2;
  width: 31px;
  height: 31px;
  padding: 0;
  border: 1px solid #d5e6ef;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 4px 12px rgba(31, 77, 105, 0.15);
  cursor: pointer;
}

.guide-bubble {
  position: relative;
  width: min(280px, calc(100vw - 166px));
  margin-bottom: 58px;
  padding: 13px 16px;
  border: 1px solid #cfe2ef;
  border-radius: 16px 16px 4px 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 30px rgba(31, 77, 105, 0.14);
  color: #315267;
  text-align: left;
}

.guide-bubble strong,
.guide-bubble span,
.guide-bubble small { display: block; }
.guide-bubble strong { margin-bottom: 3px; color: #1874ca; font-size: 13px; }
.guide-bubble span { font-size: 14px; line-height: 1.55; }
.guide-bubble small { margin-top: 5px; color: #90a3b0; font-size: 10px; }

.speaking-dot {
  position: absolute;
  right: 8px;
  top: 8px;
  width: 11px;
  height: 11px;
  border: 2px solid white;
  border-radius: 50%;
  background: #2fc384;
  box-shadow: 0 0 0 0 rgba(47, 195, 132, 0.5);
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  70% { box-shadow: 0 0 0 8px rgba(47, 195, 132, 0); }
  100% { box-shadow: 0 0 0 0 rgba(47, 195, 132, 0); }
}

@media (max-width: 640px) {
  .page-guide {
    right: 9px;
    bottom: max(9px, env(safe-area-inset-bottom));
    gap: 5px;
  }
  .guide-avatar { width: 74px; height: 90px; }
  .voice-button { width: 27px; height: 27px; font-size: 12px; }
  .guide-bubble {
    width: min(244px, calc(100vw - 92px));
    margin-bottom: 26px;
    padding: 10px 12px;
    border-radius: 13px 13px 3px 13px;
  }
  .guide-bubble span { font-size: 12px; line-height: 1.45; }
  .guide-bubble small { display: none; }
}
</style>
