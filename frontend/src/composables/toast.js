import { reactive } from 'vue'

/** 极简 toast */
export const toastState = reactive({ list: [] })
let seq = 0

export function toast(msg, type = 'info', dur = 2600) {
  const id = ++seq
  toastState.list.push({ id, msg, type })
  setTimeout(() => {
    const i = toastState.list.findIndex((t) => t.id === id)
    if (i !== -1) toastState.list.splice(i, 1)
  }, dur)
}
