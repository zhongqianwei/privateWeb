<script setup>
import { onMounted, ref, watch } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import Avatar from '../components/Avatar.vue'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import EmptyState from '../components/EmptyState.vue'
import { diariesApi } from '../api/index.js'
import { userStore, isAdmin } from '../store/user.js'
import { toast } from '../composables/toast.js'
import { formatDate, plainText } from '../utils/format.js'

const KINDS = [
  { value: '', label: '全部', icon: 'layers' },
  { value: 'diary', label: '日记', icon: 'bookmark' },
  { value: 'essay', label: '随笔', icon: 'pen' },
  { value: 'note', label: '学习记录', icon: 'code' },
  { value: 'saying', label: '说说', icon: 'chat' },
]
const LABEL = { diary: '日记', essay: '随笔', note: '学习记录', saying: '说说', journal: '日记' }

const items = ref([])
const pages = ref(1)
const page = ref(1)
const kind = ref('')
const keyword = ref('')
const showForm = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref({ title: '', content: '', kind: 'diary', mood: '', weather: '' })

async function load() {
  try {
    const res = await diariesApi.list({
      kind: kind.value || undefined,
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: 12,
    })
    items.value = res.items || []
    pages.value = res.pages || 1
  } catch {
    items.value = []
  }
}

let timer = null
watch([kind, keyword], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})
watch(page, load)

function openNew() {
  editing.value = null
  form.value = { title: '', content: '', kind: kind.value || 'diary', mood: '', weather: '' }
  showForm.value = true
}

function openEdit(item) {
  editing.value = item.id
  form.value = {
    title: item.title || '', content: item.content || '', kind: item.kind || 'diary',
    mood: item.mood || '', weather: item.weather || '',
  }
  showForm.value = true
}

async function save() {
  if (!form.value.content.trim()) return toast('写点什么再保存吧', 'error')
  saving.value = true
  try {
    if (editing.value) await diariesApi.update(editing.value, form.value)
    else await diariesApi.create(form.value)
    toast('已保存', 'success')
    showForm.value = false
    load()
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function remove(item) {
  if (!confirm('确定删除这条记录吗？')) return
  try {
    await diariesApi.remove(item.id)
    toast('已删除', 'success')
    load()
  } catch (e) {
    toast(e.message || '删除失败', 'error')
  }
}

// 自己的记录或管理员可编辑
function canEdit(item) {
  if (!userStore.user) return false
  return isAdmin.value || item.user_id === userStore.user.id
}

onMounted(load)
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="MOMENTS / NOTES" title="记录" desc="不必完整，不必深刻。只是把那些一闪而过的东西留下来。">
      <template #action>
        <button v-if="userStore.user" class="btn btn-primary" @click="openNew">
          <AppIcon name="plus" :size="15" /> 写一条
        </button>
      </template>
    </PageHeader>

    <!-- 筛选 -->
    <div class="mb-7 flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="k in KINDS"
          :key="k.value"
          class="chip"
          :class="kind === k.value ? 'chip-active' : ''"
          @click="kind = k.value"
        >{{ k.label }}</button>
      </div>
      <div class="relative sm:ml-auto sm:w-64">
        <AppIcon name="search" :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
        <input v-model="keyword" class="input py-2 pl-9 text-xs" placeholder="搜索记录…" />
      </div>
    </div>

    <!-- 时间线 -->
    <div v-if="items.length" class="relative space-y-4 border-l border-line pl-5 sm:pl-7">
      <div v-for="item in items" :key="item.id" class="glass glass-hover group relative p-5 sm:p-6">
        <span class="absolute -left-[26px] top-7 h-2.5 w-2.5 rounded-full border-2 border-canvas bg-accent sm:-left-[34px]"></span>
        <div class="mb-3 flex flex-wrap items-center gap-2 text-[11px] text-faint">
          <Avatar
            v-if="item.author_id"
            :user="{ nickname: item.author, avatar: item.author_avatar }"
            :to="`/u/${item.author_id}`"
            :size="26"
          />
          <span class="rounded-full bg-accent/10 px-2 py-0.5 text-accent">{{ LABEL[item.kind] || '记录' }}</span>
          <span class="font-mono">{{ formatDate(item.created_at, true) }}</span>
          <span v-if="item.weather">· {{ item.weather }}</span>
          <span v-if="item.mood">· {{ item.mood }}</span>
          <div v-if="canEdit(item)" class="ml-auto flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            <button class="text-faint hover:text-accent" title="编辑" @click="openEdit(item)"><AppIcon name="edit" :size="14" /></button>
            <button class="text-faint hover:text-danger" title="删除" @click="remove(item)"><AppIcon name="trash" :size="14" /></button>
          </div>
        </div>
        <h3 v-if="item.title" class="text-[15px] font-medium text-ink">{{ item.title }}</h3>
        <p class="mt-2 whitespace-pre-wrap text-[13px] leading-[1.9] text-muted">{{ plainText(item.content) }}</p>
      </div>
    </div>
    <EmptyState v-else icon="pen" title="还没有记录" desc="随手写下今天的一句话，也算没有虚度。" />

    <Pagination :page="page" :pages="pages" @change="page = $event" />

    <!-- 编辑抽屉 -->
    <div v-if="showForm" class="fixed inset-0 z-[80] flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-6" @click.self="showForm = false">
      <div class="glass w-full max-w-2xl rounded-b-none p-6 sm:rounded-2xl">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-lg font-semibold">{{ editing ? '编辑记录' : '写一条记录' }}</h2>
          <button class="btn btn-icon btn-ghost" @click="showForm = false"><AppIcon name="close" :size="18" /></button>
        </div>
        <div class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="k in KINDS.filter(k => k.value)"
              :key="k.value"
              class="chip"
              :class="form.kind === k.value ? 'chip-active' : ''"
              @click="form.kind = k.value"
            >{{ k.label }}</button>
          </div>
          <input v-model="form.title" class="input" placeholder="标题（可选）" />
          <textarea v-model="form.content" rows="9" class="textarea" placeholder="此刻在想什么…"></textarea>
          <div class="grid grid-cols-2 gap-3">
            <input v-model="form.mood" class="input text-xs" placeholder="心情（可选）" />
            <input v-model="form.weather" class="input text-xs" placeholder="天气（可选）" />
          </div>
          <div class="flex justify-end gap-2 border-t border-line pt-4">
            <button class="btn" @click="showForm = false">取消</button>
            <button class="btn btn-primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
