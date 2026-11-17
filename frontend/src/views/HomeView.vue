<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PostCard from '../components/PostCard.vue'
import EmptyState from '../components/EmptyState.vue'
import { postsApi, diariesApi, statsApi } from '../api/index.js'
import { siteStore } from '../store/site.js'
import { formatDate, excerpt } from '../utils/format.js'

const featured = ref([])
const latest = ref([])
const notes = ref([])
const stats = ref({})

const KIND = { diary: '日记', essay: '随笔', note: '学习' }

const author = computed(() => siteStore.settings.author_name || siteStore.settings.site_name || '朋友')
const intro = computed(() => siteStore.settings.site_desc || '一个安静的程序员角落，记录文章、随笔与生活。')

const statCards = computed(() => [
  { label: '文章', value: stats.value.posts ?? '—', icon: 'layers' },
  { label: '精选', value: featured.value.length || '—', icon: 'spark' },
  { label: '记录', value: stats.value.diaries ?? '—', icon: 'pen' },
  { label: '访问', value: stats.value.total_pv ?? '—', icon: 'eye' },
])

onMounted(async () => {
  const jobs = [
    postsApi.list({ featured: true, page_size: 3 }).then((r) => (featured.value = r.items || [])).catch(() => {}),
    postsApi.list({ page_size: 6 }).then((r) => (latest.value = r.items || [])).catch(() => {}),
    diariesApi.list({ page_size: 3 }).then((r) => (notes.value = r.items || [])).catch(() => {}),
    statsApi.summary().then((r) => (stats.value = r || {})).catch(() => {}),
  ]
  await Promise.allSettled(jobs)
  if (!featured.value.length) featured.value = latest.value.slice(0, 3)
})
</script>

<template>
  <div class="animate-rise">
    <section class="glass relative overflow-hidden rounded-3xl px-6 py-12 sm:px-10 sm:py-16">
      <div class="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full bg-accent/10 blur-3xl"></div>
      <div class="relative grid gap-10 lg:grid-cols-[1.25fr_0.75fr] lg:items-center">
        <div>
          <div class="glass-lens glass-lens--pill mb-6 inline-flex items-center gap-2 px-3.5 py-1.5 font-mono text-[11px] text-muted">
            <span class="h-1.5 w-1.5 rounded-full bg-success shadow-[0_0_8px_var(--success)]"></span>
            PERSONAL SPACE · 2026
          </div>
          <h1 class="text-[30px] font-semibold leading-[1.2] tracking-tight sm:text-5xl">
            你好，这里是<span class="bg-gradient-to-r from-accent to-accent-purple bg-clip-text text-transparent">{{ author }}</span>
          </h1>
          <p class="mt-6 max-w-xl text-[15px] leading-[1.9] text-muted">{{ intro }}</p>
          <div class="mt-8 flex flex-wrap items-center gap-3">
            <router-link to="/posts" class="btn btn-primary">
              阅读文章 <AppIcon name="arrowUp" :size="15" class="rotate-90" />
            </router-link>
            <router-link to="/about" class="btn">关于我</router-link>
          </div>
        </div>

        <div class="glass-soft hidden overflow-hidden font-mono text-[12px] leading-6 text-muted lg:block">
          <div class="flex items-center gap-2 border-b border-line px-4 py-3">
            <span class="h-2.5 w-2.5 rounded-full bg-danger/70"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-accent/60"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-success/70"></span>
            <span class="ml-3 text-[11px] text-faint">~/little-home/profile.ts</span>
          </div>
          <pre class="overflow-x-auto p-5"><code><span class="text-accent-2">const</span> me = {
  role: <span class="text-accent-3">'developer'</span>,
  focus: [<span class="text-accent-3">'web'</span>, <span class="text-accent-3">'systems'</span>],
  writing: <span class="text-accent-2">true</span>,
  coffee: <span class="text-accent-2">Infinity</span>,
}

