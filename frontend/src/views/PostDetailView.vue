<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import MarkdownView from '../components/MarkdownView.vue'
import EmptyState from '../components/EmptyState.vue'
import { postsApi } from '../api/index.js'
import { isAdmin } from '../store/user.js'
import { toast } from '../composables/toast.js'
import { formatDate, readingTime } from '../utils/format.js'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const md = ref(null)
const activeId = ref('')

const toc = computed(() => md.value?.toc || [])
const meta = computed(() => [
  { icon: 'clock', text: formatDate(post.value?.created_at) },
  { icon: 'eye', text: `${post.value?.views || 0} 次阅读` },
  { icon: 'bookmark', text: `${readingTime(post.value?.content || '')} 分钟` },
])

async function load() {
  loading.value = true
  activeId.value = ''
  try {
    const res = await postsApi.detail(route.params.id)
    post.value = res.post
    await nextTick()
  } catch {
    post.value = null
  } finally {
    loading.value = false
  }
}

function onScroll() {
  const heads = toc.value
  if (!heads.length) return
  let current = heads[0].id
  for (const h of heads) {
    const el = document.getElementById(h.id)
    if (el && el.getBoundingClientRect().top <= 140) current = h.id
  }
  activeId.value = current
}

function copyLink() {
  navigator.clipboard?.writeText(window.location.href)
    .then(() => toast('链接已复制', 'success'))
    .catch(() => toast('复制失败，请手动复制', 'error'))
}

function jump(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

watch(() => route.params.id, load)
onMounted(() => { load(); window.addEventListener('scroll', onScroll, { passive: true }) })
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <div v-if="loading" class="glass animate-pulse p-10 text-center text-sm text-muted">正在打开文章…</div>

  <EmptyState v-else-if="!post" icon="info" title="文章不存在" desc="它可能已被删除，或者链接不正确。">
    <router-link to="/posts" class="btn">返回文章列表</router-link>
  </EmptyState>

  <article v-else class="animate-rise">
    <div class="mb-8">
      <button class="mb-6 inline-flex items-center gap-1.5 text-xs text-faint hover:text-accent" @click="router.back()">
        <AppIcon name="chevronLeft" :size="14" /> 返回
      </button>

      <div class="mb-4 flex flex-wrap items-center gap-2 text-[11px]">
        <router-link v-if="post.category_name" :to="`/posts?category=${post.category_id}`" class="rounded-full bg-accent/10 px-2.5 py-1 text-accent">
          {{ post.category_name }}
        </router-link>
        <span v-if="post.featured" class="inline-flex items-center gap-1 rounded-full bg-accent-purple/10 px-2.5 py-1 text-accent-purple">
          <AppIcon name="spark" :size="11" /> 精选
        </span>
      </div>

      <h1 class="text-3xl font-semibold leading-tight tracking-tight sm:text-[40px]">{{ post.title }}</h1>

      <div class="mt-6 flex flex-wrap items-center justify-between gap-4 border-b border-line pb-6">
        <div class="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-faint">
          <span v-for="m in meta" :key="m.text" class="inline-flex items-center gap-1.5">
            <AppIcon :name="m.icon" :size="14" /> {{ m.text }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn btn-sm" @click="copyLink"><AppIcon name="copy" :size="14" /> 复制链接</button>
          <router-link v-if="isAdmin" :to="`/posts/${post.id}/edit`" class="btn btn-sm">
            <AppIcon name="edit" :size="14" /> 编辑
          </router-link>
        </div>
      </div>
    </div>

    <div class="grid gap-10 lg:grid-cols-[minmax(0,1fr)_220px]">
      <div class="min-w-0">
        <div v-if="post.cover" class="card-cover mb-9 h-56 rounded-2xl border border-line sm:h-72">
          <img :src="post.cover" :alt="post.title" />
        </div>

        <MarkdownView ref="md" :content="post.content" />

        <div v-if="post.tags?.length" class="mt-12 flex flex-wrap gap-2 border-t border-line pt-6">
          <router-link v-for="t in post.tags" :key="t.id" :to="`/posts?tag=${t.id}`" class="chip">#{{ t.name }}</router-link>
        </div>

        <nav class="mt-10 grid gap-3 border-t border-line pt-6 sm:grid-cols-2">
          <router-link
            v-if="post.prev"
            :to="`/posts/${post.prev.id}`"
            class="glass-soft group flex flex-col p-4 transition-colors hover:border-accent/40"
          >
            <span class="text-[11px] text-faint">← 上一篇</span>
            <span class="mt-1 truncate text-sm text-muted group-hover:text-accent">{{ post.prev.title }}</span>
          </router-link>
          <router-link
            v-if="post.next"
            :to="`/posts/${post.next.id}`"
            class="glass-soft group flex flex-col p-4 text-right transition-colors hover:border-accent/40"
          >
            <span class="text-[11px] text-faint">下一篇 →</span>
            <span class="mt-1 truncate text-sm text-muted group-hover:text-accent">{{ post.next.title }}</span>
          </router-link>
        </nav>
      </div>

      <!-- 目录：滚动高亮 -->
      <aside v-if="toc.length" class="hidden lg:block">
        <div class="sticky top-24">
          <p class="section-kicker mb-4">ON THIS PAGE</p>
          <ul class="space-y-1 border-l border-line">
            <li v-for="h in toc" :key="h.id">
              <button
                class="block w-full border-l-2 py-1.5 text-left text-xs leading-relaxed transition-colors"
                :class="[
                  h.level === 3 ? 'pl-6' : 'pl-3',
                  activeId === h.id ? 'border-accent text-accent' : 'border-transparent text-faint hover:text-muted'
                ]"
                @click="jump(h.id)"
              >{{ h.text }}</button>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </article>
</template>
