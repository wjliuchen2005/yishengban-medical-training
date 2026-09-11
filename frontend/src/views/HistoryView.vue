<template>
  <div class="history-view">
    <AppHeader />

    <main class="history-container">
      <header class="history-heading">
        <div>
          <span class="eyebrow">TRAINING HISTORY</span>
          <h1>训练历史</h1>
          <p>回顾历次训练的成绩，看看自己进步了多少</p>
        </div>
        <div class="heading-actions">
          <el-button plain @click="openSummary">成长总结</el-button>
          <el-button type="primary" @click="router.push('/')"><el-icon><Plus /></el-icon>开始新训练</el-button>
        </div>
      </header>

      <section v-if="records.length" class="history-filters" aria-label="训练历史筛选排序">
        <el-select v-model="sceneFilter" placeholder="全部场景" clearable><el-option v-for="name in sceneOptions" :key="name" :label="name" :value="name" /></el-select>
        <el-select v-model="statusFilter" placeholder="全部状态" clearable>
          <el-option label="已完成" value="completed" /><el-option label="未评分" value="unrated" /><el-option label="进行中" value="running" />
        </el-select>
        <el-select v-model="sortBy" aria-label="排序方式">
          <el-option label="置顶优先 · 最新" value="pinned" /><el-option label="用时从短到长" value="duration_asc" /><el-option label="用时从长到短" value="duration_desc" /><el-option label="成绩从高到低" value="score_desc" />
        </el-select>
      </section>

      <el-empty
        v-if="!loading && !loadError && !records.length"
        description="还没有训练记录，选一个场景开始第一次训练吧"
      >
        <el-button type="primary" @click="router.push('/')">去选场景</el-button>
      </el-empty>

      <el-alert
        v-else-if="loadError"
        :title="loadError"
        type="error"
        show-icon
        :closable="false"
        class="load-alert"
      />

      <el-table
        v-else
        :data="displayedRecords"
        v-loading="loading"
        class="history-table"
      >
        <el-table-column label="训练场景" min-width="150">
          <template #default="{ row }">
            <div class="scene-cell">
              <span class="scene-dot" :class="sceneKind(row)" />
              <span>{{ row.scene_title }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="started_at" label="开始时间" width="170" sortable>
          <template #default="{ row }">{{ formatDateTime(row.started_at) }}</template>
        </el-table-column>

        <el-table-column label="用时" width="90" align="center">
          <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
        </el-table-column>

        <el-table-column label="总分" width="100" align="center" sortable prop="total_score">
          <template #default="{ row }">
            <strong v-if="row.total_score != null" :class="scoreClass(row.total_score)">{{ row.total_score }}</strong>
            <span v-else class="muted">--</span>
          </template>
        </el-table-column>

        <el-table-column label="三维得分" min-width="220">
          <template #default="{ row }">
            <div v-if="row.total_score != null" class="dim-bars">
              <div class="dim-bar">
                <span>准确</span>
                <el-progress :percentage="pct(row.accuracy, dimMax(row, 'accuracy'))" :stroke-width="6" :show-text="false" color="#2c7be5" />
                <b>{{ row.accuracy }}</b>
              </div>
              <div class="dim-bar">
                <span>温度</span>
                <el-progress :percentage="pct(row.warmth, dimMax(row, 'warmth'))" :stroke-width="6" :show-text="false" color="#2a9d74" />
                <b>{{ row.warmth }}</b>
              </div>
              <div class="dim-bar">
                <span>决策</span>
                <el-progress :percentage="pct(row.decision, dimMax(row, 'decision'))" :stroke-width="6" :show-text="false" color="#e49a19" />
                <b>{{ row.decision }}</b>
              </div>
            </div>
            <span v-else class="muted">未评分</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.total_score != null" type="success" size="small" effect="light">已完成</el-tag>
            <el-tag v-else-if="row.ended_at" type="warning" size="small" effect="light">未评分</el-tag>
            <el-tag v-else type="info" size="small" effect="light">进行中</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="300" align="center" fixed="right">
          <template #default="{ row }">
            <div class="record-actions">
              <el-button size="small" text @click="toggleFlag(row, 'is_favorite')">{{ row.is_favorite ? '★ 已收藏' : '☆ 收藏' }}</el-button>
              <el-button size="small" text @click="toggleFlag(row, 'is_pinned')">{{ row.is_pinned ? '取消置顶' : '置顶' }}</el-button>
              <el-button
                v-if="row.total_score != null || row.ended_at"
                type="primary"
                size="small"
                plain
                @click="router.push(`/result/${row.session_id}`)"
              >
                查看复盘
              </el-button>
              <el-button
                v-else
                type="success"
                size="small"
                plain
                @click="router.push(`/chat/${row.scene_id}?session=${row.session_id}`)"
              >
                继续训练
              </el-button>
              <el-button
                type="danger"
                size="small"
                plain
                :loading="deletingSessionId === row.session_id"
                @click="deleteRecord(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <section v-if="!loading && !loadError && records.length" class="history-cards" aria-label="训练历史记录">
        <article v-for="row in displayedRecords" :key="row.session_id" class="history-card" :class="{ pinned: row.is_pinned }">
          <div class="mobile-card-heading">
            <div class="scene-cell">
              <span class="scene-dot" :class="sceneKind(row)" />
              <strong>{{ row.scene_title }}</strong>
            </div>
            <el-tag v-if="row.total_score != null" type="success" size="small" effect="light">已完成</el-tag>
            <el-tag v-else-if="row.ended_at" type="warning" size="small" effect="light">未评分</el-tag>
            <el-tag v-else type="info" size="small" effect="light">进行中</el-tag>
          </div>

          <dl class="mobile-facts">
            <div><dt>开始时间</dt><dd>{{ formatDateTime(row.started_at) }}</dd></div>
            <div><dt>用时</dt><dd>{{ formatDuration(row.duration) }}</dd></div>
            <div><dt>总分</dt><dd><strong v-if="row.total_score != null" :class="scoreClass(row.total_score)">{{ row.total_score }}</strong><span v-else>--</span></dd></div>
          </dl>

          <div v-if="row.total_score != null" class="dim-bars mobile-dim-bars">
            <div class="dim-bar"><span>准确</span><el-progress :percentage="pct(row.accuracy, dimMax(row, 'accuracy'))" :stroke-width="6" :show-text="false" color="#2c7be5" /><b>{{ row.accuracy }}</b></div>
            <div class="dim-bar"><span>温度</span><el-progress :percentage="pct(row.warmth, dimMax(row, 'warmth'))" :stroke-width="6" :show-text="false" color="#2a9d74" /><b>{{ row.warmth }}</b></div>
            <div class="dim-bar"><span>决策</span><el-progress :percentage="pct(row.decision, dimMax(row, 'decision'))" :stroke-width="6" :show-text="false" color="#e49a19" /><b>{{ row.decision }}</b></div>
          </div>

          <div class="mobile-actions">
            <el-button size="small" plain @click="toggleFlag(row, 'is_favorite')">{{ row.is_favorite ? '★' : '☆' }}</el-button>
            <el-button size="small" plain @click="toggleFlag(row, 'is_pinned')">{{ row.is_pinned ? '取消置顶' : '置顶' }}</el-button>
            <el-button
              v-if="row.total_score != null || row.ended_at"
              type="primary"
              size="small"
              plain
              @click="router.push(`/result/${row.session_id}`)"
            >查看复盘</el-button>
            <el-button
              v-else
              type="success"
              size="small"
              plain
              @click="router.push(`/chat/${row.scene_id}?session=${row.session_id}`)"
            >继续训练</el-button>
            <el-button
              type="danger"
              size="small"
              plain
              :loading="deletingSessionId === row.session_id"
              @click="deleteRecord(row)"
            >删除</el-button>
          </div>
        </article>
      </section>
    </main>

    <el-dialog v-model="summaryVisible" title="训练成长总结" width="min(660px, 94vw)">
      <div v-loading="summaryLoading" class="summary-report">
        <h3>{{ trainingSummary?.headline }}</h3>
        <section><strong>值得肯定</strong><p v-for="item in trainingSummary?.highlights || []" :key="item">✓ {{ item }}</p></section>
        <section><strong>下一步可以更好</strong><p v-for="item in trainingSummary?.opportunities || []" :key="item">→ {{ item }}</p></section>
        <div class="scene-summary" v-for="item in trainingSummary?.scenes || []" :key="item.scene"><span>{{ item.scene }} · {{ item.count }}次</span><b>{{ item.average }}分</b></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import { deleteChatSession, getChatHistory, getTrainingSummary, updateChatSessionFlags } from '@/api/chat'

const router = useRouter()
const records = ref([])
const loading = ref(true)
const loadError = ref('')
const deletingSessionId = ref(null)
const sceneFilter = ref('')
const statusFilter = ref('')
const sortBy = ref('pinned')
const summaryVisible = ref(false)
const summaryLoading = ref(false)
const trainingSummary = ref(null)

const sceneOptions = computed(() => [...new Set(records.value.map((row) => row.scene_title))])
const displayedRecords = computed(() => {
  const filtered = records.value.filter((row) => {
    if (sceneFilter.value && row.scene_title !== sceneFilter.value) return false
    const state = row.total_score != null ? 'completed' : row.ended_at ? 'unrated' : 'running'
    return !statusFilter.value || state === statusFilter.value
  })
  return [...filtered].sort((a, b) => {
    if (sortBy.value === 'duration_asc') return (a.duration ?? Infinity) - (b.duration ?? Infinity)
    if (sortBy.value === 'duration_desc') return (b.duration ?? -1) - (a.duration ?? -1)
    if (sortBy.value === 'score_desc') return (b.total_score ?? -1) - (a.total_score ?? -1)
    return Number(b.is_pinned) - Number(a.is_pinned) || b.started_at - a.started_at
  })
})

onMounted(async () => {
  try {
    records.value = (await getChatHistory()) || []
  } catch (error) {
    console.warn('训练历史加载失败', error)
    loadError.value = '训练历史暂时无法加载，请确认后端服务已启动后重试。'
  } finally {
    loading.value = false
  }
})

function pct(score, max) {
  return Math.max(0, Math.min(100, Math.round((Number(score) / max) * 100)))
}

function sceneKind(row) {
  if (row.scene_title?.includes('梗阻')) return 'choking'
  if (/OSCE|模拟问诊|病例书写/i.test(row.scene_title || '')) return 'osce'
  return 'visit'
}

function dimMax(row, key) {
  const kind = sceneKind(row)
  if (kind === 'osce') return ({ accuracy: 40, warmth: 20, decision: 40 })[key]
  if (kind === 'visit') return ({ accuracy: 30, warmth: 40, decision: 30 })[key]
  return ({ accuracy: 40, warmth: 30, decision: 30 })[key]
}

function scoreClass(score) {
  if (score >= 85) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

async function toggleFlag(row, key) {
  const value = !row[key]
  await updateChatSessionFlags(row.session_id, { [key]: value })
  row[key] = value
}

async function openSummary() {
  summaryVisible.value = true
  summaryLoading.value = true
  try {
    trainingSummary.value = await getTrainingSummary()
  } finally {
    summaryLoading.value = false
  }
}

async function deleteRecord(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除“${row.scene_title}”这次训练吗？对话、教练记录和评分都会删除，且无法恢复。`,
      '删除训练记录',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  deletingSessionId.value = row.session_id
  try {
    await deleteChatSession(row.session_id)
    records.value = records.value.filter((record) => record.session_id !== row.session_id)
    ElMessage.success('训练记录已删除')
  } catch {
    // 请求层已经展示具体错误，这里只负责恢复按钮状态。
  } finally {
    deletingSessionId.value = null
  }
}

function formatDateTime(timestamp) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  const pad = (n) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatDuration(seconds) {
  if (seconds == null) return '--'
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分${seconds % 60}秒`
  return `${Math.floor(minutes / 60)}小时${minutes % 60}分`
}
</script>

<style scoped lang="scss">
.history-view { min-height: 100vh; background: linear-gradient(180deg, #f4f7fa, #eef2f6); }
.history-container { max-width: 1440px; margin: 0 auto; padding: 36px 24px 60px; min-height: 600px; }
.load-alert { margin-bottom: 20px; }

.history-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 22px;
  .eyebrow { color: #54778e; font-size: 11px; font-weight: 800; letter-spacing: 0.14em; }
  h1 { margin: 4px 0; color: #172d3c; font-size: 32px; }
  p { margin: 0; color: #6c8190; }
}
.heading-actions { display: flex; gap: 8px; }
.heading-actions :deep(.el-button) { margin: 0; }
.heading-actions :deep(.el-button > span) { display: inline-flex; align-items: center; gap: 8px; }
.history-filters { display: grid; grid-template-columns: repeat(3, minmax(0, 220px)); gap: 10px; margin-bottom: 16px; }
.summary-report h3 { margin: 0 0 18px; color: #24485f; line-height: 1.65; }
.summary-report section { margin: 14px 0; padding: 14px 16px; border-radius: 12px; background: #f5f9fc; }
.summary-report section strong { color: #285a76; }
.summary-report section p { margin: 8px 0 0; color: #506979; line-height: 1.6; }
.scene-summary { display: flex; justify-content: space-between; padding: 10px 4px; border-bottom: 1px solid #e7edf1; color: #597182; }
.history-card.pinned { border-color: #e4b85d; box-shadow: 0 7px 20px rgba(190, 137, 35, 0.1); }

.history-table { border: 1px solid #dfe6eb; border-radius: 16px; overflow: hidden; }
.history-cards { display: none; }
.record-actions { display: flex; align-items: center; justify-content: center; gap: 4px; }
.record-actions .el-button + .el-button { margin-left: 0; }
.scene-cell { display: flex; align-items: center; gap: 8px; color: #2f4c5e; font-weight: 600; }
.scene-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
.scene-dot.choking { background: #e55b48; }
.scene-dot.visit { background: #2c7be5; }
.scene-dot.osce { background: #168f83; }
.muted { color: #9aa9b4; }

.score-high { color: #1f9d63; }
.score-mid { color: #c78312; }
.score-low { color: #d9503d; }

.dim-bars { display: flex; flex-direction: column; gap: 5px; }
.dim-bar { display: grid; grid-template-columns: 34px 1fr 30px; align-items: center; gap: 8px; font-size: 12px; color: #617787; }
.dim-bar b { color: #294656; text-align: right; }

@media (max-width: 640px) {
  .history-container { padding: 24px 12px 40px; }
  .history-heading { align-items: center; gap: 12px; }
  .history-heading h1 { font-size: 26px; }
  .history-heading p { display: none; }
  .history-heading :deep(.el-button) { width: 100%; min-height: 40px; margin: 0; padding-inline: 12px; }
  .heading-actions { flex: 0 0 136px; flex-direction: column-reverse; align-items: stretch; gap: 8px; }
  .history-filters { grid-template-columns: 1fr; }
  .history-table { display: none; }
  .history-cards { display: grid; gap: 12px; }
  .history-card { padding: 15px; border: 1px solid #dfe6eb; border-radius: 14px; background: #fff; box-shadow: 0 7px 20px rgba(40, 61, 75, 0.05); }
  .mobile-card-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  .mobile-card-heading .scene-cell { min-width: 0; }
  .mobile-card-heading .scene-cell strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .mobile-facts { display: grid; grid-template-columns: 1.5fr 0.8fr 0.55fr; gap: 8px; margin: 14px 0 0; }
  .mobile-facts div { min-width: 0; padding: 9px 8px; border-radius: 9px; background: #f5f8fa; }
  .mobile-facts dt { margin-bottom: 4px; color: #8294a1; font-size: 10px; }
  .mobile-facts dd { margin: 0; color: #334f60; font-size: 12px; overflow-wrap: anywhere; }
  .mobile-dim-bars { margin-top: 13px; padding-top: 12px; border-top: 1px solid #edf1f4; }
  .mobile-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
  .mobile-actions :deep(.el-button) { width: 100%; min-height: 38px; margin: 0; }
  .mobile-actions :deep(.el-button:nth-child(-n+2)) { width: auto; flex: 1; }
}
</style>
