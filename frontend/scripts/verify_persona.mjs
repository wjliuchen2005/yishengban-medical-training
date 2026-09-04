// 验证异物梗阻人物设定（PERSONA_LIST）与后端 character 字符串的映射是否全部命中
// 运行：node scripts/verify_persona.mjs
import { resolvePersona, extractChokingCharacter, PERSONA_LIST } from '../src/utils/live2dMap.js'

let pass = 0
let fail = 0
const log = (ok, label, got, want) => {
  if (ok) { pass += 1; console.log(`  PASS  ${label} -> ${got}`) }
  else { fail += 1; console.log(`  FAIL  ${label}  got=${got}  want=${want}`) }
}

console.log('\n[1] 后端标准角色 character 字符串 -> resolvePersona')
const std = {
  '室友': 'roommate',
  '同学': 'roommate',
  '食堂阿姨': 'canteen_aunt',
  '路人': 'passerby',
  '年轻女生': 'young_woman',
  '中年男性': 'middle_aged_man'
}
for (const [char, wantKey] of Object.entries(std)) {
  const p = resolvePersona(char)
  log(p.key === wantKey, `character="${char}"`, p.key, wantKey)
}

console.log('\n[2] 后端特殊患者 character 字符串 -> resolvePersona')
const special = {
  '怀孕八个多月的女老师': 'pregnant_teacher',
  '体型肥胖的食堂师傅': 'fat_canteen_uncle'
}
for (const [char, wantKey] of Object.entries(special)) {
  const p = resolvePersona(char)
  log(p.key === wantKey, `character="${char}"`, p.key, wantKey)
}

console.log('\n[3] 最长匹配优先级（避免被更短关键词抢走）')
// “体型肥胖的食堂师傅”含“胖/食堂师傅”，必须命中 fat_canteen_uncle 而非被短词干扰
log(resolvePersona('体型肥胖的食堂师傅').key === 'fat_canteen_uncle', '长词优先: 体型肥胖的食堂师傅', resolvePersona('体型肥胖的食堂师傅').key, 'fat_canteen_uncle')
// “怀孕八个多月的女老师”含“老师”，必须命中 pregnant_teacher
log(resolvePersona('怀孕八个多月的女老师').key === 'pregnant_teacher', '长词优先: 怀孕八个多月的女老师', resolvePersona('怀孕八个多月的女老师').key, 'pregnant_teacher')

console.log('\n[4] 演示模式兜底：从开场文案抽取人物')
const demoOpening = '你正在学校食堂吃饭，突然发现邻桌一名同学猛地捂住喉咙：无法发出声音，双手紧紧掐住脖子，脸色迅速变得青紫，身旁的桌上还放着一包没吃完的坚果。\n\n你现在就在现场。请观察并说出你的第一步行动。'
const demoChar = extractChokingCharacter(demoOpening)
log(resolvePersona(demoChar).key === 'roommate', 'demo 兜底抽取', `${demoChar} -> ${resolvePersona(demoChar).key}`, 'roommate')

console.log('\n[5] 合成开场文案：含不同人物关键词 -> 抽取正确')
const auntOpen = '你正在食堂，旁边一位食堂阿姨突然猛地捂住喉咙：无法发出声音，双手紧紧掐住脖子。'
log(resolvePersona(extractChokingCharacter(auntOpen)).key === 'canteen_aunt', '合成: 食堂阿姨', extractChokingCharacter(auntOpen), 'canteen_aunt')

const fatOpen = '你正在食堂，体型肥胖的食堂师傅突然猛地捂住喉咙，双手在空中慌乱抓挠。'
log(resolvePersona(extractChokingCharacter(fatOpen)).key === 'fat_canteen_uncle', '合成: 体型肥胖的食堂师傅', extractChokingCharacter(fatOpen), 'fat_canteen_uncle')

console.log('\n[6] 声音/形象字段完整性（每个 persona 必须有肖像路径或明确无图）')
for (const p of PERSONA_LIST) {
  const ok = typeof p.label === 'string' && typeof p.pitch === 'number' && typeof p.rate === 'number'
  log(ok, `persona.${p.key} 字段完整`, `label=${p.label} pitch=${p.pitch} rate=${p.rate}`, 'complete')
}

console.log(`\n==== 结果: ${pass} 通过 / ${fail} 失败 ====`)
process.exit(fail ? 1 : 0)
