/**
 * 数字人 —— 角色 / 文本 / 语音 / 机器人形象工具层
 *
 * 三条核心规则：
 * 1. 语音只朗读对话正文，剔除【】身份介绍与（）动作神态描写
 * 2. （）里的内容反过来驱动数字人表情
 * 3. 回复开头的【角色名】用来判定此刻该由哪个角色出场
 *
 * 形象体系：统一使用 SVG/CSS 机器人 Avatar（RobotAvatar.vue），
 * 视觉不再区分男/女；音色仍按从文本抽取的人物设定（年龄/体型/性别）自动切换。
 */

// ---------- 六个角色 ----------
export const ROLE_LIST = ['patient', 'registrar', 'doctor', 'cashier', 'pharmacist', 'coach']

// =====================================================
// 异物梗阻场景的「人物设定」—— 不同患者声音/体型
// 后端 scenario_generator.py 的 CHOKING_CHARACTERS 与 CHOKING_SPECIAL_CASES
// 会给出角色（食堂阿姨 / 胖叔 / 中年男性 / 怀孕女老师 …）。
// 这里为每个角色配置：展示名、性别、音色（音高/语速 + 系统语音名偏好）、体型标签。
// 视觉统一由机器人 Avatar 呈现；声音仍按年龄/体型/性别区分。
// =====================================================
export const PERSONA_LIST = [
  {
    key: 'canteen_aunt',
    match: ['食堂阿姨', '阿姨', '大妈'],
    label: '食堂阿姨',
    gender: 'female',
    voiceHint: '女|瑶|晓|婷|姨',
    pitch: 1.28,
    rate: 0.96,
    bodyType: '中年女性'
  },
  {
    key: 'fat_canteen_uncle',
    match: ['体型肥胖的食堂师傅', '胖', '食堂师傅', '大叔', '叔叔'],
    label: '胖叔（食堂师傅）',
    gender: 'male',
    voiceHint: '男|康|刚|叔',
    pitch: 0.74,
    rate: 0.9,
    bodyType: '肥胖男性'
  },
  {
    key: 'middle_aged_man',
    match: ['中年男性', '中年男人', '大伯', '老伯', '叔'],
    label: '中年男性',
    gender: 'male',
    voiceHint: '男|康|刚',
    pitch: 0.82,
    rate: 0.95,
    bodyType: '中年男性'
  },
  {
    key: 'young_woman',
    match: ['年轻女生', '年轻女孩', '姑娘', '女生'],
    label: '年轻女生',
    gender: 'female',
    voiceHint: '女|瑶|晓|婷',
    pitch: 1.32,
    rate: 1.06,
    bodyType: '年轻女性'
  },
  {
    key: 'pregnant_teacher',
    match: ['怀孕', '孕妇', '女老师', '老师'],
    label: '怀孕女老师',
    gender: 'female',
    voiceHint: '女|瑶|晓|婷',
    pitch: 1.12,
    rate: 0.94,
    bodyType: '孕妇'
  },
  {
    key: 'roommate',
    match: ['室友', '同学', '同龄'],
    label: '室友',
    gender: 'female',
    voiceHint: '女|瑶|晓|婷',
    pitch: 1.18,
    rate: 1.04,
    bodyType: '年轻学生'
  },
  {
    key: 'passerby',
    match: ['路人', '陌生'],
    label: '路人',
    gender: 'male',
    voiceHint: '男|康|刚',
    pitch: 0.9,
    rate: 1.0,
    bodyType: '不详'
  }
]

export const DEFAULT_PERSONA = {
  key: 'generic_patient',
  label: '异物梗阻患者',
  gender: 'female',
  voiceHint: '',
  pitch: 1.0,
  rate: 1.0,
  bodyType: '未知'
}

// 根据后端给的 character 字符串（如「体型肥胖的食堂师傅」）匹配人物设定
// 并换算出音色参数；视觉不再随性别切换模型。
export function resolvePersona(character) {
  if (!character) return { ...DEFAULT_PERSONA }
  for (const p of PERSONA_LIST) {
    if (p.match.some((m) => character.includes(m))) {
      return { ...p }
    }
  }
  return { ...DEFAULT_PERSONA, label: character }
}

