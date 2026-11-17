<script setup>
/**
 * AuthHint — 未登录引导条
 * 用于 博文 / 随笔 / 相册 顶部：提示"登录后可以写/传"，一键去登录（带回跳）。
 */
import { useRoute } from 'vue-router'
import { userStore } from '../store/user.js'
import AppIcon from './AppIcon.vue'

const route = useRoute()
const TEXT = {
  '/posts': '登录后可以写文章、管理标签和分类',
  '/diary': '登录后可以写随笔，日记只属于你自己',
  '/gallery': '登录后可以上传照片、整理你的墙'
}
</script>

<template>
  <div v-if="!userStore.user" class="authhint glass">
    <AppIcon name="info" :size="15" />
    <span>{{ TEXT[route.path] || '登录后可以发布内容' }}</span>
    <RouterLink class="btn small primary" :to="{ path: '/login', query: { redirect: route.fullPath } }">去登录</RouterLink>
  </div>
</template>

<style scoped>
.authhint {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 16px; border-radius: 14px;
  margin: 0 0 16px; font-size: 13.5px; color: var(--c-text-dim);
  animation: rise 0.35s ease both;
}
.authhint .btn { margin-left: auto; flex: none; }
</style>
