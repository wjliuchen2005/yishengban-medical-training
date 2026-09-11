<template>
  <div class="psych-view">
    <AppHeader />

    <section v-if="!privacyAccepted" class="privacy-gate" role="dialog" aria-labelledby="privacy-title" aria-modal="true">
      <div class="privacy-gate-card">
        <div class="privacy-symbol">🔐</div>
        <p class="privacy-eyebrow">进入易心前，请先确认</p>
        <h1 id="privacy-title">你的文字会如何被处理</h1>
        <div class="privacy-details">
          <p><strong>大模型对话</strong><span>你发送的文字会上传给大模型，用于生成易心的回复。</span></p>
          <p><strong>MiMo 语音</strong><span>开启语音时，易心待朗读的回复会上传给小米 MiMo 生成语音；关闭语音则不会上传朗读文本。</span></p>
          <p><strong>语音输入（可选）</strong><span>另行同意并使用麦克风后，录音与对话语境会上传给小米 MiMo，用于转写和辅助理解声音表达。原始录音不在本系统保存；关闭朗读不等于开启或关闭麦克风。</span></p>
          <p><strong>历史记录</strong><span>只有你主动选择保存时，本次对话才会加密保存到易心历史。</span></p>
        </div>
        <div class="privacy-buttons">
          <el-button size="large" @click="leaveBeforeConsent">退出</el-button>
          <el-button size="large" plain type="warning" @click="enterWithoutVoice">继续但关闭语音</el-button>
          <el-button size="large" type="warning" @click="enterWithVoice">同意并开启语音</el-button>
        </div>
      </div>
    </section>

    <main v-else class="psych-container">
      <!-- 数字人舞台 -->
      <AvatarStage
        v-if="isMobile || !avatarCollapsed"
        class="avatar-side"
        :role="'psych'"
        :speaking="stageSpeaking"
        :expression="currentExpression"
        :action="currentAction"
        :pressure="0"
        :scene="'psych'"
        :persona="psychPersona"
        :tts-available="ttsAvailable"
        @collapse="avatarCollapsed = true"
      >
        <template #controls><div ref="mobileHeaderTarget" class="mobile-session-controls" /></template>
      </AvatarStage>
      <button v-else type="button" class="avatar-reopen" title="展开数字人" @click="avatarCollapsed = false">
        <span class="arrow">›</span>
        <span class="txt">数字人</span>
      </button>

      <!-- 聊天区 -->
      <div class="psych-main" :class="{ 'has-quick': showQuick }">
        <Teleport :to="mobileHeaderTarget || 'body'" :disabled="!isMobile || !mobileHeaderTarget">
        <header class="psych-header">
          <div class="scene-icon" aria-hidden="true"><el-icon><ChatLineRound /></el-icon></div>
          <div class="scene-copy">
            <div class="eyebrow">心理陪伴 · 情绪疏导</div>
            <h1>和「易心」聊一聊</h1>
            <p>这里没有评判，你可以放心说任何心里话</p>
          </div>
          <div class="chat-actions">
            <VoiceButton v-if="ttsAvailable" :enabled="voiceEnabled" @toggle="value => { voiceEnabled = value; onVoiceToggle(value) }" />
            <el-button plain @click="openPsychHistory">🔒 易心历史</el-button>
            <el-button type="warning" plain @click="resetChat">换个话题</el-button>
            <el-button type="danger" plain @click="goHome">退出陪伴</el-button>
          </div>
        </header>
        </Teleport>

        <!-- 危机提醒条 -->
        <transition name="crisis-pop">
          <div v-if="crisisShown" class="crisis-banner" role="alert">
            <div class="crisis-icon">💛</div>
            <div class="crisis-copy">
              <strong>如果你现在很不好受，请一定不要一个人扛</strong>
              <p>请立即拨打 <b>12356</b>（全国 24 小时心理援助热线，免费保密），或联系身边信任的人、学校心理中心；有紧急危险请直接拨打 120/110。易心会一直陪着你。</p>
            </div>
            <el-button size="small" @click="crisisShown = false">知道了</el-button>
          </div>
        </transition>

        <!-- 开场情绪引导：选一张卡片即可开聊 -->
        <section v-if="showQuick" class="quick-starter" aria-label="快捷话题">
          <p class="quick-title">今天想聊聊什么？选一个开始 👇</p>
          <div class="quick-chips">
            <button
              v-for="q in QUICK_TOPICS"
              :key="q.text"
              type="button"
              class="quick-chip"
              :disabled="loading"
              @click="quickAsk(q.text)"
            >
              <span class="chip-emoji">{{ q.emoji }}</span>
              <span class="chip-text">{{ q.text }}</span>
            </button>
          </div>
        </section>

        <section ref="messageListRef" class="psych-messages" aria-live="polite">
          <article v-for="msg in messages" :key="msg.id" class="message-wrapper" :class="{ 'is-user': msg.role === 'user' }">
            <el-avatar :size="40" :class="['message-avatar', msg.role === 'user' ? 'user-avatar' : 'ai-avatar']">
              {{ msg.role === 'user' ? '我' : '心' }}
            </el-avatar>
            <div class="message-content">
              <div class="message-sender">{{ msg.role === 'user' ? '我' : '易心' }}</div>
              <div class="message-bubble">{{ displayContent(msg) }}</div>
              <VoiceFeedback v-if="msg.role === 'user'" :items="msg.voice_assessments || []" psych />
              <div v-if="msg.role === 'assistant'" class="message-actions">
                <button v-if="ttsAvailable" type="button" class="replay-btn" @click="replayMessage(msg)">🔊 重播</button>
                <time class="message-time">{{ formatTime(msg.ts) }}</time>
              </div>
            </div>
          </article>

          <article v-if="loading" class="message-wrapper">
            <el-avatar :size="40" class="message-avatar ai-avatar">心</el-avatar>
            <div class="message-content">
              <div class="message-sender">易心</div>
              <div class="message-bubble typing" aria-label="易心正在输入">
                <span class="dot" /><span class="dot" /><span class="dot" />
              </div>
            </div>
          </article>
        </section>

        <footer class="psych-input">
          <div class="input-hint">
            <span>聊聊今天的心情、最近的压力，或者任何想说的话</span>
            <span>Ctrl + Enter 发送</span>
          </div>
          <VoiceComposer ref="voiceInputRef" v-model="inputText" target="psych" :context="messages"
            :maxlength="1000" placeholder="说说你的心事吧…" :disabled="loading" :sending="loading"
            @send="onSend" @recording="active => { inputRecording = active; if (active) stopVoice() }" />
        </footer>
      </div>
    </main>

    <el-drawer v-model="historyVisible" title="易心历史" size="min(440px, 94vw)" class="psych-history-drawer">
      <div class="privacy-note">🔒 对话正文与摘要均加密保存；只有当前账号可以查看。</div>
      <el-empty v-if="!historyLoading && !psychHistory.length" description="还没有保存过易心对话" />
      <div v-loading="historyLoading" class="psych-history-list">
        <article v-for="item in psychHistory" :key="item.id" class="psych-history-item" :class="{ pinned: item.is_pinned }">
          <button class="history-open" type="button" @click="loadHistory(item)">
            <strong>{{ item.is_pinned ? '📌 ' : '' }}{{ item.summary }}</strong>
            <small>{{ formatHistoryTime(item.updated_at) }} · 已加密</small>
          </button>
          <div class="history-actions">
            <button type="button" @click="toggleHistoryFlag(item, 'is_favorite')">{{ item.is_favorite ? '★ 已收藏' : '☆ 收藏' }}</button>
            <button type="button" @click="toggleHistoryFlag(item, 'is_pinned')">{{ item.is_pinned ? '取消置顶' : '置顶' }}</button>
            <button type="button" class="danger" @click="removeHistory(item)">删除</button>
          </div>
        </article>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import AvatarStage from '@/components/AvatarStage.vue'
