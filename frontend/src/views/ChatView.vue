<template>
  <div class="chat-view">
    <AppHeader />

    <main
      class="chat-container"
      :class="{ 'is-osce-layout': isOsce }"
      v-loading="initializing"
      element-loading-text="正在生成本次训练情景…"
    >
      <AvatarStage
        v-if="isMobile || !avatarCollapsed"
        ref="stageRef"
        :role="currentSpeakerRole"
        :speaking="stageSpeaking"
        :expression="currentExpression"
        :action="currentAction"
        :pressure="pressureLevel"
        :scene="sceneKey"
        :persona="currentPersona"
        :replayable="canReplay"
        :tts-available="ttsAvailable"
        @collapse="onCollapseAvatar"
        @replay="replaySpeech(lastSpokenMsg)"
        @switch-style="cycleExpression"
      >
        <template #controls><div ref="mobileHeaderTarget" class="mobile-session-controls" /></template>
      </AvatarStage>
      <button
        v-else
        type="button"
        class="avatar-reopen"
        title="展开数字人"
        @click="onExpandAvatar"
      >
        <span class="arrow">›</span>
        <span class="txt">数字人</span>
      </button>

      <div class="chat-main">
      <Teleport :to="mobileHeaderTarget || 'body'" :disabled="!isMobile || !mobileHeaderTarget">
      <header class="chat-header">
        <div class="scene-info">
          <div class="scene-icon" aria-hidden="true">
            <el-icon><FirstAidKit /></el-icon>
          </div>
          <div class="scene-copy">
            <div class="eyebrow">沉浸式模拟训练</div>
            <h1>{{ sceneInfo.title || '对话训练' }}</h1>
            <p>{{ isFirstVisit ? currentSpeakerName : (sceneInfo.role || '正在加载…') }}</p>
          </div>
        </div>

        <div class="chat-actions">
          <VoiceButton v-if="ttsAvailable" :enabled="voiceEnabled" @toggle="value => { voiceEnabled = value; onVoiceToggle(value) }" />
          <el-badge :value="unreadCoachCount" :hidden="!unreadCoachCount" :max="99">
            <el-button class="coach-button" aria-label="观察者教练记录" :type="coachHistory.length ? 'warning' : 'default'" @click="openCoachHistory">
              <el-icon><Bell /></el-icon>
              <span>{{ isMobile ? '教练' : '观察者教练' }}</span>
            </el-button>
          </el-badge>
          <el-button type="danger" plain :disabled="loading || initializing" @click="onEnd">
            结束训练
          </el-button>
        </div>
      </header>

      <section v-if="currentStage" class="stage-strip" aria-label="训练进度">
        <div class="stage-main">
          <span class="stage-index">阶段 {{ currentStage.id }}/{{ currentStage.total || stageNames.length }}</span>
          <strong>{{ currentStage.name }}</strong>
          <span class="stage-progress">{{ currentStage.progress }}%</span>
        </div>
        <div class="stage-dots" aria-hidden="true">
          <span
            v-for="(name, index) in stageNames"
            :key="name"
            :class="{ active: index + 1 <= currentStage.id }"
          />
        </div>
      </section>
      </Teleport>

      <section ref="messageListRef" class="chat-messages" aria-live="polite">
        <template v-for="msg in messages" :key="msg.id">
          <article v-if="msg.role === 'system'" class="scene-brief">
            <div class="brief-heading">
              <span class="agent-mark"><el-icon><MagicStick /></el-icon></span>
              <div>
                <span class="brief-kicker">{{ msg.meta?.agent_name || '情景生成智能体' }}</span>
                <h2>本次情景</h2>
              </div>
              <el-tag effect="plain" round>{{ msg.meta?.scenario_id || '动态生成' }}</el-tag>
            </div>
            <p class="brief-content">{{ msg.content }}</p>
            <div v-if="msg.meta?.first_step" class="first-step">
              <span>第一步</span>
              <strong>{{ msg.meta.first_step }}</strong>
            </div>
            <el-button v-if="isFirstVisit && !hasUserMessage" class="visit-entry-reopen" round @click="visitEntryVisible = true">选择就医方式</el-button>
            <div v-if="!isFirstVisit && canUseQuickActions(msg)" class="quick-actions">
              <button
                v-for="action in msg.meta.quick_actions"
                :key="action.label"
                type="button"
                :disabled="loading"
                @click="onSend(action.value)"
              >
                {{ action.label }}
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </article>

          <article
            v-else-if="msg.role === 'coach'"
            class="message-wrapper is-coach"
            :class="msg.extra?.type"
          >
            <el-avatar :size="40" class="message-avatar coach-avatar">教</el-avatar>
            <div class="message-content">
              <div class="message-sender">观察者教练</div>
              <div class="message-bubble">{{ isFirstVisit && msg.role === 'ai' ? msg.content.replace(/^【[^】\n]{1,30}】\s*/, '') : msg.content }}</div>
              <button
                v-if="ttsAvailable"
                type="button"
                class="bubble-speak"
                title="重播语音"
                @click="replaySpeech(msg)"
              >🔊 重播</button>
              <time class="message-time">{{ formatTime(msg.timestamp) }}</time>
            </div>
          </article>

          <article
            v-else
            class="message-wrapper"
            :class="{ 'is-user': msg.role === 'user', 'is-ai': msg.role === 'ai' }"
          >
            <el-avatar :size="40" :src="msg.role === 'ai' ? sceneInfo.role_avatar : userAvatar" class="message-avatar">
              {{ msg.role === 'ai' ? aiAvatarText : '我' }}
            </el-avatar>
            <div class="message-content">
              <div class="message-sender">{{ msg.role === 'ai' ? speakerName(msg) : '我' }}</div>
              <div class="message-bubble">{{ msg.content }}</div>
              <VoiceFeedback v-if="msg.role === 'user'" :items="msg.extra?.voice_assessments || []" />
              <div v-if="msg.role === 'ai' && msg.extra?.attachments?.length" class="message-attachments">
                <a v-for="item in msg.extra.attachments" :key="item.url" :href="item.url" target="_blank" rel="noopener">
                  <span class="attachment-icon"><el-icon><Document /></el-icon></span>
                  <span><strong>{{ item.title }}</strong><small>点击打开医保资料</small></span>
                  <el-icon><ArrowRight /></el-icon>
                </a>
              </div>
              <button
                v-if="ttsAvailable && msg.role === 'ai'"
                type="button"
                class="bubble-speak"
                title="重播语音"
                @click="replaySpeech(msg)"
              >🔊 重播</button>
              <time class="message-time">{{ formatTime(msg.timestamp) }}</time>
            </div>
          </article>
        </template>

        <article v-if="loading && replyPending" class="message-wrapper is-ai">
          <el-avatar :size="40" class="message-avatar">{{ aiAvatarText }}</el-avatar>
          <div class="message-content">
            <div class="message-sender">{{ isFirstVisit ? '正在生成本轮回复…' : currentSpeakerName }}</div>
            <div class="message-bubble typing" aria-label="正在回复">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </article>
        <article v-if="coachLoading && coachReplyPending" class="message-wrapper is-coach">
          <el-avatar :size="40" class="message-avatar coach-avatar">教</el-avatar>
          <div class="message-content">
            <div class="message-sender">观察者教练</div>
            <div class="message-bubble typing coach-typing" aria-label="观察者教练正在回复">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </article>
      </section>

      <transition name="coach-pop">
        <button v-if="coachTip" type="button" class="coach-tip" :class="coachTip.type" @click="openCoachHistory">
          <span class="coach-tip-icon"><el-icon><View /></el-icon></span>
          <span class="coach-tip-copy">
            <strong>观察者教练</strong>
            <span>{{ coachTip.text }}</span>
          </span>
          <el-icon><ArrowRight /></el-icon>
        </button>
      </transition>

      <footer class="chat-input">
        <div class="input-help">
          <span class="input-toggles">
            <label v-if="sessionId && isChoking" class="toggle-item">
              <el-switch v-model="timePressureEnabled" size="small" @change="onTimePressureToggle" />
              时间压力
            </label>
            <label v-if="sessionId" class="toggle-item" :class="{ 'is-active': coachMode }">
              <el-switch v-model="coachMode" size="small" />
              问教练
            </label>
            <span v-if="!sessionId">用自己的话说出判断和行动</span>
          </span>
          <span>Ctrl + Enter 发送</span>
        </div>
        <VoiceComposer ref="voiceInputRef" v-model="inputText" :session-id="sessionId || undefined"
          :target="coachMode ? 'coach' : 'patient'" :placeholder="inputPlaceholder"
          :disabled="initializing || (coachMode && coachLoading)" :sending="coachMode ? coachLoading : (isFirstVisit && loading)"
          :send-label="!coachMode && loading ? (isFirstVisit ? '正在回复' : '补充') : '发送'" @send="onSend()"
          @recording="onInputRecording" />
      </footer>
      </div>

      <aside v-if="isOsce" ref="recordWorkspaceRef" class="record-workspace" aria-label="OSCE 病历书写区">
        <div class="record-workspace-header">
          <div class="record-title">
            <span class="record-title-icon"><el-icon><DocumentChecked /></el-icon></span>
            <div>
              <span>OSCE 同屏病历</span>
              <small>边问诊，边记录</small>
            </div>
          </div>
          <span class="record-status" :class="medicalRecordSaved ? 'saved' : 'unsaved'">
            {{ medicalRecordSaved ? '已保存' : '待保存' }}
          </span>
        </div>

        <div class="record-intro">
          <el-icon><DocumentChecked /></el-icon>
          <div>
            <strong>请根据你亲自问到的内容书写</strong>
            <p>问诊是重点；体格检查与辅助检查只需整理考官快速给出的关键结果。病历单独评分。</p>
          </div>
        </div>
        <div class="record-framework" aria-label="病历框架">
          <span v-for="item in recordSections" :key="item">{{ item }}</span>
        </div>
        <el-input
          ref="recordInputRef"
          v-model="medicalRecordDraft"
          class="record-editor"
          type="textarea"
          :rows="8"
          maxlength="12000"
          resize="vertical"
          placeholder="请完成主诉、现病史、其他病史、检查结果、病历摘要和初步诊断…"
        />
        <div class="record-actions">
          <span class="record-count">{{ medicalRecordDraft.length }} / 12000</span>
          <span :class="medicalRecordSaved ? 'saved' : 'unsaved'">
            {{ medicalRecordSaved ? '已保存并纳入评分' : '修改后请保存' }}
          </span>
          <el-button type="primary" :loading="recordSaving" @click="saveRecord">保存病历</el-button>
        </div>
      </aside>
    </main>

    <el-drawer v-model="coachDrawerVisible" title="观察者教练记录" size="min(420px, 92vw)" class="coach-drawer">
      <div class="drawer-intro">
        <el-icon><View /></el-icon>
        <p>教练只观察并反馈你的表现，不参与患者或医护人员的对话。所有提示都会保留在这里。</p>
      </div>
      <el-empty v-if="!coachHistory.length" description="完成一次回复后，教练提示会出现在这里" />
      <ol v-else class="coach-history">
        <li v-for="(tip, index) in coachHistory" :key="tip.id || index" :class="tip.type">
          <div class="history-meta">
            <el-tag :type="coachTagType(tip.type)" size="small" effect="light">{{ coachTypeLabel(tip.type) }}</el-tag>
            <time>{{ formatTime(tip.timestamp) }}</time>
          </div>
          <p>{{ tip.text }}</p>
          <el-button
            v-if="tip.type === 'error' && sessionId"
            type="danger"
            plain
            size="small"
            @click="restartCurrentStage"
          >
            重新开始本阶段
          </el-button>
        </li>
      </ol>
    </el-drawer>

    <el-dialog
      v-model="setupVisible"
      title="训练前设置"
      width="min(480px, 92vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="setup-copy">
        <span class="setup-icon"><el-icon><UserFilled /></el-icon></span>
        <div>
          <h3>第一次独立看病</h3>
          <p>性别会影响妇科、泌尿外科等病例匹配和医生问诊内容，仅用于本次模拟。</p>
        </div>
      </div>
      <el-form label-position="top">
        <el-form-item label="请选择你的性别">
          <el-radio-group v-model="selectedGender" class="gender-options">
            <el-radio-button value="male">男</el-radio-button>
            <el-radio-button value="female">女</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="router.push('/')">返回场景列表</el-button>
        <el-button type="primary" :disabled="!selectedGender" @click="beginSession">下一步</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="visitEntryVisible" title="开启本次就医体验" width="min(940px, 94vw)"
      class="visit-entry-dialog" top="5vh" :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
      <div class="visit-entry-content" aria-busy="initializing">
        <section class="visit-situation" aria-label="当前场景情况">
          <span class="visit-eyebrow">你的情景 · 江苏省人民医院</span>
          <h2>{{ initializing ? '正在准备本次情景' : '现在，发生了什么？' }}</h2>
          <p v-if="initializing" role="status">正在根据你的选择生成情景，请稍候…</p>
          <p v-else>{{ visitSituation }}</p>
        </section>
        <div class="visit-options-heading"><h3>你想从哪里开始？</h3><span>选择一种方式，进入模拟</span></div>
        <div class="visit-entry-options">
          <button v-for="entry in visitEntries" :key="entry.id" type="button" class="visit-entry-card"
            :disabled="initializing || loading" @click="chooseVisitEntry(entry)">
            <img :src="entry.image" alt="" width="360" height="240" />
            <span class="visit-entry-copy"><strong>{{ entry.title }}</strong><span>{{ entry.description }}</span></span>
            <span class="visit-entry-arrow" aria-hidden="true">↗</span>
          </button>
        </div>
        <p class="visit-entry-note">智能分诊是可选功能，选择后模拟省人医微信公众号相关功能。</p>
      </div>
      <template #footer><el-button text @click="visitEntryVisible = false">稍后选择</el-button></template>
    </el-dialog>

    <el-dialog v-model="actionDialogVisible" :title="pendingAction?.title || '补充动作细节'" width="min(560px, 94vw)">
      <p class="action-description">{{ pendingAction?.description }}</p>
      <el-form label-position="top">
        <el-form-item v-for="field in pendingAction?.fields || []" :key="field.key" :label="field.label">
          <el-input v-model="actionForm[field.key]" :placeholder="field.placeholder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">稍后补充</el-button>
        <el-button type="primary" :disabled="!actionFormComplete" @click="submitActionDetails">提交动作描述</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import AvatarStage from '@/components/AvatarStage.vue'