<span class="text-faint">// 保持好奇，保持简单。</span>
<span class="text-accent-2">export default</span> me</code></pre>
        </div>
      </div>
    </section>

    <section class="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
      <div v-for="s in statCards" :key="s.label" class="glass glass--lens flex items-center gap-3.5 px-4 py-4 sm:px-5">
        <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/[0.06] text-accent shadow-[inset_0_1px_0_rgba(255,255,255,.14)]">
          <AppIcon :name="s.icon" :size="18" />
        </div>
        <div class="min-w-0">
          <div class="font-mono text-xl font-semibold text-ink">{{ s.value }}</div>
          <div class="text-[11px] text-faint">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <section class="mt-16">
      <div class="mb-6 flex items-end justify-between">
        <div>
          <p class="section-kicker mb-2">FEATURED</p>
          <h2 class="text-xl font-semibold sm:text-2xl">精选内容</h2>
        </div>
        <router-link to="/posts" class="hidden text-xs text-muted hover:text-accent sm:block">全部文章 →</router-link>
      </div>
      <div v-if="featured.length" class="grid gap-4 md:grid-cols-3">
        <PostCard v-for="p in featured" :key="p.id" :post="p" featured />
      </div>
      <EmptyState v-else icon="spark" title="还没有精选文章" desc="在后台把喜欢的文章标记为精选，就会出现在这里。" />
    </section>

    <section class="mt-16">
      <div class="mb-6 flex items-end justify-between">
        <div>
          <p class="section-kicker mb-2">LATEST</p>
          <h2 class="text-xl font-semibold sm:text-2xl">最近更新</h2>
        </div>
        <router-link to="/posts" class="text-xs text-muted hover:text-accent">查看全部 →</router-link>
      </div>
      <div class="glass divide-y divide-line overflow-hidden">
        <router-link
          v-for="p in latest"
          :key="p.id"
          :to="`/posts/${p.id}`"
          class="group flex items-start gap-4 px-5 py-5 transition-colors hover:bg-white/[0.02] sm:px-6"
        >
          <div class="hidden w-24 shrink-0 pt-1 font-mono text-[11px] text-faint sm:block">{{ formatDate(p.created_at) }}</div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span v-if="p.featured" class="rounded bg-accent/10 px-1.5 py-0.5 text-[10px] text-accent">精选</span>
              <h3 class="truncate text-[15px] font-medium text-ink transition-colors group-hover:text-accent">{{ p.title }}</h3>
            </div>
            <p class="mt-1.5 line-clamp-1 text-[13px] text-muted sm:line-clamp-2">{{ excerpt(p.excerpt, 120) }}</p>
            <div class="mt-2 flex items-center gap-3 text-[11px] text-faint sm:hidden">
              <span>{{ formatDate(p.created_at) }}</span>
              <span v-if="p.category_name">{{ p.category_name }}</span>
            </div>
          </div>
          <AppIcon name="chevronRight" :size="16" class="mt-2 shrink-0 text-faint transition-transform group-hover:translate-x-1 group-hover:text-accent" />
        </router-link>
        <div v-if="!latest.length" class="px-6 py-12 text-center text-sm text-muted">还没有发布文章。</div>
      </div>
    </section>

    <section class="mt-16">
      <div class="mb-6 flex items-end justify-between">
        <div>
          <p class="section-kicker mb-2">NOTES</p>
          <h2 class="text-xl font-semibold sm:text-2xl">生活切片</h2>
        </div>
        <router-link to="/diary" class="text-xs text-muted hover:text-accent">全部记录 →</router-link>
      </div>
      <div class="grid gap-4 md:grid-cols-3">
        <router-link
          v-for="n in notes"
          :key="n.id"
          to="/diary"
          class="glass glass-hover flex flex-col p-5"
        >
          <div class="mb-3 flex items-center gap-2 text-[11px] text-faint">
            <span class="rounded-full bg-accent/10 px-2 py-0.5 text-accent">{{ KIND[n.kind] || '记录' }}</span>
            <span>{{ formatDate(n.created_at) }}</span>
          </div>
          <h3 class="text-[15px] font-medium text-ink">{{ n.title || '无题' }}</h3>
          <p class="mt-2 line-clamp-3 text-[13px] leading-relaxed text-muted">{{ excerpt(n.content, 110) }}</p>
        </router-link>
        <div v-if="!notes.length" class="glass col-span-full px-6 py-10 text-center text-sm text-muted">还没有写下记录。</div>
      </div>
    </section>
  </div>
</template>
