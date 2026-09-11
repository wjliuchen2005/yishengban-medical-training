const { chromium } = require('playwright-core')
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const projectRoot = path.resolve(__dirname, '..')
const frontendRoot = path.join(projectRoot, 'frontend')
const outputRoot = path.join(projectRoot, 'exports', 'digital-human-avatars')
const port = 5197
const origin = `http://127.0.0.1:${port}`
const width = 2160
const height = 2430

const roles = [
  ['narrator', '情景旁白'],
  ['patient', '患者同学'],
  ['registrar', '挂号员'],
  ['doctor', '接诊医生'],
  ['cashier', '收费员'],
  ['pharmacist', '药师'],
  ['coach', '观察者教练'],
  ['psych', '易心']
]

const actionExpression = {
  idle: 'neutral', idleClap: 'happy', idleStretch: 'happy', idleChoke: 'choking',
  deepBreath: 'concerned', waveHigh: 'anxious', clutchThroat: 'choking',
  chestPat: 'relieved', startledPant: 'surprised', slump: 'listless',
  reachOut: 'calm', nod: 'calm', shakeHead: 'confused', explain: 'explaining', psychOpen: 'calm'
}

const actions = [
  ['idle', '待机', 'doctor', 'other', 0],
  ['idleClap', '拍手', 'doctor', 'other', 0],
  ['idleStretch', '外展双臂', 'doctor', 'other', 0],
  ['idleChoke', '捂喉干呕', 'patient', 'choking', 0.55],
  ['deepBreath', '深呼吸', 'patient', 'choking', 0],
  ['waveHigh', '高臂挥手', 'doctor', 'other', 0],
  ['clutchThroat', '捂住脖子', 'patient', 'choking', 0.72],
  ['chestPat', '拍胸脯', 'patient', 'choking', 0],
  ['startledPant', '受惊后喘气', 'patient', 'choking', 0],
  ['slump', '瘫软无力', 'patient', 'choking', 0.9],
  ['reachOut', '伸手', 'registrar', 'firstVisit', 0],
  ['nod', '点头', 'doctor', 'other', 0],
  ['shakeHead', '摇头', 'patient', 'firstVisit', 0],
  ['explain', '摆手说明', 'coach', 'other', 0],
  ['psychOpen', '温柔摊手', 'psych', 'psych', 0]
]

const expressions = [
  ['neutral', '平静'], ['calm', '从容'], ['smile', '微笑'], ['happy', '开心'],
  ['crying', '流泪'], ['anxious', '着急'], ['confused', '疑惑'], ['concerned', '担忧'],
  ['suffering', '窒息难受'], ['collapsed', '支撑不住'], ['listless', '精神萎靡'],
  ['explaining', '在说明'], ['observing', '在观察'], ['relieved', '松了口气'],
  ['angry', '激动'], ['surprised', '惊讶'], ['choking', '异物哽咽'],
  ['sad', '难过'], ['tired', '累了']
]

function cleanOutput() {
  fs.rmSync(outputRoot, { recursive: true, force: true })
  for (const format of ['svg', 'png']) {
    for (const group of ['appearances', 'actions', 'expressions', 'speaking']) {
      fs.mkdirSync(path.join(outputRoot, format, group), { recursive: true })
    }
  }
}

async function waitForServer() {
  for (let i = 0; i < 80; i++) {
    try {
      const response = await fetch(`${origin}/avatar-export.html`)
      if (response.ok) return
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 150))
  }
  throw new Error('Vite export page did not start')
}