import VoiceButton from '@/components/VoiceButton.vue'
import VoiceComposer from '@/components/VoiceComposer.vue'
import VoiceFeedback from '@/components/VoiceFeedback.vue'
import { useMobileViewport } from '@/utils/useMobileViewport'

const isMobile = useMobileViewport()
const mobileHeaderTarget = ref(null)
import { useUserStore } from '@/stores/user'
import { askCoach, endChat, getSession, getSessionPressure, restartChatStage, saveMedicalRecord, sendMessage, startChat } from '@/api/chat'
import { getSceneDetail } from '@/api/scene'
import {
  stripForSpeech,
  extractPerformanceCue,
  resolveCharacterRole,
  resolvePersona,
  extractChokingCharacter,
  PERSONA_LIST,
  ROLE_PROFILE
} from '@/utils/live2dMap'
import { isMiMoTTSSupported, unifiedSpeak, stopUnifiedSpeaking } from '@/utils/ttsService'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const sceneId = route.params.sceneId
const sessionId = ref(null)
const sceneInfo = ref({})
// Keep scene classification ahead of watchers. This prevents a temporal-dead-
// zone crash after production minification in embedded WebViews such as WeChat.
const isFirstVisit = computed(() => sceneInfo.value.title?.includes('独立看病'))
const isOsce = computed(() => /OSCE|模拟问诊|病例书写/i.test(sceneInfo.value.title || ''))
const isChoking = computed(() => sceneInfo.value.title?.includes('梗阻'))
const messages = ref([])
const inputText = ref('')
const voiceInputRef = ref(null)
const inputRecording = ref(false)
function onInputRecording(active) {
  inputRecording.value = active
  if (active) stopVoice()
}
const loading = ref(false)
const initializing = ref(true)
const messageListRef = ref(null)
const coachTip = ref(null)
const coachHistory = ref([])
const coachDrawerVisible = ref(false)
const unreadCoachCount = ref(0)
const currentStage = ref(null)
const setupVisible = ref(false)
const selectedGender = ref('')
const visitEntryVisible = ref(false)
const visitSituation = computed(() => messages.value.find((message) => message.role === 'system')?.content || messages.value[0]?.content || '')
const visitEntries = [
  { id: 'online', title: '线上预约', description: '提前选择科室与时间', image: '/images/visit-entry/online.png', value: '我选择线上预约挂号。' },
  { id: 'counter', title: '线下窗口', description: '到院后寻求人工帮助', image: '/images/visit-entry/counter.png', value: '我选择到医院线下现场挂号。' },
  { id: 'wechat', title: '智能分诊', description: '省人医微信公众号相关功能', image: '/images/visit-entry/wechat.png', value: '我不确定该挂哪个科，先打开省人医微信公众号使用智能分诊。' }
]
function chooseVisitEntry(entry) {
  if (initializing.value || loading.value) return
  visitEntryVisible.value = false
  onSend(entry.value, { target: 'patient' })
}
const backendAvailable = ref(true)
const pendingAction = ref(null)
const actionDialogVisible = ref(false)
const actionForm = reactive({})
const recordWorkspaceRef = ref(null)
const recordInputRef = ref(null)
const recordSaving = ref(false)
const recordSections = ['基本信息', '主诉', '现病史', '其他病史', '体格检查', '辅助检查', '病历摘要', '初步诊断/鉴别']
const MEDICAL_RECORD_TEMPLATE = `基本信息（姓名、性别、年龄、民族、婚姻、职业、籍贯、住址、记录日期、病史陈述者及可靠程度）：

主诉：

现病史：

其他病史（既往史、过敏史、个人婚育史、家族史）：

体格检查：

辅助检查：

病历摘要：

初步诊断：

鉴别诊断：`
const medicalRecordDraft = ref(MEDICAL_RECORD_TEMPLATE)
const lastSavedRecord = ref('')
let coachTipTimer = null
let pressureTimer = null
let quotaWarningShown = false
// 结束训练后主动跳转（已确认过），路由守卫不再二次弹窗
let leavingAfterEnd = false

// 教练问答模式：输入直接发给观察者教练，不进入患者对话
const coachMode = ref(false)
const coachLoading = ref(false)
// Network/TTS work may continue after a message becomes visible. These flags
// represent only the period before text and audio are ready, so a second
// "..." bubble never appears underneath an already displayed reply.
const replyPending = ref(false)
const coachReplyPending = ref(false)
// 患者回复生成期间，学生可继续补充；旧回复将被废弃，再合并上下文生成一次新回复。
const queuedPatientMessages = ref([])
// 时间压力（仅异物梗阻）：超时未施救患者会恶化甚至昏倒，可关闭
const timePressureEnabled = ref(localStorage.getItem('yishengban_time_pressure') !== 'off')
const finishPromptShown = ref(false)

