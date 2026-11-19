<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import Avatar from './Avatar.vue'
import { userStore, isAdmin, doLogout } from '../store/user.js'
import { siteStore } from '../store/site.js'

const route = useRoute()
const router = useRouter()
const open = ref(false)
const theme = ref(document.documentElement.dataset.theme || 'dark')

const links = [
  { to: '/home', label: '首页', icon: 'home' },
  { to: '/posts', label: '文章', icon: 'layers' },
  { to: '/diary', label: '记录', icon: 'pen' },
  { to: '/gallery', label: '相册', icon: 'camera' },
  { to: '/about', label: '关于', icon: 'user' },
]

const siteName = computed(() => siteStore.settings.site_name || '我的小窝')
const active = (to) => route.path === to || route.path.startsWith(to + '/')
const spacePath = computed(() => (userStore.user ? `/u/${userStore.user.id}` : '/login'))

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  try { localStorage.setItem('lh_theme', theme.value) } catch {}
}

function close() { open.value = false }

async function logout() {
  await doLogout()
  close()
  router.push('/home')
}
</script>

<template>
  <header class="sticky top-0 z-50">
    <div class="absolute inset-0 glass-bar"></div>
    <div class="relative mx-auto flex h-16 w-full max-w-content items-center gap-6 px-5 sm:px-8">
      <router-link to="/home" class="group flex shrink-0 items-center gap-3" @click="close">
        <span class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-accent to-accent-purple text-[15px] font-bold tracking-tight text-white shadow-glow">
          L
        </span>
        <span class="hidden text-[15px] font-semibold tracking-tight text-ink sm:block">{{ siteName }}</span>
      </router-link>

      <nav class="hidden flex-1 items-center gap-1 md:flex">
        <router-link
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          class="relative rounded-lg px-3.5 py-2 text-sm transition-colors duration-200"
          :class="active(l.to) ? 'text-ink' : 'text-muted hover:text-ink'"
        >
          {{ l.label }}
          <span v-if="active(l.to)" class="absolute inset-x-3.5 -bottom-[9px] h-[2px] rounded-full bg-accent"></span>
        </router-link>
      </nav>

      <div class="flex-1 md:hidden"></div>

      <div class="flex items-center gap-1.5">
        <button class="btn btn-icon btn-ghost" title="搜索文章" @click="router.push('/posts?focus=1')">
          <AppIcon name="search" :size="18" />
        </button>
        <button class="btn btn-icon btn-ghost" :title="theme === 'dark' ? '切换浅色' : '切换深色'" @click="toggleTheme">
          <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" :size="18" />
        </button>

        <template v-if="userStore.user">
          <router-link v-if="isAdmin" to="/posts/new" class="btn btn-primary btn-sm hidden sm:inline-flex">
            <AppIcon name="plus" :size="15" /> 写文章
          </router-link>
          <router-link :to="spacePath" class="hidden sm:inline-flex" title="我的空间">
            <Avatar :user="userStore.user" :size="32" ring />
          </router-link>
          <button class="btn btn-icon btn-ghost" title="退出登录" @click="logout">
            <AppIcon name="logout" :size="18" />
          </button>
        </template>
        <router-link v-else to="/login" class="btn btn-sm">登录</router-link>

        <button class="btn btn-icon btn-ghost md:hidden" :aria-label="open ? '关闭菜单' : '打开菜单'" @click="open = !open">
          <AppIcon :name="open ? 'close' : 'menu'" :size="20" />
        </button>
      </div>
    </div>

    <transition name="view-fade">
      <div v-if="open" class="relative border-t border-line md:hidden">
        <div class="absolute inset-0 glass-bar"></div>
        <nav class="relative grid grid-cols-2 gap-2 px-5 py-4 sm:grid-cols-3">
          <router-link
            v-for="l in links"
            :key="l.to"
            :to="l.to"
            class="flex items-center gap-2.5 rounded-xl px-3.5 py-3 text-sm"
            :class="active(l.to) ? 'bg-accent/10 text-accent' : 'text-muted hover:bg-white/5'"
            @click="close"
          >
            <AppIcon :name="l.icon" :size="17" /> {{ l.label }}
          </router-link>
          <router-link v-if="userStore.user" :to="spacePath" class="flex items-center gap-2.5 rounded-xl px-3.5 py-3 text-sm text-muted hover:bg-white/5" @click="close">
            <Avatar :user="userStore.user" :size="20" /> 我的空间
          </router-link>
          <router-link v-if="isAdmin" to="/posts/new" class="flex items-center gap-2.5 rounded-xl bg-accent/10 px-3.5 py-3 text-sm text-accent" @click="close">
            <AppIcon name="plus" :size="17" /> 写文章
          </router-link>
          <router-link v-if="isAdmin" to="/manage" class="flex items-center gap-2.5 rounded-xl px-3.5 py-3 text-sm text-muted hover:bg-white/5" @click="close">
            <AppIcon name="grid" :size="17" /> 后台
          </router-link>
        </nav>
      </div>
    </transition>
  </header>
</template>
