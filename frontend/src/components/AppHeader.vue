<template>
  <header class="app-header">
    <div class="header-container">
      <router-link to="/" class="logo">
        <img class="logo-icon" :src="brandIcon" alt="" aria-hidden="true" />
        <span class="logo-text">“易”生伴</span>
      </router-link>

      <nav class="nav-menu">
        <router-link to="/" class="nav-item">训练场景</router-link>
        <router-link to="/history" class="nav-item">训练历史</router-link>
        <router-link to="/profile" class="nav-item">个人中心</router-link>
      </nav>

      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <span v-if="quota" class="quota-pill" :class="{ exhausted: quota.exhausted }" :title="quota.message || '按大模型估算费用计算'">
            <span class="quota-copy"><small>今日剩余</small><b>{{ remainingPercent }}%</b></span>
            <span class="quota-track" aria-hidden="true"><i :style="{ width: `${remainingPercent}%` }" /></span>
          </span>
          <el-dropdown @command="onCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar_url">
                {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">{{ userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="$router.push('/login')">登录</el-button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import brandIcon from '@/assets/images/brand-dialogue.svg'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getDailyQuota } from '@/api/user'

const router = useRouter()
const userStore = useUserStore()
const quota = ref(null)
const remainingPercent = computed(() => Math.max(0, Math.min(100, 100 - Number(quota.value?.percent || 0))))

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  try { quota.value = await getDailyQuota() } catch { /* 顶栏增强信息失败不影响使用 */ }
})

async function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    try {
      // 先让路由守卫处理易心当前对话的保存确认；确认离开后再清理登录态，
      // 避免用户点“取消”时已经被登出。
      const navigation = await router.push('/login')
      if (navigation) return
      userStore.logout()
    } catch {
      // 用户取消
    }
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.app-header {
  background: white;
  border-bottom: 1px solid $border;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: $shadow-sm;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 $spacing-lg;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  text-decoration: none;
  color: $primary;
  flex-shrink: 0;

  .logo-icon {
    width: 28px; height: 25px; object-fit: contain; flex-shrink: 0;
  }

  .logo-text {
    font-size: $fs-xl;
    font-weight: 600;
    white-space: nowrap;
  }
}

.nav-menu {
  display: flex;
  gap: $spacing-xl;

  .nav-item {
    color: $text-primary;
    text-decoration: none;
    font-size: $fs-base;
    padding: $spacing-xs 0;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    white-space: nowrap;

    &:hover {
      color: $primary;
    }

    &.router-link-active {
      color: $primary;
      border-bottom-color: $primary;
    }
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  cursor: pointer;
  padding: $spacing-xs $spacing-sm;
  border-radius: $radius;
  transition: background 0.2s;

  &:hover {
    background: $bg;
  }

  .username {
    color: $text-primary;
    font-size: $fs-base;
  }
}
.header-right { display: flex; align-items: center; gap: 8px; }
.quota-pill {
  width: 104px;
  padding: 6px 9px 7px;
  border: 1px solid #d8ece4;
  border-radius: 13px;
  background: linear-gradient(135deg, #f6fcf9, #eaf7f1);
  color: #28745a;
  white-space: nowrap;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}
.quota-copy { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; }
.quota-copy small { font-size: 9px; letter-spacing: .04em; }
.quota-copy b { font-size: 12px; }
.quota-track { display: block; height: 4px; margin-top: 4px; overflow: hidden; border-radius: 99px; background: rgba(40,116,90,.12); }
.quota-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #58c49c, #2b8fc5); transition: width .35s ease; }
.quota-pill.exhausted { background: #fff2df; color: #a46516; }
.quota-pill.exhausted .quota-track i { background: #e5a43c; }

@media (max-width: 980px) {
  .header-container {
    height: 58px;
    padding: 0 12px;
    gap: 7px;
  }

  .logo {
    gap: 5px;

    .logo-icon { width: 22px; height: 20px; }
    .logo-text { font-size: 14px; white-space: nowrap; }
  }

  .nav-menu {
    flex: 1;
    justify-content: center;
    gap: 9px;

    .nav-item { font-size: 12px; white-space: nowrap; }
  }

  .user-info {
    padding: 2px;

    .username,
    > .el-icon {
      display: none;
    }
  }
  .header-right { gap: 5px; flex-shrink: 0; }
  .user-info :deep(.el-avatar) { width: 28px; height: 28px; }
  .quota-pill { width: 42px; padding: 5px 5px 6px; flex-shrink: 0; }
  .quota-copy small { display: none; }
  .quota-copy { justify-content: center; }
  .quota-copy b { font-size: 10px; }
}

@media (max-width: 380px) {
  .header-container { padding-inline: 8px; gap: 6px; }
  .logo .logo-text { display: none; }
  .nav-menu { gap: 10px; }
  .nav-menu .nav-item { font-size: 12px; }
  .quota-pill { display: none; }
}
</style>