// 从开场文案里兜底抽取患者人物（后端没带 opening_meta.character 时用）
// 例：「邻桌一名同学猛地捂住喉咙」→「同学」、「体型肥胖的食堂师傅」→「体型肥胖的食堂师傅」
// 优先匹配最长的描述词（如「体型肥胖的食堂师傅」优先于「胖」），再交给 resolvePersona 映射音色
export function extractChokingCharacter(text) {
  if (!text) return ''
  let best = ''
  let bestLen = 0
  for (const p of PERSONA_LIST) {
    for (const m of p.match) {
      if (text.includes(m) && m.length > bestLen) {
        best = m
        bestLen = m.length
      }
    }
  }
  if (best) return best
  // 退化：从「一名/一个 X（猛地/突然/捂住…）」句式里抓人物词
  const fallback = text.match(/(?:一名|一个|一位|邻桌|旁边)?[的]?([\u4e00-\u9fa5]{2,6}?)(?:猛地|突然|捂住|掐住|掐着|倒下|瘫|晕|发紫|青紫|呛)/)
  return fallback ? fallback[1] : ''
}

export const ROLE_PROFILE = {
  narrator: {
    name: '情景旁白',
    title: '场景引导',
    bg: 'linear-gradient(165deg,#f2f4fb 0%,#dfe6f5 100%)',
    accent: '#596a9d',
    gender: 'male',
    pitch: 0.96,
    rate: 0.94
  },
  patient: {
    name: '患者同学',
    title: '就诊学生',
    bg: 'linear-gradient(165deg,#e7f6f2 0%,#c9ece2 100%)',
    accent: '#0f8f7e',
    gender: 'female',
    pitch: 1.05,
    rate: 1.0
  },
  registrar: {
    name: '挂号员',
    title: '门诊挂号窗口',
    bg: 'linear-gradient(165deg,#e9f0fb 0%,#cfe0f6 100%)',
    accent: '#2f6ec4',
    gender: 'female',
    pitch: 1.18,
    rate: 1.12
  },
  doctor: {
    name: '接诊医生',
    title: '诊室',
    bg: 'linear-gradient(165deg,#eef4fb 0%,#dae7f5 100%)',
    accent: '#1c5fa8',
    gender: 'male',
    pitch: 0.92,
    rate: 0.96
  },
  cashier: {
    name: '收费员',
    title: '人工收费窗口',
    bg: 'linear-gradient(165deg,#e8f7ee 0%,#d1efdf 100%)',
    accent: '#1f8a52',
    gender: 'female',
    pitch: 1.14,
    rate: 1.1
  },
  pharmacist: {
    name: '药师',
    title: '药房发药窗口',
    bg: 'linear-gradient(165deg,#eaf6f6 0%,#d5eded 100%)',
    accent: '#12868a',
    gender: 'female',
    pitch: 1.08,
    rate: 1.02
  },
  coach: {
    name: '观察者教练',
    title: '复盘与指导',
    bg: 'linear-gradient(165deg,#fff5e8 0%,#ffe6c7 100%)',
    accent: '#b8791c',
    gender: 'male',
    pitch: 1.0,
    rate: 0.98
  },
  psych: {
    name: '易心',
    title: '心理陪伴',
    bg: 'linear-gradient(165deg,#fff3e0 0%,#ffe0b8 100%)',
    accent: '#ea8a3c',
    gender: 'female',
    pitch: 1.1,
    rate: 0.95
  }
}

// ---------- 机器人表情索引 ----------
// 与 Live2D 不同，机器人用 CSS 类 + CSS 变量控制：
// 眼色、嘴型、泪滴、摆手、呼吸、脸色银→紫、时间压迫（蓝→黄 / 黑→红）
export const EXPRESSION_INDEX = {
  neutral: 'neutral',
  calm: 'calm',
  smile: 'smile',
  happy: 'happy',
  crying: 'crying',
  anxious: 'anxious',
  confused: 'confused',
  concerned: 'concerned',
  suffering: 'suffering',
  collapsed: 'collapsed',
  listless: 'listless',
  explaining: 'explaining',
  observing: 'observing',
  relieved: 'relieved',
  angry: 'angry',
  surprised: 'surprised',
  choking: 'choking'
}

