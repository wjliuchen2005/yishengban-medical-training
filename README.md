# 易生伴 - 高校健康教育情境训练平台
# Yishengban - University Health Education Scenario Training Platform

<div align="center">

![易生伴Logo](docs/assets/logo.svg)

**基于五智能体协作的沉浸式医疗急救对话训练系统**  
**Immersive Medical Training System Based on Five-Agent Collaboration**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.4-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)

[在线体验 Demo](http://43.155.14.215/yishengban/) | [English Version](#english-version) | [部署指南 Deployment](#-生产部署)

</div>

---

## 🏷️ 关键词 Keywords

**中文**：医学教育 | 医学科普 | 虚拟仿真实验 | 急救培训 | 多智能体系统 | 情境训练 | OSCE | 数字人交互

**English**: Medical Education | Medical Science Popularization | Virtual Simulation Experiment | First Aid Training | Multi-Agent System | Scenario-Based Training | OSCE | Digital Human Interaction

---

## 📖 项目简介

**易生伴**（Yishengban）是一款面向高校学生的开源Web端情境化健康实训平台。针对医学科普缺乏临场感、大学生就医流程生疏、青年学生日常心理压力大且缺乏低门槛倾诉渠道、医学生临床实操试错成本高等现实痛点，平台借助拟真数字人的动作与语音交互，为学生打造了一个**低风险、可反复试错的沉浸式虚拟仿真实训空间**。

### 🎯 核心价值

- 🏥 **医学生**：零风险临床实训，OSCE标准化问诊训练
- 🎓 **普通学生**：学会独立看病，掌握急救技能，了解医保流程
- 💚 **心理健康**：低门槛倾诉渠道，隐私加密保护
- 🏫 **教育机构**：完整的虚拟仿真教学工具，可追溯的训练数据

### 🤖 开发工具

本项目使用 **Claude Code** 和 **Codex** 辅助生成部分代码和文档。

---

## ✨ 核心特性

### 🤖 五智能体实时协作框架

支撑平台极致沉浸感的，是我们自主构建的**"场景生成—场景角色—观察者教练—阶段判断—评分复盘"五智能体实时协作框架**：

```
场景生成智能体 ──→ 动态构建训练情境（人物、地点、病情）
       ↓
场景角色智能体 ──→ 扮演患者/医生/挂号员等多重角色
       ↓
观察者教练智能体 ──→ 实时监督并纠正危险操作
       ↓
阶段判断智能体 ──→ 追踪训练进度与关键节点
       ↓
评分复盘智能体 ──→ 多维评价与成长建议
```

五大智能体紧密咬合、各司其职，全面支撑起四大训练板块。

### 🎓 四大训练场景

#### 1️⃣ 异物梗阻急救训练

**基于 ERC 2025 & AHA 2025 急救指南**

- 🎲 **动态场景生成**：覆盖孕晚期、肥胖者等特殊群体
- ⏱️ **时间压力机制**：真实模拟生理恶化进程（60-150秒）
- 🎭 **数字人拟真反馈**：从剧烈呛咳→缺氧发绀→晕厥倒地→复苏喘息
- 🛡️ **危险操作拦截**：即时阻断喂水、抠喉等致命误操作
- 📊 **实操级纠偏**：站位、手位、发力方向的结构化指导

**训练流程**：评估分级 → 呼救 → 5次拍背 → 5次腹部冲击 → 交替循环 → 失去反应后CPR

#### 2️⃣ 第一次独立看病

**深度复刻江苏省人民医院完整就医流程**

- 🏥 **全链路模拟**：线上预约 → 挂号 → 问诊 → 取药 → 医保报销
- 📚 **医保知识库**：南京医科大学医保政策智能解读
- 🎯 **智能分诊**：公众号智能问诊界面
- 📋 **SAMPLE/OPQRST原则**：标准化病史采集训练
- 🔄 **病例池管理**：10个审核病例 + 大模型动态生成

**覆盖病种**：感冒发热、急腹症、运动损伤、皮疹、胸闷、剧烈头痛等

#### 3️⃣ OSCE模拟问诊

**面向专业医学生的标准化患者问诊训练**

- 📝 **实时病历书写**：边问随记、实时修改
- 🔍 **智能审阅**：问诊逻辑审查 + 病理机制剖析
- ✅ **医学合理性校验**：自动验证生成病例的专业性
- 📈 **能力追踪**：长期训练数据分析与成长曲线

**实现 "边问、边写、边学" 的高效提升**

#### 4️⃣ 易心心理陪伴

**低门槛、隐私保护的心理健康支持**

- 🔒 **端到端加密**：用户派生密钥 + Fernet对称加密
- 🤝 **温柔陪伴**：非评判性倾听，情感支持
- 🚪 **无状态对话**：前端传入历史，后端不留痕迹
- 💾 **可选保存**：用户自主决定是否保存对话

---

## 🏗️ 技术架构

### 核心技术栈

```
前端：Vue 3.4 + Composition API + Pinia + Element Plus + GSAP
后端：FastAPI + Python 3.10+ + SQLAlchemy 2.0 + MySQL 8.0
AI模型：智谱GLM 5.3 Flash / DeepSeek V4 Pro
语音服务：小米MiMo V2.5 (ASR + TTS + 多模态情感解析)
部署：Nginx + Uvicorn + 腾讯云轻量服务器
```

### 五智能体实现

所有智能体均通过**精密的Prompt工程**实现（~1,400行专业医学提示词）：

| 智能体 | 实现位置 | 核心功能 |
|--------|---------|---------|
| **场景生成** | `backend/app/ai/scenario_generator.py` | 病例池 + 大模型生成 + 结构校验 + 本地回退 |
| **场景角色** | `backend/app/ai/prompts.py` | 扮演患者/医生/挂号员，注入医学知识与行为规则 |
| **观察者教练** | `backend/app/routers/chat.py` + `prompts.py` | 并行调用，输出tip/warning/danger三级反馈 |
| **阶段判断** | `backend/app/ai/prompts.py` | 追踪训练进度，返回当前阶段与完成度 |
| **评分复盘** | `backend/app/routers/result.py` | 懒加载评分，三维评价体系（准确性/沟通/决策） |

### AI模型接入

**国产自研大模型**：智谱GLM 5.3 Flash（发布于2026年8月26日）

- ⚡ **极低调用成本** + **超快响应速度**（0.21-0.48秒）
- 🧠 **优异的多智能体复杂推理能力**
- 🔄 **多Key负载均衡**：支持3-8个API key轮询，QPS 4.69
- 🎚️ **推理力度控制**：对话场景low（快速），评分场景high（深度）

**语音多模态**：小米MiMo V2.5

- 🎤 **流式ASR**：实时语音转写，前端逐字插入
- 🔊 **高表现力TTS**：6种角色声线，自然拟真
- 💬 **情感解析**：语音语调、沟通温度、表达清晰度结构化标签

### 数字人交互

**技术实现**：SVG + GSAP动画 + 完整状态机

**表情系统**：
- 眉毛形态（担忧/惊讶/正常）
- 眼睛状态（睁眼/眨眼/开心眯眼）
- 嘴型（微笑/说话/惊讶O型/难受）
- 腮红（正常/紧张青紫渐变）

**动作库**：
```javascript
idle      // 待机轻微摆动
speaking  // 口型动画循环
waveHigh  // 打招呼抬手
explain   // 讲解展开双臂
chestPat  // 拍胸（梗阻手势）
slump     // 昏倒旋转65°
...
```

**异物梗阻特殊表现**：
- 压力值驱动肤色渐变（正常→青紫）
- 双手掐脖子（通用窒息手势）
- 失去意识后倒地动画

---

## 🎨 核心创新点

### 1. **五智能体协作框架**

业界首创的**场景生成→角色扮演→实时教练→阶段判断→评分复盘**完整闭环，所有智能体通过Prompt工程实现，无需训练模型。

### 2. **动态情景生成**

- **首次训练**：审核病例池（医学专家验证）
- **后续训练**：大模型动态生成 + 结构化校验
- **兜底机制**：模型不可用时自动回退本地模板

### 3. **时间压力机制**

异物梗阻场景真实模拟生理恶化：
- 60-90秒：呼吸困难加剧
- 120-150秒：失去意识
- 压力值驱动数字人状态变化

### 4. **加密隐私保护**

心理陪伴对话采用**用户派生密钥**（`JWT_SECRET + user_id` → Fernet密钥）：
- 摘要和完整对话均加密存储
- 数据库不存明文
- 前端负责加解密

### 5. **多维度评分体系**

三维评价（按场景动态配比）：
- **医学准确性**（30-40分）：操作规范、知识掌握
- **沟通温度**（30-40分）：语气、共情、清晰度
- **决策合理性**（30分）：应急反应、逻辑连贯

### 6. **语音表达观察**

基于小米MiMo V2.5的声音情感分析：
- 吐字清晰度
- 语速节奏
- 语调起伏
- 沟通温度

**HMAC签名防篡改**，不作为硬性评分依据，仅辅助教练理解沟通节奏。

### 7. **移动端优化**

- 📱 按住说话、松开停止
- 🎹 虚拟键盘自动适配
- 🔊 音频自动播放解锁
- 📐 响应式布局（390px - 1920px）

---

## 📊 项目规模

| 指标 | 数据 |
|------|------|
| **后端代码** | ~3,500行核心Python代码 |
| **前端代码** | ~8,200行Vue代码 |
| **总文件数** | 8,446个项目文件 |
| **AI提示词** | ~1,400行专业医学提示词 |
| **数据库表** | 7个核心表 |
| **API接口** | 30+个RESTful接口 |
| **测试验证** | 200+次端到端全流程测试 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Nginx（生产环境）

### 本地开发

#### 1. 克隆仓库

```bash
git clone https://github.com/wjliuchen2005/yishengban-medical-training.git
cd yishengban-medical-training
```

#### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入必要的API密钥
```

**必填配置**（`backend/.env`）：

```bash
# 数据库
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=yishengban

# 大模型API（多个key用逗号分隔）
LLM_API_KEYS=your_glm_key1,your_glm_key2,your_glm_key3
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-5.3-flash

# 小米MiMo语音服务
MIMO_API_KEY=your_mimo_key

# JWT密钥（随机生成）
JWT_SECRET=your_secret_key_here

# CORS允许的域名
CORS_ORIGINS=http://localhost:5173,http://43.155.14.215
```

#### 3. 初始化数据库

```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source database/init.sql

# 执行迁移脚本
source database/migrations/20260904_add_osce_scene.sql
source database/migrations/20260905_add_psych_history.sql
source database/migrations/20260905_add_daily_usage.sql
source database/migrations/20260905_add_history_features.sql
```

#### 4. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端API文档：http://localhost:8000/docs

#### 5. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问地址：http://localhost:5173

---

## 📦 生产部署

### 自动化部署脚本

项目提供了完整的自动化部署脚本（需要服务器SSH访问权限）：

```bash
cd /path/to/project
./deploy_to_server.sh
```

脚本会自动完成：
- ✅ 压缩上传代码
- ✅ 安装系统依赖
- ✅ 初始化数据库
- ✅ 配置环境变量
- ✅ 构建前端（base路径：`/yishengban`）
- ✅ 设置Systemd服务
- ✅ 配置Nginx反向代理
- ✅ 启用防火墙与安全加固

### 手动部署步骤

详细的手动部署指南请参考：[DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)

**关键配置点**：

1. **前端构建**（子路径部署）：

```javascript
// frontend/vite.config.js
export default defineConfig({
  base: '/yishengban/',  // 重要！匹配Nginx配置
  // ...
})
```

2. **Nginx配置**：

```nginx
location /yishengban/ {
    alias /var/www/yishengban/frontend/dist/;
    try_files $uri $uri/ /yishengban/index.html;
}

location /api {
    proxy_pass http://127.0.0.1:8000;
    # ...
}
```

3. **Systemd服务**（自动重启）：

```bash
sudo systemctl enable yishengban
sudo systemctl start yishengban
sudo systemctl status yishengban
```

---

## 📂 项目结构

```
yishengban-medical-training/
├── backend/                    # 后端服务（FastAPI）
│   ├── app/
│   │   ├── main.py            # FastAPI入口
│   │   ├── models.py          # ORM模型
│   │   ├── schemas.py         # Pydantic数据验证
│   │   ├── auth.py            # JWT认证
│   │   ├── routers/           # API路由
│   │   │   ├── auth.py        # 登录注册
│   │   │   ├── chat.py        # 对话训练（核心）
│   │   │   ├── result.py      # 评分复盘
│   │   │   ├── psych.py       # 心理陪伴
│   │   │   ├── voice.py       # ASR接口
│   │   │   └── tts.py         # TTS接口
│   │   └── ai/
│   │       ├── llm.py         # 大模型调用封装
│   │       ├── prompts.py     # Prompt工程（1444行）
│   │       └── scenario_generator.py  # 情景生成
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # 前端应用（Vue 3）
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── ChatView.vue   # 对话训练（2000+行）
│   │   │   ├── ResultView.vue # 评分结果
│   │   │   └── PsychView.vue  # 心理陪伴
│   │   ├── components/
│   │   │   ├── RobotAvatar.vue      # 数字人（SVG+GSAP）
│   │   │   ├── VoiceComposer.vue    # 语音输入
│   │   │   └── VoiceFeedback.vue    # 表达反馈
│   │   ├── stores/            # Pinia状态管理
│   │   ├── api/               # 接口封装
│   │   └── utils/             # 工具函数
│   ├── public/
│   │   └── audio/tts/         # 预生成音频
│   └── vite.config.js
│
├── database/                   # 数据库脚本
│   ├── init.sql               # 初始化
│   └── migrations/            # 增量迁移
│
├── docs/                       # 文档与素材
├── scripts/                    # 辅助脚本
├── README.md                   # 项目说明（本文件）
├── DEPLOY_CHECKLIST.md         # 部署检查清单
└── implementation_report.md    # 功能完善报告
```

---

## 🧪 测试与质量保证

### 后端单元测试

```bash
cd backend
pytest tests/ -v
```

**测试覆盖**：
- ✅ 用户认证与JWT
- ✅ 场景列表与详情
- ✅ 对话流程（患者+教练并行）
- ✅ 评分逻辑
- ✅ 心理对话加密
- ✅ 语音ASR/TTS
- ✅ 数据库CRUD

### 前端构建验证

```bash
cd frontend
npm run build
npm run preview
```

### 端到端测试

项目经过**200+次完整流程验证**：
- 四大场景全流程测试
- 移动端兼容性测试
- 语音输入输出测试
- 数字人动画测试
- 并发压力测试（20用户）

---

## 📈 性能指标 Performance Metrics

| 指标 Metric | 数据 Data |
|------|------|
| **后端API响应 Backend API Response** | <500ms（对话场景 Dialogue） |
| **前端首屏加载 Frontend Initial Load** | <2s（Vite优化 Vite Optimized） |
| **数据库查询 Database Query** | <50ms（索引优化 Index Optimized） |
| **并发支持 Concurrent Users** | 15-20用户（2核2GB配置 2-core 2GB） |
| **QPS（3个key）** | 4.69（20并发测试 20 Concurrent） |
| **平均AI响应 Average AI Response** | 0.21-0.48秒 seconds |

---

## 🔒 安全与隐私 Security & Privacy

### 已实施的安全措施 Security Measures

- 🔐 **JWT认证 JWT Authentication** + bcrypt密码哈希 Password Hashing
- 🔒 **心理对话端到端加密 E2E Encryption**（Fernet对称加密 Symmetric Encryption）
- 🛡️ **Nginx速率限制 Rate Limiting**（API 10次/秒，登录 5次/分钟）
- 🔥 **UFW防火墙 Firewall**（仅开放22/80/443 Only ports 22/80/443）
- 🚫 **CORS严格域名白名单 CORS Whitelist**
- 🔑 **敏感密钥环境变量隔离 Secret Key Isolation**（`.env`不提交版本控制）
- 💾 **每日自动备份 Daily Backup**（数据库+源码，凌晨3点）
- 📝 **访问日志与错误日志 Access & Error Logs**

### 隐私保护特性 Privacy Features

- 心理对话加密存储，数据库不存明文 Psychological dialogue encrypted storage
- 用户可自主删除训练记录 User-controlled data deletion
- 后端只监听本地127.0.0.1，公网不可直达 Backend only listens on localhost
- 语音表达观察数据仅辅助反馈，不长期存储 Voice feedback data not permanently stored

---

---

## 📄 开源协议

本项目采用 [MIT License](./LICENSE) 开源协议。

您可以自由地：
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发
- ✅ 私人使用

唯一要求：保留原作者版权声明。

---

## 👥 致谢 Acknowledgments

### 特别致谢

- **南京医科大学**：提供医保知识库与测试支持
- **江苏省人民医院**：提供就医流程参考
- **智谱AI**：GLM 5.3 Flash模型支持
- **小米MiMo团队**：语音多模态技术支持
- **测试志愿者**：200+次测试验证

### 引用的医学指南

- ERC 2025 European Resuscitation Council Guidelines
- AHA 2025 American Heart Association Guidelines
- OSCE标准化患者问诊规范
- SAMPLE病史采集原则
- OPQRST疼痛评估原则

---

## 📞 联系方式 Contact

- **项目主页 Repository**：https://github.com/wjliuchen2005/yishengban-medical-training
- **在线体验 Demo**：http://43.155.14.215/yishengban/
- **问题反馈 Issues**：[GitHub Issues](https://github.com/wjliuchen2005/yishengban-medical-training/issues)

---

<div align="center">

**易生伴 - 让医学教育更有温度**  
**Yishengban - Making Medical Education More Accessible**

[⬆ 回到顶部 Back to Top](#易生伴---高校健康教育情境训练平台)

</div>

---

# English Version

## 📖 Project Introduction

**Yishengban** is an open-source web-based scenario training platform for university students' health education. Addressing the real-world challenges of lack of immersive medical science popularization, students' unfamiliarity with hospital procedures, insufficient low-barrier psychological support channels, and high trial-and-error costs in clinical practice for medical students, the platform creates a **low-risk, repeatable immersive virtual simulation training space** through realistic digital human interaction with motion and voice.

### 🎯 Core Values

- 🏥 **Medical Students**: Zero-risk clinical training, OSCE standardized patient interviews
- 🎓 **General Students**: Learn to seek medical care independently, master first aid skills, understand medical insurance
- 💚 **Mental Health**: Low-barrier emotional support channel with encrypted privacy protection
- 🏫 **Educational Institutions**: Complete virtual simulation teaching tools with traceable training data

### 🤖 Development Tools

This project uses **Claude Code** and **Codex** to assist in generating parts of the code and documentation.

---

## ✨ Core Features

### 🤖 Five-Agent Real-Time Collaboration Framework

The platform's immersive experience is powered by our self-built **"Scenario Generation → Role Playing → Observer Coach → Stage Judgment → Evaluation Review"** five-agent real-time collaboration framework:

```
Scenario Generator → Dynamically constructs training scenarios
       ↓
Role Player Agent → Acts as patient/doctor/receptionist
       ↓
Observer Coach Agent → Real-time supervision and error correction
       ↓
Stage Judgment Agent → Tracks training progress
       ↓
Evaluation Agent → Multi-dimensional assessment and feedback
```

### 🎓 Four Training Scenarios

#### 1️⃣ Foreign Body Airway Obstruction First Aid

**Based on ERC 2025 & AHA 2025 Guidelines**

- 🎲 **Dynamic Scenario Generation**: Covers special groups like pregnant women, obese patients
- ⏱️ **Time Pressure Mechanism**: Realistic simulation of physiological deterioration (60-150 seconds)
- 🎭 **Digital Human Realistic Feedback**: From severe coughing → hypoxia cyanosis → fainting → resuscitation
- 🛡️ **Dangerous Operation Interception**: Immediately blocks fatal mistakes like feeding water
- 📊 **Practical-Level Correction**: Structured guidance on positioning, hand placement, force direction

#### 2️⃣ First Independent Medical Visit

**Replicating Jiangsu Provincial People's Hospital Complete Medical Process**

- 🏥 **Full-Chain Simulation**: Online appointment → Registration → Consultation → Medication → Insurance
- 📚 **Insurance Knowledge Base**: Intelligent interpretation of Nanjing Medical University insurance policies
- 🎯 **Intelligent Triage**: WeChat official account intelligent consultation interface
- 📋 **SAMPLE/OPQRST Principles**: Standardized medical history taking training

#### 3️⃣ OSCE Simulated Consultation

**Standardized Patient Interview Training for Medical Students**

- 📝 **Real-time Medical Record Writing**: Write while asking, real-time modification
- 🔍 **Intelligent Review**: Consultation logic review + pathological mechanism analysis
- ✅ **Medical Rationality Verification**: Automatic verification of generated case professionalism

#### 4️⃣ Yixin Psychological Companion

**Low-Barrier, Privacy-Protected Mental Health Support**

- 🔒 **End-to-End Encryption**: User-derived key + Fernet symmetric encryption
- 🤝 **Gentle Companionship**: Non-judgmental listening, emotional support
- 🚪 **Stateless Dialogue**: Frontend passes history, backend leaves no trace

---

## 🏗️ Technical Architecture

### Core Technology Stack

```
Frontend: Vue 3.4 + Composition API + Pinia + Element Plus + GSAP
Backend: FastAPI + Python 3.10+ + SQLAlchemy 2.0 + MySQL 8.0
AI Models: Zhipu GLM 5.3 Flash / DeepSeek V4 Pro
Voice Service: Xiaomi MiMo V2.5 (ASR + TTS + Multimodal Emotion Analysis)
Deployment: Nginx + Uvicorn + Tencent Cloud Lighthouse Server
```

### Five-Agent Implementation

All agents are implemented through **precise prompt engineering** (~1,400 lines of professional medical prompts):

| Agent | Implementation | Core Function |
|--------|---------|---------|
| **Scenario Generator** | `backend/app/ai/scenario_generator.py` | Case pool + LLM generation + validation + fallback |
| **Role Player** | `backend/app/ai/prompts.py` | Play patient/doctor/receptionist with medical knowledge |
| **Observer Coach** | `backend/app/routers/chat.py` + `prompts.py` | Parallel calls, output tip/warning/danger feedback |
| **Stage Judgment** | `backend/app/ai/prompts.py` | Track training progress, return current stage |
| **Evaluation** | `backend/app/routers/result.py` | Lazy loading, three-dimensional evaluation system |

---

## 🚀 Quick Start

### Environment Requirements

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- Nginx (production)

### Local Development

#### 1. Clone Repository

```bash
git clone https://github.com/wjliuchen2005/yishengban-medical-training.git
cd yishengban-medical-training
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and fill in necessary API keys
```

**Required Configuration** (`backend/.env`):

```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=yishengban

# LLM API (multiple keys separated by commas)
LLM_API_KEYS=your_glm_key1,your_glm_key2,your_glm_key3
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-5.3-flash

# Xiaomi MiMo Voice Service
MIMO_API_KEY=your_mimo_key

# JWT Secret (randomly generated)
JWT_SECRET=your_secret_key_here

# CORS allowed origins
CORS_ORIGINS=http://localhost:5173,http://43.155.14.215
```

#### 3. Initialize Database

```bash
# Login to MySQL
mysql -u root -p

# Execute initialization script
source database/init.sql

# Execute migration scripts
source database/migrations/20260904_add_osce_scene.sql
source database/migrations/20260905_add_psych_history.sql
source database/migrations/20260905_add_daily_usage.sql
source database/migrations/20260905_add_history_features.sql
```

#### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API Documentation: http://localhost:8000/docs

#### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend Access: http://localhost:5173

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

You are free to:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

Only requirement: Retain original author copyright notice.

---

## 👥 Acknowledgments

### Special Thanks

- **Nanjing Medical University**: Medical insurance knowledge base and testing support
- **Jiangsu Provincial People's Hospital**: Medical process reference
- **Zhipu AI**: GLM 5.3 Flash model support
- **Xiaomi MiMo Team**: Voice multimodal technology support
- **Test Volunteers**: 200+ testing validations

### Referenced Medical Guidelines

- ERC 2025 European Resuscitation Council Guidelines
- AHA 2025 American Heart Association Guidelines
- OSCE Standardized Patient Interview Standards
- SAMPLE Medical History Taking Principles
- OPQRST Pain Assessment Principles

---

## 📞 Contact

- **Repository**: https://github.com/wjliuchen2005/yishengban-medical-training
- **Demo**: http://43.155.14.215/yishengban/
- **Issues**: [GitHub Issues](https://github.com/wjliuchen2005/yishengban-medical-training/issues)

---

<div align="center">

**Yishengban - Making Medical Education More Accessible**

[⬆ Back to Top](#易生伴---高校健康教育情境训练平台)

</div>
