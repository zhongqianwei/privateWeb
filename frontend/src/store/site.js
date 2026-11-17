import { reactive } from 'vue'
import { api } from '../api/index.js'

export const siteStore = reactive({
  settings: {
    site_name: '我的小窝',
    site_desc: '一个安静的程序员角落，记录文章、随笔与生活。',
    author_name: '',
    author_title: '',
    author_bio: '',
    location: '',
    email: '',
    github: '',
    footer_text: '',
  },
  loaded: false,
})

export async function fetchSettings() {
  try {
    const res = await api('/api/settings')
    if (res?.settings) Object.assign(siteStore.settings, res.settings)
    siteStore.loaded = true
  } catch {
    // 站点设置接口不可用时保留默认值，不打断页面
    siteStore.loaded = true
  }
}