// ---------- 左侧机器人数字人 ----------
const stageRef = ref(null)
const avatarCollapsed = ref(localStorage.getItem('yishengban_avatar_collapsed') === '1')
const ttsAvailable = ref(isMiMoTTSSupported())
const voiceEnabled = ref(localStorage.getItem('yishengban_voice') !== '0')
const currentSpeakerRole = ref('patient')
const currentExpression = ref('neutral')
// 肢体动作（与表情解耦）：捂脖子 / 高臂挥手 / 深呼吸 / 拍胸脯 / 伸手 / 点头 / 摇头 …
const currentAction = ref('idle')
// 时间压迫强度 0→1：驱动机器人眼睛蓝→黄→红、头部屏幕黑→红
const pressureLevel = ref(0)
const stageSpeaking = ref(false)
const lastSpokenMsg = ref(null)

// 语音代际：打断旧朗读后，旧 speakMessage 迟到的 finally 不能误清新一轮 speaking 状态
let speakGen = 0
let visitPlaybackGeneration = 0

// 打断正在播放的语音（使用者在角色说话时发言 / 关掉语音开关）并复位说话状态
function stopVoice() {
  visitPlaybackGeneration += 1
  speakGen += 1
  stopUnifiedSpeaking()
  stageSpeaking.value = false
}

// 调试用：点面板上的"切换表情"按钮会按这个组合轮播，
// 覆盖异物梗阻（捂脖子/深呼吸/挥手/萎靡/拍胸）与首次看病（伸手/点头/摇头）两套动作
const PERFORMANCE_CYCLE = [
  { expression: 'choking', action: 'clutchThroat' },
  { expression: 'suffering', action: 'deepBreath' },
  { expression: 'anxious', action: 'waveHigh' },
  { expression: 'listless', action: 'slump' },
  { expression: 'relieved', action: 'chestPat' },
  { expression: 'crying', action: 'idle' },
  { expression: 'smile', action: 'nod' },
  { expression: 'calm', action: 'reachOut' },
  { expression: 'confused', action: 'shakeHead' },
  { expression: 'anxious', action: 'explain' },
  { expression: 'neutral', action: 'idle' }
]

const canReplay = computed(() => {
  const message = lastSpokenMsg.value
  if (!message) return false
  if (isChoking.value && message.role === 'ai') return !!message.extra?.speech_text
  return true
})

const userAvatar = computed(() => userStore.user?.avatar_url || '')
// 异物梗阻场景：左侧数字人是「被噎住的患者」，需要按人物设定（阿姨/胖叔…）换声音与形象
// 当前场景类型：choking（异物梗阻）/ firstVisit（第一次独立看病）/ other
// 决定机器人用哪套「表情 + 动作」规则
const sceneKey = computed(() => {
  if (isChoking.value) return 'choking'
  if (isFirstVisit.value) return 'firstVisit'
  if (isOsce.value) return 'osce'
  return 'other'
})
// 后端开场元信息里给出的患者人物（如「体型肥胖的食堂师傅」），用于匹配音色/形象
const chokingCharacter = ref('')
const voiceCast = ref({})
const currentPersona = computed(() => {
  if (isChoking.value && currentSpeakerRole.value === 'patient' && chokingCharacter.value) return resolvePersona(chokingCharacter.value)
  const cast = voiceCast.value?.[currentSpeakerRole.value]
  return isFirstVisit.value ? { gender: cast?.gender, label: currentSpeakerName.value } : (cast ? { gender: cast.gender } : null)
})
function speakerName(msg) {
  if (!isFirstVisit.value) return sceneInfo.value.role || '患者'
  const named = (msg?.content || '').match(/^【([^】]{1,30})】/)
  if (named && !/角色|发送资料/.test(named[1])) return named[1]
  const role = resolveCharacterRole('ai', { isFirstVisit: true, content: msg?.content, stageId: msg?.extra?.stage_info?.id || currentStage.value?.id, kind: msg?.meta?.kind || msg?.extra?.kind })
  return voiceCast.value?.[role]?.display_name || ROLE_PROFILE[role]?.name || '就医引导'
}
const currentSpeakerName = computed(() => {
  const last = [...messages.value].reverse().find(m => m.role === 'ai')
  return last ? speakerName(last) : '就医引导'
})
// AI 角色头像文字：异物梗阻场景扮演患者，首次看病扮演医院流程角色
const aiAvatarText = computed(() => (isFirstVisit.value ? '医' : '患'))
const hasUserMessage = computed(() => messages.value.some((message) => message.role === 'user'))
const stageNames = computed(() => {
  if (isFirstVisit.value) return ['挂号报到', '症状问诊', '诊断医嘱', '人工缴费', '取药执行']
  if (isOsce.value) return ['接诊准备', '主诉现病史', '其他病史', '快速检查', '病历诊断']
  return ['评估判断', '急救执行', '后续处理']
})
const medicalRecordSaved = computed(() => !!lastSavedRecord.value && medicalRecordDraft.value.trim() === lastSavedRecord.value)
const inputPlaceholder = computed(() => {
  if (coachMode.value) return '向观察者教练提问（不进入患者对话）…'
  if (isOsce.value) return '以接诊医生身份继续问诊…'
  return '输入你的回复…'
})
const actionFormComplete = computed(() => (pendingAction.value?.fields || []).every((field) => actionForm[field.key]?.trim()))

const scenePlaceholders = {
  1: {
    title: '异物梗阻急救',
    role: '窒息患者（演示模式）',
    role_avatar: '',
    opening: '你正在学校食堂吃饭，突然发现邻桌一名同学猛地捂住喉咙：无法发出声音，双手紧紧掐住脖子，脸色迅速变得青紫，身旁的桌上还放着一包没吃完的坚果。\n\n你现在就在现场。请观察并说出你的第一步行动。',
    firstStep: ''
  },
  2: {
    title: '第一次独立看病',
    role: '就医引导',
    role_avatar: '',
    opening: '周末留校期间，你出现鼻塞、咽痛和低热，这是你第一次独自处理就医流程。\n\n你的第一步是选择挂号方式和科室。请告诉我你准备怎么做。',
    firstStep: '选择挂号方式'
  },
  3: {
    title: 'OSCE模拟问诊与病历书写',
    role: '标准化患者（演示模式）',
    role_avatar: '',
    opening: '你进入内科 OSCE 模拟考站，面前坐着一位因不适前来就诊的年轻女性。本考站以问诊为重点，检查环节将快速带过。\n\n请以接诊医生身份开始问诊，并在右侧病历区同步整理问诊信息。',
    firstStep: '规范问候并核对患者身份'
  }
}

// 异物梗阻演示模式：开场文案里写明人物（这里固定为「中年男性」，便于直接看到男性数字人），
// 数字人形象按从文本抽取的人物性别切换（非随机）。真实后端会从 scenario_generator 随机给不同患者。
const DEMO_CHOKING_OPENING =
  '你正在图书馆自习区，一位中年男性突然从座位上站起，双手掐住脖子，眼睛惊恐地瞪大，喉咙里发出窒息的咯咯声，面色青紫。\n\n你现在就在现场。请观察并说出你的第一步行动。'

// ---------- 数字人：角色判定 / 表情 / 朗读 ----------

// 一条消息进来后，决定"谁来说"和"什么表情"
function applySpeaker(msg) {
  if (!msg) return
  const role = resolveCharacterRole(msg.role, {
    isFirstVisit: isFirstVisit.value,
    content: msg.content,
    stageId: currentStage.value?.id,
    kind: msg.meta?.kind || msg.extra?.kind
  })
  currentSpeakerRole.value = role

  // 教练：固定「讲解」表情 + 摆手说明动作
  if (msg.role === 'coach') {
    currentExpression.value = 'explaining'
    currentAction.value = 'explain'
    return
  }
  // 用户发言时数字人是「倾听方」，回到平静待机，避免沿用上一条角色的夸张动作
  if (msg.role === 'user') {
    currentExpression.value = 'neutral'
    currentAction.value = 'idle'
    return
  }

  // 异物梗阻：没命中任何规则时，兜底用「异物哽咽 + 捂住脖子」——这是窒息者的默认姿态
  const fallback = isChoking.value ? 'choking' : 'neutral'
  const { expression, action } = extractPerformanceCue(msg.content, sceneKey.value, fallback)
  currentExpression.value = expression
  currentAction.value = action === 'idle' && fallback === 'choking' ? 'clutchThroat' : action
}

// 会话恢复/重开后，用最后一条角色发言重算当前说话人
function recomputeSpeaker() {
  for (let i = messages.value.length - 1; i >= 0; i -= 1) {
    const m = messages.value[i]
    if (m.role === 'ai' || m.role === 'coach') {
      applySpeaker(m)
      return
    }
  }
  currentSpeakerRole.value = isFirstVisit.value ? 'registrar' : 'patient'
  currentExpression.value = 'neutral'
  currentAction.value = 'idle'
}

// 超过这个长度就不自动朗读：情景简报动辄几百字，念完要一两分钟，体验很差。
// 用户点气泡上的"重播"仍可强制朗读。
const AUTO_SPEAK_MAX = 400

