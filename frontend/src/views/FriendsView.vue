<script setup>
import { onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import { friendsApi } from '../api/index.js'

const items = ref([])
onMounted(async () => {
  try { items.value = (await friendsApi.list()).items || [] } catch { items.value = [] }
})
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="LINKS" title="朋友" desc="一些值得常去坐坐的地方。" />

    <div v-if="items.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <a
        v-for="f in items"
        :key="f.id"
        :href="f.url"
        target="_blank"
        rel="noopener"
        class="glass glass-hover group flex items-start gap-4 p-5"
      >
        <div class="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-line bg-white/[0.03] font-mono text-sm text-accent">
          {{ (f.name || '?').slice(0, 1).toUpperCase() }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <h3 class="truncate text-[15px] font-medium text-ink group-hover:text-accent">{{ f.name }}</h3>
            <AppIcon name="link" :size="14" class="text-faint" />
          </div>
          <p class="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted">{{ f.description || f.url }}</p>
          <p class="mt-2 truncate font-mono text-[10px] text-faint">{{ f.url.replace(/^https?:\/\//, '') }}</p>
        </div>
      </a>
    </div>
    <EmptyState v-else icon="link" title="还没有朋友" desc="友情链接可以在后台添加。" />
  </div>
</template>
