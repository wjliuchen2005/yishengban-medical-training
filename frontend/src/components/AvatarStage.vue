<template>
  <aside class="avatar-stage" :class="{ 'has-controls': !!$slots.controls }" aria-label="数字人">
    <button
      type="button"
      class="collapse-btn"
      title="收起数字人"
      aria-label="收起数字人"
      @click="emit('collapse')"
    >
      ‹
    </button>

    <div class="stage-scene">
      <RobotAvatar
        ref="avatarRef"
        :role="role"
        :speaking="speaking"
        :expression="expression"
        :action="action"
        :pressure="pressure"
        :scene="scene"
        :persona="persona"
      />
    </div>

    <div class="stage-info">
      <slot name="controls" />
      <div class="identity-row">
      <div class="role-line">
        <span class="role-name">{{ displayName }}</span>
        <span class="role-title">{{ roleTitle }}</span>
      </div>
      <div class="badge-row">
        <span
          class="mood-badge"
          :style="{ color: moodInk(expression), borderColor: moodColor(expression), background: moodSoft(expression) }"
        >
          {{ mood.emoji }} {{ mood.text }}
        </span>
        <span v-if="actionMeta" class="action-badge">{{ actionMeta.emoji }} {{ actionMeta.text }}</span>
      </div>
      <div class="badge-row">
        <span class="gender-badge" :class="gender">{{ genderText }}</span>
        <span class="medical-badge">{{ sceneBadgeText }}</span>
      </div>
      </div>
    </div>

    <div v-if="replayable" class="stage-actions">
      <button v-if="ttsAvailable" type="button" class="act" @click="onReplay">
        🔊 重播
      </button>
    </div>

    <p class="stage-tip">语音仅朗读对话正文</p>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import RobotAvatar from '@/components/RobotAvatar.vue'
import { ACTION_LABEL, MOOD_LABEL, ROLE_PROFILE, moodColor, moodInk, moodSoft } from '@/utils/live2dMap'

const props = defineProps({
  role: { type: String, default: 'patient' },
  speaking: { type: Boolean, default: false },
  expression: { type: String, default: 'neutral' },
  // 肢体动作：深呼吸 / 高臂挥手 / 捂住脖子 / 拍胸脯 / 伸手 / 点头 / 摇头 …
  action: { type: String, default: 'idle' },
  // 时间压迫强度 0→1，仅异物梗阻场景使用
  pressure: { type: Number, default: 0 },
  // 场景：choking（异物梗阻）/ firstVisit（第一次独立看病）/ other
  scene: { type: String, default: 'other' },
  replayable: { type: Boolean, default: false },
  ttsAvailable: { type: Boolean, default: false },
  // 异物梗阻场景的「人物设定」：携带 label / gender / voiceHint / pitch / rate
  persona: { type: Object, default: null }
})

const emit = defineEmits(['collapse', 'replay'])

const avatarRef = ref(null)

const profile = computed(() => ROLE_PROFILE[props.role] || ROLE_PROFILE.patient)
// 异物梗阻挂机干呕时，情绪徽章统一显示「异物哽咽」，与机器人脸色保持一致
const mood = computed(() => MOOD_LABEL[props.action === 'idleChoke' ? 'choking' : props.expression] || MOOD_LABEL.neutral)
// 待机不显示动作徽章，避免"🧍 待机"这种无信息量的标签
const actionMeta = computed(() =>
  props.action && props.action !== 'idle' ? ACTION_LABEL[props.action] || null : null
)

// 若传了人物设定，展示名优先用人物设定（如「胖叔（食堂师傅）」），否则用角色名
const displayName = computed(() => props.persona?.label || profile.value.name)
const roleTitle = computed(() => {
  if (props.scene === 'choking' && props.role === 'patient') return '异物梗阻患者'
  return profile.value.title
})

// 人物设定的性别标签文案（声音区分仍保留）
const gender = computed(() => props.persona?.gender || profile.value.gender || 'female')
const genderText = computed(() => (gender.value === 'male' ? '男' : '女'))

// 场景徽章：心理陪伴模块不显示「医疗场景」
const sceneBadgeText = computed(() =>
  props.scene === 'psych' ? '💬 心理陪伴' : '🩺 医疗训练'
)

function onReplay() {
  emit('replay')
}

defineExpose({
  startTalk: () => avatarRef.value?.startTalk?.()
})
</script>

<style scoped lang="scss">
.avatar-stage {
  position: relative;
  flex: none;
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 12px 12px;
  border-right: 1px solid #e2eaf1;
  background: linear-gradient(180deg, #fbfdff 0%, #f2f7fb 100%);
}

.collapse-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border: 1px solid #dde6ee;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.9);
  color: #7d92a3;
  font-size: 17px;
  line-height: 1;
  cursor: pointer;
  z-index: 3;
  transition: all 0.18s;

  &:hover {
    color: #2c7be5;
    border-color: #9dc4ea;
    background: #fff;
  }
}