async function standaloneSvg(page, mouthScale = null) {
  return page.evaluate(async ({ width, height, mouthScale }) => {
    const source = document.querySelector('.robot-svg')
    const svg = source.cloneNode(true)
    if (mouthScale !== null) {
      const mouth = svg.querySelector('.talk-mouth')
      const translateY = 197 * (1 - mouthScale)
      mouth?.removeAttribute('style')
      mouth?.setAttribute('transform', `matrix(1 0 0 ${mouthScale} 0 ${translateY})`)
    }
    for (const image of svg.querySelectorAll('image')) {
      const href = image.getAttribute('href')
      if (!href || href.startsWith('data:')) continue
      const response = await fetch(new URL(href, location.href))
      const blob = await response.blob()
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
      image.setAttribute('href', dataUrl)
    }
    svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    svg.setAttribute('width', String(width))
    svg.setAttribute('height', String(height))
    svg.setAttribute('viewBox', '0 0 320 360')
    svg.removeAttribute('class')
    return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(svg)}`
  }, { width, height, mouthScale })
}

async function writePng(page, svg, destination) {
  const encoded = Buffer.from(svg).toString('base64')
  await page.setContent(`<style>*{box-sizing:border-box}html,body{margin:0;width:${width}px;height:${height}px;overflow:hidden;background:transparent}img{display:block;width:${width}px;height:${height}px}</style><img alt="" src="data:image/svg+xml;base64,${encoded}">`)
  await page.locator('img').evaluate((image) => image.decode())
  await page.screenshot({ path: destination, omitBackground: true })
}

async function main() {
  cleanOutput()
  const vite = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
    cwd: frontendRoot,
    stdio: ['ignore', 'ignore', 'inherit']
  })
  let browser
  try {
    await waitForServer()
    browser = await chromium.launch({
      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      headless: true
    })
    const sourceContext = await browser.newContext({ viewport: { width: 320, height: 360 }, reducedMotion: 'reduce' })
    const page = await sourceContext.newPage()
    await page.goto(`${origin}/avatar-export.html`)
    await page.waitForFunction(() => Boolean(window.__avatarExport))

    const motionContext = await browser.newContext({ viewport: { width: 320, height: 360 }, reducedMotion: 'no-preference' })
    const motionPage = await motionContext.newPage()
    await motionPage.goto(`${origin}/avatar-export.html`)
    await motionPage.waitForFunction(() => Boolean(window.__avatarExport))

    const pngContext = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 })
    const pngPage = await pngContext.newPage()
    const manifest = []

    async function render(group, order, key, label, props, options = {}) {
      const renderPage = options.motionDelay ? motionPage : page
      if (options.motionDelay) {
        await renderPage.evaluate(() => window.__avatarExport.set({ role: 'doctor', action: 'idle', expression: 'neutral', scene: 'other', pressure: 0, speaking: false }))
      }
      await renderPage.evaluate((next) => window.__avatarExport.set(next), props)
      if (options.motionDelay) await renderPage.waitForTimeout(options.motionDelay)
      const svg = await standaloneSvg(renderPage, options.mouthScale ?? null)
      const stem = `${String(order).padStart(2, '0')}-${key}`
      const svgRelative = path.join('svg', group, `${stem}.svg`)
      const pngRelative = path.join('png', group, `${stem}.png`)
      fs.writeFileSync(path.join(outputRoot, svgRelative), svg)
      await writePng(pngPage, svg, path.join(outputRoot, pngRelative))
      manifest.push({ group, key, label, width, height, props, svg: svgRelative, png: pngRelative })
      process.stdout.write(`rendered ${group}/${stem}\n`)
    }

    for (let i = 0; i < roles.length; i++) {
      const [role, label] = roles[i]
      await render('appearances', i + 1, role, label, { role, action: 'idle', expression: 'neutral', scene: role === 'psych' ? 'psych' : 'other', pressure: 0, speaking: false })
    }
    for (let i = 0; i < actions.length; i++) {
      const [action, label, role, scene, pressure] = actions[i]
      await render('actions', i + 1, action, label, { role, action, expression: actionExpression[action], scene, pressure, speaking: false }, action === 'slump' ? { motionDelay: 1650 } : {})
    }
    for (let i = 0; i < expressions.length; i++) {
      const [expression, label] = expressions[i]
      const choking = ['choking', 'suffering', 'collapsed'].includes(expression)
      await render('expressions', i + 1, expression, label, { role: choking ? 'patient' : 'psych', action: expression === 'collapsed' ? 'slump' : 'idle', expression, scene: choking ? 'choking' : 'psych', pressure: expression === 'choking' ? 0.55 : 0, speaking: false }, expression === 'collapsed' ? { motionDelay: 1650 } : {})
    }

    const speaking = [
      ['patient-small', '患者说话·小口型', 'patient', 'firstVisit', 0.34],
      ['patient-medium', '患者说话·中口型', 'patient', 'firstVisit', 0.62],
      ['patient-wide', '患者说话·大口型', 'patient', 'firstVisit', 1],
      ['doctor-wide', '医护说话·大口型', 'doctor', 'other', 1],
      ['psych-wide', '易心说话·大口型', 'psych', 'psych', 1]
    ]
    for (let i = 0; i < speaking.length; i++) {
      const [key, label, role, scene, mouthScale] = speaking[i]
      await render('speaking', i + 1, key, label, { role, action: 'explain', expression: 'explaining', scene, pressure: 0, speaking: true }, { mouthScale })
    }

    fs.writeFileSync(path.join(outputRoot, 'manifest.json'), JSON.stringify({ generated_at: new Date().toISOString(), width, height, transparent_background: true, count: manifest.length, items: manifest }, null, 2))
    const rows = manifest.map((item) => `| ${item.group} | ${item.label} | ${item.key} | ${item.svg} | ${item.png} |`).join('\n')
    fs.writeFileSync(path.join(outputRoot, 'README.md'), `# 易生伴数字人导出\n\n共 ${manifest.length} 个状态。SVG 与透明 PNG 一一对应；PNG 为 ${width} × ${height}px。\n\n| 分组 | 中文名 | 状态键 | SVG | PNG |\n|---|---|---|---|---|\n${rows}\n`)
    await pngContext.close()
    await motionContext.close()
    await sourceContext.close()
  } finally {
    await browser?.close()
    vite.kill('SIGTERM')
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
