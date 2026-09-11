import { createApp, nextTick, reactive } from 'vue/dist/vue.esm-bundler.js'
import RobotAvatar from './components/RobotAvatar.vue'

const state = reactive({
  role: 'patient',
  action: 'idle',
  expression: 'neutral',
  scene: 'other',
  pressure: 0,
  speaking: false
})

window.__avatarExport = {
  async set(next) {
    Object.assign(state, next)
    await nextTick()
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  }
}

createApp({
  components: { RobotAvatar },
  setup: () => ({ state }),
  template: '<RobotAvatar v-bind="state" />'
}).mount('#app')

const style = document.createElement('style')
style.textContent = `
  html, body, #app { width: 320px; height: 360px; margin: 0; overflow: hidden; background: transparent !important; }
  .robot-host { width: 320px !important; height: 360px !important; background: transparent !important; border-radius: 0 !important; }
  .speaking-badge, .pressure-bar { display: none !important; }
`
document.head.appendChild(style)
