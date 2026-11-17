<script setup>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'
import { glassStore, resetGlass } from '../store/glass.js'

const open = ref(false)

const sliders = [
  { key: 'opacity', label: '不透明度', min: 0.12, max: 1, step: 0.01, hint: 'L1 · 越通透越能透出背景' },
  { key: 'scale', label: '折射强度', min: 0, max: 60, step: 1, hint: 'L2 · 位移贴图取色偏移' },
  { key: 'highlight', label: '高光亮度', min: 0, max: 3, step: 0.05, hint: 'L3 · 边缘曲面受光' },
  { key: 'shadow', label: '阴影范围', min: 0, max: 60, step: 1, hint: 'L4 · 与背景板的距离' },
]

/* 轨道已走过的部分点亮，让"玻璃滑槽"像苹果滑块一样有进度感 */
function fillPct(s) {
  const v = Number(glassStore[s.key])
  return ((v - s.min) / (s.max - s.min)) * 100 + '%'
}
</script>

<template>
  <div class="fixed bottom-5 right-5 z-[80] flex flex-col items-end gap-3">
    <transition name="panel-pop">
      <div v-if="open" class="glass-lens glass-lens--deep w-[286px] rounded-2xl p-4">
        <div class="mb-3 flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2 text-sm font-semibold text-ink">
              <AppIcon name="spark" :size="15" class="text-accent" />
              玻璃材质
            </div>
            <p class="mt-0.5 text-[11px] text-muted">四层参数 · 实时调节</p>
          </div>
          <button class="glass-lens glass-lens--circle grid h-8 w-8 place-items-center text-muted hover:text-ink" title="重置参数" @click="resetGlass">
            <AppIcon name="clock" :size="14" />
          </button>
        </div>

        <div class="mb-1 flex items-center justify-between rounded-xl bg-white/[0.03] px-3 py-2">
          <div>
            <div class="text-xs text-ink">启用玻璃折射</div>
            <div class="text-[10px] text-muted">关闭可减少低端设备负载</div>
          </div>
          <button
            class="glass-switch"
            :data-on="glassStore.enabled"
            role="switch"
            :aria-checked="glassStore.enabled"
            aria-label="启用玻璃折射"
            @click="glassStore.enabled = !glassStore.enabled"
          ></button>
        </div>

        <div class="space-y-3 pt-2">
          <label v-for="s in sliders" :key="s.key" class="block">
            <div class="mb-1.5 flex items-baseline justify-between">
              <span class="text-xs text-ink">{{ s.label }}</span>
              <span class="font-mono text-[11px] text-accent">{{ Number(glassStore[s.key]).toFixed(s.step < 1 ? 2 : 0) }}</span>
            </div>
            <input
              v-model.number="glassStore[s.key]"
              type="range"
              class="glass-range"
              :min="s.min" :max="s.max" :step="s.step"
              :style="{ '--fill': fillPct(s) }"
              :aria-label="s.label"
            />
            <span class="mt-1 block text-[10px] text-muted">{{ s.hint }}</span>
          </label>
        </div>
      </div>
    </transition>

    <button
      class="glass-lens glass-lens--circle glass-lens--lite grid h-12 w-12 place-items-center text-ink shadow-lg"
      :title="open ? '收起玻璃设置' : '调节玻璃材质'"
      :aria-expanded="open"
      @click="open = !open"
    >
      <AppIcon :name="open ? 'close' : 'palette'" :size="20" />
    </button>
  </div>
</template>

<style scoped>
.panel-pop-enter-active, .panel-pop-leave-active {
  transition: opacity .22s ease, transform .22s cubic-bezier(.2,.8,.2,1);
  transform-origin: bottom right;
}
.panel-pop-enter-from, .panel-pop-leave-to {
  opacity: 0;
  transform: scale(.92) translateY(8px);
}
</style>
