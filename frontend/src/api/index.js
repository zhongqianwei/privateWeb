/** API 封装：fetch + 自动携带 token + 统一错误抛出 */

/**
 * 后端地址：
 *  - 留空 '' = 同源（推荐：dist 由 FastAPI 托管，或 Nginx 反代 /api、/uploads）
 *  - 前后端分开部署（例如前端传 GitHub Pages）时，填后端完整地址，
 *    例：export const API_BASE = 'http://127.0.0.1:8000'
 *      （后端需在 .env 设 CORS_ORIGINS=* 或加上前端域名）
 */
export const API_BASE = ''

const TOKEN_KEY = 'lh_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * 通用请求
 * @param path /api/xxx
 * @param opts { method, data(JSON), form(FormData), params(GET query) }
 */
export async function api(path, opts = {}) {
  const { method = 'GET', data, form, params } = opts
  let url = path
  if (params) {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.append(k, v)
    })
    const qs = q.toString()
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (form) {
    body = form
  } else if (data !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(data)
  }
  const res = await fetch(API_BASE + url, { method, headers, body })
  const text = await res.text()
  let json = {}
  try {
    json = text ? JSON.parse(text) : {}
  } catch {
    json = { detail: text }
  }
  if (!res.ok) {
    if (res.status === 401) {
      clearToken()
      window.dispatchEvent(new CustomEvent('lh:logout'))
    }
    throw new Error(typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail || res.statusText))
  }
  return json
}

/* ------------- 各模块 API ------------- */
export const authApi = {
  register: (d) => api('/api/auth/register', { method: 'POST', data: d }),
  login: (d) => api('/api/auth/login', { method: 'POST', data: d }),
  me: () => api('/api/auth/me'),
  updateProfile: (d) => api('/api/auth/profile', { method: 'PUT', data: d }),
  uploadAvatar: (formData) => api('/api/auth/avatar', { method: 'POST', form: formData }),
}

export const usersApi = {
  profile: (id) => api(`/api/users/${id}/profile`),
  contents: (id, params) => api(`/api/users/${id}/contents`, { params }),
}

export const postsApi = {
  list: (params) => api('/api/posts', { params }),
  detail: (id) => api(`/api/posts/${id}`),
  create: (d) => api('/api/posts', { method: 'POST', data: d }),
  update: (id, d) => api(`/api/posts/${id}`, { method: 'PUT', data: d }),
  remove: (id) => api(`/api/posts/${id}`, { method: 'DELETE' }),
  archives: () => api('/api/posts/archives')
}

export const diariesApi = {
  list: (params) => api('/api/diaries', { params }),
  detail: (id) => api(`/api/diaries/${id}`),
  create: (d) => api('/api/diaries', { method: 'POST', data: d }),
  update: (id, d) => api(`/api/diaries/${id}`, { method: 'PUT', data: d }),
  remove: (id) => api(`/api/diaries/${id}`, { method: 'DELETE' })
}

export const photosApi = {
  list: () => api('/api/photos'),
  upload: (formData) => api('/api/photos', { method: 'POST', form: formData }),
  remove: (id) => api(`/api/photos/${id}`, { method: 'DELETE' })
}

export const messagesApi = {
  list: () => api('/api/messages'),
  create: (d) => api('/api/messages', { method: 'POST', data: d }),
  remove: (id) => api(`/api/messages/${id}`, { method: 'DELETE' })
}

export const friendsApi = {
  list: () => api('/api/friends'),
  create: (d) => api('/api/friends', { method: 'POST', data: d }),
  remove: (id) => api(`/api/friends/${id}`, { method: 'DELETE' })
}

export const categoriesApi = {
  list: () => api('/api/categories'),
  create: (d) => api('/api/categories', { method: 'POST', data: d }),
  rename: (id, name) => api(`/api/categories/${id}`, { method: 'PUT', data: { name } }),
  remove: (id) => api(`/api/categories/${id}`, { method: 'DELETE' })
}

export const tagsApi = {
  list: () => api('/api/tags'),
  create: (d) => api('/api/tags', { method: 'POST', data: d }),
  rename: (id, name) => api(`/api/tags/${id}`, { method: 'PUT', data: { name } }),
  remove: (id) => api(`/api/tags/${id}`, { method: 'DELETE' })
}

export const statsApi = {
  visit: () => api('/api/stats/visit', { method: 'POST' }),
  summary: () => api('/api/stats')
}

/* 站点设置 */
export const settingsApi = {
  get: () => api('/api/settings'),
  update: (d) => api('/api/settings', { method: 'PUT', data: d }),
}
