<template>
  <main class="login-view">
    <div class="login-container">
      <section class="brand-panel" aria-labelledby="brand-title">
        <img class="brand-background" :src="background" alt="" aria-hidden="true" fetchpriority="high" />
        <div class="brand-content">
          <div class="brand-identity">
            <img class="brand-mark" :src="brandIcon" alt="" aria-hidden="true" />
            <h1 id="brand-title">“易”生伴</h1>
          </div>
          <p class="brand-subtitle">高校学生健康情境训练与心理陪伴平台</p>
          <ul class="scene-labels" aria-label="四种场景">
            <li>急救训练</li><li>独立就医</li><li>OSCE问诊</li><li>心理陪伴</li>
          </ul>
        </div>
        <div class="quote-section" @mouseenter="hovering = true" @mouseleave="hovering = false">
          <div class="quote-window" aria-hidden="true">
            <Transition name="quote-roll"><p :key="quoteIndex" class="quote-line">{{ quotes[quoteIndex] }}</p></Transition>
          </div>
          <p class="sr-only">{{ quotes.join('。') }}</p>
          <div class="quote-controls">
            <div class="quote-dots" aria-hidden="true"><span v-for="(_, index) in quotes" :key="index" :class="{ current: index === quoteIndex }" /></div>
          </div>
        </div>
      </section>

      <section class="login-form-panel" aria-labelledby="login-title">
        <h2 id="login-title">登录 / 注册</h2>
        <p class="registration-note">直接输入账号密码即可注册</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
          <el-form-item label="账号" prop="username">
            <el-input v-model.trim="form.username" placeholder="输入账号/手机号" :prefix-icon="User" autocomplete="username" name="username" :maxlength="20" :disabled="loading" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" autocomplete="current-password" name="password" show-password :maxlength="20" :disabled="loading" />
          </el-form-item>
          <p class="field-help">新账号 3–20 个字符，密码 6–20 个字符</p>
          <el-button class="submit-btn" type="primary" native-type="submit" :loading="loading" :disabled="loading">{{ loading ? '正在进入…' : '开始我的体验' }}</el-button>
        </el-form>
        <p class="existing-note">已有账号请使用原密码登录</p>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { unlockMiMoAudio } from '@/utils/ttsService'
import background from '@/assets/images/login-blue.webp'
import brandIcon from '@/assets/images/brand-dialogue.svg'