// ---------- 机器人肢体动作索引 ----------
// 与表情解耦：表情管「脸」，动作管「身体」，两者可自由组合
export const ACTION_INDEX = {
  idle: 'idle',
  // 挂机动作（无对话时自动轮换，避免数字人僵住）
  idleClap: 'idleClap',
  idleStretch: 'idleStretch',
  // 异物梗阻场景挂机：双手捂喉 + 难受表情 + 干呕（不出现拍手/外展这类轻松动作）
  idleChoke: 'idleChoke',
  // 异物梗阻场景
  deepBreath: 'deepBreath',
  waveHigh: 'waveHigh',
  clutchThroat: 'clutchThroat',
  chestPat: 'chestPat',
  startledPant: 'startledPant',
  slump: 'slump',
  // 看病 / 通用场景
  reachOut: 'reachOut',
  nod: 'nod',
  shakeHead: 'shakeHead',
  explain: 'explain'
}

// ---------- 表情主题色 ----------
// 每种表情一个专属颜色，四处复用：
//   1. 机器人眼睛发光（moodColor，亮色适合发光）
//   2. 机器人面部氛围辉光 + 屏幕描边（moodColor）
//   3. 情绪徽章边框 + 浅底（moodColor / moodSoft）
//   4. 情绪徽章文字（moodInk，深色保证白底可读）
// 颜色偏亮，是为了让 SVG 发光滤镜（eyeGlow）有足够亮度。
export const MOOD_LABEL = {
  neutral: { emoji: '😐', text: '平静', color: '#7ec8e3' },
  calm: { emoji: '😌', text: '从容', color: '#4dd8c0' },
  smile: { emoji: '🙂', text: '微笑', color: '#5ce6a8' },
  happy: { emoji: '😊', text: '开心', color: '#4dffb0' },
  crying: { emoji: '😢', text: '流泪', color: '#7fd4ff' },
  anxious: { emoji: '😰', text: '着急', color: '#ffd166' },
  confused: { emoji: '🤔', text: '疑惑', color: '#a99cff' },
  relieved: { emoji: '😮‍💨', text: '松了口气', color: '#4dffdf' },
  suffering: { emoji: '😣', text: '窒息难受', color: '#d8b4fe' },
  collapsed: { emoji: '😵', text: '支撑不住', color: '#c084fc' },
  listless: { emoji: '😔', text: '精神萎靡', color: '#a8bdd0' },
  explaining: { emoji: '💬', text: '在说明', color: '#a0e7ff' },
  observing: { emoji: '👀', text: '在观察', color: '#8fd8f8' },
  concerned: { emoji: '😟', text: '担忧', color: '#ff8c5a' },
  angry: { emoji: '😠', text: '激动', color: '#ff6b6b' },
  surprised: { emoji: '😲', text: '惊讶', color: '#ffb04d' },
  choking: { emoji: '😖', text: '异物哽咽', color: '#e879f9' },
  // —— 心理陪伴专属（柔和情绪，供 PsychView 使用）
  sad: { emoji: '🥺', text: '难过', color: '#7da9ff' },
  tired: { emoji: '😮‍💨', text: '累了', color: '#9fb8c9' }
}

// 取表情主色（未登记的表情退回平静色）
export function moodColor(expression) {
  return (MOOD_LABEL[expression] || MOOD_LABEL.neutral).color
}

