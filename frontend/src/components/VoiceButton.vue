<template>
  <button type="button" class="voice-button" :class="{ 'is-on': enabled }"
    :aria-label="enabled ? '关闭语音' : '开启语音'" :title="enabled ? '关闭语音' : '开启语音'"
    :aria-pressed="enabled" @click="$emit('toggle', !enabled)">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M11 5 6 9H3v6h3l5 4z" />
      <template v-if="enabled"><path d="M15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14" /></template>
      <path v-else d="m16 9 5 6m0-6-5 6" />
    </svg>
  </button>
</template>
<script setup>
defineProps({ enabled: Boolean })
defineEmits(['toggle'])
</script>
<style scoped>
.voice-button { flex: none; display: inline-grid; place-items: center; width: 36px; height: 36px; padding: 8px; border: 1px solid #dce6eb; border-radius: 11px; background: #fff; color: #82939e; cursor: pointer; transition: background .18s, color .18s; }
.voice-button.is-on { color: #287fab; background: #edf7fb; border-color: #cce4ee; }
.voice-button:hover { background: #e5f1f6; }
.voice-button:focus-visible { outline: 2px solid #2985b6; outline-offset: 3px; }
svg { width: 20px; height: 20px; }
</style>
