// Regression: recording must remain available while prior ASR/assessment is pending.
const { chromium } = require('playwright-core')
const assert = require('node:assert/strict')
async function main() {
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']})
 try {
  for (const fallback of [false,true]) {
   const context=await browser.newContext({viewport:{width:390,height:1000},permissions:['microphone']})
   await context.addInitScript(({fallback})=>{
    localStorage.setItem('yishengban_token','mock');localStorage.setItem('yishengban_user',JSON.stringify({id:1,username:'test'}));localStorage.setItem('yishengban_psych_voice','off')
    window.__tracks=[];window.__contexts=0;window.__getMediaCalls=0;window.__delay=250;window.__hangResume=false
    const get=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
    navigator.mediaDevices.getUserMedia=async options=>{window.__getMediaCalls++;const s=await get(options);window.__tracks.push(...s.getTracks());await new Promise(r=>setTimeout(r,window.__delay));return s}
    const Native=window.AudioContext
    window.AudioContext=class extends Native {constructor(...args){super(...args);window.__contexts++}resume(){return window.__hangResume?new Promise(()=>{}):super.resume()}}
    if(fallback)Object.defineProperty(window,'AudioWorkletNode',{value:undefined})
   },{fallback})
   const page=await context.newPage();page.setDefaultTimeout(15000)
   const errors=[];page.on('pageerror',e=>errors.push(e.message))
   const assessments=[];let asrCount=0,releaseFirst,sendBody
   const firstGate=new Promise(r=>releaseFirst=r)
   await page.route('**/api/**',async route=>{
    const url=new URL(route.request().url());if(!url.pathname.startsWith('/api/'))return route.continue()
    if(url.pathname.endsWith('/voice/transcribe')){
     const n=++asrCount;if(n===1)await firstGate
     return route.fulfill({contentType:'text/event-stream',body:`data: ${JSON.stringify({type:'text',text:`第${n}段`})}\n\ndata: {"type":"done"}\n\n`})
    }
    if(url.pathname.endsWith('/voice/assess')){assessments.push(route);return}
    if(url.pathname.endsWith('/psych/chat'))sendBody=route.request().postDataJSON()
    return route.fulfill({contentType:'application/json',body:JSON.stringify(url.pathname.endsWith('/psych/chat')?{reply:'收到。'}:{})})
   })
   await page.goto((process.env.VOICE_TEST_BASE_URL||'http://127.0.0.1:5174')+'/psych')
   await page.getByRole('button',{name:'继续但关闭语音',exact:true}).click()
   const input=page.locator('.voice-composer textarea');await input.fill('前后')
   await input.evaluate(el=>{el.focus();el.setSelectionRange(1,1);el.dispatchEvent(new Event('select',{bubbles:true}))})
   await page.getByRole('button',{name:'语音输入',exact:true}).click()
   await page.getByRole('button',{name:'同意并启用',exact:true}).click()
   const hold=page.locator('.hold-talk')
   for(let i=0;i<3;i++) {
    await hold.dispatchEvent('pointerdown',{pointerId:i+1})
    await page.waitForFunction(()=>document.querySelector('.record-status')?.textContent.includes('正在聆听'),null,{timeout:2500})
    await page.waitForTimeout(1250)
    await hold.dispatchEvent('pointerup',{pointerId:i+1})
    assert.equal(await hold.isEnabled(),true,'prior ASR and assessment must not block the next recording')
    assert.equal(await page.evaluate(()=>window.__tracks.every(t=>t.readyState==='live' && !t.enabled)),true,'released recording must park the mic without capturing')
   }
   assert.equal(await page.evaluate(()=>window.__contexts),1,'reuse the unlocked AudioContext across recordings')
   assert.equal(await page.evaluate(()=>window.__getMediaCalls),1,'repeated iPhone presses must reuse the authorized microphone stream')
   releaseFirst()
   await page.waitForFunction(()=>document.querySelector('.voice-composer textarea')?.value==='前第1段第2段第3段后')
   assert.equal(assessments.length,3)
   for(const index of [2,0,1])await assessments[index].fulfill({contentType:'application/json',body:JSON.stringify({receipt:`receipt-${index+1}`,assessment:{id:String(index+1),status:'limited',duration:1.3,impression:`反馈${index+1}`}})})
   await page.waitForFunction(()=>!document.querySelector('.record-status'))
   await page.locator('.voice-composer summary').click()
   const feedback=await page.locator('.voice-composer .feedback-body article').allTextContents()
   assert.ok(feedback[0].includes('反馈1')&&feedback[1].includes('反馈2')&&feedback[2].includes('反馈3'),'out-of-order responses must keep recording order')
   // A hung resume must time out, release the mic and allow a later press.
   await page.evaluate(()=>{window.__hangResume=true})
   await hold.dispatchEvent('pointerdown',{pointerId:8})
   await page.waitForFunction(()=>document.querySelector('.voice-error')?.textContent.includes('启动超时'),null,{timeout:11000})
   assert.equal(await page.evaluate(()=>window.__tracks.every(t=>t.readyState==='ended')),true)
   await hold.dispatchEvent('pointerup',{pointerId:8})
   await page.evaluate(()=>{window.__hangResume=false;window.__delay=500})
   await hold.dispatchEvent('pointerdown',{pointerId:9})
   await hold.dispatchEvent('pointerup',{pointerId:9})
   await page.waitForTimeout(750)
   assert.equal(await page.evaluate(()=>window.__tracks.every(t=>t.readyState==='ended')),true,'late permission result after release must close tracks')
   await page.locator('.voice-composer').getByRole('button',{name:'发送',exact:true}).click()
   await page.waitForTimeout(300)
   assert.deepEqual(sendBody.messages.at(-1).voice_receipts,['receipt-1','receipt-2','receipt-3'])
   assert.equal(errors.length,0,errors.join('\n'))
   console.log(`PASS ${fallback?'fallback':'worklet'}: three recordings during delayed APIs, order, mic cleanup, startup timeout, late permission and send`)
   await context.close()
  }
 }finally{await browser.close()}
}
main().catch(e=>{console.error(e);process.exitCode=1})
