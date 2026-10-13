const { createSSRApp, h } = require('vue')
const { renderToString } = require('@vue/server-renderer')
const fs = require('fs')
const path = require('path')

// 动态导入图标
async function extractIcons() {
  const icons = await import('@element-plus/icons-vue')

  const iconList = [
    { name: 'Aim', label: 'NEXT', title: '下一次重点', color: '#a76a08', bg: '#fff3db' },
    { name: 'Clock', label: 'TIMELINE', title: '对话与决策回放', color: '#536b7d', bg: '#edf2f5' },
    { name: 'Share', label: 'PATH REVIEW', title: '决策路径对比', color: '#6552a2', bg: '#f0ecfb' },
    { name: 'CircleCheck', label: 'KEEP', title: '做得好的地方', color: '#23805b', bg: '#e8f7ef' }
  ]

  const results = []

  for (const icon of iconList) {
    const IconComponent = icons[icon.name]
    if (!IconComponent) {
      console.log(`图标 ${icon.name} 未找到`)
      continue
    }

    const app = createSSRApp({
      render() {
        return h(IconComponent)
      }
    })

    try {
      const html = await renderToString(app)
      results.push({
        ...icon,
        svg: html
      })
      console.log(`✓ 提取 ${icon.name} (${icon.title})`)
    } catch (error) {
      console.error(`✗ 提取 ${icon.name} 失败:`, error.message)
    }
  }

  // 保存为 JSON
  const outputPath = path.join(__dirname, 'icons-data.json')
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2))
  console.log(`\n图标数据已保存到: ${outputPath}`)

  return results
}

extractIcons().catch(console.error)
