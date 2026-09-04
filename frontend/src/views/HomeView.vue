<template>
  <div class="home-view">
    <AppHeader />

    <div class="home-container">
      <div class="home-hero">
        <h1>您好，欢迎来到“易”生伴！很高兴与您见面！</h1>
        <p>训练急救对话能力，或让 AI 陪你说说话、纾解心情</p>
      </div>

      <!-- 心理陪伴入口横幅 -->
      <div class="psych-banner" @click="router.push('/psych')">
        <div class="psych-avatar" aria-hidden="true">
          <span class="psych-emoji">🧡</span>
        </div>
        <div class="psych-info">
          <h2>心理陪伴 · 易心</h2>
          <p>不开心、压力大、心里堵得慌的时候，有个人愿意安静听你说说话。</p>
          <el-tag size="small" type="warning" effect="light" class="psych-tag">
            倾听 / 共情 / 情绪疏导
          </el-tag>
        </div>
        <el-button type="warning" round class="psych-btn">
          <el-icon><ChatDotRound /></el-icon>
          找易心聊聊
        </el-button>
      </div>

      <h2 class="section-title">场景对话训练</h2>

      <div class="scene-grid">
        <el-empty
          v-if="!scenes.length && !loading"
          description="暂无可用场景，请等待后端接入"
        />

        <el-skeleton v-else-if="loading" :rows="3" animated />

        <el-card
          v-for="scene in scenes"
          :key="scene.id"
          class="scene-card"
          shadow="hover"
          @click="enterScene(scene)"
        >
          <div class="scene-cover">
            <el-image
              :src="sceneCover(scene)"
              fit="cover"
              class="cover-img"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>

          <div class="scene-info">
            <h3>{{ scene.title }}</h3>
            <p class="scene-desc">{{ scene.description }}</p>

            <div class="scene-meta">
              <el-tag size="small" type="info">
                <el-icon><User /></el-icon>
                扮演：{{ traineeRole(scene) }}
              </el-tag>
              <span class="difficulty-rate">
                <span class="difficulty-label">难度</span>
                <el-rate
                  v-model="scene.difficulty"
                  disabled
                  :max="5"
                  size="small"
                />
              </span>
            </div>

            <el-button type="primary" class="enter-btn">
              <el-icon><Promotion /></el-icon>
              进入对话
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import { getSceneList } from '@/api/scene'
import defaultCover from '@/assets/images/default-scene.svg'
import chokingCover from '@/assets/images/scene-choking-cover.webp'
import firstVisitCover from '@/assets/images/scene-first-visit-cover.webp'
import osceCover from '@/assets/images/scene-osce-cover.webp'

const router = useRouter()
const scenes = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getSceneList()
    scenes.value = res || []
  } catch (err) {
    console.warn('场景列表加载失败，使用占位数据', err)
    // 占位数据（后端未就绪时显示）
    scenes.value = [
      {
        id: 1,
        title: '异物梗阻急救',
        description: '面对突发异物梗阻患者，进行海姆立克急救法指导与情绪安抚',
        cover: '',
        role: '成人患者',
        difficulty: 4
      },
      {
        id: 2,
        title: '第一次独立看病',
        description: '以江苏省人民医院为背景，体验第一次独立看病中的关键决策与沟通',
        cover: '',
        role: '医院流程角色',
        difficulty: 2
      },
      {
        id: 3,
        title: 'OSCE模拟问诊与病历书写',
        description: '以问诊为核心，训练规范病史采集、临床归纳和独立病历书写',
        cover: '',
        role: '标准化患者',
        difficulty: 5
      }
    ]
  } finally {
    loading.value = false
  }
})

function enterScene(scene) {
  router.push(`/chat/${scene.id}`)
}

// 核心训练场景使用专属封面，其他场景仍兼容后端配置的图片。
function sceneCover(scene) {
  if (scene.title?.includes('异物梗阻')) return chokingCover
  if (scene.title?.includes('第一次独立看病')) return firstVisitCover
  if (/OSCE|模拟问诊|病例书写/i.test(scene.title || '')) return osceCover
  return scene.cover || defaultCover
}

// 场景卡展示的是学生将扮演的角色（急救者/患者），AI 角色在对话页另有标注
function traineeRole(scene) {
  if (/OSCE|模拟问诊|病例书写/i.test(scene.title || '')) return '接诊医生'
  if (scene.title?.includes('独立看病') || (scene.role || '').includes('医院流程')) return '患者'
  if (scene.title?.includes('梗阻') || (scene.role || '').includes('患者')) return '急救者'
  return scene.role || '训练者'
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.home-view {
  min-height: 100vh;
  background: $bg;
}

.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg;
}