function hexToRgb(hex) {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

// 徽章文字色：主色向深蓝黑混合，保证浅色背景上可读
const INK_BASE = [11, 43, 58]
export function moodInk(expression) {
  const [r, g, b] = hexToRgb(moodColor(expression))
  const safe = [r, g, b].map((v, i) => Math.round(v * 0.42 + INK_BASE[i] * 0.58))
  return `rgb(${safe[0]}, ${safe[1]}, ${safe[2]})`
}

// 徽章浅底：主色 16% 透明度
export function moodSoft(expression) {
  const [r, g, b] = hexToRgb(moodColor(expression))
  return `rgba(${r}, ${g}, ${b}, 0.16)`
}

export const ACTION_LABEL = {
  idle: { emoji: '🧍', text: '待机' },
  idleClap: { emoji: '👏', text: '拍手' },
  idleStretch: { emoji: '🤸', text: '外展双臂' },
  idleChoke: { emoji: '🤢', text: '捂喉干呕' },
  deepBreath: { emoji: '🫁', text: '深呼吸' },
  waveHigh: { emoji: '🙋', text: '高臂挥手' },
  clutchThroat: { emoji: '🖐️', text: '捂住脖子' },
  chestPat: { emoji: '🤲', text: '拍胸脯' },
  startledPant: { emoji: '😮‍💨', text: '受惊后喘气' },
  slump: { emoji: '😞', text: '瘫软无力' },
  reachOut: { emoji: '🤝', text: '伸手' },
  nod: { emoji: '👍', text: '点头' },
  shakeHead: { emoji: '👎', text: '摇头' },
  explain: { emoji: '💬', text: '摆手说明' },
  psychOpen: { emoji: '🫱', text: '温柔摊手' }
}

// ---------- 挂机动作轮换池 ----------
// 无对话、且当前动作为 idle 时，由 RobotAvatar 按序轮换，让数字人不呆立
// 普通场景：待机 → 拍手 → 待机 → 外展双臂（轻松放松姿态）
export const IDLE_CYCLE = ['idle', 'idleClap', 'idle', 'idleStretch']
// 异物梗阻场景：双手捂喉 + 难受表情 + 干呕，不出现拍手/外展这类轻松动作
export const IDLE_CYCLE_CHOKING = ['idleChoke', 'clutchThroat']
// 心理陪伴场景：安静倾听为主。等待时「待机 → 温柔摊手 → 待机 → 点头」循环，
// 让易心在用户不说话时也有轻微的“我在听、等你继续说”的生命感
export const IDLE_CYCLE_PSYCH = ['idle', 'psychOpen', 'idle', 'nod']

// ---------- 场景动作兜底池 ----------
// 文本没命中任何规则时，从这里按序取一个动作，保证该场景的动作出现频次。
// 只放「语义安全」的动作：摇头这类否定动作只在明确命中时才出现。
const SCENE_ACTION_POOL = {
  // 第一次独立看病：以伸手 / 点头为主，穿插摆手说明，偶尔摇头
  firstVisit: ['reachOut', 'nod', 'reachOut', 'explain', 'nod', 'reachOut', 'shakeHead', 'nod'],
  // 异物梗阻：以捂脖子 / 呼救为主
  choking: ['clutchThroat', 'waveHigh', 'clutchThroat', 'deepBreath', 'clutchThroat'],
  // 心理陪伴：安静倾听，偶尔点头回应
  psych: ['idle', 'idle', 'nod', 'idle'],
  other: ['explain', 'nod', 'reachOut']
}

// 轮换游标（模块级，保证同一场景连续对话不会重复同一个动作）
const poolCursor = { firstVisit: 0, choking: 0, psych: 0, other: 0 }

/**
 * 取场景兜底动作（轮换，不随机 —— 保证可预期且每次对话都换一个）
 * @param {'choking'|'firstVisit'|'other'} scene
 */
export function nextSceneAction(scene = 'other') {
  const pool = SCENE_ACTION_POOL[scene] || SCENE_ACTION_POOL.other
  const i = poolCursor[scene] % pool.length
  poolCursor[scene] = (poolCursor[scene] + 1) % pool.length
  return pool[i]
}

// ---------- 时间压迫：0（无）→ 1（濒危）----------
// 0.00-0.33 蓝（正常） / 0.34-0.66 青→黄（紧张） / 0.67-1.00 橙→红（危急）
export const PRESSURE_STAGE = [
  { max: 0.33, key: 'safe', text: '状态平稳', emoji: '🟢' },
  { max: 0.66, key: 'tense', text: '开始缺氧', emoji: '🟡' },
  { max: 1.01, key: 'critical', text: '濒危', emoji: '🔴' }
]

export function pressureStage(level) {
  const v = Number(level) || 0
  return PRESSURE_STAGE.find((s) => v <= s.max) || PRESSURE_STAGE[PRESSURE_STAGE.length - 1]
}

// ---------- 文本清洗：只留要朗读的正文 ----------
export function stripForSpeech(text) {
  if (!text) return ''
  return text
    .replace(/【[^】]*】/g, '') // 全角【】身份介绍
    .replace(/（[^）]*）/g, '') // 全角（）动作神态
    .replace(/\([^)]*\)/g, '') // 半角 () 动作神态
    .replace(/\[[^\]]*\]/g, '') // 半角 [] 舞台提示
    .replace(/［[^］]*］/g, '') // 全角 ［］舞台提示
    .replace(/〔[^〕]*〕/g, '') // 全角 〔〕舞台提示
    .replace(/\*{1,3}/g, '') // Markdown 强调符号不朗读
    .replace(/\s+/g, ' ')
    .trim()
}

