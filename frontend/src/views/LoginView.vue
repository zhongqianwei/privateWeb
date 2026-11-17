<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { doLogin, doRegister } from '../store/user.js'
import { toast } from '../composables/toast.js'

const route = useRoute()
const router = useRouter()
const mode = ref('login')
const username = ref('')
const password = ref('')
const nickname = ref('')
const busy = ref(false)

async function submit() {
  if (!username.value || !password.value) return toast('请填写账号和密码', 'error')
  busy.value = true
  try {
    if (mode.value === 'login') await doLogin(username.value, password.value)
    else await doRegister(username.value, password.value, nickname.value || undefined)
    toast(mode.value === 'login' ? '欢迎回来' : '账号已创建', 'success')
    router.push(String(route.query.redirect || '/home'))
  } catch (e) {
    toast(e.message || '操作失败', 'error')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center animate-rise">
    <div class="mb-7 text-center">
      <div class="mx-auto mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-accent to-accent-purple font-mono text-xl font-bold text-white shadow-glow">L</div>
      <h1 class="text-2xl font-semibold">{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</h1>
      <p class="mt-2 text-sm text-muted">{{ mode === 'login' ? '登录后可写作与管理小窝' : '第一个注册的账号就是这里的主人' }}</p>
    </div>

    <div class="glass p-7">
      <div class="mb-6 grid grid-cols-2 gap-1 rounded-xl border border-line p-1">
        <button
          v-for="m in [{v:'login',t:'登录'},{v:'register',t:'注册'}]"
          :key="m.v"
          class="rounded-lg py-2 text-sm transition-colors"
          :class="mode === m.v ? 'bg-accent/10 text-accent' : 'text-muted hover:text-ink'"
          @click="mode = m.v"
        >{{ m.t }}</button>
      </div>

      <form class="space-y-4" @submit.prevent="submit">
        <div>
          <label class="mb-2 block text-xs text-muted">用户名</label>
          <input v-model="username" class="input" autocomplete="username" placeholder="3–20 个字符" />
        </div>
        <div v-if="mode === 'register'">
          <label class="mb-2 block text-xs text-muted">昵称（可选）</label>
          <input v-model="nickname" class="input" placeholder="怎么称呼你" />
        </div>
        <div>
          <label class="mb-2 block text-xs text-muted">密码</label>
          <input v-model="password" type="password" class="input" autocomplete="current-password" placeholder="至少 6 位" @keyup.enter="submit" />
        </div>
        <button type="submit" class="btn btn-primary w-full" :disabled="busy">
          <AppIcon name="arrowUp" :size="15" class="rotate-90" /> {{ busy ? '请稍候…' : (mode === 'login' ? '登录' : '注册并登录') }}
        </button>
      </form>

      <p class="mt-5 text-center text-[11px] leading-relaxed text-faint">
        密码使用 PBKDF2 加盐哈希存储，登录态由 JWT 维持。
      </p>
    </div>
  </div>
</template>
