<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import { postsApi } from '../api/index.js'

const items = ref([])
const grouped = computed(() => {
  const map = new Map()
  items.value.forEach((r) => {
    if (!map.has(r.year)) map.set(r.year, [])
    map.get(r.year).push(r)
  })
  return [...map.entries()].sort((a, b) => b[0] - a[0])
})

onMounted(async () => {
  try { items.value = (await postsApi.archives()).items || [] } catch { items.value = [] }
})
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="TIMELINE" title="归档" desc="所有写过的东西，按时间排好放在这里。" />

    <div class="space-y-5">
      <section v-for="[year, months] in grouped" :key="year" class="glass p-6 sm:p-8">
        <div class="mb-6 flex items-baseline gap-3">
          <h2 class="font-mono text-2xl font-semibold text-ink">{{ year }}</h2>
          <span class="text-xs text-faint">{{ months.reduce((s, m) => s + Number(m.count), 0) }} 篇</span>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <router-link
            v-for="m in months"
            :key="m.month"
            :to="`/posts?year=${year}&month=${m.month}`"
            class="glass-soft group flex items-center justify-between px-4 py-3.5 transition-colors hover:border-accent/40"
          >
            <span class="font-mono text-sm text-muted group-hover:text-accent">{{ year }}.{{ m.month }}</span>
            <span class="flex items-center gap-2 text-xs text-faint">
              {{ m.count }} 篇 <AppIcon name="chevronRight" :size="14" class="transition-transform group-hover:translate-x-1" />
            </span>
          </router-link>
        </div>
      </section>
      <div v-if="!grouped.length" class="glass p-12 text-center text-sm text-muted">还没有归档内容。</div>
    </div>
  </div>
</template>
