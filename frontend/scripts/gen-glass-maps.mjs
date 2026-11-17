/**
 * 玻璃折射位移贴图生成器（零依赖）—— Snell 定律 + 超椭圆倒角
 *
 * 物理模型（参考文献见文末注释）：
 *   1) 形状：圆角矩形有向距离场 d。d<0 在内部，depth=-d 即"离边缘有多远"。
 *   2) 剖面：真实玻璃的倒角截面是 y(t) = (1-(1-t)^p)^(1/p)，
 *      t=0 在最外沿（切线垂直，等于侧壁），t=1 在平坦顶面（切线水平）。
 *      p=2 是正圆弧，p=4 是超椭圆（苹果 squircle）——两者都是 C1 连续，
 *      即"边缘到中心平滑过渡"，不会出现棱/折角。
 *   3) 折射：光线穿过倾斜表面时按 Snell 定律偏折
 *        θs = atan(slope)            表面倾角
 *        θr = asin(sinθs / n)        折射角，n=1.5168（BK7 冕牌玻璃）
 *        Δ  = thickness(t)·tan(θs-θr) 横向位移
 *      并按 Fresnel 透射率 (1-R) 加权：掠射角处几乎全反射，所以边缘反而
 *      变亮、不再继续位移——这同时解释了玻璃边缘那条亮线。
 *   ⚠️ 不能用 Δ ∝ 斜率：斜率式等于 ½sin2θ，在 45° 处最大、到边缘归零，
 *      恰好在最该弯的地方出现"死区"，边缘会被压成一条硬线。
 *
 * 输出 RGBA PNG（512×512）：
 *   R = 128 + 横向偏移（128 = 零偏移）
 *   G = 128 + 纵向偏移
 *   B = 倒角高度场（0=外沿，255=平坦中心），供高光层重建法线
 *   A = 255
 */
import { deflateSync } from 'node:zlib'
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
// 输出到 src/assets：由 Vite 以 ?inline 方式内联成 data URI。
// ⚠️ feImage 引用外部 URL 在 Chromium 的 CSS backdrop-filter 里不生效（输出为空），
//    必须内联，否则整条折射链静默失效。
const OUT = join(HERE, '..', 'src', 'assets', 'glass')
mkdirSync(OUT, { recursive: true })

/* ---------- 纯 JS PNG 编码 ---------- */
const CRC_TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()
function crc32(buf) {
  let c = 0xffffffff
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0)
  const tag = Buffer.from(type, 'ascii')
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(Buffer.concat([tag, data])), 0)
  return Buffer.concat([len, tag, data, crc])
}
function encodePNG(width, height, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4)
  ihdr[8] = 8; ihdr[9] = 6 // 8-bit RGBA
  const stride = width * 4
  const raw = Buffer.alloc((stride + 1) * height)
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride)
  }
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

/* ---------- 玻璃截面数学 ---------- */
const clamp = (v, a, b) => Math.min(b, Math.max(a, v))
const IOR = 1.5168            // BK7 冕牌玻璃
const R0 = ((IOR - 1) / (IOR + 1)) ** 2

/** 倒角剖面：0=最外沿，1=平坦顶面。p=4 超椭圆 / p=2 正圆 */
const profile = (t, p = 4) => Math.pow(Math.max(0, 1 - Math.pow(1 - t, p)), 1 / p)
/** 剖面斜率 dy/dt（无因次，t→0 时发散 = 垂直侧壁） */
function dProfile(t, p = 4) {
  const u = 1 - t
  const s = 1 - Math.pow(u, p)
  if (s <= 1e-6) return 40                 // 外沿：数值上限，等价于垂直侧壁
  return Math.min(40, Math.pow(u, p - 1) / Math.pow(s, (p - 1) / p))
}

/**
 * 折射量 = 物理量级 × 径向权重。
 *
 * 为什么拆开：理想倒角在外沿切线垂直（斜率→∞），Snell 偏差在贴边 1px 内就发散，
 * 归一化后整条曲线的 99% 被压进最外两三像素——渲染出来是一条硬折线，
 * 也就是"棱角/金属"感的来源。真实玻璃板外沿有一圈微小圆角（fillet）把尖峰磨平，
 * 所以这里用 (1-t²)^1.5 做径向权重：两端导数都为 0，C1 连续，
 * 扫成圆角矩形后拐角处不会出现接缝断裂。
 *
 * @param {number} t 倒角归一化位置 0(外沿)→1(平坦顶面)
 */
const lensWeight = (t) => Math.pow(1 - t * t, 1.5)

/** 边缘处的物理偏差量级（用于换算 feDisplacementMap.scale），t 取倒角最陡处 */
function physicalPeak(kA, p = 4) {
  const slope = dProfile(0.1, p) * kA
  const thetaS = Math.atan(slope)
  const sinR = Math.sin(thetaS) / IOR
  const thetaR = Math.asin(sinR > 1 ? 1 : sinR)
  return Math.tan(thetaS - thetaR)
}

// 圆角矩形有符号距离场；r 接近 hy 时退化为胶囊
function sdfRoundRect(x, y, hx, hy, r) {
  const qx = Math.abs(x) - (hx - r)
  const qy = Math.abs(y) - (hy - r)
  return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r
}