// ---------- 从（）里提取「表情 + 动作」线索 ----------
// 表情管脸（眼色/嘴型/泪滴），动作管身体（手臂/头部/躯干），两者独立组合。
// 每条规则可只给 expression 或只给 action，也可两者都给。

// 【异物梗阻急救场景】—— 患者是窒息者，动作幅度大、戏剧性强
const CHOKING_RULES = [
  // —— 极端危急：优先于一切
  {
    action: 'clutchThroat',
    expression: 'choking',
    words: ['捂住喉咙', '捂着喉咙', '掐住脖子', '掐着脖子', '双手护喉', '抓挠脖子', '抓住脖子', '卡住喉咙', '喉咙被卡', '扼住']
  },
  {
    action: 'slump',
    expression: 'collapsed',
    words: ['昏倒', '倒地', '失去意识', '瘫倒', '瘫软', '意识模糊', '昏迷', '身体逐渐瘫', '没了反应', '软倒']
  },
  // —— 劫后余生：异物排出后的典型反应
  {
    action: 'startledPant',
    expression: 'surprised',
    words: ['拍胸', '拍着胸口', '拍胸口', '劫后余生', '缓过来了', '缓过劲儿', '咳出来', '咳出', '终于顺', '大口喘气', '喘上气', '活过来', '好多了', '顺畅了']
  },
  // —— 呼救 / 求助
  {
    action: 'waveHigh',
    expression: 'anxious',
    words: ['挥手', '挥舞', '招手', '呼救', '求助', '举手', '高举', '挥动双臂', '向周围', '示意周围', '求救', '救命']
  },
  // —— 深呼吸（配合急救节奏，可能是施救前调整或缓解后）
  {
    action: 'deepBreath',
    expression: 'concerned',
    words: ['深呼吸', '深吸一口气', '深吸', '吸气', '用力呼吸', '大口呼吸', '调整呼吸', '平缓呼吸', '呼吸急促', '喘']
  },
  // —— 精神萎靡
  {
    action: 'slump',
    expression: 'listless',
    words: ['萎靡', '无力', '虚弱', '没力气', '精神不济', '疲惫', '乏力', '软绵绵', '有气无力', '倦怠', '蔫']
  },
  // —— 流泪
  {
    action: 'idle',
    expression: 'crying',
    words: ['流泪', '泪水', '眼泪', '哭了', '哭泣', '呜咽', '抽泣', '眼眶', '哽咽']
  },
  // —— 微笑 / 感激
  {
    action: 'nod',
    expression: 'smile',
    words: ['微笑', '笑了', '露出笑容', '感激', '感谢', '谢谢', '点头致意', '欣慰']
  },
  // —— 纯窒息状态（无特定动作时的兜底）
  {
    action: 'clutchThroat',
    expression: 'suffering',
    words: ['噎', '窒息', '呛', '掐', '惊恐', '翻白眼', '缺氧', '发紫', '青紫', '发黑', '憋', '咳嗽', '难受', '痛苦', '挣扎', '面色', '脸色', '说不出话', '发不出声']
  },
  // —— 惊讶 / 愣住
  {
    action: 'idle',
    expression: 'surprised',
    words: ['惊讶', '意外', '愣', '吃惊', '睁大', '呆住']
  }
]

