import { computed, reactive } from 'vue'
import { authApi, getToken, setToken, clearToken } from '../api/index.js'

/** 极简用户状态（Vue3 reactive，不引入 pinia） */
export const userStore = reactive({
  user: null, // { id, username, nickname, avatar, is_admin }
  ready: false,
})

/** 是否管理员（后端权威判定，前端只用于展示与路由拦截） */
export const isAdmin = computed(() => Boolean(userStore.user?.is_admin))

let initPromise = null

/** 启动/守卫共用：只实际请求一次（幂等） */
export async function initUser() {
  if (userStore.ready) return
  if (!initPromise) {
    initPromise = (async () => {
      if (!getToken()) {
        userStore.ready = true
        return
      }
      try {
        const { user } = await authApi.me()
        userStore.user = user
      } catch {
        userStore.user = null
      }
      userStore.ready = true
    })()
  }
  await initPromise
}

export async function doLogin(username, password) {
  const r = await authApi.login({ username, password })
  setToken(r.token)
  userStore.user = r.user
  return r.user
}

export async function doRegister(username, password, nickname) {
  const r = await authApi.register({ username, password, nickname })
  setToken(r.token)
  userStore.user = r.user
  return r.user
}

export async function updateProfile(data) {
  const r = await authApi.updateProfile(data)
  if (r.user) userStore.user = r.user
  return r.user
}

export async function uploadAvatar(file) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await authApi.uploadAvatar(fd)
  if (r.avatar && userStore.user) userStore.user.avatar = r.avatar
  return r.avatar
}

export function doLogout() {
  clearToken()
  userStore.user = null
}

// 401 全局监听（token 过期）
window.addEventListener('lh:logout', () => {
  userStore.user = null
})
