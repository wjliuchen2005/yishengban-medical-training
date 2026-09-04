# “易”生伴：高校健康教育多智能体情境训练平台

> 面向高校学生的健康素养、就医能力、急救能力与临床问诊训练作品。

## 中文说明

### 应用入口

- 公网体验：[https://43-129-236-191.sslip.io](https://43-129-236-191.sslip.io)
- 测试账号：`test`
- 测试密码：`123456`
- 仓库地址：[https://github.com/wjliuchen2005/yishengban-medical-training](https://github.com/wjliuchen2005/yishengban-medical-training)

![GitHub 仓库二维码](github-repository-qr.png)

### 项目简介

“易”生伴围绕高校真实健康教育场景，把传统知识讲解转化为可互动、可反馈、可复盘的智能体训练。学生不只阅读正确答案，而是在动态情境中做出判断、与虚拟角色沟通、接受观察者教练提示，并在训练结束后查看三维评分与完整对话回放。

系统当前提供三类核心训练：

1. **第一次独立看病**：以江苏省人民医院普通门诊流程为例，训练挂号、报到、候诊、问诊、缴费、检查、治疗与复诊等关键决策。
2. **异物梗阻急救**：训练危险识别、呼救、成人海姆立克急救和后续处置；患者脱离最大危险后不会再被时间压力误判为倒地。
3. **OSCE 模拟问诊与病历书写**：以问诊为主线，体格检查和辅助检查快速过渡，并将学生独立填写的病历记录纳入评分。

平台还提供“易心聊”心理陪伴、训练历史、完整回放、记录删除和个人信息管理。页面内的原始“易”生伴数字人会根据所在页面主动介绍功能，并在切换页面时停止上一段语音。

### 多智能体协作

| 智能体 | 职责 |
|---|---|
| 场景生成智能体 | 根据训练主题生成背景、角色状态、阶段目标和动态事件 |
| 场景角色智能体 | 扮演患者、陪同者或工作人员，维持角色边界并根据学生行为回应 |
| 观察者教练智能体 | 在不中断主对话的前提下提供即时、可回看的训练提示 |
| 阶段判断智能体 | 判断学生是否达到当前阶段目标，并控制流程推进或快速跳过体验节点 |
| 评分智能体 | 综合对话、处置路径和病历记录，输出评分、检查表与改进建议 |

训练闭环为：**情境生成 → 对话训练 → 即时教练 → 阶段判断 → 评分复盘**。

### OSCE 问诊框架

OSCE 场景遵循“问诊重点、检查从简”的设计：

1. 礼仪与身份确认：问候、自我介绍、核对患者身份、取得沟通同意。
2. 主诉与现病史：起病情况、主要症状、伴随症状、诱因、演变、诊疗经过和一般情况。
3. 其他病史：既往史、用药史、过敏史、个人史、婚育史、月经史和家族史，并按病例选择重点。
4. 快速检查过渡：学生提出一项合理体格检查或辅助检查后，考官在不超过四个短句内给出关键结果并进入病历书写，不反复训练操作细节。
5. 病历记录：学生独立填写主诉、现病史、相关病史、查体/检查摘要和初步诊断后才能结束训练。

OSCE 评分总分 100 分：医学准确性 40 分、沟通温度 20 分、决策合理性 40 分。其中病历记录本身占决策评分的重要部分。

### 功能特色

- 动态生成情境，避免固定题库的机械背诵。
- 五类智能体分工协作，形成全过程训练闭环。
- 观察者教练提示可在训练历史中回看。
- 危险操作识别与阶段约束，避免错误流程被直接放行。
- OSCE 独立病历记录框与结构化评分反馈。
- 对话、语音播报、数字人状态和场景阶段联动。
- 响应式布局，适配桌面浏览器和手机内置浏览器。
- 网络评分中断后可重试，不会永久停留在“正在评分”。
- 支持删除个人训练记录。

### 测试情况（2026-09-04）

| 项目 | 结果 |
|---|---|
| 后端自动化单元测试 | 21/21 通过 |
| 前端生产构建 | 通过 |
| 公网健康检查 | `/api/health` 返回 `{"status":"ok"}` |
| OSCE 完整流程 | 场景进入、问诊、病历保存、结束与评分链路通过 |
| 手机端检查 | 数字人可见、场景图片无右侧空白、OSCE 病历抽屉无横向溢出 |

预期结果：学生能够在低风险模拟环境中反复练习首次就医、急救沟通和结构化问诊，形成更明确的流程认知、危险识别能力、沟通意识与复盘习惯。

### 技术架构

- 前端：Vue 3、Vite 5、Pinia、Vue Router、Element Plus、Axios、meSpeak
- 后端：FastAPI、SQLAlchemy 2、Pydantic 2、JWT、bcrypt
- 数据库：MySQL 8.0
- 智能体模型：兼容 OpenAI API 的大模型服务，可配置智谱 GLM、DeepSeek 等服务
- 部署：Nginx + HTTPS + Uvicorn/systemd

### 本地运行

#### 环境要求

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- MySQL 8.0
- 一个兼容 OpenAI API 的大模型服务密钥

#### 1. 初始化数据库

> `database/init.sql` 会删除并重建名为 `yishengban` 的数据库，请勿对存有正式数据的数据库直接执行。

```bash
mysql -u root -p < database/init.sql
```

#### 2. 配置后端

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，至少填写数据库密码、`JWT_SECRET_KEY`、`LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL`。生产部署还应把 `CORS_ORIGINS` 设置为实际 HTTPS 域名。

生成 JWT 随机密钥示例：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

#### 3. 安装并启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### 4. 安装并启动前端

```bash
cd frontend
npm ci
npm run dev
```

浏览器访问 `http://localhost:5173`。后端接口文档位于 `http://localhost:8000/docs`。

macOS 也可双击 `启动服务.command`，Windows 可双击 `启动服务.bat`。首次运行前仍需安装 MySQL、Python、Node.js，并完成 `backend/.env` 配置。

### 测试与构建

```bash
# 后端测试
cd backend
python -m unittest discover -s tests -p 'test_*.py' -v

# 前端生产构建
cd frontend
npm ci
npm run build
```

### 生产部署安全清单

- 不提交 `backend/.env`、API 密钥、服务器私钥、数据库备份或用户上传文件。
- 使用足够长且唯一的 `JWT_SECRET_KEY`，并限制 LLM API 额度和来源。
- 仅允许实际 HTTPS 域名出现在 `CORS_ORIGINS`。
- Uvicorn 仅监听 `127.0.0.1`，由 Nginx 反向代理；公网只开放必要的 22、80、443 端口。
- 数据库只监听内网或本机，并使用专用低权限账号。
- 启用 HTTPS、安全响应头、登录限流、系统更新、日志轮转和定期备份。
- 发布前修改或停用公开测试账号。

### 项目结构

```text
.
├── backend/                  # FastAPI API、智能体流程、评分和测试
├── database/                 # MySQL 初始化与迁移脚本
├── frontend/                 # Vue 3 界面、数字人、语音和移动端适配
├── 启动服务.command          # macOS 本地启动器
├── 启动服务.bat              # Windows 本地启动器
└── README.md
```

### 医疗免责声明

本项目用于教学、训练和作品演示，不提供真实诊断、治疗或急救替代方案。真实紧急情况应立即联系当地急救服务并遵循专业人员指导。

---

## English Documentation

### Application Access

- Live demo: [https://43-129-236-191.sslip.io](https://43-129-236-191.sslip.io)
- Test username: `test`
- Test password: `123456`
- Repository: [https://github.com/wjliuchen2005/yishengban-medical-training](https://github.com/wjliuchen2005/yishengban-medical-training)

![GitHub repository QR code](github-repository-qr.png)

### Overview

Yishengban is a multi-agent, scenario-based health education platform for university students. It turns static health knowledge into interactive practice with decisions, role-play conversations, observer-coach feedback, stage progression, structured scoring, and full-session review.

The current release provides three core training scenarios:

1. **First Independent Hospital Visit**: uses the outpatient workflow of Jiangsu Province Hospital as an example and trains registration, check-in, consultation, payment, examination, treatment, and follow-up decisions.
2. **Foreign-Body Airway Obstruction First Aid**: trains danger recognition, emergency activation, adult Heimlich maneuvers, and follow-up care. Once the patient is out of immediate danger, the timer no longer incorrectly causes a collapse.
3. **OSCE History Taking and Medical Record Writing**: focuses on history taking, transitions quickly through physical and auxiliary examinations, and includes the student's independently written medical record in the assessment.

The platform also includes the “Yixin Chat” wellbeing companion, training history, complete replay, record deletion, and profile management. The original Yishengban digital mascot introduces each page and stops the previous voice line whenever navigation occurs.

### Multi-Agent Collaboration

| Agent | Responsibility |
|---|---|
| Scenario generation agent | Generates context, character status, stage objectives, and dynamic events |
| Scenario role agent | Acts as the patient, companion, or staff member while maintaining role boundaries |
| Observer coach agent | Provides timely, reviewable guidance without replacing the main conversation |
| Stage assessment agent | Determines whether objectives are met and advances or fast-forwards the workflow |
| Scoring agent | Evaluates dialogue, decisions, and medical records and returns actionable feedback |

The training loop is: **scenario generation → dialogue practice → live coaching → stage assessment → scored review**.

### OSCE History-Taking Framework

The OSCE design emphasizes history taking and keeps examinations deliberately brief:

1. Etiquette and identity: greeting, introduction, identity verification, and consent.
2. Chief complaint and history of present illness: onset, key symptoms, associated symptoms, triggers, progression, previous care, and general condition.
3. Other history: past medical, medication, allergy, personal, marital/reproductive, menstrual, and family history as relevant.
4. Fast examination transition: after the student proposes one reasonable physical or auxiliary examination, the examiner returns key findings in no more than four short sentences and moves to record writing.
5. Medical record: the student must independently complete the chief complaint, HPI, relevant history, examination summary, and preliminary diagnosis before ending the session.

The OSCE total is 100 points: medical accuracy 40, communication warmth 20, and decision quality 40. The medical record is a major component of the decision score.

### Key Features

- Dynamically generated scenarios instead of a purely fixed question bank.
- Five specialized agents working through a complete training loop.
- Reviewable observer-coach feedback in training history.
- Unsafe-action interception and stage constraints.
- Independent OSCE medical-record editor and structured assessment.
- Synchronized dialogue, speech, digital-human state, and scenario stage.
- Responsive layouts for desktop and mobile in-app browsers.
- Recoverable rating when a network interruption occurs.
- User-controlled deletion of training records.

### Verification Snapshot (2026-09-04)

| Check | Result |
|---|---|
| Backend automated unit tests | 21/21 passed |
| Frontend production build | Passed |
| Public health endpoint | `/api/health` returned `{"status":"ok"}` |
| Complete OSCE flow | Scenario, interview, record save, completion, and rating path passed |
| Mobile checks | Digital human visible, scene cover aligned, and OSCE record drawer had no horizontal overflow |

Expected outcome: students can repeatedly practice first-time care navigation, emergency communication, and structured history taking in a low-risk environment, improving procedural understanding, danger recognition, communication awareness, and reflective learning.

### Technology Stack

- Frontend: Vue 3, Vite 5, Pinia, Vue Router, Element Plus, Axios, meSpeak
- Backend: FastAPI, SQLAlchemy 2, Pydantic 2, JWT, bcrypt
- Database: MySQL 8.0
- Agent model: OpenAI-compatible LLM services, configurable for Zhipu GLM, DeepSeek, and similar providers
- Deployment: Nginx, HTTPS, Uvicorn, and systemd

### Local Setup

#### Requirements

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- An API key for an OpenAI-compatible LLM provider

#### 1. Initialize the Database

> `database/init.sql` drops and recreates the `yishengban` database. Never run it against a database that contains production data.

```bash
mysql -u root -p < database/init.sql
```

#### 2. Configure the Backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and provide at least the database password, `JWT_SECRET_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`. In production, set `CORS_ORIGINS` to the actual HTTPS domain.

Example JWT secret generator:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

#### 3. Install and Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### 4. Install and Start the Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Backend API documentation is available at `http://localhost:8000/docs`.

On macOS, you may also double-click `启动服务.command`; on Windows, double-click `启动服务.bat`. MySQL, Python, Node.js, and a completed `backend/.env` are still required before first use.

### Tests and Production Build

```bash
# Backend tests
cd backend
python -m unittest discover -s tests -p 'test_*.py' -v

# Frontend production build
cd frontend
npm ci
npm run build
```

### Production Security Checklist

- Never commit `backend/.env`, API keys, SSH keys, database backups, or user uploads.
- Use a long, unique `JWT_SECRET_KEY`; restrict LLM API quota and allowed sources.
- List only the real HTTPS domain in `CORS_ORIGINS`.
- Bind Uvicorn to `127.0.0.1` behind Nginx and expose only the required 22, 80, and 443 ports.
- Keep MySQL on the host/private network and use a dedicated least-privilege account.
- Enable HTTPS, security headers, login rate limiting, OS updates, log rotation, and regular backups.
- Change or disable the public test account before a production launch.

### Repository Layout

```text
.
├── backend/                  # FastAPI APIs, agent flow, scoring, and tests
├── database/                 # MySQL initialization and migrations
├── frontend/                 # Vue 3 UI, mascot, speech, and responsive layouts
├── 启动服务.command          # macOS local launcher
├── 启动服务.bat              # Windows local launcher
└── README.md
```

### Medical Disclaimer

This project is intended for education, training, and competition demonstration. It does not provide real medical diagnosis or treatment and must not replace emergency services or professional clinical guidance.