// 【第一次独立看病场景】—— 医院流程角色，动作克制、生活化
// 顺序即优先级：伸手 / 点头 / 摇头排最前，保证这三类动作优先命中
const FIRST_VISIT_RULES = [
  // —— 伸手（递单据 / 递卡 / 交接物品 / 取东西）
  {
    action: 'reachOut',
    expression: 'calm',
    words: [
      '伸手', '递出', '递给', '递过来', '递上', '递过', '接过', '接过去', '拿好', '给您', '给你', '给到',
      '交给', '出示', '拿出', '取出', '刷卡', '扫码', '凭条', '单据', '发票', '医保卡', '校园卡',
      '身份证', '病历本', '检查单', '处方', '取药', '拿药', '收好', '放这里', '放进', '塞进',
      '这边请', '请到', '请往', '带您', '领您', '指了指', '指著', '指向'
    ]
  },
  // —— 点头（肯定 / 确认 / 应答 / 招呼）
  {
    action: 'nod',
    expression: 'calm',
    words: [
      '点头', '颔首', '肯定', '嗯嗯', '示意可以', '确认', '没错', '对的', '是这样', '可以了',
      '好的', '是的', '没问题', '可以的', '欢迎', '请进', '下一个', '已挂', '已办好', '办好了',
      '登记好了', '成功了', '完成', '收到', '明白', '知道了', '了解', '对', '行', '成', '可以',
      '同学', '您好', '你好', '请坐', '坐下', '别急', '慢慢来'
    ]
  },
  // —— 摇头（否定 / 纠正 / 缺失 / 拒绝）
  {
    action: 'shakeHead',
    expression: 'confused',
    words: [
      '摇头', '摆手', '否定', '不对', '不是这样', '搞错', '弄错', '挂错', '走错', '排错', '不在这里',
      '要先', '不行', '不可以', '不能', '还没', '未满', '需要重新', '重新', '错了', '不是', '并非',
      '缺少', '没带', '漏了', '差', '不能这样', '顺序反', '反了', '颠倒', '再来一次', '重来'
    ]
  },
  // —— 着急 / 催促
  {
    action: 'explain',
    expression: 'anxious',
    words: ['着急', '焦急', '催促', '快点', '赶时间', '不耐烦', '赶紧', '来不及', '马上', '加快', '排队', '人多']
  },
  // —— 疑惑 / 不确定
  {
    action: 'shakeHead',
    expression: 'confused',
    words: ['疑惑', '不解', '纳闷', '不确定', '皱眉', '啊？', '愣', '想了想', '犹豫', '为难', '不太清楚', '查一下']
  },
  // —— 微笑 / 温和
  {
    action: 'nod',
    expression: 'smile',
    words: ['微笑', '笑了', '温和', '亲切', '安抚', '别紧张', '不用怕', '放心', '耐心']
  },
  // —— 平静 / 从容（流程性说明）
  {
    action: 'explain',
    expression: 'calm',
    words: [
      '平静', '从容', '淡定', '解释', '说明', '叮嘱', '交代', '介绍', '告知', '讲解', '提醒',
      '请先', '需要', '按照', '流程', '步骤', '先去', '然后', '接着', '再去', '等号', '窗口',
      '报到', '自助机', '挂号', '分诊', '候诊', '缴费', '检查', '复诊'
    ]
  },
  // —— 观察 / 查询（看屏幕、翻记录）
  {
    action: 'idle',
    expression: 'observing',
    words: ['观察', '打量', '端详', '记录', '翻看', '查看', '查询', '核对', '盯着屏幕', '敲键盘', '输入']
  },
  // —— 担忧 / 关心
  {
    action: 'idle',
    expression: 'concerned',
    words: ['担心', '担忧', '紧张', '不安', '叹气', '严重', '注意', '小心']
  },
  // —— 惊讶
  {
    action: 'idle',
    expression: 'surprised',
    words: ['惊讶', '意外', '愣', '吃惊', '睁大']
  }
]

