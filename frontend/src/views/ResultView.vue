<template>
  <div class="result-view">
    <AppHeader />

    <main class="result-container" v-loading="loading" element-loading-text="评分智能体正在复盘，首次约需 30-60 秒…">
      <el-alert v-if="loadError" :title="loadError" type="error" show-icon :closable="false" class="load-alert" />
      <div v-if="loadError" class="retry-row">
        <el-button type="primary" :loading="loading" @click="manualRetry"><el-icon><Refresh /></el-icon>重新发起评分</el-button>
      </div>

      <template v-if="!loadError">
        <header class="result-heading">
          <div>
            <span class="eyebrow">TRAINING REVIEW</span>
            <h1>训练复盘</h1>
            <p>{{ result.scene_title || '模拟训练' }} · 每一次复盘都让下一次行动更稳</p>
          </div>
          <el-tag v-if="result.rating_source" effect="plain" round>
            {{ sourceLabel }}
          </el-tag>
        </header>

        <section class="score-card">
          <div class="total-score">
            <span class="score-caption">综合得分</span>
            <strong>{{ result.total_score ?? '--' }}</strong>
            <span>满分 100</span>
          </div>

          <div class="radar-wrap" aria-label="三维能力雷达图">
            <svg viewBox="0 0 220 190" role="img">
              <polygon points="110,18 190,158 30,158" class="radar-grid outer" />
              <polygon points="110,53 170,158 50,158" class="radar-grid" />
              <polygon points="110,88 150,158 70,158" class="radar-grid" />
              <line x1="110" y1="18" x2="110" y2="158" class="radar-axis" />
              <line x1="30" y1="158" x2="190" y2="158" class="radar-axis" />
              <polygon :points="radarPoints" class="radar-score" />
              <circle v-for="(point, index) in radarVertices" :key="index" :cx="point.x" :cy="point.y" r="4" class="radar-point" />
              <text x="110" y="11" text-anchor="middle">医学准确性</text>
              <text x="12" y="178" text-anchor="start">沟通温度</text>
              <text x="208" y="178" text-anchor="end">决策合理性</text>
            </svg>
          </div>

          <div class="dimension-scores">
            <div v-for="item in dimensionItems" :key="item.key" class="dimension">
              <div class="dim-heading">
                <span>{{ item.label }}</span>
                <strong>{{ item.score }}/{{ item.max }}</strong>
              </div>
              <el-progress :percentage="item.percentage" :stroke-width="8" :show-text="false" :color="item.color" />
              <small>{{ item.percentage }}%</small>
            </div>
          </div>
        </section>

        <section class="feedback-grid">
          <article class="section feedback-main">
            <div class="section-title">
              <span class="title-icon blue"><el-icon><ChatDotRound /></el-icon></span>
              <div><span>评分智能体</span><h2>综合评语</h2></div>
            </div>
            <p class="summary">{{ result.summary || '完成更多对话后，评分智能体会生成针对性的综合评语。' }}</p>
          </article>

          <article class="section compact-list strengths">
            <div class="section-title">
              <span class="title-icon green"><el-icon><CircleCheck /></el-icon></span>
              <div><span>KEEP</span><h2>做得好的地方</h2></div>
            </div>
            <ul v-if="result.highlights?.length">
              <li v-for="item in result.highlights" :key="item">{{ item }}</li>
            </ul>
            <p v-else class="empty-copy">暂无突出项，继续完成训练步骤。</p>
          </article>

          <article class="section compact-list improvements">
            <div class="section-title">
              <span class="title-icon amber"><el-icon><Aim /></el-icon></span>
              <div><span>NEXT</span><h2>下一次重点</h2></div>
            </div>
            <ul v-if="result.key_mistakes?.length">
              <li v-for="item in result.key_mistakes" :key="item">{{ item }}</li>
            </ul>
            <p v-else class="empty-copy">关键流程完整，继续巩固。</p>
          </article>
        </section>

        <section v-if="result.decision_tree" class="section path-section">
          <div class="section-title">
            <span class="title-icon violet"><el-icon><Share /></el-icon></span>
            <div><span>PATH REVIEW</span><h2>决策路径对比</h2></div>
          </div>
          <div class="path-row user-path">
            <strong>你的路径</strong>
            <div class="path-nodes">
              <template v-for="(node, index) in result.decision_tree.user_path || []" :key="`${node}-${index}`">
                <span>{{ node }}</span><el-icon v-if="index < result.decision_tree.user_path.length - 1"><ArrowRight /></el-icon>
              </template>
            </div>
          </div>
          <div class="path-row optimal-path">
            <strong>最优路径</strong>
            <div class="path-nodes">
              <template v-for="(node, index) in result.decision_tree.optimal_path || []" :key="`${node}-${index}`">
                <span>{{ node }}</span><el-icon v-if="index < result.decision_tree.optimal_path.length - 1"><ArrowRight /></el-icon>
              </template>
            </div>
          </div>
          <div v-if="result.decision_tree.gaps" class="gap-analysis">
            <el-icon><InfoFilled /></el-icon><span>{{ result.decision_tree.gaps }}</span>
          </div>
        </section>

        <section v-if="result.scene_type === 'first_visit' && result.sample_completeness" class="section sample-section">
          <div class="section-title">
            <span class="title-icon teal"><el-icon><DataAnalysis /></el-icon></span>
            <div><span>SAMPLE</span><h2>病史信息完整度</h2></div>
          </div>
          <div class="sample-grid">
            <div v-for="item in sampleItems" :key="item.key" class="sample-item">
              <div><strong>{{ item.letter }}</strong><span>{{ item.label }}</span><b>{{ item.value }}%</b></div>
              <el-progress :percentage="item.value" :stroke-width="7" :show-text="false" color="#178a8a" />
            </div>
          </div>
          <div v-if="result.communication_words?.length" class="word-insights">
            <span>沟通关键词</span>
            <div>
              <el-tag v-for="item in result.communication_words" :key="item.word" effect="plain" round>
                {{ item.word }} × {{ item.count }}
              </el-tag>
            </div>
          </div>
        </section>

        <section v-if="result.scene_type === 'osce'" class="section osce-section">
          <div class="section-title">
            <span class="title-icon teal"><el-icon><DocumentChecked /></el-icon></span>
            <div><span>OSCE CHECKLIST</span><h2>问诊与病历完成度</h2></div>
          </div>
          <div class="osce-grid">
            <div v-for="item in osceItems" :key="item.key" class="osce-item">
              <div><strong>{{ item.label }}</strong><b>{{ item.value }}%</b></div>
              <el-progress :percentage="item.value" :stroke-width="8" :show-text="false" color="#187f91" />
            </div>
          </div>
          <div class="record-review">
            <strong>病历书写点评</strong>
            <p>{{ result.medical_record_review || '评分智能体会单独评价病历结构、术语、信息真实性和诊断依据。' }}</p>
          </div>
        </section>

        <section class="section replay-section">
          <div class="section-title replay-title">
            <span class="title-icon slate"><el-icon><Clock /></el-icon></span>
            <div><span>TIMELINE</span><h2>对话与决策回放</h2></div>
            <span class="message-count">{{ result.messages?.length || 0 }} 条记录</span>
          </div>
          <ol v-if="result.messages?.length" class="message-list">
            <li v-for="msg in result.messages" :key="msg.id" :class="[msg.role, { 'medical-record': msg.kind === 'medical_record' }]">
              <span class="timeline-dot" />
              <div class="msg-header">
                <span class="msg-role">{{ messageRoleLabel(msg) }}</span>
                <time>{{ formatTime(msg.timestamp) }}</time>
                <el-tag v-if="msg.issue_points" type="danger" size="small">需改进：{{ msg.issue_points }}</el-tag>
                <el-tag v-else-if="msg.good_points" type="success" size="small">做得好：{{ msg.good_points }}</el-tag>
              </div>
              <p>{{ msg.content }}</p>
            </li>
          </ol>
          <el-empty v-else description="暂无可回放的对话" />
        </section>

        <footer class="actions">
          <el-button @click="router.push('/')"><el-icon><Back /></el-icon>返回首页</el-button>
          <el-button @click="onShare"><el-icon><Share /></el-icon>分享结果</el-button>
          <el-button type="primary" @click="retryScene"><el-icon><Refresh /></el-icon>再练一次</el-button>
        </footer>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import { getResult } from '@/api/result'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.sessionId
