<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import SiteFooter from './components/SiteFooter.vue'
import { toastState } from './composables/toast.js'
import { fetchSettings } from './store/site.js'

const route = useRoute()
const progress = ref(0)
let ticking = false

function onScroll() {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    const doc = document.documentElement
    const max = doc.scrollHeight - window.innerHeight
    progress.value = max > 60 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
    ticking = false
  })
}

const showChrome = computed(() => route.name !== 'not-found')

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  fetchSettings()
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <!-- 弥散光背景：纯 CSS 静态径向渐变，无动画，玻璃可稳定合成 -->
  <div class="ambient" aria-hidden="true"></div>
  <div class="grain" aria-hidden="true"></div>

  <div
    class="pointer-events-none fixed inset-x-0 top-0 z-[90] h-[2px] origin-left bg-gradient-to-r from-accent via-accent-purple to-accent-cyan will-change-transform"
    :style="{ transform: `scaleX(${progress})` }"
  ></div>

  <div class="relative flex min-h-screen flex-col">
    <NavBar v-if="showChrome" />

    <main class="mx-auto w-full max-w-content flex-1 px-5 pb-20 pt-10 sm:px-8 sm:pt-14">
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.fullPath" />
      </router-view>
    </main>

    <SiteFooter v-if="showChrome" />
  </div>

  <!-- 全局 toast -->
  <div class="pointer-events-none fixed bottom-6 left-1/2 z-[100] flex -translate-x-1/2 flex-col items-center gap-2">
    <transition-group name="view-fade">
      <div
        v-for="t in toastState.list"
        :key="t.id"
        class="glass-soft px-4 py-2.5 text-sm text-ink shadow-glass"
        :class="t.type === 'error' ? 'border-danger/50' : t.type === 'success' ? 'border-success/40' : ''"
      >
        {{ t.msg }}
      </div>
    </transition-group>
  </div>
</template>
