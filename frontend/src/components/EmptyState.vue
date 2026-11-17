<script setup>
import AppIcon from './AppIcon.vue'
defineProps({
  icon: { type: String, default: 'spark' },
  title: { type: String, default: '这里还空着' },
  desc: { type: String, default: '' },
})
</script>

<template>
  <div class="glass flex flex-col items-center justify-center px-6 py-16 text-center">
    <div class="mb-5 grid h-14 w-14 place-items-center rounded-2xl border border-line bg-white/[0.03] text-accent">
      <AppIcon :name="icon" :size="24" />
    </div>
    <h3 class="text-base font-semibold text-ink">{{ title }}</h3>
    <p v-if="desc" class="mt-2 max-w-sm text-sm leading-relaxed text-muted">{{ desc }}</p>
    <div v-if="$slots.default" class="mt-6"><slot /></div>
  </div>
</template>
