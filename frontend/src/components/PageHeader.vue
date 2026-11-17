<script setup>
defineProps({
  kicker: { type: String, default: '' },
  title: { type: String, required: true },
  desc: { type: String, default: '' },
})
</script>

<template>
  <div class="mb-9 animate-rise">
    <p v-if="kicker" class="section-kicker mb-3">{{ kicker }}</p>
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-3xl font-semibold tracking-tight sm:text-[34px]">{{ title }}</h1>
        <p v-if="desc" class="mt-3 max-w-2xl text-sm leading-relaxed text-muted">{{ desc }}</p>
      </div>
      <div v-if="$slots.action" class="shrink-0"><slot name="action" /></div>
    </div>
  </div>
</template>
