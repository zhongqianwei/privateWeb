import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import { initUser } from './store/user.js'
import './style.css'

const app = createApp(App)
app.use(router)

// 主题在 index.html 里已同步设置，避免首屏闪白；这里只恢复登录态，不阻塞渲染
app.mount('#app')
initUser()
