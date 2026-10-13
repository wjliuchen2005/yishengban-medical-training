import { Aim, Clock, Share, CircleCheck } from '@element-plus/icons-vue'
import { createApp, h } from 'vue'
import fs from 'fs'

// 创建一个临时应用来渲染图标
const icons = [
  { name: 'Aim', component: Aim, label: 'NEXT', title: '下一次重点', color: '#a76a08', bg: '#fff3db' },
  { name: 'Clock', component: Clock, label: 'TIMELINE', title: '对话与决策回放', color: '#536b7d', bg: '#edf2f5' },
  { name: 'Share', component: Share, label: 'PATH REVIEW', title: '决策路径对比', color: '#6552a2', bg: '#f0ecfb' },
  { name: 'CircleCheck', component: CircleCheck, label: 'KEEP', title: '做得好的地方', color: '#23805b', bg: '#e8f7ef' }
]

console.log('提取 Element Plus 图标 SVG 数据：\n')

icons.forEach(icon => {
  // 创建一个临时的 div 来渲染组件
  const app = createApp({
    render() {
      return h(icon.component)
    }
  })

  const div = document.createElement('div')
  document.body.appendChild(div)
  app.mount(div)

  // 获取渲染后的 SVG
  const svg = div.querySelector('svg')
  if (svg) {
    console.log(`\n=== ${icon.name} (${icon.title}) ===`)
    console.log(svg.outerHTML)
  }

  app.unmount()
  document.body.removeChild(div)
})