// 朗读一条消息：正文剔除【】和（）后再念，同时驱动嘴型
async function speakMessage(msg, { force = false, onReady } = {}) {
  if (!msg || !voiceEnabled.value || !ttsAvailable.value || inputRecording.value) {
    onReady?.()
    return
  }
  const speakingRole = resolveCharacterRole(msg.role, {
    isFirstVisit: isFirstVisit.value,
    content: msg.content,
    stageId: currentStage.value?.id,
    kind: msg.meta?.kind || msg.extra?.kind
  })
  // 异物梗阻只朗读后端已校验的患者原话；动作、咳嗽和喘气永远不进入 TTS。
  const text = isChoking.value && speakingRole === 'patient'
    ? String(msg.extra?.speech_text || '').trim()
    : stripForSpeech(msg.content)
  if (!text) { onReady?.(); return }
  if (!force && text.length > AUTO_SPEAK_MAX) { onReady?.(); return }

  // 在等待 TTS 启动前锁定消息自己的角色，避免此时切换“问教练”后串用音色。
  const speakingPersona = isChoking.value && speakingRole === 'patient' && chokingCharacter.value
    ? resolvePersona(chokingCharacter.value)
    : null
  const gen = ++speakGen
  stopUnifiedSpeaking()
  await nextTick()
  const fallbackExpression = isChoking.value ? 'choking' : 'neutral'
  const cue = msg.role === 'coach'
    ? { expression: 'explaining', action: 'explain' }
    : extractPerformanceCue(msg.content, sceneKey.value, fallbackExpression)
  let readyCalled = false
  const ready = () => {
    if (readyCalled) return
    readyCalled = true
    onReady?.()
    stageRef.value?.startTalk?.()
    stageSpeaking.value = true
  }
  try {
    // 异物梗阻患者：用「人物设定」的音色（阿姨/胖叔…），否则用角色默认音色
    const persona = speakingPersona
    const profile = ROLE_PROFILE[speakingRole] || {}
    const gender = persona?.gender || voiceCast.value?.[speakingRole]?.gender || profile.gender || ''
    const castVoice = voiceCast.value?.[speakingRole]?.voice
    await unifiedSpeak(text, {
      role: speakingRole,
      emotion: cue.expression,
      gender,
      mimoVoice: castVoice,
      onReady: ready,
      pitch: persona?.pitch ?? profile.pitch ?? 1,
      rate: persona?.rate ?? profile.rate ?? 1
    })
  } catch (error) {
    // MiMo 是唯一语音源。失败时只显示文字，不会混入系统或 meSpeak 声音。
    if (error?.name !== 'AbortError') console.warn('[TTS] MiMo 语音不可用:', error?.message || error)
    onReady?.()
  } finally {
    if (gen === speakGen) stageSpeaking.value = false
  }
}

// 角色消息统一入口：入流 + 驱动数字人 + 自动朗读
async function appendCharacterMessage(msg) {
  const roleSegments = splitRoleSegments(msg)
  if (msg.role === 'ai' && isFirstVisit.value) {
    // Commit the entire turn before playback: no old segment can appear after a new user turn.
    const segments = roleSegments.map((content, index) => ({
      ...msg, id: `${msg.id}-${index}`, content,
      extra: index === roleSegments.length - 1 ? msg.extra : {}
    }))
    messages.value.push(...segments)
    replyPending.value = false
    applySpeaker(segments[0])
    scrollToBottom()
    const generation = ++visitPlaybackGeneration
    void (async () => {
      for (const segment of segments) {
        if (generation !== visitPlaybackGeneration) break
        applySpeaker(segment)
        lastSpokenMsg.value = segment
        await speakMessage(segment)
      }
    })().catch(error => console.warn('[TTS] 就医语音播放失败:', error))
    return
  }
  if (roleSegments.length > 1) {
    for (const [index, segment] of roleSegments.entries()) {
      await appendCharacterMessage({ ...msg, id: `${msg.id}-${index}`, content: segment, extra: index === roleSegments.length - 1 ? msg.extra : {} })
    }
    return
  }
  let displayed = false
  const display = () => {
    if (displayed) return
    displayed = true
    if (msg.role === 'coach') coachReplyPending.value = false
    else replyPending.value = false
    messages.value.push(msg)
    applySpeaker(msg)
    lastSpokenMsg.value = msg
    scrollToBottom()
  }
  let markReady
  const ready = new Promise((resolve) => { markReady = resolve })
  const reveal = () => { display(); markReady() }
  const playback = speakMessage(msg, { onReady: reveal })
    .catch((error) => console.warn('[TTS] 角色语音播放失败:', error))
    .finally(reveal)
  // 只等到音频准备好并与文字同时出现，不等待整段播放结束，输入区可立即恢复。
  await ready
  // 同一条 AI 文案出现多个角色时，按台词顺序播完再进入下一个角色，避免被 stopUnifiedSpeaking 截断。
  await playback
}

function splitRoleSegments(msg) {
  if (msg.role !== 'ai' || !isFirstVisit.value) return [msg.content]
  const pieces = String(msg.content || '').split(/(?=【[^】\n]{1,30}】)/).map((item) => item.trim()).filter(Boolean)
  return pieces.length > 1 && pieces.every((item) => /^【[^】]+】/.test(item)) ? pieces : [msg.content]
}

function replaySpeech(msg) {
  if (!msg) return
  stopVoice()
  applySpeaker(msg)
  lastSpokenMsg.value = msg
  // 重播是用户主动触发，不受长度限制
  speakMessage(msg, { force: true })
}

function cycleExpression() {
  const idx = PERFORMANCE_CYCLE.findIndex(
    (p) => p.expression === currentExpression.value && p.action === currentAction.value
  )
  const next = PERFORMANCE_CYCLE[(idx + 1) % PERFORMANCE_CYCLE.length]
  currentExpression.value = next.expression
  currentAction.value = next.action
}

function onVoiceToggle(value) {
  localStorage.setItem('yishengban_voice', value ? '1' : '0')
  if (!value) stopVoice()
}

function onCollapseAvatar() {
  avatarCollapsed.value = true
  localStorage.setItem('yishengban_avatar_collapsed', '1')
}

function onExpandAvatar() {
  avatarCollapsed.value = false
  localStorage.removeItem('yishengban_avatar_collapsed')
}

// 阶段推进时同步左侧角色（后端没带【角色名】时的兜底）
watch(
  () => currentStage.value?.id,
  () => {
    const role = currentSpeakerRole.value
    if (role === 'coach' || role === 'patient') return
    recomputeSpeaker()
  }
)

watch(coachMode, (enabled) => {
  stopVoice()
  if (enabled) {
    currentSpeakerRole.value = 'coach'
    currentExpression.value = 'explaining'
    currentAction.value = 'explain'
  } else {
    recomputeSpeaker()
  }
  nextTick(() => stageRef.value?.startTalk?.())
})

function initialStage() {
  const goal = isFirstVisit.value
    ? '选择挂号方式和科室，完成打印报到单与诊间扫码报到'
    : isOsce.value
      ? '规范问候、自我介绍、核对身份并取得配合'
      : '判断梗阻程度并建立呼救意识'
  return {
    id: 1,
    name: stageNames.value[0],
    goal,
    progress: 0,
    total: stageNames.value.length
  }
}

function buildFallbackOpening(placeholder) {
  return {
    id: `system-${Date.now()}`,
    role: 'system',
    content: `（演示模式）${placeholder.opening}`,
    timestamp: Date.now(),
    meta: {
      agent_name: '情景生成智能体',
      first_step: placeholder.firstStep,
      quick_actions: isFirstVisit.value ? [
        { label: '线上预约挂号', value: '我选择线上预约挂号。' },
        { label: '线下现场挂号', value: '我选择到医院线下现场挂号。' },
        { label: '省人医微信公众号智能分诊', value: '我不确定该挂哪个科，先打开省人医微信公众号使用智能分诊。' }
      ] : []
    }
  }
}

async function initSession() {
  initializing.value = true
  // 从训练历史"继续训练"进入：带 ?session=xxx 恢复未完成会话
  const resumeId = Number(route.query.session) || null
  try {
    sceneInfo.value = await getSceneDetail(sceneId)
    if (sceneInfo.value.title?.includes('独立看病')) {
      sceneInfo.value.role = '就医引导'
    }
    if (isOsce.value) sceneInfo.value.role = '标准化患者'
    if (resumeId) {
      const resumed = await resumeExistingSession(resumeId)
      if (resumed) return
    } else if (sceneInfo.value.title?.includes('独立看病')) {
      setupVisible.value = true
      return
    }
    await beginSession()
  } catch (error) {
    console.warn('场景加载失败，使用演示模式', error)
    backendAvailable.value = false
    const placeholder = scenePlaceholders[Number(sceneId)] || scenePlaceholders[1]
    sceneInfo.value = {
      title: placeholder.title,
      role: placeholder.role,
      role_avatar: placeholder.role_avatar
    }
    if (Number(sceneId) === 2) {
      setupVisible.value = true
    } else {
      // 异物梗阻演示模式：按固定开场文案抽人物（中年男性），数字人形象随性别切换
      if (isChoking.value) {
        messages.value = [buildFallbackOpening({ ...placeholder, opening: DEMO_CHOKING_OPENING })]
        chokingCharacter.value = extractChokingCharacter(DEMO_CHOKING_OPENING)
      } else {
        messages.value = [buildFallbackOpening(placeholder)]
      }
      currentStage.value = initialStage()
    }
  } finally {
    initializing.value = false
    startPressurePolling()
    recomputeSpeaker()
    await scrollToBottom()
  }
}

// 恢复未完成会话（训练历史"继续训练"入口）
async function resumeExistingSession(resumeId) {
  try {
    const data = await getSession(resumeId)
    if (!data || data.ended_at) return false
    sessionId.value = data.session_id
    // 恢复消息流：教练实时提示不入流，只保留"问教练"的问答
    const restoredMessages = data.messages || []
    const storedRecord = [...restoredMessages].reverse().find((m) => m.extra?.kind === 'medical_record')
    if (storedRecord) {
      const content = storedRecord.content.replace(/^【病历记录】\s*/, '')
      medicalRecordDraft.value = content
      lastSavedRecord.value = content.trim()
    }
    messages.value = restoredMessages
      .filter((m) => m.extra?.kind !== 'medical_record')
      .filter((m) => !m.extra?.superseded)
      .filter((m) => m.role !== 'coach' || m.extra?.kind === 'coach_answer')
      .map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        meta: m.extra?.display,
        extra: m.extra
      }))
    voiceCast.value = messages.value.find((message) => message.role === 'system')?.meta?.voice_cast || {}
    currentStage.value = initialStage()
    for (const m of [...restoredMessages].reverse()) {
      if (m.extra?.stage_info) {
        currentStage.value = m.extra.stage_info
        break
      }
    }
    // 恢复教练历史抽屉（实时提示；"问教练"的问答已在消息流里展示）
    coachHistory.value = (data.messages || [])
      .filter((m) => m.role === 'coach' && m.extra?.kind !== 'coach_answer' && !m.extra?.superseded)
      .map((m) => ({ id: m.id, type: m.extra?.type || 'info', text: m.content, timestamp: m.timestamp }))
    unreadCoachCount.value = 0
    ElMessage.closeAll?.()
    recomputeSpeaker()
    showTip('success', '已恢复上次未完成的训练，请继续')
    return true
  } catch (error) {
    console.warn('会话恢复失败，改为新开训练', error)
    return false
  }
}