const SHAPES = {
  // 倒角带收窄（8% ≈ 卡片上 10~14px），位移集中在薄薄一圈里，
  // 才能出现照片中那种"边缘被压缩/复制"的强折射，而不是均匀的一层雾。
  panel:  { hx: 1, hy: 1,    r: 0.24, bezel: 0.16, kA: 0.55, p: 4, size: 256 },
  pill:   { hx: 1, hy: 0.40, r: 0.40, bezel: 0.26, kA: 0.55, p: 4, size: 256 },
  circle: { hx: 1, hy: 1,    r: 1,    bezel: 0.18, kA: 0.55, p: 2, size: 256 },
}

function buildMap(shape, cfg) {
  const { size, bezel, kA, p } = cfg
  const heights = new Float32Array(size * size)
  const deltas = new Float32Array(size * size)
  const dirX = new Float32Array(size * size)
  const dirY = new Float32Array(size * size)
  const eps = Math.max(bezel * 0.3, 1.5 / size)   // 宽步长求梯度，避免中轴塌陷
  let peak = 1e-6

  const sdfAt = (u, v) => {
    const x = u * 2 - 1
    const y = v * 2 - 1
    return { d: sdfRoundRect(x, y, cfg.hx, cfg.hy, cfg.r), x, y }
  }

  for (let py = 0; py < size; py++) {
    for (let px = 0; px < size; px++) {
      const u = (px + 0.5) / size
      const v = (py + 0.5) / size
      const i = py * size + px
      const { d } = sdfAt(u, v)
      // t：0=外沿，1=平坦顶面开始处
      const t = clamp(-d / bezel, 0, 1)

      // 朝内方向 = -∇d（指向玻璃中心）
      const gx = (sdfAt(u + eps / 2, v).d - sdfAt(u - eps / 2, v).d) / eps
      const gy = (sdfAt(u, v + eps / 2).d - sdfAt(u, v - eps / 2).d) / eps
      const gl = Math.hypot(gx, gy) || 1

      // 位移在倒角内平滑收敛到 0（refract 内已含 C1 透镜权重）
      const delta = lensWeight(t)

      deltas[i] = delta
      dirX[i] = -gx / gl
      dirY[i] = -gy / gl
      // 高光用的高度场：只在外侧 18% 倒角内抬升，法线集中在细窄的一圈，
      // 高光才会是"一条亮线"而不是一整片发白的金属反光。
      heights[i] = profile(clamp(t / 0.18, 0, 1), p)
      if (delta > peak) peak = delta
    }
  }

  const rgba = Buffer.alloc(size * size * 4)
  for (let i = 0; i < size * size; i++) {
    const m = deltas[i] / peak
    rgba[i * 4] = Math.round(clamp(128 + dirX[i] * m * 127, 0, 255))
    rgba[i * 4 + 1] = Math.round(clamp(128 + dirY[i] * m * 127, 0, 255))
    rgba[i * 4 + 2] = Math.round(heights[i] * 255)
    rgba[i * 4 + 3] = 255
  }
  const png = encodePNG(size, size, rgba)
  writeFileSync(join(OUT, `displacement-${shape}.png`), png)

  // 剖面自检：打印 Δ 沿倒角的衰减曲线，边缘应最大、向内单调收敛
  const probe = [0, 0.05, 0.15, 0.3, 0.5, 0.75, 1].map((t) =>
    (lensWeight(t) / peak).toFixed(3))
  console.log(
    `${shape.padEnd(7)} ${size}x${size} ${(png.length / 1024).toFixed(1)}KB  ` +
    `bezel=${(bezel * 100).toFixed(0)}%  phys=${physicalPeak(kA, p).toFixed(2)}  ` +
    `Δtcurve=[${probe.join(' ')}]`
  )
}

function smoothstep(a, b, x) {  const t = clamp((x - a) / (b - a), 0, 1)
  return t * t * (3 - 2 * t)
}

for (const [shape, cfg] of Object.entries(SHAPES)) buildMap(shape, cfg)

/* 额外产出 JS 模块：把 base64 直接写死。
   Vite 的 ?inline 对 >4KB 资源不生效，而 feImage 又只认内联 data URI，
   所以这里自己生成常量，绕开打包器的资源处理。 */
const constName = { panel: 'panel', pill: 'pill', circle: 'circle' }
const lines = [
  '/* 自动生成，请勿手改。源：scripts/gen-glass-maps.mjs */',
]
for (const shape of Object.keys(SHAPES)) {
  const b64 = readFileSync(join(OUT, `displacement-${shape}.png`)).toString('base64')
  lines.push(`export const ${constName[shape]} = 'data:image/png;base64,${b64}'`)
}
writeFileSync(join(HERE, '..', 'src', 'assets', 'glass-maps.js'), lines.join('\n') + '\n')
console.log('位移贴图已生成到 src/assets/glass/ + glass-maps.js')

/* 参考文献
 * - kube.io/blog/liquid-glass-css-svg  : 四种剖面函数与 Snell 光线追踪推导
 * - liquidglass.shayxo.dev/research/optical-model : 超椭圆 h=(1-(1-e)^p)^(1/p)、
 *   精确 Snell 偏差（避免 slope·(1-1/n) 近似）、朝外/朝内方向之争
 * - npmjs.com/package/@sohumsuthar/liquid-glass : 不要用 Δ∝斜率（45° 峰值 + 边缘死区）
 * - github.com/styropyr0/Prismal : 四分之一圆剖面 √(2t-t²)、双边缘 rim 高光
 */
