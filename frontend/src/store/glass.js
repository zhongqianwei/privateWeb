import { reactive, watch } from 'vue'

/**
 * 玻璃材质全局参数。
 * 四层分别对应：
 *  1) opacity   —— 第一层：控件整体不透明度（越低越通透）
 *  2) scale     —— 第二层：折射取色偏移强度（来自位移贴图）
 *  3) highlight —— 第三层：边缘高光亮度（随曲面法线变化）
 *  4) shadow    —— 第四层：与背景板的距离感（投影范围）
 */
// v2：旧版会把 enabled 永久写成 false（自动降级），导致玻璃整站消失，换 key 清掉
const KEY = 'lh_glass_v2'
const DEFAULTS = {
  enabled: true,   // 只由用户手动开关，自动优化永不改动它
  lite: false,     // 弱机模式：去掉位移折射，保留模糊+边缘光（仍然是玻璃）
  opacity: 0.62,   // 0.15 ~ 1
  scale: 46,       // 0 ~ 60
  highlight: 1.35, // 0 ~ 3
  shadow: 26,      // 0 ~ 60
}

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { ...DEFAULTS }
}

export const glassStore = reactive(load())

watch(glassStore, (v) => {
  try { localStorage.setItem(KEY, JSON.stringify({ ...v })) } catch { /* ignore */ }
  applyGlass()
}, { deep: true })

/** 把参数同步到 SVG 滤镜节点与 CSS 变量 */
export function applyGlass() {
  const s = glassStore
  const root = document.documentElement
  root.style.setProperty('--g-opacity', String(s.opacity))
  root.style.setProperty('--g-scale', `${s.scale}px`)
  root.style.setProperty('--g-highlight', String(s.highlight))
  root.style.setProperty('--g-shadow', `${s.shadow}px`)
  root.dataset.glass = s.enabled ? 'on' : 'off'
  root.dataset.glassLite = s.lite ? '1' : '0'

  // SVG 滤镜属性无法读 CSS 变量，需显式写入节点属性。
  // 滤镜用 primitiveUnits="objectBoundingBox"，scale 是"元素包围盒单位"，
  // 所以滑块 0~60 需要除以 1000 换算（60 → 0.06 ≈ 元素对角线的 6%）。
  const disp = document.querySelectorAll('[data-glass-displace]')
  const spec = document.querySelectorAll('[data-glass-specular]')
  const trans = document.querySelectorAll('[data-glass-alpha]')
  disp.forEach((el) => el.setAttribute('scale', (s.scale / 1000).toFixed(4)))
  spec.forEach((el) => el.setAttribute('specularConstant', String(s.highlight)))
  trans.forEach((el) => el.setAttribute('slope', String(s.opacity)))
}

export function resetGlass() {
  Object.assign(glassStore, DEFAULTS)
}

/**
 * 判断当前设备是否走"软件渲染 / 低配"，据此自动进入 lite（只去折射，不关玻璃）。
 * 判据刻意避开"首屏 rAF 帧率"——页面刚加载时字体/接口抖动会让真显卡误判成弱机，
 * 实测导致 Intel 独显被错误降级。改用与硬件强相关、稳定的信号：
 *  1) WebGL renderer 含 SwiftShader / llvmpipe / Software（浏览器禁用了 GPU）；
 *  2) 逻辑核 ≤ 4 且内存 ≤ 4GB 的低配机；
 *  3) 仅在明确已知"连续滚动帧率过低"(<28) 时才补充降级。
 * measuredFps 为滚动场景采样；静止首屏帧率不要传进来。
 * 只在未降级时生效，尊重用户手动设置。
 */
export function autoDowngradeIfWeak(measuredFps) {
  if (glassStore.lite) return false

  let weak = false

  // 信号一（最准）：GPU 是否被禁用 / 软件渲染
  try {
    const c = document.createElement('canvas')
    const gl = c.getContext('webgl') || c.getContext('experimental-webgl')
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info')
      const r = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : ''
      if (/swiftshader|llvmpipe|software|basic render/i.test(r)) weak = true
      const lose = gl.getExtension('WEBGL_lose_context')
      if (lose) lose.loseContext()
    }
  } catch { /* 无 WebGL 信息，跳过该信号 */ }

  // 信号二：低配硬件
  if (!weak) {
    const cores = navigator.hardwareConcurrency || 8
    const mem = navigator.deviceMemory || 8
    if (cores <= 4 && mem <= 4) weak = true
  }

  // 信号三：明确的滚动低帧率（阈值压到 28，避免首屏抖动误判）
  if (!weak && measuredFps != null && measuredFps < 28) weak = true

  if (weak) {
    glassStore.lite = true
    return true
  }
  return false
}