async function beginSession() {
  setupVisible.value = false
  if (isFirstVisit.value) visitEntryVisible.value = true
  initializing.value = true
  try {
    if (!backendAvailable.value) throw new Error('演示模式')
    const response = await startChat(sceneId, {
      gender: selectedGender.value || 'unspecified'
    })
    sessionId.value = response.session_id
    sceneInfo.value = { ...sceneInfo.value, ...response.scene_info }
    voiceCast.value = response.opening_meta?.voice_cast || {}
    // 异物梗阻场景：记录患者人物设定（阿姨/胖叔…），用于换声音与形象
    if (isChoking.value) {
      chokingCharacter.value = response.opening_meta?.character || extractChokingCharacter(response.opening_message)
    }
    messages.value = [{
      id: `system-${response.session_id}`,
      role: response.opening_role || 'system',
      content: response.opening_message,
      timestamp: Date.now(),
      meta: response.opening_meta || {}
    }]
  } catch (error) {
    console.warn('会话启动失败，进入演示模式', error)
    backendAvailable.value = false
    sessionId.value = null
    const placeholder = scenePlaceholders[Number(sceneId)] || scenePlaceholders[1]
    // 异物梗阻演示模式：随机抽一个患者人物，保证反复测试人物设定会变化
    if (isChoking.value) {
      messages.value = [buildFallbackOpening({ ...placeholder, opening: DEMO_CHOKING_OPENING })]
      chokingCharacter.value = extractChokingCharacter(DEMO_CHOKING_OPENING)
    } else {
      messages.value = [buildFallbackOpening(placeholder)]
    }
  } finally {
    currentStage.value = initialStage()
    recomputeSpeaker()
    initializing.value = false
    startPressurePolling()
    await scrollToBottom()
  }
}

function canUseQuickActions(message) {
  return !hasUserMessage.value && Array.isArray(message.meta?.quick_actions) && message.meta.quick_actions.length
}

async function onSend(prefilledText = '', options = {}) {
  if (voiceInputRef.value?.busy) return
  const forcedTarget = options.target || ''
  const sendingToCoach = forcedTarget === 'coach' || (!forcedTarget && coachMode.value && !!sessionId.value)
  if (sendingToCoach && coachLoading.value) return
  if (!sendingToCoach && isFirstVisit.value && loading.value) return
  const text = (typeof prefilledText === 'string' && prefilledText ? prefilledText : inputText.value).trim()
  if (!text) return
  const voiceClips = options.voiceClips || (prefilledText ? [] : (voiceInputRef.value?.takeClips() || []))

  // 用户发言：立即打断角色正在说的话，避免“角色还在念、新的对话已开始”的叠音
  stopVoice()

  if (!options.alreadyAdded) {
    messages.value.push({ id: `user-${Date.now()}`, role: 'user', content: text, timestamp: Date.now(), extra: { voice_assessments: voiceClips.map(c => c.assessment) } })
  }
  inputText.value = ''
  await scrollToBottom()

  // 主角色仍在生成时记录补充。旧回复返回后不会显示，下一轮会把连续补充合并理解。
  if (!sendingToCoach && loading.value) {
    queuedPatientMessages.value.push({ text, voiceClips })
    ElMessage.info('补充内容已记录，将合并上下文重新回答')
    return
  }
  if (sendingToCoach) {
    coachLoading.value = true
    coachReplyPending.value = true
  } else {
    loading.value = true
    replyPending.value = true
  }

  try {
    const firstVisitUserText = messages.value
      .filter((message) => message.role === 'user')
      .map((message) => message.content)
      .join(' ')
    const hasCompletedCheckIn = firstVisitUserText.includes('报到单') && firstVisitUserText.includes('报到机')

    // 教练问答模式：直接发给观察者教练，不进入患者对话
    if (sendingToCoach) {
      const response = await askCoach(sessionId.value, text, voiceClips.map(c => c.receipt))
      if (response.quota?.exhausted && !quotaWarningShown) {
        quotaWarningShown = true
        ElMessageBox.alert(response.quota.message, '今日练习额度', { confirmButtonText: '知道了', type: 'warning' })
      }
      await appendCharacterMessage({
        id: response.message_id || `coach-${Date.now()}`,
        role: 'coach',
        content: response.content,
        timestamp: response.timestamp || Date.now(),
        extra: { kind: 'coach_answer' }
      })
      return
    }
    if (sessionId.value) {
      const response = await sendMessage({
        session_id: sessionId.value,
        message: text,
        voice_receipts: voiceClips.map(c => c.receipt),
        supersede_previous_ai: !!options.supersedePreviousAi
      })
      if (response.quota?.exhausted && !quotaWarningShown) {
        quotaWarningShown = true
        ElMessageBox.alert(response.quota.message, '今日练习额度', { confirmButtonText: '知道了', type: 'warning' })
      }
      const hasPendingCorrection = queuedPatientMessages.value.length > 0
      if (!hasPendingCorrection) await appendCharacterMessage({
        id: response.message_id || `ai-${Date.now()}`,
        role: response.role || 'ai',
        content: response.content,
        timestamp: response.timestamp || Date.now(),
        extra: {
          attachments: response.attachments || [],
          airway_state: response.airway_state,
          speech_text: response.speech_text || ''
        }
      })
      if (!hasPendingCorrection && response.stage_info) {
        const previousStage = currentStage.value
        currentStage.value = response.stage_info
        if (response.stage_info.transitioned && previousStage && response.stage_info.id > previousStage.id) {
          showTip('success', `已完成「${previousStage.name}」，进入阶段 ${response.stage_info.id}：${response.stage_info.name}`)
        }
        if (response.stage_info.finished && !finishPromptShown.value) {
          finishPromptShown.value = true
          confirmFinishTraining()
        }
      }
      if (!hasPendingCorrection && response.coach_tip) receiveCoachTip(response.coach_tip)
      if (!hasPendingCorrection && response.ui_action?.type === 'describe_action') openActionDialog(response.ui_action)
    } else {
      await new Promise((resolve) => setTimeout(resolve, 500))
      await appendCharacterMessage({
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: isFirstVisit.value
          ? (hasCompletedCheckIn
              ? '（诊间报到机）扫码报到成功，现在进入排队候诊。请先说说你现在最主要的不舒服是什么。'
              : '（挂号界面）挂号后还不能直接排队。请先到自助机打印报到单，再到诊间报到机扫码报到。')
          : isOsce.value
            ? '（患者认真看着你）我这几年总是心慌、气喘，最近一周明显重了。医生，您还想了解哪些情况？'
            : '（对方仍无法说话，双手掐着脖子，焦急地看着你。）',
        timestamp: Date.now()
      })
      receiveCoachTip({
        id: `coach-${Date.now()}`,
        type: 'info',
        text: isFirstVisit.value
          ? (hasCompletedCheckIn ? '报到流程完整，接下来清楚描述症状。' : '初诊挂号后要先打印报到单，再到诊间扫码报到。')
          : isOsce.value
            ? '继续围绕主诉按时间顺序追问，检查环节会快速带过。'
            : '先确认患者能否说话或有效咳嗽。',
        timestamp: Date.now()
      })
    }
  } catch (error) {
    showTip('error', '消息发送失败，你的输入已保留在对话中，可以稍后重试')
  } finally {
    if (sendingToCoach) {
      coachLoading.value = false
      coachReplyPending.value = false
    }
    else {
      loading.value = false
      replyPending.value = false
      const corrections = queuedPatientMessages.value.splice(0)
      if (corrections.length) {
        await onSend(corrections.map(c => c.text).join('；补充更正：'), {
          target: 'patient',
          alreadyAdded: true,
          supersedePreviousAi: true,
          voiceClips: corrections.flatMap(c => c.voiceClips)
        })
      }
    }
    await scrollToBottom()
  }
}

function receiveCoachTip(tip) {
  const normalized = { ...tip, id: tip.id || `coach-${Date.now()}`, timestamp: tip.timestamp || Date.now() }
  coachHistory.value.push(normalized)
  // 实时提示只走弹层 + 历史抽屉，不进入主对话流；
  // 只有学生主动"问教练"的问答才出现在主对话里
  coachTip.value = normalized
  if (!coachDrawerVisible.value) unreadCoachCount.value += 1
  if (coachTipTimer) window.clearTimeout(coachTipTimer)
  coachTipTimer = window.setTimeout(() => { coachTip.value = null }, 6500)
}

function openCoachHistory() {
  coachDrawerVisible.value = true
  unreadCoachCount.value = 0
}

function openActionDialog(action) {
  pendingAction.value = action
  Object.keys(actionForm).forEach((key) => delete actionForm[key])
  for (const field of action.fields || []) actionForm[field.key] = ''
  actionDialogVisible.value = true
}

async function submitActionDetails() {
  const detail = (pendingAction.value?.fields || [])
    .map((field) => `${field.label}${actionForm[field.key].trim()}`)
    .join('；')
  actionDialogVisible.value = false
  await onSend(detail)
}