const result = ref({})
const loading = ref(true)
const loadError = ref('')
let pollTimer = null
let retryCount = 0
let pendingStartedAt = 0
const PENDING_TIMEOUT_MS = 120000

const sourceLabel = computed(() => ({ agent: '评分智能体', rules: '规则引擎保底评分', demo: '演示数据' })[result.value.rating_source] || '评分智能体')
const dimensionItems = computed(() => {
  const definitions = [
    { key: 'accuracy', label: '医学准确性', color: '#2c7be5' },
    { key: 'warmth', label: '沟通温度', color: '#2a9d74' },
    { key: 'decision', label: '决策合理性', color: '#e49a19' }
  ]
  return definitions.map((item) => {
    const score = Number(result.value.dimensions?.[item.key] || 0)
    const max = Number(result.value.dimension_max?.[item.key] || 100)
    return { ...item, score, max, percentage: Math.round(Math.min(100, score / max * 100)) }
  })
})

const radarVertices = computed(() => {
  const values = dimensionItems.value.map((item) => item.percentage / 100)
  const center = { x: 110, y: 111 }
  const targets = [{ x: 110, y: 18 }, { x: 30, y: 158 }, { x: 190, y: 158 }]
  return targets.map((target, index) => ({
    x: center.x + (target.x - center.x) * values[index],
    y: center.y + (target.y - center.y) * values[index]
  }))
})
const radarPoints = computed(() => radarVertices.value.map((point) => `${point.x},${point.y}`).join(' '))

