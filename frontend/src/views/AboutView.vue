<script setup>
import { computed } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import MarkdownView from '../components/MarkdownView.vue'
import { siteStore } from '../store/site.js'

const s = computed(() => siteStore.settings)
const name = computed(() => s.value.author_name || s.value.site_name || '我的小窝')
const bio = computed(() => s.value.author_bio || '这里还没有个人简介。登录后台的「站点设置」写几句话吧。')

const facts = computed(() => [
  { icon: 'user', label: '身份', value: s.value.author_title || '开发者' },
  { icon: 'globe', label: '坐标', value: s.value.location || '地球' },
  { icon: 'chat', label: '邮箱', value: s.value.email || '' },
  { icon: 'link', label: 'GitHub', value: s.value.github || '' },
].filter((f) => f.value))

const stack = [
  { group: '前端', items: ['Vue 3', 'TypeScript', 'Vite', 'TailwindCSS'] },
  { group: '后端', items: ['Python', 'FastAPI', 'MySQL', 'Redis'] },
  { group: '日常', items: ['Git', 'Linux', 'Docker', 'Figma'] },
]
</script>

<template>
  <div class="animate-rise">
    <PageHeader kicker="ABOUT" title="关于我" desc="介绍一下自己，也介绍一下这个小站。" />

    <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div class="space-y-5">
        <section class="glass relative overflow-hidden p-7 sm:p-9">
          <div class="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-accent/10 blur-3xl"></div>
          <div class="relative">
            <div class="mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-accent to-accent-purple font-mono text-2xl font-bold text-white shadow-glow">
              {{ name.slice(0, 1).toUpperCase() }}
            </div>
            <h2 class="text-2xl font-semibold">{{ name }}</h2>
            <p v-if="s.author_title" class="mt-2 text-sm text-accent">{{ s.author_title }}</p>
            <div class="my-7 h-px bg-line"></div>
            <MarkdownView :content="bio" />
          </div>
        </section>

        <section class="glass p-7">
          <p class="section-kicker mb-5">TECH STACK</p>
          <div class="grid gap-6 sm:grid-cols-3">
            <div v-for="g in stack" :key="g.group">
              <p class="mb-3 text-xs font-medium text-ink">{{ g.group }}</p>
              <div class="flex flex-wrap gap-2">
                <span v-for="i in g.items" :key="i" class="chip cursor-default">{{ i }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <aside class="space-y-5">
        <section class="glass p-6">
          <p class="section-kicker mb-5">BASIC INFO</p>
          <div class="space-y-4">
            <div v-for="f in facts" :key="f.label" class="flex items-start gap-3 text-sm">
              <AppIcon :name="f.icon" :size="16" class="mt-0.5 shrink-0 text-faint" />
              <div class="min-w-0">
                <div class="text-[11px] text-faint">{{ f.label }}</div>
                <a v-if="f.label === '邮箱'" :href="`mailto:${f.value}`" class="break-all text-muted hover:text-accent">{{ f.value }}</a>
                <a v-else-if="f.label === 'GitHub'" :href="f.value" target="_blank" rel="noopener" class="break-all text-muted hover:text-accent">{{ f.value.replace(/^https?:\/\//, '') }}</a>
                <div v-else class="text-muted">{{ f.value }}</div>
              </div>
            </div>
            <div v-if="!facts.length" class="text-xs text-faint">信息还没填，去后台「站点设置」补充。</div>
          </div>
        </section>

        <section class="glass p-6">
          <p class="section-kicker mb-4">ABOUT THIS SITE</p>
          <ul class="space-y-3 text-[13px] text-muted">
            <li class="flex gap-2.5"><AppIcon name="check" :size="15" class="mt-0.5 shrink-0 text-accent" /> Vue 3 + TailwindCSS 构建的前台</li>
            <li class="flex gap-2.5"><AppIcon name="check" :size="15" class="mt-0.5 shrink-0 text-accent" /> FastAPI + MySQL 提供数据服务</li>
            <li class="flex gap-2.5"><AppIcon name="check" :size="15" class="mt-0.5 shrink-0 text-accent" /> 支持文章、随笔、相册与留言</li>
          </ul>
          <router-link to="/messages" class="btn mt-6 w-full">给我留言</router-link>
        </section>
      </aside>
    </div>
  </div>
</template>
