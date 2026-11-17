<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import { statsApi } from '../api/index.js'

const s = ref({})
const cards = computed(() => [
  { label: '文章总数', value: s.value.posts, icon: 'layers' },
  { label: '记录条数', value: s.value.diaries, icon: 'pen' },
  { label: '照片数量', value: s.value.photos, icon: 'camera' },
  { label: '留言数量', value: s.value.messages, icon: 'chat' },
  { label: '文章阅读', value: s.value.post_views, icon: 'eye' },
  { label: '站点访问', value: s.value.total_pv, icon: 'globe' },
  { label: '今日访问', value: s.value.today_pv, icon: 'clock' },
  { label: '累计字数', value: s.value.words, icon: 'code' },
])
const recent = computed(() => s.value.recent7 || [])
const max = computed(() => Math.max(1, ...recent.value.map((r) => Number(r.count) || 0)))

onMounted(async () => {
  try {
    const r = await statsApi.summary()
    s.value = r || {}
    await statsApi.visit().catch(() => {})
  } catch { s.value = {} }
})
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="NUMBERS" title="统计" desc="一些不重要但有意思的数字。" />

    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div v-for="c in cards" :key="c.label" class="glass p-5">
        <AppIcon :name="c.icon" :size="17" class="mb-4 text-accent" />
        <div class="font-mono text-2xl font-semibold text-ink">{{ c.value ?? '—' }}</div>
        <div class="mt-1 text-[11px] text-faint">{{ c.label }}</div>
      </div>
    </div>

    <section class="glass mt-5 p-6 sm:p-8">
      <div class="mb-7 flex items-baseline justify-between">
        <h2 class="text-sm font-semibold">近 7 天产出</h2>
        <span class="font-mono text-[11px] text-faint">文章 + 记录</span>
      </div>
      <div class="flex h-48 items-end gap-2 sm:gap-4">
        <div v-for="r in recent" :key="r.date" class="group flex flex-1 flex-col items-center gap-2">
          <span class="font-mono text-[10px] text-faint opacity-0 transition-opacity group-hover:opacity-100">{{ r.count }}</span>
          <div
            class="w-full max-w-12 rounded-t-lg bg-gradient-to-t from-accent/30 to-accent transition-all duration-500 hover:from-accent/50"
            :style="{ height: `${Math.max(4, (Number(r.count) / max) * 100)}%` }"
          ></div>
          <span class="font-mono text-[10px] text-faint">{{ r.date }}</span>
        </div>
        <div v-if="!recent.length" class="w-full text-center text-sm text-muted">暂无数据</div>
      </div>
    </section>

    <div class="glass mt-5 flex flex-wrap items-center justify-between gap-4 p-6 text-sm">
      <div class="text-muted">
        本站已运行 <span class="font-mono text-accent">{{ s.days ?? '—' }}</span> 天
        <span v-if="s.since" class="ml-2 font-mono text-xs text-faint">since {{ s.since }}</span>
      </div>
      <div class="text-xs text-faint">{{ s.categories ?? '—' }} 个分类 · {{ s.tags ?? '—' }} 个标签</div>
    </div>
  </div>
</template>