import VoiceButton from '@/components/VoiceButton.vue'
import VoiceComposer from '@/components/VoiceComposer.vue'
import VoiceFeedback from '@/components/VoiceFeedback.vue'
import { useMobileViewport } from '@/utils/useMobileViewport'
import { registerPsychExitGuard } from '@/utils/psychExitGuard'

const isMobile = useMobileViewport()
const mobileHeaderTarget = ref(null)
import {
  deletePsychSession,
  getPsychSession,
  getPsychSessions,
  savePsychSession,
  sendPsychMessage,
  updatePsychSession
} from '@/api/psych'
import { stripForSpeech, extractPerformanceCue } from '@/utils/live2dMap'
import { isMiMoTTSSupported, stopUnifiedSpeaking, unifiedSpeak } from '@/utils/ttsService'

const router = useRouter()
const privacyAccepted = ref(false)

// 「易心」：心理陪伴数字人设定（柔和女声）
const psychPersona = {
  label: '易心',
  gender: 'female',
  voiceHint: '女|晓',
  pitch: 1.1,
  rate: 0.95
}

const ttsAvailable = isMiMoTTSSupported()
const voiceEnabled = ref(ttsAvailable && localStorage.getItem('yishengban_psych_voice') !== 'off')
const avatarCollapsed = ref(false)