const sampleItems = computed(() => {
  const source = result.value.sample_completeness || {}
  return [
    { key: 'symptoms', letter: 'S', label: '症状描述' },
    { key: 'allergies', letter: 'A', label: '过敏史' },
    { key: 'medications', letter: 'M', label: '用药史' },
    { key: 'history', letter: 'P', label: '既往病史' },
    { key: 'events', letter: 'E', label: '发病经过' }
  ].map((item) => ({ ...item, value: Math.max(0, Math.min(100, Number(source[item.key] || 0))) }))
})

const osceItems = computed(() => {
  const source = result.value.osce_checklist || {}
  return [
    { key: 'opening_communication', label: '接诊沟通' },
    { key: 'chief_complaint_hpi', label: '主诉与现病史' },
    { key: 'other_history', label: '其他病史' },
    { key: 'exam_investigations', label: '快速检查' },
    { key: 'medical_record', label: '病历书写' }
  ].map((item) => ({ ...item, value: Math.max(0, Math.min(100, Number(source[item.key] || 0))) }))
})

function demoResult() {
  return {
    scene_id: 2,
    scene_title: '第一次独立看病（演示）',
    scene_type: 'first_visit',
    total_score: 82,
    dimensions: { accuracy: 24, warmth: 34, decision: 24 },
    dimension_max: { accuracy: 30, warmth: 40, decision: 30 },
    summary: '你能主动选择挂号方式并礼貌表达需求。下一次请完成自助机打印报到单、诊间扫码报到，并记得医嘱开具后先到人工收费窗口缴费。',
    highlights: ['主动选择挂号方式', '沟通礼貌、表达清楚'],
    key_mistakes: ['未完整展示打印报到单和诊间扫码报到', '未先到人工收费窗口缴费'],
    decision_tree: {
      user_path: ['线上挂号', '描述症状', '询问用药'],
      optimal_path: ['选择挂号', '打印报到单', '诊间扫码', '症状问诊', '诊断医嘱', '人工缴费', '取药执行'],
      gaps: '补齐报到两步，并保持先人工缴费、后取药或检查治疗的顺序。'
    },
    sample_completeness: { symptoms: 85, allergies: 0, medications: 50, history: 0, events: 75 },
    communication_words: [{ word: '您好', count: 2 }, { word: '请问', count: 2 }, { word: '谢谢', count: 1 }],
    messages: [],
    rating_source: 'demo'
  }
}

