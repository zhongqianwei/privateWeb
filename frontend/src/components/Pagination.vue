<script setup>
import AppIcon from './AppIcon.vue'
defineProps({
  page: { type: Number, default: 1 },
  pages: { type: Number, default: 1 },
})
const emit = defineEmits(['change'])
</script>

<template>
  <div v-if="pages > 1" class="mt-10 flex items-center justify-center gap-2">
    <button class="btn btn-sm btn-icon" :disabled="page <= 1" @click="emit('change', page - 1)">
      <AppIcon name="chevronLeft" :size="16" />
    </button>
    <template v-for="p in pages" :key="p">
      <button
        v-if="p === 1 || p === pages || Math.abs(p - page) <= 1"
        class="btn btn-sm h-9 w-9 px-0 font-mono"
        :class="p === page ? 'chip-active' : ''"
        @click="emit('change', p)"
      >{{ p }}</button>
      <span
        v-else-if="(p === 2 && page > 3) || (p === pages - 1 && page < pages - 2)"
        class="px-1 text-faint"
      >…</span>
    </template>
    <button class="btn btn-sm btn-icon" :disabled="page >= pages" @click="emit('change', page + 1)">
      <AppIcon name="chevronRight" :size="16" />
    </button>
  </div>
</template>
