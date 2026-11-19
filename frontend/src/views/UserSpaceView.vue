<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import Avatar from '../components/Avatar.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import { usersApi } from '../api/index.js'
import { userStore, isAdmin, updateProfile, uploadAvatar } from '../store/user.js'
import { toast } from '../composables/toast.js'
import { formatDate, excerpt } from '../utils/format.js'

const route = useRoute()
const userId = computed(() => Number(route.params.id))

const profile = ref(null)
const counts = ref({})
const items = ref([])
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const activeTab = ref('all')
const loading = ref(false)
const loadError = ref(false)

const TABS = [
  { key: 'all', label: '全部' },
  { key: 'posts', label: '文章' },
  { key: 'diary', label: '日记' },
  { key: 'essay', label: '随笔' },
  { key: 'note', label: '笔记' },
  { key: 'saying', label: '说说' },
  { key: 'photos', label: '图片' },
]

const TYPE_META = {
  post: { label: '文章', icon: 'layers', color: 'text-accent' },
  diary: { label: '日记', icon: 'bookmark', color: 'text-accent-2' },
  journal: { label: '日记', icon: 'bookmark', color: 'text-accent-2' },
  essay: { label: '随笔', icon: 'pen', color: 'text-accent-3' },
  note: { label: '笔记', icon: 'code', color: 'text-success' },
  saying: { label: '说说', icon: 'chat', color: 'text-accent' },
  photo: { label: '图片', icon: 'camera', color: 'text-accent-3' },
}

const isMe = computed(() => userStore.user && userStore.user.id === userId.value)

async function loadProfile() {
  try {
    const r = await usersApi.profile(userId.value)
    profile.value = r.user
    counts.value = r.counts || {}
    loadError.value = false
  } catch {
    loadError.value = true
  }
}

async function loadContents() {
  loading.value = true
  try {
    // Tab 到后端的 type 映射：diary/essay/note 走 diaries 接口的类型过滤由 all 返回后前端筛
    const r = await usersApi.contents(userId.value, { type: 'all', page: page.value, page_size: 12 })
    let list = r.items || []
    if (activeTab.value !== 'all') {
      list = list.filter((it) => it.type === activeTab.value)
    }
    items.value = list
    total.value = r.total || 0
    pages.value = r.pages || 1
    loadError.value = false
  } catch {
    items.value = []
    loadError.value = true
  } finally {
    loading.value = false
  }
}

watch(activeTab, () => { page.value = 1; loadContents() })
watch(page, loadContents)
watch(userId, () => { loadProfile(); loadContents() })

onMounted(() => { loadProfile(); loadContents() })

/* ---------- 编辑资料 / 头像 ---------- */
const showEdit = ref(false)
const editNickname = ref('')
const saving = ref(false)
const fileEl = ref(null)

function openEdit() {
  editNickname.value = profile.value?.nickname || ''
  showEdit.value = true
}

async function saveNickname() {
  if (!editNickname.value.trim()) return toast('昵称不能为空', 'error')
  saving.value = true
  try {
    const u = await updateProfile({ nickname: editNickname.value.trim() })
    if (u) profile.value = { ...profile.value, ...u }
    toast('已更新', 'success')
    showEdit.value = false
  } catch (e) {
    toast(e.message || '更新失败', 'error')
  } finally {
    saving.value = false
  }
}

async function onAvatarPick(e) {
  const file = e.target.files?.[0]
  if (!file) return
  saving.value = true
  try {
    const url = await uploadAvatar(file)
    profile.value = { ...profile.value, avatar: url }
    toast('头像已更新', 'success')
  } catch (err) {
    toast(err.message || '上传失败', 'error')
  } finally {
    saving.value = false
    if (fileEl.value) fileEl.value.value = ''
  }
}

function meta(type) {
  return TYPE_META[type] || TYPE_META.diary
}
</script>

