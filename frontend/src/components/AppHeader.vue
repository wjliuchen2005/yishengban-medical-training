<template>
  <header class="app-header">
    <div class="header-container">
      <router-link to="/" class="logo">
        <el-icon class="logo-icon"><FirstAidKit /></el-icon>
        <span class="logo-text">“易”生伴</span>
      </router-link>

      <nav class="nav-menu">
        <router-link to="/" class="nav-item">训练场景</router-link>
        <router-link to="/history" class="nav-item">训练历史</router-link>
        <router-link to="/profile" class="nav-item">个人中心</router-link>
      </nav>

      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
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
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

async function onCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定退出登录？', '提示', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning'
      })
      userStore.logout()
      router.push('/login')
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
    font-size: 28px;
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

@media (max-width: 640px) {
  .header-container {
    height: 58px;
    padding: 0 12px;
    gap: 10px;
  }

  .logo {
    gap: 5px;

    .logo-icon { font-size: 22px; }
    .logo-text { font-size: 17px; }
  }

  .nav-menu {
    flex: 1;
    justify-content: center;
    gap: 14px;

    .nav-item { font-size: 13px; }
  }

  .user-info {
    padding: 2px;

    .username,
    > .el-icon {
      display: none;
    }
  }
}

@media (max-width: 360px) {
  .header-container { padding-inline: 8px; gap: 6px; }
  .logo .logo-text { display: none; }
  .nav-menu { gap: 10px; }
  .nav-menu .nav-item { font-size: 12px; }
}
</style>
