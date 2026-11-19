<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import PostCard from '../components/PostCard.vue'
import EmptyState from '../components/EmptyState.vue'
import { postsApi, categoriesApi, tagsApi } from '../api/index.js'
import { isAdmin } from '../store/user.js'

const route = useRoute()
const router = useRouter()

const items = ref([])
const categories = ref([])
const tags = ref([])
const total = ref(0)
const pages = ref(1)
const loading = ref(false)
const keyword = ref(String(route.query.keyword || ''))
const categoryId = ref(Number(route.query.category) || null)
const tagId = ref(Number(route.query.tag) || null)
const year = ref(Number(route.query.year) || null)
const month = ref(Number(route.query.month) || null)
const page = ref(Number(route.query.page) || 1)
const searchEl = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await postsApi.list({
      keyword: keyword.value || undefined,
      category_id: categoryId.value || undefined,
      tag_id: tagId.value || undefined,
      year: year.value || undefined,
      month: month.value || undefined,
      page: page.value,
      page_size: 9,
    })
    items.value = res.items || []
    total.value = res.total || 0
    pages.value = res.pages || 1
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

function syncQuery() {
  const q = {}
  if (keyword.value) q.keyword = keyword.value
  if (categoryId.value) q.category = categoryId.value
  if (tagId.value) q.tag = tagId.value
  if (year.value) q.year = year.value
  if (month.value) q.month = month.value
  if (page.value > 1) q.page = page.value
  router.replace({ path: '/posts', query: q })
}

let timer = null
watch([keyword, categoryId, tagId, year, month], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(() => { load(); syncQuery() }, 260)
})
watch(page, () => { load(); syncQuery() })

watch(() => route.query, (q) => {
  const next = {
    keyword: String(q.keyword || ''),
    category: Number(q.category) || null,
    tag: Number(q.tag) || null,
    year: Number(q.year) || null,
    month: Number(q.month) || null,
    page: Number(q.page) || 1,
  }
  if (next.keyword !== keyword.value) keyword.value = next.keyword
  if (next.category !== categoryId.value) categoryId.value = next.category
  if (next.tag !== tagId.value) tagId.value = next.tag
  if (next.year !== year.value) year.value = next.year
  if (next.month !== month.value) month.value = next.month
  if (next.page !== page.value) page.value = next.page
})

function reset() {
  keyword.value = ''
  categoryId.value = null
  tagId.value = null
  year.value = null
  month.value = null
  page.value = 1
}

onMounted(async () => {
  const [c, t] = await Promise.allSettled([categoriesApi.list(), tagsApi.list()])
  categories.value = c.value?.items || []
  tags.value = t.value?.items || []
  await load()
  if (route.query.focus === '1') {
    await nextTick()
    searchEl.value?.focus()
  }
})
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="ARCHIVE / NOTES" title="文章" desc="把想明白的事写下来，也把没想明白的写下来。">
      <template #action>
        <router-link v-if="isAdmin" to="/posts/new" class="btn btn-primary">
          <AppIcon name="plus" :size="15" /> 写文章
        </router-link>
      </template>
    </PageHeader>

    <!-- 搜索与筛选 -->
    <div class="glass mb-7 p-4 sm:p-5">
      <div class="flex flex-col gap-3 sm:flex-row">
        <div class="relative flex-1">
          <AppIcon name="search" :size="17" class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-faint" />
          <input ref="searchEl" v-model="keyword" class="input pl-10" placeholder="搜索标题或正文…" />
        </div>
        <button class="btn shrink-0" :class="keyword || categoryId || tagId ? 'chip-active' : ''" @click="reset">
          清除筛选
        </button>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-2 border-t border-line pt-4">
        <span class="mr-1 text-[11px] text-faint">分类</span>
        <button class="chip" :class="!categoryId ? 'chip-active' : ''" @click="categoryId = null">全部</button>
        <button
          v-for="c in categories"
          :key="c.id"
          class="chip"
          :class="categoryId === c.id ? 'chip-active' : ''"
          @click="categoryId = c.id"
        >{{ c.name }}</button>
      </div>

      <div v-if="tags.length" class="mt-3 flex flex-wrap items-center gap-2">
        <span class="mr-1 text-[11px] text-faint">标签</span>
        <button
          v-for="t in tags"
          :key="t.id"
          class="chip"
          :class="tagId === t.id ? 'chip-active' : ''"
          @click="tagId = tagId === t.id ? null : t.id"
        >#{{ t.name }}</button>
      </div>
    </div>

    <div class="mb-4 flex items-center justify-between text-xs text-faint">
      <span>共 <span class="font-mono text-muted">{{ total }}</span> 篇文章</span>
      <span v-if="loading" class="animate-pulse">加载中…</span>
    </div>

    <div v-if="items.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PostCard v-for="p in items" :key="p.id" :post="p" />
    </div>
    <EmptyState
      v-else-if="!loading"
      icon="search"
      title="没有找到匹配的文章"
      desc="换个关键词，或清除筛选条件再试试。"
    >
      <button class="btn" @click="reset">清除筛选</button>
    </EmptyState>

    <Pagination :page="page" :pages="pages" @change="page = $event" />
  </div>
</template>
