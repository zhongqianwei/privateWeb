/**
 * UI 自检：桌面 + 移动端逐页截图，收集控制台错误与横向溢出。
 * 用法：node check-ui.mjs
 */
import puppeteer from 'puppeteer-core'
import { mkdirSync } from 'node:fs'

const BASE = process.env.BASE || 'http://127.0.0.1:8000'
const OUT = new URL('./qa/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
mkdirSync(OUT, { recursive: true })

const routes = [
  'home', 'posts', 'diary', 'gallery', 'about', 'archive',
  'friends', 'messages', 'stats', 'login', 'posts/1', 'posts/new', 'u/1',
]

const sizes = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
]

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
})

const report = []

for (const size of sizes) {
  const page = await browser.newPage()
  await page.setViewport({ width: size.width, height: size.height, deviceScaleFactor: 1 })
  for (const route of routes) {
    const errors = []
    page.removeAllListeners('console')
    page.removeAllListeners('pageerror')
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
    page.on('pageerror', (e) => errors.push(String(e)))
    try {
      await page.goto(`${BASE}/#/${route}`, { waitUntil: 'networkidle0', timeout: 25000 })
      await new Promise((r) => setTimeout(r, 450))
      const info = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        bodyText: document.body.innerText.slice(0, 80),
        images: [...document.images].map((i) => i.currentSrc || i.src).filter(Boolean),
        bgImages: getComputedStyle(document.body).backgroundImage,
      }))
      const file = `${OUT}${size.name}-${route.replace(/\//g, '_')}.png`
      await page.screenshot({ path: file, fullPage: false })
      report.push({ size: size.name, route, overflow: info.overflow, errors, images: info.images.length, file })
    } catch (e) {
      report.push({ size: size.name, route, fatal: String(e), errors })
    }
  }
  await page.close()
}

await browser.close()

const bad = report.filter((r) => r.fatal || r.errors.length || (r.overflow ?? 0) > 2)
console.log(JSON.stringify({
  total: report.length,
  passed: report.length - bad.length,
  bad,
  all: report.map(({ size, route, overflow, errors, images }) => ({ size, route, overflow, errors, images })),
}, null, 2))
if (bad.length) process.exit(1)
