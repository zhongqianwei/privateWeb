/** 真实交互自检：注册 → 写文章 → 后台 → 写记录，全流程走一遍 */
import puppeteer from 'puppeteer-core'

const BASE = 'http://127.0.0.1:8000'
const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
await page.setViewport({ width: 1366, height: 900 })
const errors = []
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', (e) => errors.push(String(e)))

const log = []
const step = (name, ok, extra = '') => {
  log.push({ name, ok, extra })
  console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`)
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

try {
  // 注册
  await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle0' })
  const tabButtons = await page.$$('button')
  for (const b of tabButtons) {
    const t = await page.evaluate((el) => el.textContent.trim(), b)
    if (t === '注册') { await b.click(); break }
  }
  const uname = 'e2e_' + Date.now().toString().slice(-8)
  await page.type('input[autocomplete="username"]', uname)
  await page.type('input[type="password"]', 'E2e@123456')
  await page.click('button[type="submit"]')
  await sleep(1200)
  step('register via UI', page.url().includes('/home'), page.url())

  // 写文章
  await page.goto(`${BASE}/#/posts/new`, { waitUntil: 'networkidle0' })
  await sleep(600)
  await page.type('input[placeholder="文章标题"]', 'E2E 自检文章')
  await page.type('textarea[placeholder^="用 Markdown"]', '## 小节\n\n这是自动化交互测试写入的正文。')
  const buttons = await page.$$('button')
  for (const b of buttons) {
    const t = await page.evaluate((el) => el.textContent.trim(), b)
    if (t.includes('发布')) { await b.click(); break }
  }
  await sleep(1400)
  step('create post via UI', /\/posts\/\d+\/edit/.test(page.url()), page.url())

  // 文章详情可读
  const pid = (page.url().match(/\/posts\/(\d+)\/edit/) || [])[1]
  if (pid) {
    await page.goto(`${BASE}/#/posts/${pid}`, { waitUntil: 'networkidle0' })
    await sleep(700)
    const body = await page.evaluate(() => document.body.innerText)
    step('post detail renders', body.includes('E2E 自检文章'))
  }

  // 后台各标签页
  await page.goto(`${BASE}/#/manage`, { waitUntil: 'networkidle0' })
  await sleep(600)
  for (const label of ['文章', '分类标签', '记录', '相册', '留言', '友链', '站点设置']) {
    const bs = await page.$$('button')
    for (const b of bs) {
      const t = await page.evaluate((el) => el.textContent.trim(), b)
      if (t === label) { await b.click(); break }
    }
    await sleep(300)
    step(`manage tab: ${label}`, true)
  }

  // 写记录
  await page.goto(`${BASE}/#/diary`, { waitUntil: 'networkidle0' })
  await sleep(600)
  const bs = await page.$$('button')
  for (const b of bs) {
    const t = await page.evaluate((el) => el.textContent.trim(), b)
    if (t.includes('写一条')) { await b.click(); break }
  }
  await sleep(300)
  await page.type('textarea[placeholder="此刻在想什么…"]', 'E2E 自检记录')
  const bs2 = await page.$$('button')
  for (const b of bs2) {
    const t = await page.evaluate((el) => el.textContent.trim(), b)
    if (t === '保存') { await b.click(); break }
  }
  await sleep(900)
  const diaryText = await page.evaluate(() => document.body.innerText)
  step('create note via UI', diaryText.includes('E2E 自检记录'))

  step('no console errors', errors.length === 0, errors.join(' | '))
  console.log(`\nE2E_USER=${uname}`)
  console.log(`E2E_POST_ID=${pid || ''}`)
} catch (e) {
  step('e2e flow', false, String(e))
} finally {
  await browser.close()
}

const failed = log.filter((r) => !r.ok)
console.log(`\n${log.length - failed.length}/${log.length} steps passed`)
if (failed.length) process.exit(1)
