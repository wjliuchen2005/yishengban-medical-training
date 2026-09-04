import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getProfile as apiGetProfile } from '@/api/auth'

/**
 * 用户状态管理
 * 存储 token 和用户信息
 *
 * 后端接口位置：
 * - 登录：POST /api/auth/login
 * - 获取当前用户：GET /api/auth/me
 */
export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('yishengban_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('yishengban_user') || 'null'))

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')

  /**
   * 登录
   * @param {Object} credentials - { username, password }
   */
  async function login(credentials) {
    const res = await apiLogin(credentials)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('yishengban_token', res.token)
    localStorage.setItem('yishengban_user', JSON.stringify(res.user))
    return res
  }

  /**
   * 登出
   */
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('yishengban_token')
    localStorage.removeItem('yishengban_user')
  }

  /**
   * 刷新当前用户信息（从后端重新拉取）
   * 后端接口：GET /api/auth/me
   */
  async function refreshProfile() {
    const res = await apiGetProfile()
    user.value = res
    localStorage.setItem('yishengban_user', JSON.stringify(res))
    return res
  }

  return {
    token,
    user,
    isLoggedIn,
    username,
    login,
    logout,
    refreshProfile
  }
})