const messages = ref([])
const inputText = ref('')
const voiceInputRef = ref(null)
const inputRecording = ref(false)
const loading = ref(false)
const messageListRef = ref(null)
let messageSeq = 0
let quotaWarningShown = false
const activeHistoryId = ref(null)

const stageSpeaking = ref(false)
const currentExpression = ref('calm')
const currentAction = ref('idle')

const crisisShown = ref(false)
const historyVisible = ref(false)
const historyLoading = ref(false)
const psychHistory = ref([])
let unregisterExitGuard = null

// 开场白
const OPENING_TEXT =
  '嗨，我是易心。今天感觉怎么样？不管是开心的、烦心的还是心里堵着说不出口的，都可以慢慢告诉我，我会认真听。'

// 开场情绪引导卡片（点选即发送）
const QUICK_TOPICS = [
  { emoji: '📚', text: '最近压力好大，快撑不住了' },
  { emoji: '🌙', text: '晚上总睡不着，脑子里乱糟糟的' },
  { emoji: '😔', text: '心情很低落，做什么都提不起劲' },
  { emoji: '👥', text: '和同学/朋友相处让我很烦' },
  { emoji: '🧭', text: '对未来很迷茫，不知道该怎么办' },
  { emoji: '💬', text: '没什么大事，就是想找人说说话' }
]

const showQuick = computed(() => !messages.value.some((m) => m.role === 'user'))

function quickAsk(text) {
  inputText.value = text
  onSend()
}

function initializePsych() {
  if (messages.value.length) return
  applyCue(OPENING_TEXT)
  const displayOpening = () => {
    if (!messages.value.some((m) => m.role === 'assistant')) addMessage('assistant', OPENING_TEXT)
  }
  if (!privacyAccepted.value || !voiceEnabled.value) {
    displayOpening()
    return
  }
  window.setTimeout(() => {
    if (!messages.value.some((m) => m.role === 'user')) {
      speak(OPENING_TEXT, { onReady: displayOpening }).finally(displayOpening)
    }
  }, 220)
}

function leaveBeforeConsent() {
  stopVoice()
  router.push('/')
}

function enterWithoutVoice() {
  voiceEnabled.value = false
  localStorage.setItem('yishengban_psych_voice', 'off')
  privacyAccepted.value = true
  initializePsych()
}

