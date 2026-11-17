import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base: './'  -> 打包后用相对路径，直接丢 GitHub Pages 子目录也能跑
// proxy       -> 本地开发时把 /api、/uploads 转发到 FastAPI(8000)
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  },
  build: {
    chunkSizeWarningLimit: 500,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router']
        }
      }
    }
  }
})
