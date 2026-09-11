const { chromium } = require('playwright-core')
const assert = require('node:assert/strict')
const fs = require('node:fs')
async function main() {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true})
  try {
    for(const width of [1440,390,320,820]) {
      const context=await browser.newContext({viewport:{width,height:width>1000?1000:844}})
      const page=await context.newPage();const errors=[];let sent=0
      await page.clock.install()
      page.on('pageerror',e=>errors.push(e.message))
      await page.route('**/api/**',async route=>{
        if(!new URL(route.request().url()).pathname.startsWith('/api/'))return route.continue()
        if(route.request().url().endsWith('/auth/login')) {
          sent++;const body=route.request().postDataJSON();assert.equal(body.register_if_missing,true)
          if(sent===1)return route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({detail:'账号或密码不正确，请检查后重试'})})
          return route.fulfill({contentType:'application/json',body:JSON.stringify({token:'mock',registered:true,user:{id:999,username:'newstudent'}})})
        }
        return route.fulfill({contentType:'application/json',body:'[]'})
      })
      await page.goto((process.env.LOGIN_TEST_BASE_URL||'http://127.0.0.1:5174')+'/login')
      await page.locator('.brand-background').evaluate(img=>img.decode())
      await page.clock.runFor(650)
      assert.equal(await page.getByText('直接输入账号密码即可注册',{exact:true}).count(),1)
      assert.equal(await page.getByText('测试账号',{exact:true}).count(),0)
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true)
      const first = await page.locator('.quote-line').innerText()
      const before = await page.locator('.login-form-panel').boundingBox()
      for (let i=0;i<6;i++) {
        await page.clock.fastForward(4000)
        await page.clock.runFor(650)
        const fits = await page.locator('.quote-line').evaluate(el => {
          const range = document.createRange(); range.selectNodeContents(el)
          const text = range.getBoundingClientRect(), box = el.getBoundingClientRect()
          return text.left >= box.left-1 && text.right <= box.right+1
        })
        assert.equal(fits, true, `quote clips at ${width}px`)
      }
      assert.equal(await page.locator('.quote-line').innerText(), first)
      assert.deepEqual(await page.locator('.login-form-panel').boundingBox(), before)
      await page.getByRole('button',{name:'暂停文案轮播'}).click()
      const paused = await page.locator('.quote-line').innerText()
      await page.clock.fastForward(8000)
      assert.equal(await page.locator('.quote-line').innerText(), paused)
      await page.mouse.move(0,0)
      fs.mkdirSync('/tmp/yishengban-login-tests',{recursive:true})
      await page.screenshot({path:`/tmp/yishengban-login-tests/login-${width}.png`,fullPage:true})
      await page.locator('input[name="username"]').fill('newstudent')
      await page.locator('input[name="password"]').fill('secure123')
      await page.getByRole('button',{name:'开始我的体验'}).click()
      await page.getByText('账号或密码不正确，请检查后重试',{exact:true}).waitFor()
      assert.equal(new URL(page.url()).pathname,'/login')
      assert.equal(await page.locator('input[name="username"]').inputValue(),'newstudent')
      await page.locator('input[name="password"]').press('Enter')
      await page.waitForURL(url=>url.pathname==='/')
      assert.equal(sent,2)
      assert.equal(errors.length,0,errors.join('\n'))
      console.log(`PASS ${width}px: blue design, six single-line quotes, stable layout, pause, no overflow, incorrect-password feedback, Enter submission and registration redirect`)
      await context.close()
    }
  } finally {await browser.close()}
}
main().catch(e=>{console.error(e);process.exitCode=1})