// 【心理陪伴场景】—— AI「易心」倾听用户情绪，表情随用户话题起伏但动作温和克制
const PSYCH_RULES = [
  // —— 后端（神态）标注直达（最优先）：半角括号里的表情代码精确映射
  { action: 'idle', expression: 'crying', words: ['crying', 'cry'] },
  { action: 'idle', expression: 'sad', words: ['sad'] },
  { action: 'idle', expression: 'concerned', words: ['worry', 'worried', 'concerned'] },
  { action: 'idle', expression: 'anxious', words: ['anxious', 'nervous'] },
  { action: 'idle', expression: 'angry', words: ['angry', 'upset'] },
  { action: 'idle', expression: 'tired', words: ['tired', 'exhausted'] },
  { action: 'idle', expression: 'confused', words: ['confused', 'lost'] },
  { action: 'nod', expression: 'smile', words: ['smile', 'happy', 'glad'] },
  { action: 'idle', expression: 'relieved', words: ['relieved', 'peaceful'] },
  { action: 'idle', expression: 'calm', words: ['calm'] },
  // —— 哭 / 流泪：优先捕捉
  { action: 'idle', expression: 'crying', words: ['哭', '流泪', '眼泪', '泪', '抽泣', '呜咽', '泣'] },
  // —— 难过 / 低落 / 沮丧
  { action: 'idle', expression: 'sad', words: ['难过', '伤心', '委屈', '心碎', '沮丧', '低落', '抑郁', '不开心', '难受', '堵得慌', '想哭', '想家', '失落', '郁闷', '烦闷', '压抑'] },
  // —— 担心 / 忧虑（温和的挂念与不安，眼睛变暖橙「担心色」）
  { action: 'idle', expression: 'concerned', words: ['担心', '担忧', '忧虑', '害怕', '怕', '不安', '忐忑', '挂念', '放心不下', '惦记', '心疼', '叹气', '唉'] },
  // —— 焦虑 / 紧张 / 恐惧（程度更强的情绪）
  { action: 'idle', expression: 'anxious', words: ['焦虑', '紧张', '压力', '慌', '恐惧', '惊恐', '睡不着', '失眠', '想太多', '喘不过气', '心慌', '发抖', 'panic'] },
  // —— 生气 / 烦躁
  { action: 'idle', expression: 'angry', words: ['生气', '愤怒', '气死', '火大', '烦死', '讨厌', '受不了', '凭什么', '不公平'] },
  // —— 疲惫 / 累 / 崩溃
  { action: 'idle', expression: 'tired', words: ['好累', '累了', '疲惫', '没力气', '撑不住', '崩溃', '扛不住', '筋疲力尽', '虚脱', '熬'] },
  // —— 迷茫 / 困惑 / 想不通
  { action: 'idle', expression: 'confused', words: ['迷茫', '困惑', '想不通', '不知道怎么办', '不知所措', '没方向', '纠结', '犹豫', '脑子乱', '乱糟糟'] },
  // —— 微笑 / 好起来 / 感谢（倾诉后释放的正面信号）
  { action: 'nod', expression: 'smile', words: ['微笑', '笑了', '好多了', '谢谢你', '感觉好点', '想开了', '舒服多了', '说出来好', '开心'] },
  // —— 轻松 / 释怀
  { action: 'idle', expression: 'relieved', words: ['轻松', '释怀', '放下', '松口气', '没事了', '安心', '坦然'] },
  // —— 平静 / 回应安抚（表示愿意继续听）
  { action: 'nod', expression: 'calm', words: ['嗯', '我在', '慢慢说', '别急', '我懂', '抱抱', '拍拍', '深呼吸', '平静'] }
]

// 通用兜底规则（两个场景都会走一遍，作为最后一层）
const COMMON_RULES = [
  { action: 'explain', expression: 'explaining', words: ['解释', '说明', '讲解'] },
  { action: 'idle', expression: 'observing', words: ['观察', '查看', '查询'] }
]

// 场景 → 规则表
const SCENE_RULES = {
  choking: CHOKING_RULES,
  firstVisit: FIRST_VISIT_RULES,
  psych: PSYCH_RULES
}

// 取文本里所有（）包裹的动作/神态描写；没有（）时，退化为用整段正文匹配
function collectCues(text) {
  const parens = (text.match(/[（(]([^）)]*)[）)]/g) || []).join(' ')
  return parens || text || ''
}

// 动作 → 默认表情：文本没描写神态时，给动作配一个协调的表情
const ACTION_DEFAULT_EXPRESSION = {
  idle: 'neutral',
  idleClap: 'happy',
  idleStretch: 'happy',
  idleChoke: 'choking',
  deepBreath: 'concerned',
  waveHigh: 'anxious',
  clutchThroat: 'choking',
  chestPat: 'relieved',
  slump: 'listless',
  reachOut: 'calm',
  nod: 'calm',
  shakeHead: 'confused',
  explain: 'explaining',
  psychOpen: 'calm'
}