.home-hero {
  text-align: center;
  margin-bottom: $spacing-xl;

  h1 {
    font-size: 32px;
    color: $text-primary;
    margin: 0 0 $spacing-sm;
  }

  p {
    color: $text-secondary;
    margin: 0;
  }
}

// 心理陪伴入口横幅
.psych-banner {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  background: linear-gradient(120deg, #fff7ed 0%, #ffedd5 60%, #fde9d0 100%);
  border: 1px solid #fbd9a8;
  border-radius: $radius-lg;
  padding: $spacing-lg $spacing-xl;
  margin-bottom: $spacing-xl;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(249, 115, 22, 0.14);
  }

  .psych-avatar {
    flex: 0 0 auto;
    width: 84px;
    height: 84px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #fb923c, #f97316);
    box-shadow: 0 6px 16px rgba(249, 115, 22, 0.35);

    .psych-emoji {
      font-size: 44px;
      line-height: 1;
    }
  }

  .psych-info {
    flex: 1;
    min-width: 0;

    h2 {
      margin: 0 0 6px;
      font-size: $fs-xl;
      color: #7c2d12;
    }

    p {
      margin: 0 0 10px;
      color: #9a3412;
      font-size: $fs-base;
    }

    .psych-tag {
      border-radius: 999px;
    }
  }

  .psych-btn {
    flex: 0 0 auto;
  }
}

.section-title {
  font-size: $fs-xl;
  color: $text-primary;
  margin: 0 0 $spacing-lg;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: $spacing-lg;
}

.scene-card {
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: $radius-lg;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
  }

  .scene-cover {
    // el-card 内容区默认左右各有 20px 内边距。封面通过负边距贴边时，
    // 宽度也要补回这 40px，否则右侧会固定留下空白。
    width: calc(100% + 40px);
    height: 180px;
    overflow: hidden;
    border-radius: $radius $radius 0 0;
    margin: -20px -20px $spacing;

    :deep(.cover-img) {
      width: 100%;
      height: 100%;
    }

    .image-error {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #E8F0FE 0%, #F5F7FA 100%);
      color: $primary;
      font-size: 40px;
    }
  }

  .scene-info {
    h3 {
      margin: 0 0 $spacing-sm;
      font-size: $fs-lg;
      color: $text-primary;
    }

    .scene-desc {
      color: $text-secondary;
      margin: 0 0 $spacing;
      min-height: 44px;
      font-size: $fs-base;
    }

    .scene-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing;
    }

    .difficulty-rate {
      display: inline-flex;
      align-items: center;
      gap: 5px;

      .difficulty-label {
        color: $text-secondary;
        font-size: $fs-sm;
      }
    }

    .enter-btn {
      width: 100%;
    }
  }
}

@media (max-width: 640px) {
  .home-container {
    padding: 22px 14px 40px;
  }

  .home-hero {
    margin-bottom: 20px;
    text-align: left;

    h1 {
      margin-bottom: 8px;
      font-size: clamp(25px, 7.4vw, 30px);
      line-height: 1.35;
      letter-spacing: -0.02em;
    }

    p {
      font-size: 14px;
      line-height: 1.65;
    }
  }

  .psych-banner {
    display: grid;
    grid-template-columns: 58px minmax(0, 1fr);
    gap: 12px;
    padding: 16px;
    margin-bottom: 24px;
    border-radius: 16px;

    .psych-avatar {
      width: 58px;
      height: 58px;

      .psych-emoji { font-size: 30px; }
    }

    .psych-info {
      h2 { font-size: 18px; }
      p { margin-bottom: 8px; font-size: 14px; line-height: 1.55; }
    }

    .psych-btn {
      grid-column: 1 / -1;
      width: 100%;
      min-height: 42px;
      margin: 2px 0 0;
    }
  }

  .section-title {
    margin-bottom: 14px;
    font-size: 20px;
  }

  .scene-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }

  .scene-card {
    .scene-cover { height: 160px; }
    .scene-info .scene-desc { min-height: 0; line-height: 1.6; }
    .scene-info .scene-meta { flex-wrap: wrap; gap: 10px; }
  }
}
</style>
