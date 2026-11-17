<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/common'

const props = defineProps({
  content: { type: String, default: '' },
})

const toc = ref([])
const root = ref(null)

marked.setOptions({ gfm: true, breaks: false })

const html = computed(() => marked.parse(props.content || ''))

async function decorate() {
  await nextTick()
  if (!root.value) return
  const items = []
  root.value.querySelectorAll('h2, h3').forEach((el, i) => {
    const id = `sec-${i + 1}`
    el.id = id
    items.push({ id, text: el.textContent.trim(), level: Number(el.tagName.slice(1)) })
  })
  toc.value = items
  root.value.querySelectorAll('pre code').forEach((el) => {
    try { hljs.highlightElement(el) } catch {}
  })
  root.value.querySelectorAll('a').forEach((a) => {
    a.setAttribute('target', '_blank')
    a.setAttribute('rel', 'noopener noreferrer')
  })
}

watch(() => props.content, decorate, { immediate: true, flush: 'post' })

defineExpose({ toc })
</script>

<template>
  <div ref="root" class="prose-mini" v-html="html"></div>
</template>
