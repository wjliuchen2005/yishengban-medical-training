import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
// 后端端口可配：VITE_BACKEND_PORT=8001 npm run dev（默认 8000，端口被旧进程占用时可切）
const BACKEND_PORT = process.env.VITE_BACKEND_PORT || 8000

export default defineConfig({
  // 换缓存目录，避免 lockfile 变更后 Vite 批量清理旧 .vite/deps 触发沙箱删除限制
  cacheDir: '.vite-cache',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  css: {
    // 解决 Sass legacy-js-api 警告：强制使用 modern-compiler
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler'
      }
    }
  },
  server: {
    port: 5173,
    open: true,
    proxy: {
      // 路径约定：axios baseURL='/api' + API url='/auth/login' = '/api/auth/login'
      // Vite proxy 收到 '/api/auth/login' 后转发到后端 BACKEND_PORT 端口
      '/api': {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true
      }
    }
  }
})