<template>
  <div class="animate-rise">
    <div class="mx-auto max-w-2xl">
      <!-- 个人资料横幅 -->
      <section class="glass relative overflow-hidden rounded-3xl px-6 py-8 sm:px-8">
        <div class="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-accent/10 blur-3xl"></div>
        <div v-if="loadError" class="relative py-6 text-center text-sm text-muted">
          暂时无法读取这个空间（后端未连接）。
        </div>
        <template v-else-if="profile">
          <div class="relative flex items-center gap-5">
            <div class="relative">
              <Avatar :user="profile" :size="76" ring />
              <label v-if="isMe" class="absolute -bottom-1 -right-1 grid h-7 w-7 cursor-pointer place-items-center rounded-full bg-accent text-white shadow-lg" title="更换头像">
                <AppIcon name="camera" :size="14" />
                <input ref="fileEl" type="file" accept="image/*" class="hidden" @change="onAvatarPick" />
              </label>
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h1 class="truncate text-2xl font-semibold tracking-tight">{{ profile.nickname }}</h1>
                <span v-if="profile.is_admin" class="rounded-full bg-accent/15 px-2.5 py-0.5 text-[11px] font-medium text-accent">管理员</span>
              </div>
              <p class="mt-1 text-xs text-faint">@{{ profile.username }} · {{ formatDate(profile.joined_at) }} 加入</p>
              <div class="mt-3 flex flex-wrap gap-4 text-xs text-muted">
                <span><b class="font-mono text-ink">{{ counts.posts || 0 }}</b> 文章</span>
                <span><b class="font-mono text-ink">{{ counts.diaries || 0 }}</b> 记录</span>
                <span><b class="font-mono text-ink">{{ counts.photos || 0 }}</b> 图片</span>
              </div>
            </div>
            <button v-if="isMe" class="btn btn-sm shrink-0" @click="openEdit">
              <AppIcon name="edit" :size="14" /> 编辑
            </button>
          </div>
        </template>
      </section>

      <!-- Tab 栏 -->
      <div class="sticky top-16 z-20 mt-5 -mx-1 px-1">
        <div class="glass flex gap-1 overflow-x-auto rounded-2xl p-1.5">
          <button
            v-for="t in TABS"
            :key="t.key"
            class="shrink-0 rounded-xl px-3.5 py-2 text-xs font-medium transition-colors"
            :class="activeTab === t.key ? 'bg-accent text-white shadow-sm' : 'text-muted hover:text-ink'"
            @click="activeTab = t.key"
          >{{ t.label }}</button>
        </div>
      </div>

      <!-- 贴吧式内容：中间一列小窗口卡片 -->
      <div class="mt-5 space-y-3">
        <div v-if="loading" class="glass rounded-2xl px-6 py-16 text-center text-sm text-muted">加载中…</div>
        <article
          v-for="it in items"
          :key="`${it.type}-${it.id}`"
          class="glass glass-hover feed-card rounded-2xl p-5 sm:p-6"
        >
          <!-- 卡片头：作者 + 类型 + 时间 -->
          <div class="mb-3 flex items-center gap-2.5">
            <Avatar :user="profile" :to="`/u/${profile?.id}`" :size="30" />
            <div class="min-w-0">
              <div class="truncate text-[13px] font-medium text-ink">{{ profile?.nickname }}</div>
              <div class="text-[10px] text-faint">{{ formatDate(it.created_at, true) }}</div>
            </div>
            <span class="ml-auto inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium" :class="meta(it.type).color">
              <AppIcon :name="meta(it.type).icon" :size="12" /> {{ it.kind_label || meta(it.type).label }}
            </span>
          </div>

          <!-- 标题 -->
          <h3 v-if="it.title" class="text-[16px] font-semibold leading-snug text-ink">{{ it.title }}</h3>

          <!-- 图片 -->
          <div v-if="it.cover" class="mt-3 overflow-hidden rounded-xl">
            <img :src="it.cover" :alt="it.title || '图片'" class="w-full object-cover" loading="lazy" decoding="async" />
          </div>

          <!-- 正文 -->
          <p v-if="it.content" class="mt-2 whitespace-pre-wrap text-[13px] leading-[1.85] text-muted">{{ excerpt(it.content, 220) }}</p>

          <!-- 心情天气 -->
          <div v-if="it.mood || it.weather" class="mt-3 flex gap-3 text-[11px] text-faint">
            <span v-if="it.mood">心情 · {{ it.mood }}</span>
            <span v-if="it.weather">天气 · {{ it.weather }}</span>
          </div>

          <!-- 卡片脚：文章可点进详情 -->
          <div v-if="it.type === 'post'" class="mt-4 border-t border-line pt-3">
            <router-link :to="it.ref" class="inline-flex items-center gap-1 text-xs text-accent hover:gap-2 transition-all">
              阅读全文 <AppIcon name="chevronRight" :size="14" />
            </router-link>
          </div>
        </article>

        <EmptyState
          v-if="!loading && items.length === 0"
          icon="layers"
          title="这里还空着"
          desc="这一栏暂时没有内容。"
        />
      </div>

      <Pagination :page="page" :pages="pages" @change="page = $event" />
    </div>

    <!-- 编辑昵称弹层 -->
    <div v-if="showEdit" class="fixed inset-0 z-[80] flex items-center justify-center bg-black/50 p-6 backdrop-blur-sm" @click.self="showEdit = false">
      <div class="glass w-full max-w-md rounded-2xl p-6">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-lg font-semibold">编辑资料</h2>
          <button class="btn btn-icon btn-ghost" @click="showEdit = false"><AppIcon name="close" :size="18" /></button>
        </div>
        <label class="mb-2 block text-xs text-muted">昵称</label>
        <input v-model="editNickname" class="input" maxlength="30" placeholder="你的昵称" @keyup.enter="saveNickname" />
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn" @click="showEdit = false">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="saveNickname">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
