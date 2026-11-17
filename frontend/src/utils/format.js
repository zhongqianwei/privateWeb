export function formatDate(value, withTime = false) {
  if (!value) return ''
  const d = new Date(String(value).replace(/-/g, '/'))
  if (Number.isNaN(d.getTime())) return String(value).slice(0, 10)
  const pad = (n) => String(n).padStart(2, '0')
  const base = `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`
  return withTime ? `${base} ${pad(d.getHours())}:${pad(d.getMinutes())}` : base
}

export function plainText(text = '') {
  return String(text)
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_`~|>-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function readingTime(text = '') {
  const count = plainText(text).length
  return Math.max(1, Math.ceil(count / 400))
}

export function excerpt(text = '', len = 140) {
  const t = plainText(text)
  return t.length > len ? t.slice(0, len) + '…' : t
}
