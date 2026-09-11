// Local-only smoke test. Fake microphone + mocked APIs; no user data or paid calls.
const { chromium } = require('playwright-core')
const assert = require('node:assert/strict')
const fs = require('node:fs')

async function main() {
  const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true,
    args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] })
  try {
    for (const width of [1440, 390, 980]) {
      const mobile = width <= 980
      const context = await browser.newContext({ viewport: { width, height: 1000 }, permissions: ['microphone'] })
      await context.addInitScript(({ fallback }) => {
        window.__voiceTracks = []
        const acquire = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
        navigator.mediaDevices.getUserMedia = async constraints => {
          const stream = await acquire(constraints)
          window.__voiceTracks.push(...stream.getTracks())
          if (window.__delayPermission) await new Promise(resolve => setTimeout(resolve, 500))
          return stream
        }
        if (fallback) Object.defineProperty(window, 'AudioWorkletNode', { value: undefined })
        localStorage.setItem('yishengban_token', 'mock')
        localStorage.setItem('yishengban_user', JSON.stringify({ id: 1, username: 'test' }))
        localStorage.setItem('yishengban_psych_voice', 'off')
      }, { fallback: width === 980 })
      const page = await context.newPage()
      page.setDefaultTimeout(12000)
      let asrCount = 0, assessCount = 0, sent
      const errors = []
      page.on('pageerror', error => errors.push(error.message))
      await page.route('**/api/**', async route => {
        const url = route.request().url()
        if (!new URL(url).pathname.startsWith('/api/')) return route.continue()
        const body = route.request().postDataJSON()
        let data = {}
        if (url.endsWith('/voice/transcribe')) {
          const bytes = Buffer.from(body.audio, 'base64')
          assert.equal(bytes.toString('ascii', 0, 4), 'RIFF')
          assert.equal(bytes.readUInt32LE(24), 16000)
          asrCount++
          return route.fulfill({ contentType: 'text/event-stream', body: 'data: '+JSON.stringify({ type: 'text', text: asrCount === 1 ? '语音一' : '语音二' })+'\n\ndata: {"type":"done"}\n\n' })
        }
        if (url.endsWith('/voice/assess')) {
          assessCount++
          data = { receipt: 'receipt-'+assessCount, assessment: { id:String(assessCount), status:'assessed', score:83, emotion:'平稳', duration:3, impression:'声音平稳，停顿自然。', evidence:['停顿自然'], dimensions:{warmth:80} } }
        } else if (url.endsWith('/psych/chat')) { sent = body; data = { reply:'我在认真听。' } }
        else if (url.endsWith('/auth/me')) data = { id:1, username:'test' }
        else if (url.includes('quota')) data = { remaining_rmb:2, percent:0 }
        return route.fulfill({ contentType:'application/json', body:JSON.stringify(data) })
      })
      await page.goto((process.env.VOICE_TEST_BASE_URL || 'http://127.0.0.1:5174') + '/psych')
      await page.waitForTimeout(500)
      if (errors.length) throw new Error(errors.join('\n'))
      await page.getByRole('button', { name:'继续但关闭语音', exact:true }).click()
      const input = page.locator('.voice-composer textarea')
      await input.fill('前后')
      await input.evaluate(el => { el.focus(); el.setSelectionRange(1, 1); el.dispatchEvent(new Event('select', { bubbles:true })) })
      await page.getByRole('button', { name:'语音输入', exact:true }).click()
      await page.getByRole('button', { name:'同意并启用', exact:true }).click()
      const hold = page.locator('.hold-talk')
      if (mobile) {
        await page.evaluate(() => { window.__delayPermission = true })
        await hold.dispatchEvent('pointerdown', { pointerId:1 })
        await hold.dispatchEvent('pointerup', { pointerId:1 })
        await page.waitForTimeout(700)
        assert.equal(await page.evaluate(() => window.__voiceTracks.every(t => t.readyState === 'ended')), true)
        assert.equal(asrCount, 0)
        await page.evaluate(() => { window.__delayPermission = false })
      }
      for (let i=0;i<2;i++) {
        if (mobile) await hold.dispatchEvent('pointerdown', { pointerId:1 })
        else if (i) await page.getByRole('button', { name:'语音输入', exact:true }).click()
        await page.waitForFunction(() => document.querySelector('.record-status')?.textContent.includes('正在聆听')).catch(async e => { throw new Error(e.message+'\n'+await page.locator('.voice-composer').innerText()+'\n'+errors.join('\n')) })
        await page.waitForTimeout(2400)
        if (mobile) await hold.dispatchEvent('pointerup', { pointerId:1 })
        else await page.getByRole('button', { name:'停止语音输入', exact:true }).click().catch(async e => { throw new Error(e.message + '\n' + await page.locator('.voice-composer').innerText() + '\n' + errors.join('\n')) })
        await page.waitForFunction(() => !document.querySelector('.record-status'))
        assert.equal(assessCount, i+1)
        assert.equal(await page.evaluate(() => window.__voiceTracks.every(t => t.readyState === 'ended' || !t.enabled) && window.__voiceTracks.some(t => t.readyState === 'live' && !t.enabled)), true)
      }
      assert.equal(await input.inputValue(), '前语音一语音二后')
      await input.fill('前语音一语音二后，手动修订')
      await page.locator('.voice-composer summary').click()
      assert.equal(await page.locator('.voice-composer .feedback-body article').count(), 2)
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
      fs.mkdirSync('/tmp/yishengban-voice-tests', { recursive:true })
      await page.screenshot({ path:`/tmp/yishengban-voice-tests/voice-${width}.png`, fullPage:true })
      await page.locator('.voice-composer').getByRole('button', { name:'发送', exact:true }).click()
      await page.waitForFunction(() => !document.querySelector('.record-status'))
      await page.waitForTimeout(400)
      assert.equal(sent.messages.at(-1).content, '前语音一语音二后，手动修订')
      assert.equal(sent.messages.at(-1).voice_receipts.length, 2)
      assert.equal(await page.locator('.is-user .voice-feedback').count(), 1)
      assert.equal(errors.length, 0, errors.join('\n'))
      console.log(`PASS ${width}px: WAV, cursor insertion, two recordings, editing, message metadata, no overflow`)
      await context.close()
    }
  } finally { await browser.close() }
}
main().catch(error => { console.error(error); process.exitCode = 1 })
