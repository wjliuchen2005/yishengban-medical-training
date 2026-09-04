<template>
  <aside v-if="guideText" class="page-guide" aria-label="易生伴页面助手">
    <button v-if="bubbleVisible" type="button" class="guide-bubble" title="重新朗读" @click="speakGuide">
      <strong>“易”生伴</strong>
      <span>{{ guideText }}</span>
      <small>点击可重播</small>
    </button>
    <button type="button" class="guide-avatar" title="让易生伴再说一次" :aria-expanded="bubbleVisible" @click="speakGuide">
      <img :src="mascot" alt="易生伴数字人" />
      <span v-if="speaking" class="speaking-dot" aria-hidden="true" />
    </button>
  </aside>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import mascot from '@/assets/images/yishengban-original-mascot.png'
import { preheatMeSpeak, stopUnifiedSpeaking, unifiedSpeak } from '@/utils/ttsService'

const route = useRoute()
const speaking = ref(false)
const bubbleVisible = ref(true)
let speechGeneration = 0
let bubbleTimer = null
const guideText = computed(() => route.meta.guideText || '')

async function speakGuide() {
  const text = guideText.value
  if (!text) return
  const generation = ++speechGeneration
  bubbleVisible.value = true
  if (bubbleTimer) window.clearTimeout(bubbleTimer)
  bubbleTimer = window.setTimeout(() => { bubbleVisible.value = false }, 8000)
  stopUnifiedSpeaking()
  speaking.value = true
  try {
    await unifiedSpeak(text, { gender: 'female', rate: 1.02, pitch: 1.08 })
  } finally {
    if (generation === speechGeneration) speaking.value = false
  }
}

watch(guideText, () => {
  stopUnifiedSpeaking()
  if (guideText.value) window.setTimeout(speakGuide, 180)
}, { immediate: true })

onMounted(preheatMeSpeak)
onBeforeUnmount(() => {
  speechGeneration += 1
  stopUnifiedSpeaking()
  if (bubbleTimer) window.clearTimeout(bubbleTimer)
})
</script>

<style scoped lang="scss">
.page-guide {
  position: fixed;
  right: 22px;
  bottom: max(20px, env(safe-area-inset-bottom));
  z-index: 90;
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
  width: 112px;
  height: 132px;
  padding: 0;
  overflow: hidden;
  border-radius: 48% 48% 42% 42%;
  background: linear-gradient(160deg, #effaff, #dff6ef);
  filter: drop-shadow(0 10px 18px rgba(20, 67, 92, 0.18));
}

.guide-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center bottom;
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
  .guide-avatar { width: 68px; height: 80px; }
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
