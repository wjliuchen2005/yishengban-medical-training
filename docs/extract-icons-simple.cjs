const fs = require('fs')
const path = require('path')

// 直接读取 Element Plus Icons 的源码文件
const iconsPath = path.join(__dirname, '../frontend/node_modules/@element-plus/icons-vue/dist/index.js')
const iconSource = fs.readFileSync(iconsPath, 'utf-8')

const iconList = [
  { name: 'Aim', label: 'NEXT', title: '下一次重点', color: '#a76a08', bg: '#fff3db' },
  { name: 'Clock', label: 'TIMELINE', title: '对话与决策回放', color: '#536b7d', bg: '#edf2f5' },
  { name: 'Share', label: 'PATH REVIEW', title: '决策路径对比', color: '#6552a2', bg: '#f0ecfb' },
  { name: 'CircleCheck', label: 'KEEP', title: '做得好的地方', color: '#23805b', bg: '#e8f7ef' }
]

// 从编译后的代码中提取 SVG 路径数据
function extractIconSvg(iconName, source) {
  // 查找图标定义
  const patterns = [
    // 匹配 viewBox 和 path
    new RegExp(`${iconName}.*?viewBox[^>]*>([\\s\\S]*?)</svg>`, 'i'),
    // 另一种格式
    new RegExp(`render.*${iconName}[\\s\\S]{0,500}?viewBox[^>]*>([\\s\\S]{0,500}?)</svg>`, 'i')
  ]

  for (const pattern of patterns) {
    const match = source.match(pattern)
    if (match) {
      return match[0]
    }
  }
  return null
}

console.log('从 Element Plus Icons 源码中提取图标...\n')

const results = []

iconList.forEach(icon => {
  const svg = extractIconSvg(icon.name, iconSource)
  if (svg) {
    results.push({
      ...icon,
      svg: svg
    })
    console.log(`✓ 找到 ${icon.name} (${icon.title})`)
  } else {
    console.log(`✗ 未找到 ${icon.name}`)
  }
})

// 保存为 JSON
const outputPath = path.join(__dirname, 'icons-data.json')
fs.writeFileSync(outputPath, JSON.stringify(results, null, 2))
console.log(`\n图标数据已保存到: ${outputPath}`)
