<template>
  <details v-if="items.length" class="voice-feedback">
    <summary><span aria-hidden="true">◉</span> 声音表达 <span class="count">{{ items.length }} 段</span></summary>
    <div class="feedback-body">
      <article v-for="(item, i) in items" :key="item.id || i">
        <header><strong>片段 {{ i + 1 }} · {{ item.duration || '—' }} 秒</strong>
          <span>{{ item.status === 'assessed' ? item.emotion : item.status === 'limited' ? '评价意义有限' : '评价暂不可用' }}</span>
          <button v-if="editable" type="button" @click="$emit('remove', i)">移除</button>
        </header>
        <p>{{ item.impression }}</p>
        <template v-if="item.status === 'assessed'">
          <div v-if="!psych" class="voice-scores"><span v-if="item.score != null">表达参考 {{ item.score }}/100</span>
            <span v-for="(value, name) in item.dimensions" :key="name">{{ labels[name] }} {{ value == null ? '—' : value }}</span>
          </div>
          <ul v-if="item.evidence?.length"><li v-for="evidence in item.evidence" :key="evidence">{{ evidence }}</li></ul>
          <p v-if="item.suggestion" class="suggestion">{{ item.suggestion }}</p>
        </template>
      </article>
    </div>
  </details>
</template>
<script setup>
defineProps({ items: { type: Array, default: () => [] }, editable: Boolean, psych: Boolean })
defineEmits(['remove'])
const labels = { articulation: '吐字', pace_pauses: '语速停顿', warmth: '温度', tone_regulation: '语调', context_fit: '情境匹配' }
</script>
<style scoped>
.voice-feedback { color: #5b7889; font-size: 12px; margin: 6px 0; text-align: left; max-width: 100%; }
summary { cursor: pointer; width: fit-content; padding: 5px 9px; border-radius: 12px; background: #edf5f8; list-style: none; }
summary::-webkit-details-marker { display:none }
.count { margin-left: 5px; opacity: .7; }
.feedback-body { margin-top: 8px; padding: 12px; border: 1px solid #deebee; border-radius: 12px; background: #f8fbfc; max-height: 260px; overflow: auto; overflow-wrap: anywhere; }
.feedback-note, small { color: #718490; line-height: 1.6; }
article + article { border-top: 1px solid #deebee; margin-top: 10px; padding-top: 10px; }
header { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
header button { margin-left:auto; border:0; background:none; color:#936254; cursor:pointer; padding: 6px; }
p { margin: 7px 0; line-height: 1.65; }
.voice-scores { display:flex; flex-wrap:wrap; gap:6px 12px; color:#397a7b; }
ul { padding-left: 18px; line-height:1.7; }
.suggestion { color:#357878; }
</style>
