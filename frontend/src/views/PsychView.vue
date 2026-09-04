<template>
  <div class="psych-view">
    <AppHeader />

    <main class="psych-container">
      <!-- 数字人舞台 -->
      <AvatarStage
        v-if="!avatarCollapsed"
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
      />
      <button v-else type="button" class="avatar-reopen" title="展开数字人" @click="avatarCollapsed = false">
        <span class="arrow">›</span>
        <span class="txt">数字人</span>
      </button>

      <!-- 聊天区 -->
      <div class="psych-main">
        <header class="psych-header">
          <div class="scene-icon" aria-hidden="true"><el-icon><ChatLineRound /></el-icon></div>
          <div class="scene-copy">
            <div class="eyebrow">心理陪伴 · 情绪疏导</div>
            <h1>和「易心」聊一聊</h1>
            <p>这里没有评判，你可以放心说任何心里话</p>
          </div>
          <div class="chat-actions">
            <label v-if="ttsAvailable" class="voice-toggle" :class="{ 'is-on': voiceEnabled }">
              <el-switch v-model="voiceEnabled" size="small" @change="onVoiceToggle" /> 🔊 语音
            </label>
            <el-button type="warning" plain @click="resetChat">换个话题</el-button>
            <el-button type="danger" plain @click="goHome">退出陪伴</el-button>
          </div>
        </header>

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
          <div class="input-row">
            <el-input
              v-model="inputText"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 5 }"
              maxlength="1000"
              show-word-limit
              placeholder="说说你的心事吧…"
              :disabled="loading"
              @keydown.ctrl.enter="onSend"
            />
            <el-button type="warning" round :loading="loading" :disabled="!inputText.trim()" @click="onSend">
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AvatarStage from '@/components/AvatarStage.vue'
import { sendPsychMessage } from '@/api/psych'
import { isTTSSupported, stripForSpeech, extractPerformanceCue } from '@/utils/live2dMap'
import { preheatMeSpeak, stopUnifiedSpeaking, unifiedSpeak } from '@/utils/ttsService'

const router = useRouter()

// 「易心」：心理陪伴数字人设定（柔和女声）
const psychPersona = {
  label: '易心',
  gender: 'female',
  voiceHint: '女|晓',
  pitch: 1.1,
  rate: 0.95
}

const ttsAvailable = isTTSSupported()
const voiceEnabled = ref(ttsAvailable)
const avatarCollapsed = ref(false)

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messageListRef = ref(null)
let messageSeq = 0

const stageSpeaking = ref(false)
const currentExpression = ref('calm')
const currentAction = ref('idle')

const crisisShown = ref(false)

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

const historyForApi = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({ role: m.role, content: m.content }))
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

async function speak(text) {
  if (!text) return
  const gen = ++speakGen
  // 语音关闭 / 不可用时同样把身体动作复位，让易心回到待机陪伴姿态
  if (!voiceEnabled.value || !ttsAvailable) {
    stageSpeaking.value = false
    currentAction.value = 'idle'
    return
  }
  stageSpeaking.value = true
  try {
    await unifiedSpeak(stripForSpeech(text), {
      gender: 'female',
      pitch: psychPersona.pitch,
      rate: psychPersona.rate
    })
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
  if (!value) stopVoice()
}

function applyCue(text) {
  const cue = extractPerformanceCue(text, 'psych', 'calm')
  currentExpression.value = cue.expression
  currentAction.value = cue.action
}

async function onSend() {
  const text = (inputText.value || '').trim()
  if (!text || loading.value) return
  // 用户发言时立即打断易心正在说的话，避免新旧声音叠在一起
  stopVoice()
  inputText.value = ''
  addMessage('user', text)
  applyCue(text)
  loading.value = true

  try {
    const res = await sendPsychMessage(historyForApi.value)
    const reply = (res && res.reply) || '嗯，我在听。你愿意再说说吗？'
    addMessage('assistant', reply)
    applyCue(reply)
    if (res && res.crisis) crisisShown.value = true
    await speak(reply)
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

function resetChat() {
  messages.value = []
  crisisShown.value = false
  currentExpression.value = 'calm'
  currentAction.value = 'idle'
  addMessage('assistant', OPENING_TEXT)
  speak(OPENING_TEXT)
}

function goHome() {
  stopVoice()
  router.push('/')
}

onMounted(() => {
  preheatMeSpeak()
  addMessage('assistant', OPENING_TEXT)
  applyCue(OPENING_TEXT)
  // 延迟一点再开口欢迎；若用户在欢迎词响起前已经发言（比如抢点快捷话题卡），就不再念开场白了
  window.setTimeout(() => {
    if (!messages.value.some((m) => m.role === 'user')) speak(OPENING_TEXT)
  }, 900)
})

onBeforeUnmount(() => {
  stopVoice()
})
</script>

<style scoped lang="scss">
.psych-view {
  min-height: 100vh;
  background: linear-gradient(180deg, #fffaf3 0%, #fff4e4 40%, #fdf1df 100%);
}

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

.psych-main {
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
    background: linear-gradient(135deg, #ffb057, #f97316);
    box-shadow: 0 4px 12px rgba(249, 115, 22, 0.35);
  }

  .scene-copy {
    flex: 1;
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
    display: flex;
    align-items: center;
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

.crisis-pop-enter-active, .crisis-pop-leave-active { transition: all 0.3s; }
.crisis-pop-enter-from, .crisis-pop-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 720px) {
  .psych-container {
    width: 100%;
    height: calc(100dvh - 58px);
    min-height: 560px;
    padding: 0;
    flex-direction: column;
  }

  .avatar-side { width: 100%; }
  .avatar-reopen { display: none; }

  .psych-main {
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
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) minmax(0, 1fr);
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
}
</style>
