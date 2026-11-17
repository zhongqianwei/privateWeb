<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import {
  postsApi, diariesApi, photosApi, messagesApi, friendsApi,
  categoriesApi, tagsApi, statsApi, settingsApi,
} from '../api/index.js'
import { siteStore, fetchSettings } from '../store/site.js'
import { toast } from '../composables/toast.js'
import { formatDate, plainText } from '../utils/format.js'

const router = useRouter()
const tab = ref('overview')
const tabs = [
  { id: 'overview', label: '概览', icon: 'chart' },
  { id: 'posts', label: '文章', icon: 'layers' },
  { id: 'taxonomy', label: '分类标签', icon: 'tag' },
  { id: 'notes', label: '记录', icon: 'pen' },
  { id: 'photos', label: '相册', icon: 'camera' },
  { id: 'inbox', label: '留言', icon: 'chat' },
  { id: 'friends', label: '友链', icon: 'link' },
  { id: 'settings', label: '站点设置', icon: 'user' },
]

const stats = ref({})
const posts = ref([])
const postPage = ref(1)
const postPages = ref(1)
const notes = ref([])
const photos = ref([])
const messages = ref([])
const friends = ref([])
const categories = ref([])
const tags = ref([])
const loading = ref(false)

const newCategory = ref('')
const newTag = ref('')
const newFriend = reactive({ name: '', url: '', description: '' })
const settings = reactive({ ...siteStore.settings })

async function loadOverview() {
  const [s, p] = await Promise.allSettled([statsApi.summary(), postsApi.list({ status: 'all', page_size: 6 })])
  stats.value = s.value || {}
  posts.value = p.value?.items || []
}

async function loadPosts() {
  loading.value = true
  try {
    const r = await postsApi.list({ status: 'all', page: postPage.value, page_size: 12 })
    posts.value = r.items || []
    postPages.value = r.pages || 1
  } catch (e) { toast(e.message, 'error') } finally { loading.value = false }
}

async function loadTaxonomy() {
  const [c, t] = await Promise.allSettled([categoriesApi.list(), tagsApi.list()])
  categories.value = c.value?.items || []
  tags.value = t.value?.items || []
}

async function loadAllContent() {
  const [n, p, m, f] = await Promise.allSettled([
    diariesApi.list({ page_size: 30 }), photosApi.list(), messagesApi.list(), friendsApi.list(),
  ])
  notes.value = n.value?.items || []
  photos.value = p.value?.items || []
  messages.value = m.value?.items || []
  friends.value = f.value?.items || []
}

function switchTab(id) {
  tab.value = id
  if (id === 'overview') loadOverview()
  if (id === 'posts') loadPosts()
  if (id === 'taxonomy') loadTaxonomy()
  if (['notes', 'photos', 'inbox', 'friends'].includes(id)) loadAllContent()
  if (id === 'settings') Object.assign(settings, siteStore.settings)
}

