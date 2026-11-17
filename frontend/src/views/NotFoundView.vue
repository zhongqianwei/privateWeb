<script setup>
import AppIcon from '../components/AppIcon.vue'
</script>

<template>
  <div class="flex min-h-[70vh] flex-col items-center justify-center text-center animate-rise">
    <div class="font-mono text-[96px] font-semibold leading-none tracking-tighter text-accent/20 sm:text-[140px]">404</div>
    <h1 class="mt-4 text-xl font-semibold">这里什么也没有</h1>
    <p class="mt-3 max-w-sm text-sm text-muted">这扇门后面是空的。也许换个地址，或者回到首页重新开始。</p>
    <router-link to="/home" class="btn btn-primary mt-8">
      <AppIcon name="home" :size="15" /> 回到首页
    </router-link>
  </div>
</template>
