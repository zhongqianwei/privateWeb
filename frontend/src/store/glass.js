/**
 * 玻璃系统 v3：SVG 位移滤镜方案已移除（滚动重影与掉帧的根源）。
 * 新实现是 style.css 里的标准 backdrop-filter，无需运行时参数。
 * 保留导出以兼容旧引用（App.vue / 旧面板），全部为无操作。
 */
import { reactive } from 'vue'

export const glassStore = reactive({
  enabled: true,
  lite: false,
  opacity: 0.62,
  scale: 46,
  highlight: 1.35,
  shadow: 26,
})

export function applyGlass() {
  /* no-op：材质全部由 CSS 声明 */
}

export function autoDowngradeIfWeak() {
  return true
}

export function resetGlass() {
  Object.assign(glassStore, {
    enabled: true,
    lite: false,
    opacity: 0.62,
    scale: 46,
    highlight: 1.35,
    shadow: 26,
  })
}
