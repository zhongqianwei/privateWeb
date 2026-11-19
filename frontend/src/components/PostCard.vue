<script setup>
import AppIcon from './AppIcon.vue'
import Avatar from './Avatar.vue'
import { useRouter } from 'vue-router'
import { formatDate, readingTime } from '../utils/format.js'

const router = useRouter()
function goSpace(e) {
  e.preventDefault()
  e.stopPropagation()
  if (props.post.author_id) router.push(`/u/${props.post.author_id}`)
}

const props = defineProps({
  post: { type: Object, required: true },
  featured: { type: Boolean, default: false },
})

const excerptText = () => props.post.excerpt || ''
</script>

<template>
  <router-link
    :to="`/posts/${post.id}`"
    class="glass glass-hover group flex h-full flex-col overflow-hidden"
    :class="featured ? 'p-0' : 'p-0'"
  >
    <div v-if="post.cover" class="card-cover h-40 w-full sm:h-44">
      <img :src="post.cover" :alt="post.title" loading="lazy" decoding="async" />
    </div>
    <div class="flex flex-1 flex-col p-5 sm:p-6">
      <div class="mb-3 flex items-center gap-2 text-[11px] font-medium tracking-wide text-faint">
        <span v-if="post.featured" class="inline-flex items-center gap-1 rounded-full bg-accent/10 px-2 py-0.5 text-accent">
          <AppIcon name="spark" :size="11" /> 精选
        </span>
        <span v-if="post.category_name" class="text-accent/80">{{ post.category_name }}</span>
        <span v-if="post.category_name" class="opacity-40">/</span>
        <time>{{ formatDate(post.created_at) }}</time>
      </div>

      <h3 class="text-[17px] font-semibold leading-snug tracking-tight text-ink transition-colors group-hover:text-accent sm:text-lg">
        {{ post.title }}
      </h3>
      <p class="mt-3 line-clamp-3 text-[13px] leading-relaxed text-muted">{{ excerptText() }}</p>

      <div class="mt-auto flex items-center gap-4 border-t border-line pt-4 text-[11px] text-faint">
        <button
          v-if="post.author_id"
          type="button"
          class="flex items-center gap-2 transition-colors hover:text-accent"
          title="查看作者空间"
          @click="goSpace"
        >
          <Avatar :user="{ nickname: post.author, avatar: post.author_avatar }" :size="24" />
          <span class="max-w-20 truncate">{{ post.author || '作者' }}</span>
        </button>
        <span class="inline-flex items-center gap-1"><AppIcon name="clock" :size="13" /> {{ readingTime(post.content || excerptText()) }} 分钟</span>
        <span class="inline-flex items-center gap-1"><AppIcon name="eye" :size="13" /> {{ post.views || 0 }}</span>
        <AppIcon name="chevronRight" :size="15" class="ml-auto text-faint transition-transform group-hover:translate-x-1 group-hover:text-accent" />
      </div>
    </div>
  </router-link>
</template>
