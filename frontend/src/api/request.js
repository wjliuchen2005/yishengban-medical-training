import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

/**
 * Axios 实例
 * - baseURL: 后端 API 基础路径
 * - 拦截器：自动加 token、统一错误处理
 */
const request = axios.create({
  baseURL: '/api',  // Vite proxy 会代理到 http://localhost:8000/api
  timeout: 60000,  // AI 对话/评分需要调用大模型，放宽到 60s
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动加 JWT token
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => {
    // 后端约定：{ code: 0, data: ... } 或直接返回数据
    // 这里两种格式都兼容
    if (response.data?.code !== undefined) {
      if (response.data.code === 0) {
        return response.data.data
      } else {
        ElMessage.error(response.data.message || '请求失败')
        return Promise.reject(response.data)
      }
    }
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // 未登录或 token 过期
      ElMessage.error('登录已过期，请重新登录')
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    } else if (error.response?.status === 403) {
      ElMessage.error('没有权限')
    } else if (error.response?.status === 404) {
      ElMessage.error('资源不存在')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default request