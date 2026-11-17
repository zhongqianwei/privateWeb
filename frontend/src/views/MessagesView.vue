<script setup>
import { onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import { messagesApi } from '../api/index.js'
import { toast } from '../composables/toast.js'
import { formatDate } from '../utils/format.js'

const items = ref([])
const form = ref({ nickname: '', content: '' })
const sending = ref(false)

async function load() {
  try { items.value = (await messagesApi.list()).items || [] } catch { items.value = [] }
}

async function send() {
  if (!form.value.nickname.trim() || !form.value.content.trim()) return toast('请填写昵称和内容', 'error')
  sending.value = true
  try {
    await messagesApi.create(form.value)
    form.value.content = ''
    toast('留言已送达', 'success')
    load()
  } catch (e) { toast(e.message || '发送失败', 'error') } finally { sending.value = false }
}

onMounted(load)
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="GUESTBOOK" title="留言" desc="想说的话，放在这里就好。" />

    <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div v-if="items.length" class="space-y-3">
        <div v-for="m in items" :key="m.id" class="glass p-5">
          <div class="flex items-center gap-3">
            <div class="grid h-8 w-8 place-items-center rounded-lg bg-accent/10 font-mono text-xs text-accent">{{ m.nickname.slice(0, 1).toUpperCase() }}</div>
            <span class="text-sm font-medium text-ink">{{ m.nickname }}</span>
            <span class="ml-auto font-mono text-[10px] text-faint">{{ formatDate(m.created_at, true) }}</span>
          </div>
          <p class="mt-3 whitespace-pre-wrap text-[13px] leading-[1.9] text-muted">{{ m.content }}</p>
        </div>
      </div>
      <EmptyState v-else icon="chat" title="还没有留言" desc="成为第一个留下声音的人吧。" />

      <aside class="glass h-fit p-6">
        <p class="section-kicker mb-5">SAY SOMETHING</p>
        <div class="space-y-4">
          <div>
            <label class="mb-2 block text-xs text-muted">昵称</label>
            <input v-model="form.nickname" class="input text-xs" placeholder="怎么称呼你" />
          </div>
          <div>
            <label class="mb-2 block text-xs text-muted">内容</label>
            <textarea v-model="form.content" rows="5" class="textarea text-xs" placeholder="写点什么…"></textarea>
          </div>
          <button class="btn btn-primary w-full" :disabled="sending" @click="send">
            <AppIcon name="arrowUp" :size="15" class="rotate-90" /> {{ sending ? '发送中…' : '留下留言' }}
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>