const router = useRouter(), route = useRoute(), userStore = useUserStore()
const formRef = ref(null), loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '输入账号/手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const quotes = [
  '陪你成长，伴你从容',
  '在需要勇气的时刻',
  '多一分准备，也多一分温度',
  '四种场景，练习应对真实情境',
  '每一次练习，都是对自己和他人的一份关照',
  'AI 情境学习 · 健康陪伴'
]
const quoteIndex = ref(0), paused = ref(false), hovering = ref(false)
let quoteTimer, motionPreference
function syncMotionPreference() { paused.value = motionPreference.matches }
onMounted(() => {
  motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)')
  syncMotionPreference()
  motionPreference.addEventListener('change', syncMotionPreference)
  quoteTimer = window.setInterval(() => {
    if (!paused.value && !hovering.value && !document.hidden) quoteIndex.value = (quoteIndex.value + 1) % quotes.length
  }, 4000)
})
onBeforeUnmount(() => {
  clearInterval(quoteTimer)
  motionPreference?.removeEventListener('change', syncMotionPreference)
})
async function onSubmit() {
  if (loading.value || !formRef.value) return
  unlockMiMoAudio()
  loading.value = true
  try {
    if (!(await formRef.value.validate().catch(() => false))) return
    const result = await userStore.login({ username: form.username, password: form.password, register_if_missing: true })
    ElMessage.success(result.registered ? '账号已创建，欢迎使用易生伴' : '登录成功')
    const redirect = route.query.redirect
    await router.push(typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } catch {
    // Request errors are displayed by the shared handler; keep the draft intact.
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-view { min-height:100vh; min-height:100svh; display:flex; align-items:center; justify-content:center; padding:32px 24px; background:linear-gradient(135deg,#e8f0fe 0%,#f5f7fa 75%); color:#24354d; }
.login-container { width:100%; max-width:980px; display:grid; grid-template-columns:1fr 1fr; background:white; border:1px solid #e2eaf5; border-radius:24px; overflow:hidden; box-shadow:0 16px 54px #235caf13; }
.brand-panel { min-width:0; position:relative; isolation:isolate; display:flex; flex-direction:column; justify-content:center; background:#2469c8; color:white; padding:48px 32px 30px; }
.brand-background { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; z-index:-2; opacity:.6; }
.brand-panel::after { content:""; position:absolute; inset:0; z-index:-1; background:linear-gradient(180deg,#226bd725,#1255b27d); }
.brand-content { text-align:center; padding:12px 0 60px; }
.brand-identity { display:flex; align-items:center; justify-content:center; gap:14px; margin:26px 0 24px; }
.brand-mark { width:51px; height:46px; object-fit:contain; flex-shrink:0; filter:brightness(0) invert(1); }
h1 { font-size:52px; line-height:1.25; font-weight:700; letter-spacing:1px; margin:0; white-space:nowrap; }
.brand-subtitle { margin:0; font-size:13px; line-height:1.8; letter-spacing:.6px; color:#f1f6ff; }
.scene-labels { display:flex; justify-content:center; flex-wrap:wrap; list-style:none; padding:0; margin:23px 0 0; }
.scene-labels li { font-size:11px; color:#e1edff; padding:0 11px; line-height:1.1; }
.scene-labels li + li { border-left:1px solid #ffffff44; }
.quote-section { border-top:1px solid #ffffff36; padding-top:17px; margin-top:auto; }
.quote-window { position:relative; height:28px; overflow:hidden; }
.quote-line { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; white-space:nowrap; margin:0; font-size:clamp(11px,1.05vw,14px); line-height:28px; letter-spacing:.3px; color:#fff; font-family:"Songti SC","STSong","Noto Serif CJK SC",serif; }
.quote-controls { position:relative; height:25px; display:flex; align-items:center; justify-content:center; }
.quote-dots { display:flex; align-items:center; gap:6px; }
.quote-dots span { height:3px; width:3px; border-radius:3px; background:#ffffff50; transition:width .3s,background .3s; }
.quote-dots .current { width:13px; background:#f6faff; }
.quote-toggle { position:absolute; right:0; top:0; width:30px; height:28px; display:grid; place-items:center; border:0; border-radius:5px; padding:7px; background:transparent; color:#e4edff; cursor:pointer; }
.quote-toggle:hover,.quote-toggle:focus-visible { background:#ffffff20; outline:1px solid #ffffff55; }
.quote-toggle svg { width:12px; height:12px; fill:none; stroke:currentColor; stroke-width:1.5; }
.quote-toggle[aria-pressed="true"] svg { fill:currentColor; stroke:none; }
.quote-roll-enter-active,.quote-roll-leave-active { transition:transform .55s cubic-bezier(.22,.68,.25,1),opacity .55s ease; }
.quote-roll-enter-from { transform:translateY(100%); opacity:0; }.quote-roll-leave-to { transform:translateY(-100%); opacity:0; }
.login-form-panel { padding:58px 46px 42px; }
h2 { margin:0 0 12px; font-size:25px; line-height:1.3; font-weight:600; }
.registration-note { color:#65758b; font-size:13px; margin:0 0 30px; }
:deep(.el-form-item) { margin-bottom:23px; }
:deep(.el-form-item__label) { font-size:13px; color:#3e5068; margin-bottom:8px; }
:deep(.el-form-item__label::before) { display:none; }
:deep(.el-input__wrapper) { min-height:48px; padding:1px 13px; border-radius:9px; box-shadow:0 0 0 1px #dce4ef inset; background:#fcfdff; }
:deep(.el-input__wrapper.is-focus) { box-shadow:0 0 0 1px #2c7be5 inset; }
:deep(.el-input__inner) { font-size:16px; }:deep(.el-input__inner::placeholder) { font-size:13px; color:#929fae; }
:deep(.el-input__prefix) { color:#8398b4; margin-right:5px; }
.field-help { color:#7b899c; font-size:11px; line-height:1.6; margin:-4px 0 24px; }
.submit-btn { width:100%; height:48px; border-radius:9px; font-size:15px; font-weight:500; letter-spacing:1px; background:#2c7be5; border-color:#2c7be5; }
.submit-btn:hover { background:#2269ca; border-color:#2269ca; }
.existing-note { text-align:center; color:#7b899c; font-size:12px; margin:23px 0 0; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; border:0; }
@media(max-width:800px) {
  .login-view { padding:24px 16px; }.login-container { max-width:480px; grid-template-columns:1fr; border-radius:20px; }
  .brand-panel { padding:22px 24px 12px; }.brand-content { padding:0 0 19px; }.brand-identity { gap:10px; margin:12px 0 17px; }.brand-mark { width:35px; height:32px; }
  h1 { font-size:36px; letter-spacing:1px; margin:0; }.brand-subtitle { font-size:12px; letter-spacing:0; }.scene-labels { margin-top:14px; }.scene-labels li { font-size:10px; padding:0 9px; }
  .brand-background { object-position:center 66%; opacity:.46; }.quote-section { padding-top:10px; }.quote-line { font-size:clamp(10.5px,3.05vw,13px); letter-spacing:0; }.quote-window { height:25px; }.quote-line { line-height:25px; }.quote-controls { height:20px; }.quote-toggle { top:-4px; }
  .login-form-panel { padding:27px 26px 25px; }h2 { font-size:22px; margin-bottom:9px; }.registration-note { font-size:12px; margin-bottom:24px; }:deep(.el-form-item) { margin-bottom:20px; }:deep(.el-input__wrapper) { min-height:46px; }.field-help { margin-bottom:19px; font-size:10px; }.existing-note { margin-top:18px; font-size:11px; }
}
@media(max-width:360px) { .login-view { padding:16px 12px; }.brand-panel { padding-left:18px; padding-right:18px; }.login-form-panel { padding-left:22px; padding-right:22px; }.brand-subtitle { font-size:11px; }.scene-labels li { padding:0 7px; } }
@media(prefers-reduced-motion:reduce) { .quote-roll-enter-active,.quote-roll-leave-active,.quote-dots span { transition:none; } }
</style>