async function addCategory() {
  if (!newCategory.value.trim()) return
  try { await categoriesApi.create({ name: newCategory.value.trim() }); newCategory.value = ''; loadTaxonomy(); toast('已添加', 'success') }
  catch (e) { toast(e.message, 'error') }
}
async function renameCategory(id, name) {
  if (!name.trim()) return
  try { await categoriesApi.rename(id, name.trim()); toast('已更新', 'success') } catch (e) { toast(e.message, 'error') }
}
async function removeCategory(id) {
  if (!confirm('删除这个分类？文章会被保留并变为未分类。')) return
  try { await categoriesApi.remove(id); loadTaxonomy(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}
async function addTag() {
  if (!newTag.value.trim()) return
  try { await tagsApi.create({ name: newTag.value.trim() }); newTag.value = ''; loadTaxonomy(); toast('已添加', 'success') }
  catch (e) { toast(e.message, 'error') }
}
async function renameTag(id, name) {
  if (!name.trim()) return
  try { await tagsApi.rename(id, name.trim()); toast('已更新', 'success') } catch (e) { toast(e.message, 'error') }
}
async function removeTag(id) {
  if (!confirm('删除这个标签？')) return
  try { await tagsApi.remove(id); loadTaxonomy(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}

async function deletePost(p) {
  if (!confirm(`确定删除《${p.title}》？`)) return
  try { await postsApi.remove(p.id); toast('已删除', 'success'); tab.value === 'posts' ? loadPosts() : loadOverview() }
  catch (e) { toast(e.message, 'error') }
}
async function deleteNote(n) {
  if (!confirm('删除这条记录？')) return
  try { await diariesApi.remove(n.id); loadAllContent(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}
async function deletePhoto(p) {
  if (!confirm('删除这张照片？')) return
  try { await photosApi.remove(p.id); loadAllContent(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}
async function deleteMessage(m) {
  if (!confirm('删除这条留言？')) return
  try { await messagesApi.remove(m.id); loadAllContent(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}
async function addFriend() {
  if (!newFriend.name.trim() || !newFriend.url.trim()) return toast('请填写名称和链接', 'error')
  try {
    await friendsApi.create({ ...newFriend })
    Object.assign(newFriend, { name: '', url: '', description: '' })
    loadAllContent(); toast('已添加', 'success')
  } catch (e) { toast(e.message, 'error') }
}
async function deleteFriend(f) {
  if (!confirm('删除这个友链？')) return
  try { await friendsApi.remove(f.id); loadAllContent(); toast('已删除', 'success') } catch (e) { toast(e.message, 'error') }
}
async function saveSettings() {
  try {
    await settingsApi.update({ ...settings })
    await fetchSettings()
    toast('站点设置已保存', 'success')
  } catch (e) { toast(e.message, 'error') }
}

onMounted(() => { loadOverview(); loadTaxonomy() })
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="DASHBOARD" title="后台管理" desc="管理文章、内容、分类与站点信息。" />

    <div class="no-scrollbar mb-6 flex gap-2 overflow-x-auto border-b border-line pb-3">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="inline-flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-xs transition-colors"
        :class="tab === t.id ? 'bg-accent/10 text-accent' : 'text-muted hover:bg-white/5 hover:text-ink'"
        @click="switchTab(t.id)"
      >
        <AppIcon :name="t.icon" :size="14" /> {{ t.label }}
      </button>
    </div>

    <!-- 概览 -->
    <div v-if="tab === 'overview'" class="space-y-5">
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div v-for="c in [
          { label: '文章', value: stats.posts, icon: 'layers' },
          { label: '记录', value: stats.diaries, icon: 'pen' },
          { label: '照片', value: stats.photos, icon: 'camera' },
          { label: '留言', value: stats.messages, icon: 'chat' },
          { label: '总访问', value: stats.total_pv, icon: 'eye' },
          { label: '今日访问', value: stats.today_pv, icon: 'clock' },
          { label: '分类 / 标签', value: `${stats.categories ?? '–'} / ${stats.tags ?? '–'}`, icon: 'tag' },
          { label: '累计字数', value: stats.words, icon: 'code' },
        ]" :key="c.label" class="glass flex items-center gap-3 p-4">
          <AppIcon :name="c.icon" :size="17" class="text-accent" />
          <div><div class="font-mono text-lg font-semibold text-ink">{{ c.value ?? '—' }}</div><div class="text-[11px] text-faint">{{ c.label }}</div></div>
        </div>
      </div>

      <div class="glass p-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-sm font-semibold">最近文章</h3>
          <button class="text-xs text-muted hover:text-accent" @click="switchTab('posts')">管理全部 →</button>
        </div>
        <div v-if="posts.length" class="divide-y divide-line">
          <div v-for="p in posts" :key="p.id" class="flex items-center gap-3 py-3 text-sm">
            <span class="rounded-full px-2 py-0.5 text-[10px]" :class="p.status === 'draft' ? 'bg-white/5 text-faint' : 'bg-success/10 text-success'">
              {{ p.status === 'draft' ? '草稿' : '已发布' }}
            </span>
            <router-link :to="`/posts/${p.id}/edit`" class="min-w-0 flex-1 truncate text-muted hover:text-accent">{{ p.title }}</router-link>
            <span class="hidden font-mono text-[11px] text-faint sm:block">{{ formatDate(p.created_at) }}</span>
          </div>
        </div>
        <p v-else class="py-8 text-center text-sm text-muted">还没有文章。</p>
      </div>
    </div>

    <!-- 文章 -->
    <div v-else-if="tab === 'posts'" class="glass overflow-hidden">
      <div class="flex items-center justify-between border-b border-line px-5 py-4">
        <span class="text-sm font-semibold">全部文章</span>
        <router-link to="/posts/new" class="btn btn-primary btn-sm"><AppIcon name="plus" :size="14" /> 新建</router-link>
      </div>
      <div v-if="posts.length" class="divide-y divide-line">
        <div v-for="p in posts" :key="p.id" class="flex flex-wrap items-center gap-3 px-5 py-3.5 text-sm">
          <span class="rounded-full px-2 py-0.5 text-[10px]" :class="p.status === 'draft' ? 'bg-white/5 text-faint' : 'bg-success/10 text-success'">
            {{ p.status === 'draft' ? '草稿' : '已发布' }}
          </span>
          <span v-if="p.featured" class="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] text-accent">精选</span>
          <router-link :to="`/posts/${p.id}/edit`" class="min-w-0 flex-1 truncate text-ink hover:text-accent">{{ p.title }}</router-link>
          <span class="hidden font-mono text-[11px] text-faint md:block">{{ p.category_name || '未分类' }}</span>
          <span class="hidden font-mono text-[11px] text-faint sm:block">{{ p.views }} 次</span>
          <button class="text-faint hover:text-danger" title="删除" @click="deletePost(p)"><AppIcon name="trash" :size="15" /></button>
        </div>
      </div>
      <p v-else class="px-5 py-12 text-center text-sm text-muted">暂无文章</p>
      <div class="px-5 pb-2"><Pagination :page="postPage" :pages="postPages" @change="postPage = $event; loadPosts()" /></div>
    </div>

    <!-- 分类标签 -->
    <div v-else-if="tab === 'taxonomy'" class="grid gap-5 lg:grid-cols-2">
      <div class="glass p-6">
        <h3 class="mb-5 text-sm font-semibold">分类</h3>
        <div class="mb-5 flex gap-2">
          <input v-model="newCategory" class="input text-xs" placeholder="新分类名称" @keyup.enter="addCategory" />
          <button class="btn btn-primary btn-sm shrink-0" @click="addCategory">添加</button>
        </div>
        <div class="space-y-2">
          <div v-for="c in categories" :key="c.id" class="flex items-center gap-2">
            <input class="input py-1.5 text-xs" :value="c.name" @change="renameCategory(c.id, $event.target.value)" />
            <button class="shrink-0 text-faint hover:text-danger" @click="removeCategory(c.id)"><AppIcon name="trash" :size="15" /></button>
          </div>
          <p v-if="!categories.length" class="py-4 text-center text-xs text-faint">暂无分类</p>
        </div>
      </div>
      <div class="glass p-6">
        <h3 class="mb-5 text-sm font-semibold">标签</h3>
        <div class="mb-5 flex gap-2">
          <input v-model="newTag" class="input text-xs" placeholder="新标签名称" @keyup.enter="addTag" />
          <button class="btn btn-primary btn-sm shrink-0" @click="addTag">添加</button>
        </div>
        <div class="space-y-2">
          <div v-for="t in tags" :key="t.id" class="flex items-center gap-2">
            <input class="input py-1.5 text-xs" :value="t.name" @change="renameTag(t.id, $event.target.value)" />
            <button class="shrink-0 text-faint hover:text-danger" @click="removeTag(t.id)"><AppIcon name="trash" :size="15" /></button>
          </div>
          <p v-if="!tags.length" class="py-4 text-center text-xs text-faint">暂无标签</p>
        </div>
      </div>
    </div>

    <!-- 记录 -->
    <div v-else-if="tab === 'notes'" class="glass overflow-hidden">
      <div class="border-b border-line px-5 py-4 text-sm font-semibold">随笔 / 日记 / 学习记录</div>
      <div v-if="notes.length" class="divide-y divide-line">
        <div v-for="n in notes" :key="n.id" class="flex items-center gap-4 px-5 py-3.5">
          <span class="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] text-accent">{{ n.kind }}</span>
          <span class="min-w-0 flex-1 truncate text-sm text-muted">{{ n.title || plainText(n.content).slice(0, 40) }}</span>
          <span class="hidden font-mono text-[11px] text-faint sm:block">{{ formatDate(n.created_at) }}</span>
          <button class="text-faint hover:text-danger" @click="deleteNote(n)"><AppIcon name="trash" :size="15" /></button>
        </div>
      </div>
      <p v-else class="px-5 py-12 text-center text-sm text-muted">暂无记录</p>
    </div>

    <!-- 相册 -->
    <div v-else-if="tab === 'photos'">
      <div v-if="photos.length" class="grid grid-cols-3 gap-3 sm:grid-cols-5 lg:grid-cols-7">
        <div v-for="p in photos" :key="p.id" class="glass group relative overflow-hidden">
          <img :src="p.url" :alt="p.title" class="aspect-square w-full object-cover" loading="lazy" />
          <button class="absolute right-2 top-2 rounded-lg bg-black/60 p-1.5 text-white opacity-0 transition-opacity group-hover:opacity-100" @click="deletePhoto(p)">
            <AppIcon name="trash" :size="14" />
          </button>
        </div>
      </div>
      <EmptyState v-else icon="camera" title="相册为空" />
    </div>

    <!-- 留言 -->
    <div v-else-if="tab === 'inbox'" class="glass overflow-hidden">
      <div v-if="messages.length" class="divide-y divide-line">
        <div v-for="m in messages" :key="m.id" class="px-5 py-4">
          <div class="flex items-center gap-3 text-xs">
            <span class="font-medium text-ink">{{ m.nickname }}</span>
            <span class="font-mono text-faint">{{ formatDate(m.created_at, true) }}</span>
            <button class="ml-auto text-faint hover:text-danger" @click="deleteMessage(m)"><AppIcon name="trash" :size="14" /></button>
          </div>
          <p class="mt-2 whitespace-pre-wrap text-sm text-muted">{{ m.content }}</p>
        </div>
      </div>
      <p v-else class="px-5 py-12 text-center text-sm text-muted">暂无留言</p>
    </div>

    <!-- 友链 -->
    <div v-else-if="tab === 'friends'" class="space-y-5">
      <div class="glass p-6">
        <h3 class="mb-5 text-sm font-semibold">添加友链</h3>
        <div class="grid gap-3 sm:grid-cols-3">
          <input v-model="newFriend.name" class="input text-xs" placeholder="站点名称" />
          <input v-model="newFriend.url" class="input text-xs" placeholder="https://example.com" />
          <input v-model="newFriend.description" class="input text-xs" placeholder="一句话介绍（可选）" />
        </div>
        <button class="btn btn-primary btn-sm mt-4" @click="addFriend"><AppIcon name="plus" :size="14" /> 添加</button>
      </div>
      <div class="glass divide-y divide-line">
        <div v-for="f in friends" :key="f.id" class="flex items-center gap-4 px-5 py-4">
          <div class="min-w-0 flex-1">
            <a :href="f.url" target="_blank" rel="noopener" class="text-sm text-ink hover:text-accent">{{ f.name }}</a>
            <p class="mt-0.5 truncate text-xs text-faint">{{ f.description || f.url }}</p>
          </div>
          <button class="text-faint hover:text-danger" @click="deleteFriend(f)"><AppIcon name="trash" :size="15" /></button>
        </div>
        <p v-if="!friends.length" class="px-5 py-10 text-center text-sm text-muted">暂无友链</p>
      </div>
    </div>

    <!-- 站点设置 -->
    <div v-else-if="tab === 'settings'" class="glass max-w-2xl p-6 sm:p-8">
      <h3 class="mb-6 text-sm font-semibold">站点设置</h3>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block"><span class="mb-2 block text-xs text-muted">站点名称</span><input v-model="settings.site_name" class="input" /></label>
        <label class="block"><span class="mb-2 block text-xs text-muted">作者名</span><input v-model="settings.author_name" class="input" /></label>
        <label class="block sm:col-span-2"><span class="mb-2 block text-xs text-muted">站点描述</span><input v-model="settings.site_desc" class="input" /></label>
        <label class="block sm:col-span-2"><span class="mb-2 block text-xs text-muted">一句话身份</span><input v-model="settings.author_title" class="input" placeholder="例如：后端工程师 / 独立开发者" /></label>
        <label class="block sm:col-span-2"><span class="mb-2 block text-xs text-muted">个人简介（支持 Markdown）</span><textarea v-model="settings.author_bio" rows="6" class="textarea text-xs"></textarea></label>
        <label class="block"><span class="mb-2 block text-xs text-muted">所在地</span><input v-model="settings.location" class="input" /></label>
        <label class="block"><span class="mb-2 block text-xs text-muted">邮箱</span><input v-model="settings.email" class="input" /></label>
        <label class="block sm:col-span-2"><span class="mb-2 block text-xs text-muted">GitHub 主页</span><input v-model="settings.github" class="input" placeholder="https://github.com/xxx" /></label>
        <label class="block sm:col-span-2"><span class="mb-2 block text-xs text-muted">页脚文字</span><input v-model="settings.footer_text" class="input" /></label>
      </div>
      <div class="mt-7 flex justify-end border-t border-line pt-5">
        <button class="btn btn-primary" @click="saveSettings"><AppIcon name="check" :size="15" /> 保存设置</button>
      </div>
    </div>
  </div>
</template>