function enterWithVoice() {
  voiceEnabled.value = true
  localStorage.setItem('yishengban_psych_voice', 'on')
  privacyAccepted.value = true
  initializePsych()
}

const historyForApi = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({ role: m.role, content: m.content, voice_receipts: m.voice_receipts || [] }))
    .slice(-30)
)

// 展示文本：把 AI 回复开头的（神态）标注行去掉，只留正文
function displayContent(msg) {
  if (msg.role !== 'assistant') return msg.content
  return msg.content.replace(/^[（(](?:smile|worry|sad|calm|relieved|crying|anxious|angry|tired|confused)[）)]\s*\n?/i, '')
}

function addMessage(role, content, extra = {}) {
  messageSeq += 1
  messages.value.push({ id: messageSeq, role, content, ts: Date.now(), ...extra })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    const el = messageListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function formatTime(ts) {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 语音代际：打断旧朗读后，旧 speak() 迟到的 finally 不能误清新一轮的 speaking 状态
let speakGen = 0

async function speak(text, { onReady } = {}) {
  if (inputRecording.value) { onReady?.(); return }
  if (!text) return
  const gen = ++speakGen
  // 语音关闭 / 不可用时同样把身体动作复位，让易心回到待机陪伴姿态
  if (!voiceEnabled.value || !ttsAvailable) {
    stageSpeaking.value = false
    currentAction.value = 'idle'
    onReady?.()
    return
  }
  try {
    await unifiedSpeak(stripForSpeech(text), {
      role: 'psych',
      emotion: currentExpression.value,
      gender: 'female',
      pitch: psychPersona.pitch,
      rate: psychPersona.rate,
      onReady: () => {
        if (gen !== speakGen) return
        stageSpeaking.value = true
        onReady?.()
      }
    })
  } catch (error) {
    if (error?.name !== 'AbortError') console.warn('[TTS] MiMo 语音不可用:', error?.message || error)
    onReady?.()
  } finally {
    if (gen === speakGen) {
      stageSpeaking.value = false
      // 话说完了，把身体动作交还给「待机轮换」，避免某条神态码的点头/伸手一直循环
      currentAction.value = 'idle'
    }
  }
}

// 打断正在播放的语音（使用者在易心说话时发言）并复位说话状态
function stopVoice() {
  speakGen += 1
  stopUnifiedSpeaking()
  stageSpeaking.value = false
}

// 关掉语音开关：立即停下正在说的话，避免“关了还继续念”
function onVoiceToggle(value) {
  localStorage.setItem('yishengban_psych_voice', value ? 'on' : 'off')
  if (!value) stopVoice()
}

function applyCue(text) {
  const cue = extractPerformanceCue(text, 'psych', 'calm')
  currentExpression.value = cue.expression
  currentAction.value = cue.action
}

async function onSend() {
  if (voiceInputRef.value?.busy) return
  const text = (inputText.value || '').trim()
  if (!text || loading.value) return
  // 用户发言时立即打断易心正在说的话，避免新旧声音叠在一起
  stopVoice()
  inputText.value = ''
  const voiceClips = voiceInputRef.value?.takeClips() || []
  addMessage('user', text, { voice_receipts: voiceClips.map(c => c.receipt), voice_assessments: voiceClips.map(c => c.assessment) })
  applyCue(text)
  loading.value = true

  try {
    const res = await sendPsychMessage(historyForApi.value)
    if (res?.quota?.exhausted && !quotaWarningShown) {
      quotaWarningShown = true
      ElMessageBox.alert(res.quota.message, '今日练习额度', { confirmButtonText: '知道了', type: 'warning' })
    }
    const reply = (res && res.reply) || '嗯，我在听。你愿意再说说吗？'
    applyCue(reply)
    if (res && res.crisis) crisisShown.value = true
    let displayed = false
    const display = () => {
      if (displayed) return
      displayed = true
      addMessage('assistant', reply)
    }
    let markReady
    const ready = new Promise((resolve) => { markReady = resolve })
    const reveal = () => { display(); markReady() }
    speak(reply, { onReady: reveal }).finally(reveal)
    await ready
  } catch (err) {
    console.error('心理陪伴请求失败', err)
    addMessage('assistant', '（网络有点不稳定，我这边没听清。你可以再说一遍吗？）')
  } finally {
    loading.value = false
  }
}

function replayMessage(msg) {
  if (msg.role !== 'assistant') return
  speak(msg.content)
}

async function resetChat() {
  if (!(await confirmSaveCurrentConversation())) return
  voiceInputRef.value?.clear()
  inputText.value = ''
  stopVoice()
  messages.value = []
  crisisShown.value = false
  currentExpression.value = 'calm'
  currentAction.value = 'idle'
  activeHistoryId.value = null
  addMessage('assistant', OPENING_TEXT)
  speak(OPENING_TEXT)
}

async function goHome() {
  router.push('/')
}

// 所有离开易心的动作共用这一确认：顶部导航、退出登录、退出陪伴、刷新路由等
// 都会先经过路由守卫；不保存只放行离开，关闭弹窗则停留在当前对话。
async function confirmSaveCurrentConversation() {
  if (voiceInputRef.value?.busy) { ElMessage.info('请先停止录音并等待识别完成，再切换会话'); return false }
  const history = historyForApi.value
  if (!history.some((m) => m.role === 'user')) return true
  try {
    await ElMessageBox.confirm('是否将本次谈话加密保存到“易心历史”？', '离开易心前确认', {
      confirmButtonText: '加密保存并离开',
      cancelButtonText: '不保存，直接离开',
      distinguishCancelAndClose: true,
      type: 'info'
    })
  } catch (action) {
    // Element Plus 的 cancel 是明确选择“不保存”；关闭/ESC 则视为不离开。
    return action === 'cancel'
  }
  try {
    const saved = await savePsychSession(history, activeHistoryId.value)
    activeHistoryId.value = saved.id
    ElMessage.success(saved.updated ? '易心历史已更新' : '本次谈话已加密保存')
    return true
  } catch (error) {
    console.error('保存易心历史失败', error)
    ElMessage.error('保存失败，暂不离开；请重试或选择不保存离开')
    return false
  }
}

async function openPsychHistory() {
  // Merely opening the archive does not leave the current conversation.
  // Confirmation is deferred until the user actually switches to a record.
  historyVisible.value = true
  historyLoading.value = true
  try {
    psychHistory.value = (await getPsychSessions()) || []
  } finally {
    historyLoading.value = false
  }
}

async function toggleHistoryFlag(item, key) {
  const value = !item[key]
  await updatePsychSession(item.id, { [key]: value })
  item[key] = value
  psychHistory.value.sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned) || b.updated_at - a.updated_at)
}

