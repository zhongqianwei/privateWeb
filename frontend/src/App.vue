<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import SiteFooter from './components/SiteFooter.vue'
import GlassFilters from './components/GlassFilters.vue'
import GlassControls from './components/GlassControls.vue'
import { toastState } from './composables/toast.js'
import { fetchSettings } from './store/site.js'
import { applyGlass, autoDowngradeIfWeak } from './store/glass.js'

const route = useRoute()
const progress = ref(0)
let ticking = false
let scrollIdle = 0

/* 滚动期间把 SVG 位移折射降级成纯模糊：位移贴图每帧重算是最贵的一环，
   而滚动时人眼看不出边缘弯折；停下 140ms 后自动恢复完整玻璃。 */
function markScrolling() {
  const root = document.documentElement
  if (root.dataset.scrolling !== '1') root.dataset.scrolling = '1'
  clearTimeout(scrollIdle)
  scrollIdle = setTimeout(() => { root.dataset.scrolling = '0' }, 140)
}

function onScroll() {
  markScrolling()
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
  // 等滤镜节点渲染后再同步参数。弱机判定交给 autoDowngradeIfWeak
  // 内部的 WebGL/硬件信号（比首屏 rAF 帧率准得多，不会误伤真显卡）。
  requestAnimationFrame(() => {
    applyGlass()
    autoDowngradeIfWeak()
  })
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  clearTimeout(scrollIdle)
})
</script>

<template>
  <!-- 弥散光背景：纯 CSS 静态径向渐变，无任何图片 / 实体图案 / 逐帧动画 -->
  <div class="ambient" aria-hidden="true"></div>
  <div class="grain" aria-hidden="true"></div>

  <!-- 四层物理玻璃滤镜定义 + 参数面板 -->
  <GlassFilters />
  <GlassControls />

  <div
    class="pointer-events-none fixed inset-x-0 top-0 z-[90] h-[2px] origin-left bg-gradient-to-r from-accent via-accent-purple to-accent-cyan will-change-transform"
    :style="{ transform: `scaleX(${progress})` }"
  ></div>

  <div class="relative flex min-h-screen flex-col">
    <NavBar v-if="showChrome" />

    <main class="mx-auto w-full max-w-content flex-1 px-5 pb-20 pt-10 sm:px-8 sm:pt-14">
      <router-view v-slot="{ Component, route }">
        <!-- 进场动画完全交给视图根节点的 .animate-rise：
             新页面挂载即浮入，无 out-in 空窗、无 transition/animation 叠加打架。
             key 用完整路径，确保导航到同一组件不同参数时也会重新触发进场。 -->
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
