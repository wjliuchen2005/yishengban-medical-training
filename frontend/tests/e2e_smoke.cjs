const { chromium } = require('playwright')

async function run() {
  const launchOptions = { headless: true }
  if (process.env.CHROME_PATH) launchOptions.executablePath = process.env.CHROME_PATH
  const browser = await chromium.launch(launchOptions)
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  const consoleErrors = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  await page.addInitScript(() => {
    localStorage.setItem('yilutong_token', 'visual-test-token')
    localStorage.setItem('yilutong_user', JSON.stringify({ id: 1, username: 'test', real_name: '测试用户' }))
  })

  await page.goto('http://127.0.0.1:5173/chat/2')
  await page.waitForLoadState('networkidle')
  await page.getByRole('dialog', { name: '训练前设置' }).waitFor()
  await page.getByText('女', { exact: true }).click()
  await page.getByRole('button', { name: '生成训练情景' }).click()
  await page.getByText('本次情景', { exact: true }).waitFor()

  const opening = await page.locator('.scene-brief').innerText()
  if (!opening.includes('第一步') || !opening.includes('挂号')) {
    throw new Error(`首次看病开场没有明确挂号第一步：${opening}`)
  }
  if (opening.includes('医生您好...我有点紧张')) {
    throw new Error('首次看病仍然使用患者台词作为开场')
  }

  await page.getByRole('button', { name: /线上预约挂号/ }).click()
  await page.getByText('观察者教练', { exact: true }).first().click()
  await page.getByText('所有提示都会保留在这里', { exact: false }).waitFor()
  const coachDrawerText = await page.locator('.coach-history').innerText()
  if (!coachDrawerText.includes('说明挂号方式后')) {
    throw new Error('观察者教练记录未保留演示提示')
  }
  await page.screenshot({ path: '/tmp/yilutong-chat-review.png', fullPage: true })

  await page.goto('http://127.0.0.1:5173/result/demo')
  await page.waitForLoadState('networkidle')
  await page.getByText('决策路径对比', { exact: true }).waitFor()
  await page.getByText('病史信息完整度', { exact: true }).waitFor()
  const resultText = await page.locator('main').innerText()
  if (!resultText.includes('对话与决策回放') || !resultText.includes('综合评语')) {
    throw new Error('评分页缺少回放或综合评语')
  }
  await page.screenshot({ path: '/tmp/yilutong-result-review.png', fullPage: true })

  await page.setViewportSize({ width: 390, height: 844 })
  await page.reload()
  await page.waitForLoadState('networkidle')
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  if (hasHorizontalOverflow) throw new Error('移动端评分页出现水平溢出')
  await page.screenshot({ path: '/tmp/yilutong-result-mobile.png', fullPage: true })

  console.log(JSON.stringify({
    chatOpening: opening,
    coachHistory: coachDrawerText,
    consoleErrors,
    screenshots: ['/tmp/yilutong-chat-review.png', '/tmp/yilutong-result-review.png', '/tmp/yilutong-result-mobile.png']
  }, null, 2))
  await browser.close()
}

run().catch((error) => {
  console.error(error)
  process.exit(1)
})
