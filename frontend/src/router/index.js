import { createRouter, createWebHashHistory } from 'vue-router'
import { userStore, isAdmin, initUser } from '../store/user.js'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/posts', name: 'posts', component: () => import('../views/PostsView.vue') },
  { path: '/posts/new', name: 'post-new', component: () => import('../views/PostEditView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/posts/:id/edit', name: 'post-edit', component: () => import('../views/PostEditView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/posts/:id', name: 'post-detail', component: () => import('../views/PostDetailView.vue') },
  { path: '/diary', name: 'diary', component: () => import('../views/DiaryView.vue') },
  { path: '/gallery', name: 'gallery', component: () => import('../views/GalleryView.vue') },
  { path: '/about', name: 'about', component: () => import('../views/AboutView.vue') },
  { path: '/archive', name: 'archive', component: () => import('../views/ArchiveView.vue') },
  { path: '/friends', name: 'friends', component: () => import('../views/FriendsView.vue') },
  { path: '/messages', name: 'messages', component: () => import('../views/MessagesView.vue') },
  { path: '/stats', name: 'stats', component: () => import('../views/StatsView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/u/:id', name: 'user-space', component: () => import('../views/UserSpaceView.vue') },
  { path: '/manage', name: 'manage', component: () => import('../views/ManageView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth && !to.meta.requiresAdmin) return true
  if (!userStore.ready) await initUser()
  if (!userStore.user) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.requiresAdmin && !isAdmin.value) {
    // 普通用户访问后台：挡回首页，不暴露后台入口
    return { name: 'home' }
  }
})

export default router
