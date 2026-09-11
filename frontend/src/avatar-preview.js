import { createApp, ref } from 'vue/dist/vue.esm-bundler.js'
import RobotAvatar from './components/RobotAvatar.vue'
import './avatar-preview.css'
createApp({ components: { RobotAvatar }, setup() {
 const active=ref(0), speaking=ref(false)
 const poses=[{name:'欢迎 · 医护',role:'doctor',action:'waveHigh',expression:'smile',scene:'other'}, {name:'倾听 · 易心',role:'psych',action:'psychOpen',expression:'concerned',scene:'psych'}, {name:'问诊 · 患者',role:'patient',action:'idle',expression:'neutral',scene:'firstVisit'}, {name:'讲解 · 教练',role:'coach',action:'explain',expression:'explaining',scene:'other'}, {name:'梗阻 · 求救',role:'patient',action:'clutchThroat',expression:'choking',scene:'choking',pressure:.45}, {name:'脱险 · 喘气',role:'patient',action:'startledPant',expression:'surprised',scene:'choking'}, {name:'安心 · 微笑',role:'psych',action:'nod',expression:'happy',scene:'psych'}]
 return {active,speaking,poses}
}, template:`<main><header><small>YISHENGBAN · CHARACTER STUDIO</small><h1>熟悉的伙伴，更生动的陪伴。</h1><p>圆润轮廓 / 大头短身 / 分层动作 / 保持比例</p></header><section><div class="stage"><RobotAvatar v-bind="poses[active]" :speaking="speaking"/></div><aside><span class="label">表情与动作</span><div class="choices"><button v-for="(pose,i) in poses" :key="i" :class="{active:active===i}" @click="active=i">{{pose.name}}</button></div><label class="voice"><input type="checkbox" v-model="speaking"> 模拟说话动画（不播放语音）</label><p class="note">这里使用与正式页面相同的组件。角色整体不拉伸；眨眼与嘴型独立变化。急救求救与脱险后的动作分别处理。</p></aside></section><footer>本地外观预览 · GSAP + 分层 SVG</footer></main>` }).mount('#app')