async function loadHistory(item) {
  if (!(await confirmSaveCurrentConversation())) return
  const detail = await getPsychSession(item.id)
  voiceInputRef.value?.clear()
  messages.value = (detail.messages || []).map((msg) => ({ ...msg, id: ++messageSeq, ts: Date.now() }))
  activeHistoryId.value = detail.id
  historyVisible.value = false
  stopVoice()
  ElMessage.success('已载入历史记录，后续保存会更新此记录')
  scrollToBottom()
}

async function removeHistory(item) {
  try {
    await ElMessageBox.confirm('确定永久删除这条加密记录吗？删除后无法恢复。', '删除易心历史', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
  } catch { return }
  await deletePsychSession(item.id)
  psychHistory.value = psychHistory.value.filter((row) => row.id !== item.id)
  ElMessage.success('易心历史已删除')
}

function formatHistoryTime(value) {
  if (!value) return '--'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  stopUnifiedSpeaking()
  unregisterExitGuard = registerPsychExitGuard(confirmSaveCurrentConversation)
})

onBeforeUnmount(() => {
  unregisterExitGuard?.()
  stopVoice()
})
</script>

<style scoped lang="scss">
.psych-view {
  min-height: 100vh;
  background: linear-gradient(180deg, #fffbf6 0%, #fbf0e2 40%, #f8ead9 100%);
}

.privacy-gate {
  min-height: calc(100vh - 64px);
  display: grid;
  place-items: center;
  padding: 28px 18px;
}

.privacy-gate-card {
  width: min(680px, 100%);
  padding: 34px;
  border: 1px solid #f0d4ad;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 24px 64px rgba(133, 79, 30, 0.14);
  text-align: center;
}

.privacy-symbol { font-size: 38px; }
.privacy-eyebrow { margin: 10px 0 4px; color: #d77b2d; font-size: 13px; letter-spacing: 0.12em; }
.privacy-gate-card h1 { margin: 0 0 22px; color: #603716; font-size: 27px; }
.privacy-details { display: grid; gap: 10px; text-align: left; }
.privacy-details p { margin: 0; padding: 14px 16px; border-radius: 14px; background: #fff8ee; color: #79552f; line-height: 1.65; }
.privacy-details strong, .privacy-details span { display: block; }
.privacy-details strong { color: #9a541d; }
.privacy-buttons { display: flex; justify-content: center; gap: 10px; margin-top: 24px; }

.psych-container {
  display: flex;
  max-width: 1280px;
  height: calc(100vh - 64px);
  margin: 0 auto;
  gap: 0;
  padding: 0 12px 12px;
}

.avatar-side {
  flex: none;
}

.avatar-reopen {
  flex: none;
  width: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin: 8px 0;
  border: 1px solid #f2d7b5;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  align-self: flex-start;

  .arrow { font-size: 18px; line-height: 1; color: #ea8a3c; }
  .txt { font-size: 12px; color: #b06a2c; }
}

.mobile-session-controls { display: none; }
.psych-main {
  position: relative;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #f4e2c8;
  border-radius: 18px;
  margin: 8px 0;
  overflow: hidden;
}

.psych-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid #f6ead6;

  .scene-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 20px;
    color: #fff;
    background: linear-gradient(135deg, #eda66a, #dc8253);
    box-shadow: 0 4px 12px rgba(183, 104, 57, 0.24);
  }

  .scene-copy {
    flex: 1 1 320px;
    min-width: 0;

    .eyebrow {
      font-size: 11px;
      letter-spacing: 2px;
      color: #ea8a3c;
    }
    h1 { margin: 2px 0; font-size: 20px; color: #6b3a12; }
    p { margin: 0; font-size: 13px; color: #9a7a55; }
  }

  .chat-actions {
    flex: 1 0 100%;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 10px;

    .voice-toggle {
      font-size: 13px;
      color: #b06a2c;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-right: 4px;
    }
  }
}

.crisis-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 12px 16px 0;
  padding: 12px 16px;
  border: 1px solid #ffd0a8;
  border-radius: 12px;
  background: #fff4e6;

  .crisis-icon { font-size: 24px; line-height: 1.4; }
  .crisis-copy {
    flex: 1;
    strong { display: block; color: #9a3412; margin-bottom: 4px; }
    p { margin: 0; font-size: 13px; color: #b45309; line-height: 1.6; }
  }
}

.quick-starter {
  margin: 10px 16px 0;
  padding: 12px 16px;
  background: #fff8ee;
  border: 1px dashed #f2c894;
  border-radius: 12px;

  .quick-title {
    margin: 0 0 10px;
    font-size: 13px;
    color: #a06a2f;
    font-weight: 600;
  }

  .quick-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .quick-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid #f5d6ae;
    border-radius: 999px;
    background: #fff;
    padding: 6px 12px;
    font-size: 13px;
    color: #8a5a22;
    cursor: pointer;
    transition: all 0.18s;

    &:hover {
      border-color: #f97316;
      color: #f97316;
      transform: translateY(-1px);
      box-shadow: 0 3px 8px rgba(249, 115, 22, 0.18);
    }

    &:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .chip-emoji { font-size: 15px; line-height: 1; }
  }
}

.psych-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-start;

  &.is-user {
    flex-direction: row-reverse;

    .message-content { align-items: flex-end; }
    .message-bubble {
      background: linear-gradient(135deg, #ffe0bd, #ffc98f);
      color: #5c2a05;
      border-radius: 16px 16px 4px 16px;
    }
  }

  .user-avatar { background: #f39c4a; color: #fff; font-weight: 600; }
  .ai-avatar { background: linear-gradient(135deg, #f97316, #fbb34c); color: #fff; font-weight: 600; }

  .message-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-width: 72%;
  }

  .message-sender {
    font-size: 12px;
    color: #b09070;
  }

  .message-bubble {
    background: #fff;
    border: 1px solid #f3e2cb;
    color: #6b4a2a;
    padding: 10px 14px;
    border-radius: 4px 16px 16px 16px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .replay-btn {
    border: none;
    background: none;
    color: #d98324;
    font-size: 12px;
    cursor: pointer;
    padding: 0;
  }

  .message-time {
    font-size: 11px;
    color: #cbb391;
  }
}

.typing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #eab878;
    animation: blink 1.2s infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}

.psych-input {
  border-top: 1px solid #f6ead6;
  padding: 12px 20px 16px;

  .input-hint {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #b7a089;
    margin-bottom: 8px;
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }
}

.privacy-note { margin-bottom: 14px; padding: 12px 14px; border-radius: 12px; background: #fff7e9; color: #79552f; font-size: 13px; line-height: 1.6; }
.psych-history-list { display: grid; gap: 12px; min-height: 100px; }
.psych-history-item { padding: 13px; border: 1px solid #eedfc9; border-radius: 14px; background: #fff; }
.psych-history-item.pinned { border-color: #e7b96f; background: #fffaf1; }
.history-open { width: 100%; padding: 0; border: 0; background: transparent; color: #633f1d; text-align: left; cursor: pointer; }
.history-open strong, .history-open small { display: block; }
.history-open strong { line-height: 1.55; }
.history-open small { margin-top: 5px; color: #a08568; }
.history-actions { display: flex; gap: 8px; margin-top: 11px; padding-top: 10px; border-top: 1px solid #f3e9dc; }
.history-actions button { padding: 5px 9px; border: 1px solid #ead8bf; border-radius: 8px; background: #fff; color: #87603a; cursor: pointer; }
.history-actions button.danger { margin-left: auto; color: #b34f42; border-color: #f0c6bf; }

.crisis-pop-enter-active, .crisis-pop-leave-active { transition: all 0.3s; }
.crisis-pop-enter-from, .crisis-pop-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 980px) {
  .privacy-gate { min-height: calc(100dvh - 58px); padding: 16px 12px; }
  .privacy-gate-card { padding: 24px 16px; border-radius: 20px; }
  .privacy-gate-card h1 { font-size: 23px; }
  .privacy-buttons { display: grid; grid-template-columns: 1fr; }
  .privacy-buttons :deep(.el-button) { width: 100%; margin-left: 0; }

  .psych-container {
    width: 100%;
    height: calc(100dvh - 58px);
    min-height: 0;
    padding: 0;
    flex-direction: column;
  }

  .avatar-side { width: 100%; }
  .avatar-reopen { display: none; }

  .psych-main {
    min-height: 0;
    width: 100%;
    margin: 0;
    border-right: 0;
    border-left: 0;
    border-radius: 0;
  }

  .psych-header {
    display: grid;
    grid-template-columns: 40px minmax(0, 1fr);
    gap: 9px 10px;
    padding: 11px 12px 10px;

    .scene-icon {
      width: 40px;
      height: 40px;
      font-size: 18px;
    }

    .scene-copy {
      .eyebrow { letter-spacing: 0.08em; }
      h1 { margin-top: 1px; font-size: 18px; line-height: 1.25; }
      p { overflow: hidden; font-size: 12px; line-height: 1.45; text-overflow: ellipsis; white-space: nowrap; }
    }

    .chat-actions {
      flex: initial;
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;

      .voice-toggle {
        min-height: 36px;
        margin: 0;
        padding: 0 4px;
        justify-content: center;
        white-space: nowrap;
      }

      :deep(.el-button) {
        min-width: 0;
        min-height: 36px;
        margin-left: 0;
        padding: 7px 9px;
      }
    }
  }

  .crisis-banner {
    flex-wrap: wrap;
    margin: 8px 10px 0;
    padding: 11px 12px;

    .crisis-copy { min-width: 0; }
    > .el-button { margin-left: 36px; }
  }

  .quick-starter {
    flex-shrink: 0;
    margin: 8px 10px 0;
    padding: 11px 12px;

    .quick-chips {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 7px;
    }

    .quick-chip {
      width: 100%;
      min-height: 38px;
      border-radius: 11px;
      justify-content: flex-start;
      text-align: left;
      line-height: 1.4;
    }
  }

  .psych-messages {
    gap: 12px;
    padding: 12px 10px;
  }

  .has-quick .quick-chip:nth-child(n + 3) { display: none; }
  .has-quick .psych-header { order: 0; }
  .has-quick .psych-messages { order: 1; min-height: 60px; }
  .has-quick .quick-starter { order: 2; }
  .has-quick .psych-input { order: 3; }
  .psych-header .chat-actions :deep(.el-button) { font-size: 11px; padding-inline: 3px; }

  .message-wrapper {
    gap: 8px;

    .message-content { max-width: calc(100% - 48px); }
    .message-bubble { padding: 9px 12px; line-height: 1.65; }
  }

  .psych-input {
    padding: 9px 10px max(10px, env(safe-area-inset-bottom));

    .input-hint { display: none; }
    .input-row { gap: 8px; }
    .input-row :deep(.el-button) { min-width: 72px; min-height: 42px; padding-inline: 12px; }
  }
  .mobile-session-controls { display: block; width: 100%; min-width: 0; }
  .mobile-session-controls .psych-header { display: block; padding: 0; border: 0; background: transparent; }
  .mobile-session-controls .scene-icon,
  .mobile-session-controls .scene-copy .eyebrow,
  .mobile-session-controls .scene-copy p { display: none; }
  .mobile-session-controls .scene-copy h1 { font-size: 15px; line-height: 1.4; margin: 0 0 9px; }
  .mobile-session-controls .chat-actions { display: flex; flex-wrap: wrap; justify-content: flex-start; width: 100%; gap: 6px; }
  .mobile-session-controls .chat-actions .voice-toggle { min-height: 36px; padding: 0; font-size: 11px; }
  .mobile-session-controls .chat-actions :deep(.el-button) { min-height: 36px; height: 36px; border-radius: 9px; font-size: 11px; padding: 0 7px; margin: 0; }
  .mobile-session-controls .chat-actions { margin-left: 0; max-width: 360px; }
  .psych-input { flex-shrink: 0; }
  .psych-input :deep(.el-textarea__inner) { font-size: 16px; }
  .psych-messages { min-height: 0; overscroll-behavior-y: contain; }
  .message-bubble { overflow-wrap: anywhere; font-size: 14px; }
  .quick-title { font-size: 12px; margin-bottom: 6px; }
  .quick-starter { margin: 4px 10px 0; padding: 8px 10px; border-radius: 14px; }
  .quick-chip { font-size: 12px; padding: 6px 10px; }
}
</style>
