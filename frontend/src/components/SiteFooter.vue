<script setup>
import { computed } from 'vue'
import { siteStore } from '../store/site.js'

const year = new Date().getFullYear()
const name = computed(() => siteStore.settings.author_name || siteStore.settings.site_name || '我的小窝')
const footerText = computed(() => siteStore.settings.footer_text || '用代码记录生活，用文字留住时间。')
</script>

<template>
  <footer class="mt-auto border-t border-line">
    <div class="mx-auto flex w-full max-w-content flex-col gap-3 px-5 py-8 text-xs text-faint sm:flex-row sm:items-center sm:justify-between sm:px-8">
      <div>
        <span class="font-mono text-muted">{{ name }}</span>
        <span class="mx-2 opacity-40">/</span>
        <span>{{ footerText }}</span>
      </div>
      <div class="flex items-center gap-4 font-mono">
        <router-link to="/archive" class="hover:text-accent">归档</router-link>
        <router-link to="/friends" class="hover:text-accent">友链</router-link>
        <router-link to="/manage" class="hover:text-accent">后台</router-link>
        <span>© {{ year }}</span>
      </div>
    </div>
  </footer>
</template>
