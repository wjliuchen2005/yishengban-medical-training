import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { stopUnifiedSpeaking } from '@/utils/ttsService'
import { getPsychExitGuard } from '@/utils/psychExitGuard'

const routes = [
  // 登录注册
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录 - “易”生伴', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册 - “易”生伴', requiresAuth: false }
  },

  // 主功能（需登录）
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '场景选择 - “易”生伴', requiresAuth: true, guideText: '欢迎来到训练场景，请选择你想要进行的训练。' }
  },
  {
    path: '/chat/:sceneId',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: '对话训练 - “易”生伴', requiresAuth: true, immersiveAvatar: true }
  },
  {
    path: '/result/:sessionId',
    name: 'Result',
    component: () => import('@/views/ResultView.vue'),
    meta: { title: '评分结果 - “易”生伴', requiresAuth: true, guideText: '训练完成了，我们一起看看本次复盘。' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryView.vue'),
    meta: { title: '训练历史 - “易”生伴', requiresAuth: true, guideText: '温故而知新，欢迎来到历史记录。' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '个人中心 - “易”生伴', requiresAuth: true, guideText: '在这里你可以修改个人信息。' }
  },
  {
    path: '/psych',
    name: 'Psych',
    component: () => import('@/views/PsychView.vue'),
    meta: { title: '心理陪伴 - “易”生伴', requiresAuth: true, immersiveAvatar: true }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳转登录页
router.beforeEach(async (to, from) => {
  if (from.name === 'Psych' && to.name !== 'Psych') {
    const guard = getPsychExitGuard()
    if (guard && !(await guard(to, from))) return false
  }
  // 每次切换页面先停止上一页语音，避免跨页面叠音。
  stopUnifiedSpeaking()
  document.title = to.meta.title || '“易”生伴'
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