/**
 * 综合提取一句台词该配的「表情 + 动作」
 *
 * 四轮匹配，越往后越宽松，保证「几乎每句话都有动作」而不是大部分时间僵在 idle：
 * 1. （）里的神态动作描写 —— 最准
 * 2. 整段正文 —— 有些消息没写括号
 * 3. 通用规则
 * 4. 场景动作池轮换 —— 前面的都没命中时，按场景轮换取一个安全动作，
 *    并给它配上默认表情，避免出现「点头 + 平静」这种不协调组合
 *
 * @param {string} text 原始消息正文
 * @param {'choking'|'firstVisit'|'other'} scene 场景
 * @param {string} fallbackExpression 命中不到时的兜底表情
 * @returns {{expression: string, action: string}}
 */
export function extractPerformanceCue(text, scene = 'other', fallbackExpression = 'neutral') {
  if (!text) return { expression: fallbackExpression, action: 'idle' }
  const cues = collectCues(text)
  const rules = SCENE_RULES[scene] || []

  // 第一轮：只在（）描写里找
  for (const rule of rules) {
    if (rule.words.some((w) => cues.includes(w))) {
      return {
        expression: rule.expression || fallbackExpression,
        action: rule.action || 'idle'
      }
    }
  }
  // 第二轮：放宽到整段正文
  for (const rule of rules) {
    if (rule.words.some((w) => text.includes(w))) {
      return {
        expression: rule.expression || fallbackExpression,
        action: rule.action || 'idle'
      }
    }
  }
  // 第三轮：通用兜底
  for (const rule of COMMON_RULES) {
    if (rule.words.some((w) => text.includes(w))) {
      return { expression: rule.expression, action: rule.action }
    }
  }

  // 第四轮：场景动作池轮换（提升动作出现频次，避免长时间 idle）
  const poolAction = nextSceneAction(scene)
  // 兜底表情为 neutral 时，改用动作的默认表情，让表情与动作协调
  const expr =
    fallbackExpression && fallbackExpression !== 'neutral'
      ? fallbackExpression
      : ACTION_DEFAULT_EXPRESSION[poolAction] || 'neutral'
  return { expression: expr, action: poolAction }
}

// 兼容旧调用：只取表情
export function extractExpressionCue(text) {
  return extractPerformanceCue(text, 'other', 'neutral').expression
}

// ---------- 判定当前该谁出场 ----------
// 首次看病场景：回复开头会带【角色名】，用它精确匹配；没命中再按阶段兜底
const FIRST_VISIT_ROLE_MAP = {
  旁白: 'narrator',
  情景旁白: 'narrator',
  挂号员: 'registrar',
  挂号: 'registrar',
  公众号: 'registrar',
  智能问诊: 'registrar',
  报到: 'registrar',
  智能分诊: 'registrar',
  // 兼容历史会话中仍使用旧角色名的消息
  医生: 'doctor',
  诊间: 'doctor',
  接诊: 'doctor',
  收费: 'cashier',
  缴费: 'cashier',
  药师: 'pharmacist',
  药房: 'pharmacist',
  治疗: 'pharmacist'
}

export function resolveCharacterRole(role, ctx = {}) {
  if (role === 'coach') return 'coach'
  if (role === 'user') return 'patient'

  if (role === 'ai' || role === 'system') {
    if (!ctx.isFirstVisit) return 'patient'
    if (ctx.kind === 'scene_intro') return 'narrator'
    const matched = (ctx.content || '').match(/^【([^】]{1,30})】/)
    if (matched) {
      const raw = matched[1]
      for (const key of Object.keys(FIRST_VISIT_ROLE_MAP)) {
        if (raw.includes(key)) return FIRST_VISIT_ROLE_MAP[key]
      }
    }
    // 兜底：按问诊阶段
    const stage = ctx.stageId || 1
    if (stage <= 1) return 'registrar'
    if (stage <= 3) return 'doctor'
    if (stage === 4) return 'cashier'
    return 'pharmacist'
  }
  return 'patient'
}