.stage-scene {
  height: 460px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(190, 210, 228, 0.7);
  box-shadow: inset 0 1px 6px rgba(40, 80, 120, 0.05);
}

.stage-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.identity-row { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 6px 8px; }
.identity-row .role-line { flex-basis: 100%; }

.role-line {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.role-name {
  font-size: 14px;
  font-weight: 700;
  color: #17394f;
}

.role-title {
  font-size: 11px;
  color: #78909f;
}

.badge-row {
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.mood-badge {
  display: inline-block;
  padding: 2px 9px;
  border: 1px solid;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.85);
  font-size: 11px;
}

// 当前肢体动作（待机时不显示）
.action-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 9px;
  border-radius: 99px;
  background: #eef5fb;
  border: 1px solid #cfe0f0;
  color: #35628c;
  font-size: 11px;
  font-weight: 600;
}

// 性别标签：男=冷蓝，女=暖粉
.gender-badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;

  &.male { background: #2f6ec4; }
  &.female { background: #d6728f; }
}

// 医疗场景标识
.medical-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #b8d4e8;
  color: #4a6b8a;
  font-size: 10px;
  font-weight: 600;
}

.stage-actions {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.act {
  padding: 3px 9px;
  border: 1px solid #d9e3ec;
  border-radius: 8px;
  background: #fff;
  color: #5b7386;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.18s;

  &:hover {
    color: #2c7be5;
    border-color: #9dc4ea;
  }
}

.stage-tip {
  margin: 0;
  text-align: center;
  font-size: 10px;
  color: #a3b3c0;
  line-height: 1.5;
}

@media (max-width: 960px) {
  .avatar-stage { width: 240px; padding: 12px 9px 10px; }
  .stage-scene { height: 360px; }
}

@media (max-width: 980px) {
  .avatar-stage {
    width: 100%;
    min-height: 110px;
    display: grid;
    grid-template-columns: 80px minmax(0, 1fr);
    grid-template-rows: 1fr auto;
    gap: 6px 12px;
    padding: 7px 12px;
    border-right: 0;
    border-bottom: 1px solid #e2eaf1;
  }

  .collapse-btn { display: none; }

  .stage-scene {
    grid-row: 1 / 3;
    width: 80px;
    height: 96px;
    border-radius: 12px;
  }

  .stage-info {
    min-width: 0;
    align-items: flex-start;
    justify-content: center;
    gap: 5px;
    text-align: left;
  }

  .role-line { align-items: flex-start; }
  .role-name { font-size: 13px; }
  .role-title { font-size: 10px; }
  .badge-row { justify-content: flex-start; gap: 5px; }
  .mood-badge,
  .action-badge,
  .gender-badge { padding: 2px 7px; font-size: 10px; }
  .medical-badge { padding: 2px 6px; font-size: 9px; }

  .stage-actions {
    justify-content: flex-start;
    align-self: end;
  }

  .stage-tip { display: none; }

  .avatar-stage.has-controls {
    grid-template-columns: 82px minmax(0, 1fr);
    align-items: center;
    gap: 6px 12px;
    padding: 12px;
    flex-shrink: 0;
    background: linear-gradient(115deg, #f3fafb, #fff 80%);
  }
  .has-controls .stage-scene { width: 82px; height: 112px; grid-row: 1; align-self: start; border-color: #deeaed; background: #f4faf9; }
  .has-controls .stage-info { gap: 9px; }
  .has-controls .identity-row { justify-content: flex-start; width: 100%; gap: 5px 8px; }
  .has-controls .identity-row .role-line { flex-basis: auto; }
  .has-controls .role-line { flex-direction: row; align-items: baseline; flex-wrap: wrap; gap: 6px; }
  .has-controls .role-name { font-size: 12px; color: #355866; font-weight: 700; }
  .has-controls .role-title { display: none; }
  .has-controls .badge-row { gap: 4px; }
  .has-controls .badge-row:last-child { display: none; }
  .has-controls .stage-actions { grid-column: 1; grid-row: 2; justify-content: center; }
  .has-controls .stage-actions .act { font-size: 10px; padding: 3px 7px; }
  .has-controls .identity-row .badge-row { display: contents; }
  .has-controls .identity-row .badge-row:last-child { display: none; }
  .has-controls .action-badge { max-width: 100%; }
  .has-controls .identity-row .mood-badge { white-space: nowrap; }
  .has-controls .stage-info { align-self: stretch; justify-content: flex-start; }
}
</style>