async function restartCurrentStage() {
  if (!sessionId.value || loading.value) return
  loading.value = true
  replyPending.value = true
  try {
    const response = await restartChatStage(sessionId.value)
    await appendCharacterMessage({
      id: response.id,
      role: response.role || 'system',
      content: response.content,
      timestamp: response.timestamp || Date.now(),
      meta: response.meta || {}
    })
    currentStage.value = response.stage_info || currentStage.value
    recomputeSpeaker()
    coachDrawerVisible.value = false
    coachTip.value = null
    // 重开阶段等于重新计时，压迫强度归零，机器人恢复常态
    pressureLevel.value = 0
    startPressurePolling()
    showTip('success', '已重新开始当前阶段，之前的记录仍会保留在复盘中')
    await scrollToBottom()
  } catch (error) {
    showTip('error', '阶段重置失败，请稍后重试')
  } finally {
    loading.value = false
    replyPending.value = false
  }
}

function hasMeaningfulRecordContent() {
  const headings = ['基本信息', '主诉', '现病史', '其他病史', '体格检查', '辅助检查', '病历摘要', '初步诊断', '鉴别诊断']
  const escaped = headings.map((heading) => heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  const sectionPattern = new RegExp(`(?:^|\\n)\\s*(?:${escaped})(?:[^：:\\n]*)[：:]`, 'g')
  const matches = [...medicalRecordDraft.value.matchAll(sectionPattern)]
  return matches.some((match, index) => {
    const start = (match.index || 0) + match[0].length
    const end = index + 1 < matches.length ? matches[index + 1].index : medicalRecordDraft.value.length
    return medicalRecordDraft.value.slice(start, end).replace(/\s/g, '').length >= 2
  })
}

async function saveRecord() {
  if (recordSaving.value) return
  if (!hasMeaningfulRecordContent()) {
    showTip('warning', '请至少在一个病历栏目中填写有效内容')
    return
  }
  recordSaving.value = true
  try {
    const content = medicalRecordDraft.value.trim()
    if (sessionId.value && backendAvailable.value) {
      await saveMedicalRecord(sessionId.value, content)
    }
    lastSavedRecord.value = content
    showTip('success', '病历已保存，并将作为独立评分项目')
  } catch {
    showTip('error', '病历保存失败，请稍后重试')
  } finally {
    recordSaving.value = false
  }
}

async function focusRecordWorkspace() {
  await nextTick()
  recordWorkspaceRef.value?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
  recordInputRef.value?.focus?.()
}

async function onEnd(skipConfirm = false) {
  if (voiceInputRef.value?.busy) { ElMessage.info('请先停止录音并等待识别完成'); return }
  if (isOsce.value && !medicalRecordSaved.value) {
    await focusRecordWorkspace()
    showTip('warning', '请先完成并保存病历记录，再结束训练')
    return
  }
  try {
    if (!skipConfirm) {
      await ElMessageBox.confirm('确定结束本次训练并查看评分？', '结束训练', {
        confirmButtonText: '结束并评分',
        cancelButtonText: '继续训练',
        type: 'warning'
      })
    }
    stopPressurePolling()
    if (sessionId.value) await endChat(sessionId.value)
    leavingAfterEnd = true
    router.push(sessionId.value ? `/result/${sessionId.value}` : '/result/demo')
  } catch {
    // 用户选择继续训练
  }
}

async function confirmFinishTraining() {
  try {
    await ElMessageBox.confirm(
      '阶段判断智能体认为本次训练的核心目标已经完成。要现在结束训练并查看评分吗？',
      '训练目标已完成',
      {
        confirmButtonText: '结束并评分',
        cancelButtonText: '再练一会儿',
        type: 'success'
      }
    )
    await onEnd(true)
  } catch {
    // 用户选择继续训练
  }
}

// ---------- 时间压力（仅异物梗阻场景，可关闭） ----------
function onTimePressureToggle(value) {
  localStorage.setItem('yishengban_time_pressure', value ? 'on' : 'off')
  if (value) {
    startPressurePolling()
  } else {
    stopPressurePolling()
    // 关掉压迫后机器人要立刻恢复常态（眼睛回蓝、屏幕回黑）
    pressureLevel.value = 0
  }
}

// 后端阈值：约 150-180s 昏倒（较原逻辑延长 30s）。用 elapsed 换算连续压迫强度，
// 驱动机器人眼睛「蓝→黄→红」与头部屏幕「黑→红」渐变。
const DEFAULT_COLLAPSE_AFTER = 165

function applyPressure(res) {
  // 会话结束 / 非梗阻场景 / 患者已获救 → 解除压迫，机器人恢复常态
  if (['ended', 'off', 'resolved'].includes(res?.status)) {
    pressureLevel.value = 0
    return
  }
  // 已昏倒：停在最高压迫（此时后端已停止轮询）
  if (res?.status === 'collapsed') {
    pressureLevel.value = 1
    return
  }
  const elapsed = Number(res?.elapsed) || 0
  const collapseAfter = Number(res?.collapse_after) || DEFAULT_COLLAPSE_AFTER
  pressureLevel.value = Math.min(1, elapsed / collapseAfter)
}

function startPressurePolling() {
  stopPressurePolling()
  if (!sessionId.value || !backendAvailable.value || !isChoking.value || !timePressureEnabled.value) return
  pressureTimer = window.setInterval(checkTimePressure, 5000)
}

function stopPressurePolling() {
  if (pressureTimer) {
    window.clearInterval(pressureTimer)
    pressureTimer = null
  }
}

async function checkTimePressure() {
  if (!sessionId.value || loading.value) return
  try {
    const res = await getSessionPressure(sessionId.value)
    // 先按已耗时更新机器人的压迫强度（眼睛/屏幕渐变），再做后续分支处理
    applyPressure(res)
    if (['ended', 'off', 'resolved'].includes(res.status)) {
      stopPressurePolling()
      return
    }
    if (res.message && res.message_id) {
      const exists = messages.value.some((message) => message.id === res.message_id)
      if (!exists) {
        await appendCharacterMessage({
          id: res.message_id,
          role: 'ai',
          content: res.message,
          timestamp: Date.now()
        })
        await scrollToBottom()
      }
    }
    if (res.status === 'collapsed') {
      stopPressurePolling()
      showTaskFailed()
    }
  } catch {
    // 单次轮询失败静默忽略，下一轮再试
  }
}

async function showTaskFailed() {
  try {
    await ElMessageBox.confirm(
      '患者已失去意识！因为错过了黄金急救时间，本次训练任务失败。你可以选择立即开始 CPR 抢救继续训练，或结束训练查看评分。',
      '任务失败',
      {
        confirmButtonText: '结束并评分',
        cancelButtonText: '继续CPR抢救',
        type: 'error'
      }
    )
    await onEnd(true)
  } catch {
    // 用户选择继续抢救
  }
}

// ElMessage 默认顶部居中会盖住导航条（64px 高），统一下移避开
function showTip(type, message) {
  ElMessage({ message, type, offset: 76 })
}

function coachTagType(type) {
  return ({ success: 'success', warning: 'warning', error: 'danger', info: 'info' })[type] || 'info'
}

function coachTypeLabel(type) {
  return ({ success: '做得好', warning: '请注意', error: '立即纠正', info: '观察提示' })[type] || '观察提示'
}

function formatTime(timestamp) {
  if (!timestamp) return '--:--'
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

async function scrollToBottom() {
  await nextTick()
  if (messageListRef.value) messageListRef.value.scrollTop = messageListRef.value.scrollHeight
}

onMounted(initSession)

// ---------- 离开训练保护 ----------
// 站内导航（训练历史/个人中心/场景列表等）离开前确认，防止误触
onBeforeRouteLeave(async (to, from, next) => {
  if (leavingAfterEnd || !sessionId.value) {
    next()
    return
  }
  try {
    await ElMessageBox.confirm(
      '当前训练尚未结束，离开后可以从"训练历史"里继续。确定要离开吗？',
      '离开训练',
      { confirmButtonText: '离开', cancelButtonText: '继续训练', type: 'warning' }
    )
    next()
  } catch {
    next(false)
  }
})

// 浏览器刷新/关闭/回退只能用浏览器原生确认框
function onBeforeUnload(event) {
  if (sessionId.value && !leavingAfterEnd) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  if (coachTipTimer) window.clearTimeout(coachTipTimer)
  stopPressurePolling()
  stopVoice()
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
.visit-entry-content { color: #294c5b; }
.visit-entry-dialog { max-height: 90dvh; overflow-y: auto; border-radius: 20px; }
.visit-situation { padding: 22px 24px; border: 1px solid #d4e8e4; border-radius: 18px; background: linear-gradient(120deg, #edf8f4, #f8fbff); }
.visit-eyebrow { color: #418575; font-size: 11px; letter-spacing: .08em; }
.visit-situation h2 { font-size: 21px; margin: 8px 0 12px; color: #203f4a; }
.visit-situation p { margin: 0; line-height: 1.8; white-space: pre-line; overflow-wrap: anywhere; font-size: 14px; }
.visit-options-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin: 22px 0 12px; }
.visit-options-heading h3 { margin: 0; font-size: 17px; }
.visit-options-heading > span { color: #7c929b; font-size: 11px; }
.visit-entry-options { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.visit-entry-card { position: relative; padding: 0; overflow: hidden; border: 1px solid #dce8e8; border-radius: 16px; text-align: left; color: inherit; background: #fff; cursor: pointer; transition: border-color .2s, box-shadow .2s; }
.visit-entry-card:hover, .visit-entry-card:focus-visible { border-color: #369b88; box-shadow: 0 8px 22px #285e5218; outline: 2px solid #69b9a9; outline-offset: 2px; }
.visit-entry-card:disabled { opacity: .55; cursor: wait; }
.visit-entry-card img { display: block; width: 100%; height: auto; aspect-ratio: 3 / 2; object-fit: contain; background: #f1f8f5; }
.visit-entry-copy { display: flex; flex-direction: column; gap: 6px; padding: 15px 30px 18px 16px; }
.visit-entry-copy strong { font-size: 16px; }
.visit-entry-copy > span { font-size: 12px; color: #70878d; line-height: 1.5; }
.visit-entry-arrow { position: absolute; bottom: 29px; right: 14px; color: #388b7b; }
.visit-entry-note { margin: 13px 0 0; color: #7e9399; font-size: 11px; line-height: 1.6; }
.visit-entry-reopen { margin-top: 14px; }
@media (max-width: 980px) {
  .visit-situation { padding: 15px; border-radius: 14px; }
  .visit-situation h2 { font-size: 18px; margin: 6px 0 8px; }
  .visit-situation p { font-size: 13px; max-height: 27dvh; overflow-y: auto; }
  .visit-options-heading { margin: 16px 0 10px; flex-wrap: wrap; gap: 3px; }
  .visit-options-heading h3 { font-size: 15px; }
  .visit-entry-options { grid-template-columns: 1fr; gap: 9px; }
  .visit-entry-card { display: grid; grid-template-columns: 100px minmax(0, 1fr) 22px; align-items: center; border-radius: 13px; }
  .visit-entry-card img { width: 100px; height: auto; }
  .visit-entry-copy { padding: 10px 8px 10px 12px; gap: 4px; }
  .visit-entry-copy strong { font-size: 15px; }
  .visit-entry-copy > span { font-size: 11px; }
  .visit-entry-arrow { position: static; }
}

.chat-view {
  min-height: 100vh;
  background:
    radial-gradient(circle at 8% 10%, rgba(44, 123, 229, 0.08), transparent 28%),
    linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
}

.chat-container {
  width: min(1320px, calc(100% - 32px));
  height: calc(100vh - 88px);
  min-height: 640px;
  margin: 24px auto 0;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(214, 224, 235, 0.9);
  border-radius: 20px 20px 0 0;
  box-shadow: 0 18px 50px rgba(30, 60, 90, 0.1);
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.chat-container.is-osce-layout {
  width: min(1560px, calc(100% - 24px));
}

// 右侧聊天区：必须能收缩，否则长文本会把左侧面板挤出容器
.chat-main {
  position: relative;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// 数字人面板收起后，用窄条重新展开
.avatar-reopen {
  flex: none;
  width: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-right: 1px solid #e2eaf1;
  background: linear-gradient(180deg, #fbfdff 0%, #f2f7fb 100%);
  color: #6b8299;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;

  .arrow { font-size: 20px; line-height: 1; }
  .txt { font-size: 11px; writing-mode: vertical-rl; letter-spacing: 0.14em; }

  &:hover { background: #eef5fb; color: #2c7be5; }
}

.chat-header {
  padding: 18px 24px;
  border-bottom: 1px solid $border;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: $spacing;
}

.scene-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.scene-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 23px;
  background: linear-gradient(145deg, #1769c2, #2c8bde);
  box-shadow: 0 8px 18px rgba(44, 123, 229, 0.24);
}

.scene-copy {
  .eyebrow { color: #5f7890; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; }
  h1 { margin: 2px 0; font-size: 20px; color: #172b3a; }
  p { margin: 0; color: $text-secondary; font-size: 13px; }
}

.chat-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; margin-left: auto; }
.chat-actions > .el-button { margin-left: 0; border-radius: 11px; }
.chat-actions :deep(.toggle-item) { color: #7f93a3; margin-right: 2px; }
.chat-actions :deep(.toggle-item.is-active) { color: #2c7be5; font-weight: 700; }
.coach-button { gap: 6px; }

.stage-strip {
  padding: 11px 24px;
  background: #f3f8fc;
  border-bottom: 1px solid #dfeaf3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stage-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
  .stage-index { color: #39769e; font-size: 12px; font-weight: 700; }
  strong { color: #173f59; }
  .stage-progress { color: #617b8d; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
}

.stage-dots {
  display: flex;
  gap: 5px;
  span { width: 22px; height: 4px; border-radius: 99px; background: #d4e0e8; transition: background 0.25s; }
  span.active { background: #2d84b8; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px clamp(18px, 4vw, 64px);
  scroll-behavior: smooth;
}

.scene-brief {
  max-width: 760px;
  margin: 0 auto 28px;
  padding: 22px 24px;
  border: 1px solid #cce2e4;
  border-radius: 18px;
  background: linear-gradient(145deg, #f7ffff, #eff8f8);
  box-shadow: 0 10px 26px rgba(31, 91, 97, 0.08);
}

.brief-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  .agent-mark { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 11px; color: #0e7778; background: #dff3f1; font-size: 18px; }
  > div { flex: 1; }
  .brief-kicker { color: #4c7c7d; font-size: 11px; letter-spacing: 0.08em; }
  h2 { margin: 1px 0 0; color: #153f42; font-size: 18px; }
}

.brief-content { white-space: pre-line; margin: 18px 0; color: #294b4d; font-size: 15px; line-height: 1.8; }
.first-step { display: flex; align-items: center; gap: 10px; padding: 10px 13px; border-radius: 10px; background: white; color: #24494d; }
.first-step span { padding: 3px 7px; border-radius: 6px; color: white; background: #187c7c; font-size: 11px; font-weight: 700; }

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 14px;
  button { border: 1px solid #a8d2d0; background: white; color: #176a6d; border-radius: 99px; padding: 8px 12px; cursor: pointer; display: flex; align-items: center; gap: 5px; transition: all 0.2s; }
  button:hover:not(:disabled) { transform: translateY(-1px); border-color: #187c7c; box-shadow: 0 5px 14px rgba(24, 124, 124, 0.12); }
  button:disabled { opacity: 0.55; cursor: not-allowed; }
}
.scene-resources { margin-top: 13px; color: #527087; font-size: 12px; }
.scene-resources summary { cursor: pointer; font-weight: 700; }
.scene-resources a { display: inline-block; margin: 8px 12px 0 0; color: #176a9c; text-decoration: none; }
.scene-resources a:hover { text-decoration: underline; }

.message-attachments { width: min(420px, 100%); margin-top: 8px; display: grid; gap: 7px; }
.message-attachments a {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 9px;
  padding: 9px 11px;
  border: 1px solid #cfe2ef;
  border-radius: 11px;
  background: #f7fbff;
  color: #2a5875;
  text-decoration: none;
}
.message-attachments a:hover { border-color: #8fc0e0; background: #f0f8ff; }
.attachment-icon { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 9px; color: #fff; background: linear-gradient(145deg, #2c7be5, #37a4bf); }
.message-attachments a > span:nth-child(2) { min-width: 0; display: flex; flex-direction: column; }
.message-attachments strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
.message-attachments small { margin-top: 2px; color: #8297a6; font-size: 10px; }

.message-wrapper { display: flex; gap: 10px; margin-bottom: 22px; }
.message-wrapper.is-user { flex-direction: row-reverse; }
.message-avatar { flex: none; background: #2c7be5; color: white; }
.is-user .message-avatar { background: #dfe9f2; color: #38546b; }
.coach-avatar { background: #e8a33d; color: white; }
.message-content { max-width: min(620px, 76%); display: flex; flex-direction: column; align-items: flex-start; }
.is-user .message-content { align-items: flex-end; }
.is-coach .message-bubble { border-color: #f1d394; background: #fffaf0; color: #6b4a17; }
.is-coach.error .message-bubble { border-color: #f2b8ad; background: #fff4f2; color: #9e3927; }
.is-coach.success .message-bubble { border-color: #b9dfcc; background: #f0fbf5; color: #256544; }
.typing.coach-typing .dot { background: #e8a33d; }
.message-sender { margin: 0 4px 5px; color: #7890a3; font-size: 11px; }
.message-bubble { padding: 11px 15px; border-radius: 5px 16px 16px 16px; background: white; border: 1px solid #e1e8ef; color: $text-primary; line-height: 1.65; white-space: pre-line; box-shadow: 0 4px 12px rgba(45, 65, 80, 0.05); }
.is-user .message-bubble { border: none; border-radius: 16px 5px 16px 16px; background: #2c7be5; color: white; }
.message-time { margin-top: 4px; color: #97a7b4; font-size: 11px; }

.bubble-speak {
  margin-top: 5px;
  padding: 2px 9px;
  border: 1px solid #dbe5ee;
  border-radius: 99px;
  background: #fff;
  color: #71889b;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.18s;

  &:hover {
    color: #2c7be5;
    border-color: #9dc4ea;
    background: #f5faff;
  }
}

.typing { display: flex; gap: 5px; padding: 16px 18px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #2c7be5; animation: typing 1.4s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); opacity: 0.35; } 30% { transform: translateY(-5px); opacity: 1; } }

.coach-tip {
  position: absolute;
  right: 24px;
  bottom: 132px;
  width: min(360px, calc(100vw - 40px));
  border: 1px solid #f1d394;
  border-radius: 14px;
  padding: 12px;
  background: #fffaf0;
  color: #754b14;
  box-shadow: 0 14px 34px rgba(70, 53, 23, 0.16);
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  z-index: 20;
  text-align: left;
}
.coach-tip.success { border-color: #b9dfcc; background: #f0fbf5; color: #256544; }
.coach-tip.error { border-color: #f2b8ad; background: #fff4f2; color: #9e3927; }
.coach-tip-copy { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.coach-tip-copy strong { font-size: 12px; }
.coach-tip-copy span { font-size: 13px; line-height: 1.45; }
.coach-pop-enter-active, .coach-pop-leave-active { transition: all 0.25s ease; }
.coach-pop-enter-from, .coach-pop-leave-to { opacity: 0; transform: translateY(8px); }

.chat-input { padding: 12px 20px 18px; border-top: 1px solid $border; background: rgba(255, 255, 255, 0.97); }
.input-help { display: flex; justify-content: space-between; margin-bottom: 7px; color: #8293a1; font-size: 11px; }
.input-toggles { display: flex; align-items: center; gap: 14px; min-width: 0; }
.toggle-item { display: inline-flex; align-items: center; gap: 5px; cursor: pointer; color: #8293a1; }
.toggle-item.is-active { color: #b07615; font-weight: 700; }
.input-row { display: flex; gap: 10px; align-items: flex-end; }
.input-row .el-input { flex: 1; }
.input-row .el-button { height: 42px; padding-inline: 20px; }

.drawer-intro { display: flex; gap: 12px; margin-bottom: 20px; padding: 14px; border-radius: 12px; color: #506779; background: #f4f7f9; line-height: 1.6; }
.drawer-intro .el-icon { flex: none; margin-top: 3px; color: #2c7be5; }
.drawer-intro p { margin: 0; }
.mobile-session-controls { display: none; }
.record-workspace {
  flex: 0 0 390px;
  min-width: 0;
  padding: 18px;
  border-left: 1px solid #dfe8f0;
  background: linear-gradient(180deg, #fbfdff 0%, #f4f8fb 100%);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.record-workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.record-title { display: flex; align-items: center; gap: 10px; color: #23465e; font-weight: 800; }
.record-title > div { display: flex; flex-direction: column; gap: 2px; }
.record-title small { color: #7f94a5; font-size: 11px; font-weight: 500; }
.record-title-icon {
  width: 36px;
  height: 36px;
  flex: none;
  display: grid;
  place-items: center;
  border-radius: 11px;
  color: #fff;
  background: linear-gradient(145deg, #2278cc, #34a0c7);
  box-shadow: 0 7px 16px rgba(44, 123, 229, 0.2);
}
.record-status { padding: 4px 8px; border-radius: 999px; font-size: 11px; white-space: nowrap; }
.record-status.saved { color: #247954; background: #e8f7ef; }
.record-status.unsaved { color: #9b6818; background: #fff3db; }
.record-intro { display: flex; gap: 12px; margin-bottom: 14px; padding: 14px; border-radius: 12px; background: #eef7ff; color: #456276; }
.record-intro > .el-icon { flex: none; margin-top: 3px; color: #2c7be5; font-size: 20px; }
.record-intro strong { color: #244a64; }
.record-intro p { margin: 4px 0 0; font-size: 13px; line-height: 1.65; }
.record-framework { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 12px; }
.record-framework span { padding: 4px 9px; border: 1px solid #d6e5ef; border-radius: 999px; color: #527087; background: #fff; font-size: 12px; }
.record-editor { flex: 0 0 auto; min-height: 0; overflow: visible; }
.record-editor :deep(.el-textarea) { height: 100%; display: flex; flex-direction: column; }
.record-editor :deep(.el-textarea__inner) {
  flex: 1;
  height: clamp(180px, 36dvh, 420px);
  min-height: 140px;
  max-height: 65dvh;
  padding: 14px;
  border-color: #cfdde8;
  color: #2f4658;
  line-height: 1.7;
  resize: vertical;
}
.record-actions { flex: 0 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 12px; padding-bottom: 2px; }
.record-actions span { font-size: 12px; }
.record-actions .saved { color: #269368; }
.record-actions .unsaved { color: #c07813; }
.coach-history { list-style: none; margin: 0; padding: 0 0 24px; }
.coach-history li { position: relative; margin: 0 0 12px; padding: 14px; border: 1px solid #e2e8ee; border-left: 3px solid #8ca3b5; border-radius: 10px; background: white; }
.coach-history li.success { border-left-color: #36b37e; }
.coach-history li.warning { border-left-color: #e79a19; }
.coach-history li.error { border-left-color: #e55b48; }
.history-meta { display: flex; justify-content: space-between; align-items: center; }
.history-meta time { color: #91a0ab; font-size: 11px; }
.coach-history p { margin: 10px 0 0; color: #354b5c; line-height: 1.65; }
.coach-history .el-button { margin-top: 10px; }

.setup-copy { display: flex; gap: 14px; margin-bottom: 16px; }
.setup-icon { width: 42px; height: 42px; flex: none; display: grid; place-items: center; border-radius: 13px; color: #2c7be5; background: #eaf3ff; font-size: 20px; }
.setup-copy h3 { margin: 0 0 5px; color: #243a4b; }
.setup-copy p, .action-description { margin: 0; color: #677d8d; line-height: 1.65; }
.gender-options { width: 100%; display: grid; grid-template-columns: 1fr 1fr; }
.gender-options :deep(.el-radio-button__inner) { width: 100%; }
.action-description { margin-bottom: 16px; }

@media (max-width: 1200px) and (min-width: 721px) {
  .chat-container.is-osce-layout :deep(.avatar-stage) { width: 240px; }
  .record-workspace { flex-basis: 330px; padding: 14px; }
  .record-intro { padding: 11px; }
  .record-intro p { font-size: 12px; }
}

@media (max-width: 980px) {
  .chat-container {
    width: 100%;
    height: calc(100dvh - 58px);
    min-height: 0;
    margin-top: 0;
    border: 0;
    border-radius: 0;
    flex-direction: column;
  }
  // 手机端始终展示紧凑数字人舞台，避免收起后没有恢复入口。
  .avatar-reopen { display: none; }
  .chat-main { min-height: 0; }
  .chat-container.is-osce-layout {
    height: auto;
    min-height: calc(100dvh - 58px);
    overflow: visible;
  }
  .chat-container.is-osce-layout .chat-main {
    width: 100%;
    height: clamp(430px, 72dvh, 720px);
    min-height: 0;
    flex: none;
  }
  .record-workspace {
    width: 100%;
    min-height: 0;
    flex: none;
    padding: 18px 12px 30px;
    border-top: 1px solid #dfe8f0;
    border-left: 0;
    overflow: visible;
    scroll-margin-top: 58px;
  }
  .record-editor { overflow: visible; }
  .record-editor :deep(.el-textarea__inner) { height: clamp(180px, 35dvh, 360px); min-height: 140px; resize: vertical; }
  .record-actions { flex-wrap: wrap; }
  .record-actions .el-button { margin-left: auto; }
  .chat-header { padding: 13px 14px; }
  .scene-icon { display: none; }
  .scene-copy .eyebrow, .scene-copy p { display: none; }
  .scene-copy h1 { font-size: 17px; }
  .coach-button span { display: none; }
  .chat-actions > .toggle-item { font-size: 11px; gap: 4px; margin: 0; white-space: nowrap; }
  .chat-actions > .el-button { padding-inline: 9px; }
  .chat-actions { gap: 6px; }
  .stage-strip { padding: 9px 14px; }
  .stage-main .stage-progress { display: none; }
  .stage-dots span { width: 13px; }
  .chat-messages { padding: 16px 12px; }
  .chat-container.is-osce-layout .chat-messages { padding-top: 12px; padding-bottom: 10px; }
  .chat-container.is-osce-layout .scene-brief { margin-bottom: 14px; }
  .scene-brief { padding: 17px; }
  .brief-heading > .el-tag { display: none; }
  .message-content { max-width: 82%; }
  .coach-tip { position: fixed; left: 12px; right: 12px; bottom: 116px; width: auto; }
  .chat-input { padding: 10px 12px 12px; }
  .input-help span:last-child { display: none; }
  .input-row .el-button { padding-inline: 14px; }

  .mobile-session-controls { display: block; width: 100%; min-width: 0; }
  .mobile-session-controls .chat-header {
    display: flex; flex-direction: column; align-items: stretch;
    gap: 8px; padding: 0; border: 0; background: transparent;
  }
  .mobile-session-controls .scene-info { min-width: 0; gap: 0; }
  .mobile-session-controls .scene-copy h1 { font-size: 15px; line-height: 1.4; letter-spacing: .01em; margin: 0; overflow-wrap: anywhere; }
  .mobile-session-controls .chat-actions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-start; width: 100%; margin-left: 0; }
  .mobile-session-controls .chat-actions .el-button { height: 36px; min-width: 36px; margin: 0; padding: 0 9px; font-size: 12px; border-radius: 9px; }
  .mobile-session-controls .chat-actions .toggle-item { color: #56798c; font-size: 11px; gap: 3px; min-height: 36px; }
  .mobile-session-controls .stage-strip { padding: 7px 0 0; margin-top: 6px; border: 0; border-top: 1px solid #dfebef; background: transparent; flex-wrap: wrap; gap: 5px; }
  .mobile-session-controls .stage-main { gap: 6px; font-size: 11px; flex-wrap: wrap; }
  .mobile-session-controls .stage-main strong { font-size: 12px; }
  .mobile-session-controls .stage-dots { gap: 3px; }
  .mobile-session-controls .stage-dots span { width: 9px; height: 3px; }
  .mobile-session-controls .coach-button span { display: inline; }
  .mobile-session-controls .stage-strip { color: #668693; }
  .mobile-session-controls .stage-main strong { color: #315d70; }
  .chat-messages { overscroll-behavior-y: contain; }
  .message-content { min-width: 0; max-width: calc(100% - 42px); }
  .message-bubble { overflow-wrap: anywhere; font-size: 14px; }
  .chat-input { flex-shrink: 0; padding-bottom: max(10px, env(safe-area-inset-bottom)); }
  .chat-input :deep(.el-textarea__inner), .record-editor :deep(.el-textarea__inner) { font-size: 16px; }
  .record-workspace { border-radius: 18px 18px 0 0; padding-top: 14px; }
  .record-intro { padding: 10px; margin-bottom: 10px; font-size: 12px; }
  .record-intro p { font-size: 12px; }
  .record-framework { gap: 5px; margin-bottom: 10px; }
  .record-framework span { font-size: 11px; padding: 4px 7px; }
  .record-actions { padding: 10px 0 max(4px, env(safe-area-inset-bottom)); margin-top: 0; }
  .chat-container.is-osce-layout { width: 100%; }
}
</style>
