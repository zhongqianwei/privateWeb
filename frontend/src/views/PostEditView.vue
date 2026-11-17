<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import MarkdownView from '../components/MarkdownView.vue'
import { postsApi, categoriesApi, tagsApi } from '../api/index.js'
import { plainText, readingTime } from '../utils/format.js'
import { toast } from '../composables/toast.js'

const route = useRoute()
const router = useRouter()
const editingId = ref(route.params.id ? Number(route.params.id) : null)

const form = ref({
  title: '', content: '', summary: '', cover: '',
  category_id: null, tag_ids: [], featured: false, status: 'published',
})
const categories = ref([])
const tags = ref([])
const saving = ref(false)
const loading = ref(false)
const preview = ref(false)

const count = computed(() => plainText(form.value.content).length)
const isDraft = computed(() => form.value.status === 'draft')

function toggleTag(id) {
  const i = form.value.tag_ids.indexOf(id)
  if (i >= 0) form.value.tag_ids.splice(i, 1)
  else form.value.tag_ids.push(id)
}

async function loadPost() {
  if (!editingId.value) return
  loading.value = true
  try {
    const { post } = await postsApi.detail(editingId.value)
    Object.assign(form.value, {
      title: post.title || '',
      content: post.content || '',
      summary: post.summary || '',
      cover: post.cover || '',
      category_id: post.category_id || null,
      tag_ids: (post.tags || []).map((t) => t.id),
      featured: !!post.featured,
      status: post.status || 'published',
    })
  } catch {
    toast('文章加载失败', 'error')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    toast('标题和正文不能为空', 'error')
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value }
    if (editingId.value) {
      await postsApi.update(editingId.value, payload)
      toast('已保存修改', 'success')
    } else {
      const r = await postsApi.create(payload)
      editingId.value = r.id
      router.replace({ name: 'post-edit', params: { id: r.id } })
      toast('文章已发布', 'success')
    }
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!editingId.value || !confirm('确定要删除这篇文章吗？此操作不可恢复。')) return
  try {
    await postsApi.remove(editingId.value)
    toast('已删除', 'success')
    router.push('/manage')
  } catch (e) {
    toast(e.message || '删除失败', 'error')
  }
}

watch(() => route.params.id, (v) => {
  editingId.value = v ? Number(v) : null
  loadPost()
})

onMounted(async () => {
  const [c, t] = await Promise.allSettled([categoriesApi.list(), tagsApi.list()])
  categories.value = c.value?.items || []
  tags.value = t.value?.items || []
  await loadPost()
})
</script>

<template>
  <div class="animate-rise">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="section-kicker mb-2">EDITOR</p>
        <h1 class="text-2xl font-semibold">{{ editingId ? '编辑文章' : '写点什么' }}</h1>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button class="btn btn-sm" @click="preview = !preview">
          <AppIcon :name="preview ? 'edit' : 'eye'" :size="14" /> {{ preview ? '继续编辑' : '预览' }}
        </button>
        <button v-if="editingId" class="btn btn-sm text-danger" @click="remove">
          <AppIcon name="trash" :size="14" /> 删除
        </button>
        <button class="btn btn-primary btn-sm" :disabled="saving" @click="save">
          <AppIcon name="check" :size="14" /> {{ saving ? '保存中…' : (isDraft ? '存为草稿' : '发布') }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="glass p-10 text-center text-sm text-muted">正在载入文章…</div>

    <div v-else class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
      <!-- 正文 -->
      <div class="glass min-w-0 p-5 sm:p-6">
        <input v-model="form.title" class="w-full border-0 bg-transparent text-xl font-semibold text-ink outline-none placeholder:text-faint sm:text-2xl" placeholder="文章标题" />
        <div class="my-5 h-px bg-line"></div>

        <div v-if="!preview">
          <textarea
            v-model="form.content"
            class="textarea min-h-[60vh] border-0 bg-transparent px-0 font-mono text-[13px] leading-7 focus:ring-0"
            placeholder="用 Markdown 开始写作…&#10;&#10;## 一个小标题&#10;&#10;正文从这里开始。"
          ></textarea>
          <div class="flex items-center gap-4 border-t border-line pt-4 font-mono text-[11px] text-faint">
            <span>{{ count }} 字</span>
            <span>约 {{ readingTime(form.content) }} 分钟读完</span>
            <span class="ml-auto">支持 Markdown · 代码高亮 · 表格</span>
          </div>
        </div>
        <div v-else class="min-h-[60vh] py-2">
          <MarkdownView :content="form.content || '_还没有内容。_'" />
        </div>
      </div>

      <!-- 设置 -->
      <aside class="space-y-4">
        <div class="glass p-5">
          <p class="section-kicker mb-4">发布设置</p>
          <label class="mb-2 block text-xs text-muted">摘要</label>
          <textarea v-model="form.summary" rows="3" class="textarea text-xs" placeholder="留空则自动截取正文开头"></textarea>

          <label class="mb-2 mt-4 block text-xs text-muted">分类</label>
          <select v-model="form.category_id" class="select">
            <option :value="null">未分类</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>

          <label class="mb-2 mt-4 block text-xs text-muted">封面图地址（可选）</label>
          <input v-model="form.cover" class="input text-xs" placeholder="/uploads/photos/xxx.jpg" />

          <div class="mt-5 space-y-3 border-t border-line pt-4">
            <label class="flex cursor-pointer items-center justify-between text-xs text-muted">
              <span>设为精选</span>
              <input v-model="form.featured" type="checkbox" class="h-4 w-4 accent-accent" />
            </label>
            <label class="flex cursor-pointer items-center justify-between text-xs text-muted">
              <span>存为草稿</span>
              <input :checked="isDraft" type="checkbox" class="h-4 w-4 accent-accent" @change="form.status = $event.target.checked ? 'draft' : 'published'" />
            </label>
          </div>
        </div>

        <div class="glass p-5">
          <p class="section-kicker mb-4">标签</p>
          <div v-if="tags.length" class="flex flex-wrap gap-2">
            <button
              v-for="t in tags"
              :key="t.id"
              class="chip"
              :class="form.tag_ids.includes(t.id) ? 'chip-active' : ''"
              @click="toggleTag(t.id)"
            >#{{ t.name }}</button>
          </div>
          <p v-else class="text-xs text-faint">还没有标签，可在后台创建。</p>
        </div>
      </aside>
    </div>
  </div>
</template>
