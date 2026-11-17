<script setup>
import { onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import { photosApi } from '../api/index.js'
import { userStore } from '../store/user.js'
import { toast } from '../composables/toast.js'
import { formatDate } from '../utils/format.js'

const photos = ref([])
const uploading = ref(false)
const preview = ref(null)
const fileInput = ref(null)
const title = ref('')

async function load() {
  try {
    const res = await photosApi.list()
    photos.value = res.items || []
  } catch {
    photos.value = []
  }
}

async function onUpload(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  uploading.value = true
  try {
    for (const file of files) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', title.value || file.name)
      await photosApi.upload(fd)
    }
    toast(`已上传 ${files.length} 张`, 'success')
    title.value = ''
    await load()
  } catch (err) {
    toast(err.message || '上传失败', 'error')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function remove(photo) {
  if (!confirm('确定删除这张照片吗？')) return
  try {
    await photosApi.remove(photo.id)
    toast('已删除', 'success')
    if (preview.value?.id === photo.id) preview.value = null
    load()
  } catch (e) {
    toast(e.message || '删除失败', 'error')
  }
}

onMounted(load)
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="GALLERY" title="相册" desc="一些值得留下的瞬间。">
      <template #action>
        <div v-if="userStore.user" class="flex flex-wrap items-center gap-2">
          <input v-model="title" class="input hidden w-40 text-xs sm:block" placeholder="照片标题（可选）" />
          <button class="btn btn-primary" :disabled="uploading" @click="fileInput?.click()">
            <AppIcon name="upload" :size="15" /> {{ uploading ? '上传中…' : '上传图片' }}
          </button>
          <input ref="fileInput" type="file" accept="image/*" multiple class="hidden" @change="onUpload" />
        </div>
      </template>
    </PageHeader>

    <div v-if="photos.length" class="columns-2 gap-4 sm:columns-3 lg:columns-4">
      <div v-for="p in photos" :key="p.id" class="glass group mb-4 break-inside-avoid overflow-hidden">
        <button class="relative block w-full overflow-hidden" @click="preview = p">
          <img :src="p.url" :alt="p.title || '照片'" loading="lazy" class="w-full transition-transform duration-500 group-hover:scale-[1.03]" />
        </button>
        <div class="flex items-start gap-2 p-3.5">
          <div class="min-w-0 flex-1">
            <p class="truncate text-[13px] font-medium text-ink">{{ p.title || '无题' }}</p>
            <p class="mt-0.5 font-mono text-[10px] text-faint">{{ formatDate(p.created_at) }}</p>
          </div>
          <button v-if="userStore.user" class="text-faint opacity-0 transition-opacity hover:text-danger group-hover:opacity-100" @click="remove(p)">
            <AppIcon name="trash" :size="15" />
          </button>
        </div>
      </div>
    </div>
    <EmptyState v-else icon="camera" title="相册还是空的" desc="登录后可以上传图片，把它们留在这里。">
      <button v-if="userStore.user" class="btn btn-primary" @click="fileInput?.click()">上传第一张</button>
      <router-link v-else to="/login" class="btn">登录后上传</router-link>
    </EmptyState>

    <!-- 灯箱 -->
    <div v-if="preview" class="fixed inset-0 z-[90] flex flex-col items-center justify-center bg-black/80 p-6 backdrop-blur-md" @click.self="preview = null">
      <button class="absolute right-6 top-6 btn btn-icon btn-ghost text-white" @click="preview = null"><AppIcon name="close" :size="22" /></button>
      <img :src="preview.url" :alt="preview.title" class="max-h-[76vh] max-w-full rounded-2xl border border-white/10 object-contain shadow-2xl" />
      <p class="mt-5 text-sm text-white/70">{{ preview.title }} <span class="ml-2 font-mono text-xs text-white/40">{{ formatDate(preview.created_at) }}</span></p>
    </div>
  </div>
</template>
