<script setup>
import { computed } from 'vue'

/** 头像：有图显示图片，无图用昵称首字 + 稳定渐变占位。点击可进个人空间。 */
const props = defineProps({
  user: { type: Object, default: null },
  size: { type: Number, default: 36 },
  name: { type: String, default: '' },
  to: { type: [String, null], default: null }, // 传入 '/u/1' 则可点击
  ring: { type: Boolean, default: false },
})

const displayName = computed(() => props.name || props.user?.nickname || props.user?.username || '匿')
const initial = computed(() => Array.from(displayName.value)[0]?.toUpperCase() || '匿')
const avatarUrl = computed(() => props.user?.avatar || '')

// 依据名字生成稳定的色相，保证同一个人颜色一致
const hue = computed(() => {
  let h = 0
  for (const ch of displayName.value) h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
})
const gradient = computed(() =>
  `linear-gradient(135deg, hsl(${hue.value} 70% 62%), hsl(${(hue.value + 42) % 360} 68% 48%))`
)
const style = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  fontSize: `${Math.max(11, Math.round(props.size * 0.42))}px`,
}))
</script>

<template>
  <component
    :is="to ? 'router-link' : 'span'"
    :to="to || undefined"
    class="avatar inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold text-white"
    :class="[ring ? 'avatar-ring' : '', to ? 'avatar-link' : '']"
    :style="style"
    :aria-label="displayName"
  >
    <img v-if="avatarUrl" :src="avatarUrl" :alt="displayName" class="h-full w-full object-cover" loading="lazy" />
    <span v-else class="grid h-full w-full place-items-center" :style="{ background: gradient }">{{ initial }}</span>
  </component>
</template>

<style scoped>
.avatar { box-shadow: inset 0 1px 0 rgba(255,255,255,.25), 0 1px 3px rgba(0,0,0,.18); }
.avatar-ring { outline: 2px solid rgb(var(--accent-rgb, 99 102 241) / .6); outline-offset: 2px; }
.avatar-link { transition: transform .2s ease, box-shadow .2s ease; }
.avatar-link:hover { transform: translateY(-2px) scale(1.04); box-shadow: 0 4px 12px rgba(0,0,0,.25); }
</style>