onMounted(loadResult)
onBeforeUnmount(() => {
  if (pollTimer) window.clearTimeout(pollTimer)
})

async function loadResult() {
  // 上一次轮询已触发，清掉旧计时器再开始本轮（否则 finally 会误判仍在轮询，loading 关不掉）
  if (pollTimer) {
    window.clearTimeout(pollTimer)
    pollTimer = null
  }
  loading.value = true
  loadError.value = ''
  try {
    const data = sessionId === 'demo' ? demoResult() : await getResult(sessionId)
    // 后台评分正常应在 60 秒内完成；给数据库落库留出余量，但不能无限轮询。
    if (data && data.status === 'pending') {
      if (!pendingStartedAt) pendingStartedAt = Date.now()
      if (Date.now() - pendingStartedAt >= PENDING_TIMEOUT_MS) {
        loadError.value = '评分等待时间过长，可能遇到网络中断。请点击下方按钮重新发起评分。'
        return
      }
      pollTimer = window.setTimeout(loadResult, 3000)
      return
    }
    result.value = data
    retryCount = 0
    pendingStartedAt = 0
  } catch (error) {
    console.warn('评分数据加载失败', error)
    retryCount += 1
    if (retryCount <= 3) {
      pollTimer = window.setTimeout(loadResult, 3000)
      return
    }
    loadError.value = '评分数据暂时无法加载，可能是网络或后端服务异常，请稍后重试。'
  } finally {
    // 轮询/自动重试期间保持 loading 遮罩，避免渲染空数据
    if (!pollTimer) loading.value = false
  }
}

function manualRetry() {
  retryCount = 0
  pendingStartedAt = 0
  loadResult()
}

function roleLabel(role) {
  return ({ system: '情景生成智能体', user: '你', ai: '场景角色', coach: '观察者教练' })[role] || role
}

function messageRoleLabel(message) {
  if (message.kind === 'medical_record') return '我的病历记录'
  return roleLabel(message.role)
}

function formatTime(timestamp) {
  if (!timestamp) return '--:--'
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

async function onShare() {
  const shareData = { title: '“易”生伴训练复盘', text: `我在${result.value.scene_title || '医疗训练'}中获得${result.value.total_score || 0}分。`, url: window.location.href }
  try {
    if (navigator.share) await navigator.share(shareData)
    else {
      await navigator.clipboard.writeText(`${shareData.text}\n${shareData.url}`)
      ElMessage.success('成绩和链接已复制')
    }
  } catch (error) {
    if (error?.name !== 'AbortError') ElMessage.warning('分享失败，请手动复制当前页面链接')
  }
}

function retryScene() {
  router.push(result.value.scene_id ? `/chat/${result.value.scene_id}` : '/')
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.result-view { min-height: 100vh; background: linear-gradient(180deg, #f4f7fa, #eef2f6); }
.result-container { max-width: 1080px; margin: 0 auto; padding: 36px 24px 60px; min-height: 600px; }
.load-alert { margin-bottom: 20px; }
.result-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 22px; }
.eyebrow { color: #54778e; font-size: 11px; font-weight: 800; letter-spacing: 0.14em; }
.result-heading h1 { margin: 4px 0; color: #172d3c; font-size: 32px; }
.result-heading p { margin: 0; color: #6c8190; }

.score-card { display: grid; grid-template-columns: 170px 270px 1fr; align-items: center; gap: 24px; padding: 26px 30px; border: 1px solid #dbe4eb; border-radius: 20px; background: white; box-shadow: 0 16px 40px rgba(38, 61, 78, 0.08); }
.total-score { text-align: center; border-right: 1px solid #e2e8ed; display: flex; flex-direction: column; align-items: center; }
.total-score strong { color: #176fb7; font-size: 68px; line-height: 1.05; letter-spacing: -0.06em; }
.total-score > span:last-child, .score-caption { color: #7890a1; font-size: 12px; }
.score-caption { margin-bottom: 5px; font-weight: 700; letter-spacing: 0.08em; }
.radar-wrap svg { width: 100%; display: block; overflow: visible; }
.radar-grid { fill: none; stroke: #dfe8ee; stroke-width: 1; }
.radar-grid.outer { stroke: #c6d6e0; }
.radar-axis { stroke: #e2e9ee; stroke-width: 1; }
.radar-score { fill: rgba(44, 123, 229, 0.2); stroke: #2c7be5; stroke-width: 2; }
.radar-point { fill: white; stroke: #2c7be5; stroke-width: 2; }
.radar-wrap text { fill: #5e7484; font-size: 10px; }
.dimension { margin-bottom: 15px; position: relative; padding-right: 42px; }
.dimension:last-child { margin-bottom: 0; }
.dim-heading { display: flex; justify-content: space-between; margin-bottom: 6px; color: #536a7a; font-size: 13px; }
.dim-heading strong { color: #253f52; }
.dimension small { position: absolute; right: 0; bottom: -1px; color: #8495a1; }

.feedback-grid { display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 16px; margin-top: 18px; }
.section { border: 1px solid #dfe6eb; border-radius: 16px; padding: 22px; background: white; box-shadow: 0 8px 24px rgba(40, 61, 75, 0.05); }
.section-title { display: flex; align-items: center; gap: 11px; margin-bottom: 16px; }
.section-title > div { flex: 1; }
.section-title span:not(.title-icon) { color: #8495a1; font-size: 10px; font-weight: 800; letter-spacing: 0.12em; }
.section-title h2 { margin: 2px 0 0; color: #21394a; font-size: 18px; }
.title-icon { width: 38px; height: 38px; flex: none; border-radius: 11px; display: grid; place-items: center; font-size: 18px; }
.title-icon.blue { color: #2c7be5; background: #eaf3ff; }
.title-icon.green { color: #23805b; background: #e8f7ef; }
.title-icon.amber { color: #a76a08; background: #fff3db; }
.title-icon.violet { color: #6552a2; background: #f0ecfb; }
.title-icon.teal { color: #137878; background: #e3f5f3; }
.title-icon.slate { color: #536b7d; background: #edf2f5; }
.summary { margin: 0; color: #425c6d; line-height: 1.85; }
.compact-list ul { margin: 0; padding-left: 18px; color: #425d6c; line-height: 1.7; }
.compact-list li + li { margin-top: 8px; }
.empty-copy { color: #8999a5; }

.path-section, .sample-section, .osce-section, .replay-section { margin-top: 18px; }
.path-row { display: grid; grid-template-columns: 88px 1fr; align-items: start; gap: 12px; padding: 14px; border-radius: 11px; background: #f6f8fa; }
.path-row + .path-row { margin-top: 10px; }
.path-row > strong { color: #526a7a; font-size: 13px; }
.path-nodes { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; }
.path-nodes span { padding: 5px 9px; border-radius: 7px; border: 1px solid #d5e0e7; color: #456070; background: white; font-size: 12px; }
.optimal-path .path-nodes span { border-color: #b9dfce; color: #26704f; background: #f2fbf6; }
.path-nodes .el-icon { color: #98a8b3; }
.gap-analysis { margin-top: 12px; padding: 12px 14px; display: flex; gap: 9px; border-radius: 10px; color: #815816; background: #fff8e8; line-height: 1.6; }

.sample-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
.sample-item { padding: 13px; border: 1px solid #e1e9ed; border-radius: 11px; }
.sample-item > div { display: flex; align-items: center; gap: 7px; margin-bottom: 9px; }
.sample-item strong { color: #178a8a; font-size: 18px; }
.sample-item span { flex: 1; color: #617787; font-size: 12px; }
.sample-item b { color: #294656; font-size: 12px; }
.osce-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
.osce-item { padding: 13px; border: 1px solid #dce9ed; border-radius: 11px; background: #fbfefe; }
.osce-item > div { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 9px; }
.osce-item strong { color: #365e6a; font-size: 13px; }
.osce-item b { color: #187f91; font-size: 12px; }
.record-review { margin-top: 15px; padding: 14px 16px; border-left: 3px solid #187f91; border-radius: 8px; background: #eff8f8; }
.record-review strong { color: #235c65; }
.record-review p { margin: 5px 0 0; color: #496a73; line-height: 1.7; }
.word-insights { margin-top: 18px; padding-top: 16px; border-top: 1px solid #e7ecef; display: flex; align-items: center; gap: 15px; }
.word-insights > span { color: #657c8b; font-size: 12px; font-weight: 700; }
.word-insights > div { display: flex; flex-wrap: wrap; gap: 7px; }

.replay-title .message-count { color: #7f929f; font-size: 12px; }
.message-list { list-style: none; margin: 0; padding: 0 0 0 20px; border-left: 1px solid #dce5eb; }
.message-list li { position: relative; margin: 0 0 14px; padding: 14px 16px; border-radius: 10px; background: #f7f9fa; }
.message-list li.user { background: #eef6ff; }
.message-list li.coach { background: #fff8e8; }
.message-list li.system { background: #edf8f7; }
.message-list li.medical-record { border: 1px solid #a9d7d3; background: #eefaf8; }
.timeline-dot { position: absolute; left: -25px; top: 20px; width: 9px; height: 9px; border-radius: 50%; border: 2px solid white; background: #9aabb7; box-shadow: 0 0 0 1px #c7d4dc; }
.user .timeline-dot { background: #2c7be5; }
.coach .timeline-dot { background: #e5a020; }
.system .timeline-dot { background: #188685; }
.msg-header { display: flex; flex-wrap: wrap; align-items: center; gap: 9px; }
.msg-role { color: #2f4c5e; font-weight: 700; font-size: 13px; }
.msg-header time { color: #8c9da8; font-size: 11px; }
.message-list p { margin: 8px 0 0; color: #425a69; line-height: 1.7; white-space: pre-line; }
.actions { display: flex; justify-content: center; gap: 12px; margin-top: 28px; }
.retry-row { display: flex; justify-content: center; margin-top: 20px; }

@media (max-width: 860px) {
  .score-card { grid-template-columns: 130px 1fr; }
  .radar-wrap { display: none; }
  .feedback-grid { grid-template-columns: 1fr 1fr; }
  .feedback-main { grid-column: 1 / -1; }
  .sample-grid { grid-template-columns: repeat(2, 1fr); }
  .osce-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .result-container { padding: 24px 12px 40px; }
  .result-heading h1 { font-size: 26px; }
  .result-heading p { display: none; }
  .score-card { grid-template-columns: 1fr; padding: 22px; }
  .total-score { border-right: 0; border-bottom: 1px solid #e2e8ed; padding-bottom: 18px; }
  .feedback-grid { grid-template-columns: 1fr; }
  .feedback-main { grid-column: auto; }
  .section { padding: 17px; }
  .path-row { grid-template-columns: 1fr; }
  .sample-grid { grid-template-columns: 1fr; }
  .osce-grid { grid-template-columns: 1fr; }
  .word-insights { align-items: flex-start; flex-direction: column; }
  .actions { flex-wrap: wrap; }
}
</style>
