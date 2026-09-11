# “易”生伴 · 高校健康教育情境训练平台

“易”生伴面向高校学生，把真实生活中的就医、急救与问诊需求转化为可对话、可练习、可复盘的情境学习。学生可以直接输入账号或手机号与密码完成注册，并在手机微信浏览器、手机浏览器和桌面浏览器中使用。

- 体验入口：[https://43-129-236-191.sslip.io](https://43-129-236-191.sslip.io)
- 源码仓库：[wjliuchen2005/yishengban-medical-training](https://github.com/wjliuchen2005/yishengban-medical-training)

> 本项目用于教学、训练和作品演示。真实紧急情况请立即联系当地急救服务，并遵循专业人员指导。

## 产品能力

### 四类学习场景

| 场景 | 学习内容 |
| --- | --- |
| 首次独立就医 | 在完整门诊流程中练习挂号、报到、候诊、问诊、检查、缴费和复诊沟通。 |
| 异物梗阻急救 | 识别危险、呼救、实施成人海姆立克急救，并完成脱险后的后续沟通。 |
| OSCE 模拟问诊 | 练习结构化病史采集、关键检查过渡和独立病历书写，获得量化复盘。 |
| 易心陪伴 | 在私密对话中表达近况、整理感受；系统根据完整语境保持自然回应，在明确即时危险时提供现实求助指引。 |

### 多智能体训练闭环

场景生成、情境人物对话、观察者教练、阶段判断与评分复盘共同完成一次训练。系统会把工作人员显示为具体称呼，例如“挂号员·姓名”，避免以抽象身份打断沉浸感。

训练结束后可查看完整对话、教练提示、结构化评分和改进建议。历史记录支持收藏、置顶、排序、删除与跨训练成长总结；易心历史按用户派生密钥加密保存。

### 语音输入与表达观察

- 桌面端点击语音输入后开始录音；移动端进入语音输入后，按住“按住说话”录音、松开停止。
- MiMo V2.5 ASR 以流式结果分段返回文字，结果插入当前光标位置；停止录音后仍可编辑，最终发送的文字始终以用户编辑内容为准。
- 同一条消息可包含多段录音。每段录音可附带一条基于声音的表达观察，供教练、评分或易心理解沟通节奏与语气。
- 表达观察只辅助对话，不替代文字内容，不依据性别、设备、环境或口音评分；声音证据不足时不输出分数。原始录音不作为训练历史保存。

### 数字人与语音播报

界面内置状态驱动数字人，支持说话、倾听、点头、咳嗽、喘气、惊讶等动作。对话人物可由后端通过 MiMo V2.5 TTS 合成语音；服务不可用时前端回退到浏览器语音能力。已提供页面引导音频和可导出的数字人状态素材。

## 技术架构

| 模块 | 主要技术 |
| --- | --- |
| 前端 | Vue 3、Vite 5、Pinia、Vue Router、Element Plus、Axios、GSAP、Sass |
| 后端 | FastAPI、SQLAlchemy 2、Pydantic 2、JWT、bcrypt、httpx |
| 数据库 | MySQL 8.0 |
| 智能体 | 兼容 OpenAI API 的模型服务，可配置 GLM、DeepSeek 等 |
| 语音 | 小米 MiMo V2.5 ASR、语音表达分析与 TTS；Web Speech API 作为前端播报回退 |
| 部署 | Nginx、HTTPS、Uvicorn、systemd |

主要接口包括：认证与用户资料、场景与训练会话、实时对话与教练、评分复盘、易心会话、语音转写/表达分析，以及语音合成。后端 API 文档在启动后位于 `/docs`。

## 本地运行

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0
- 一个兼容 OpenAI API 的模型服务密钥
- MiMo API 密钥（启用语音转写、表达观察或语音合成时需要）

### 1. 初始化数据库

首次本地使用可执行：

```bash
mysql -u root -p < database/init.sql
```

> `database/init.sql` 会删除并重建 `yishengban` 数据库，不能用于含有正式数据的环境。

已运行过旧版本的数据库，请在备份后按时间顺序执行 `database/migrations/` 下的 SQL 文件。

### 2. 配置后端

```bash
cd backend
cp .env.example .env
```

至少配置数据库连接、`JWT_SECRET_KEY`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 和 `MIMO_API_KEY`。生产环境还应将 `CORS_ORIGINS` 设置为实际 HTTPS 域名。

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

可用环境变量见 [`backend/.env.example`](backend/.env.example)。不要提交 `.env`、模型密钥、数据库备份或用户数据。

### 3. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端健康检查：`http://localhost:8000/api/health`；接口文档：`http://localhost:8000/docs`。

### 4. 启动前端

```bash
cd frontend
npm ci
npm run dev
```

浏览器访问 `http://localhost:5173`。开发服务器会将 `/api` 转发到本地后端；若后端使用其他端口，可执行 `VITE_BACKEND_PORT=8001 npm run dev`。

macOS 可使用 [`启动服务.command`](启动服务.command)，Windows 可使用 [`启动服务.bat`](启动服务.bat) 作为本地启动辅助脚本。首次使用前仍需完成 MySQL、Python、Node.js 和 `backend/.env` 配置。

## 验证与构建

```bash
# 在仓库根目录：安装测试工具并运行后端测试
python -m pip install pytest
PYTHONPATH=backend python -m pytest backend/tests -q

# 前端生产构建
cd frontend
npm ci
npm run build
```

本次源码同步前已完成前端生产构建与后端 Python 静态编译。语音录音在不同手机浏览器中依赖用户授予麦克风权限，发布前应在目标设备上完成一次端到端录音、转写与发送验证。

## 生产部署要点

- Uvicorn 仅监听 `127.0.0.1`，由 Nginx 提供 HTTPS 反向代理；公网只开放必要端口。
- 为数据库使用低权限专用账号，数据库仅监听本机或内网。
- 使用强且唯一的 `JWT_SECRET_KEY`，限制模型服务额度与来源，并设置明确的 `CORS_ORIGINS`。
- 保留系统更新、日志轮转和定期备份；发布前检查默认账户与演示数据。
- 语音请求仅通过受保护后端接口转发，浏览器不持有模型服务密钥。

## 目录结构

```text
.
├── backend/       # FastAPI、智能体流程、语音服务、评分与测试
├── database/      # MySQL 初始化脚本与增量迁移
├── frontend/      # Vue 界面、数字人、语音输入与移动端适配
├── scripts/       # 素材生成与界面联调脚本
├── 启动服务.command
├── 启动服务.bat
└── README.md
```

---

# Yishengban · Scenario-Based Health Training for University Students

Yishengban turns hospital navigation, first-aid response, clinical history taking, and wellbeing conversations into interactive learning sessions. It supports desktop browsers, mobile browsers, and in-app mobile browsers. Users can register directly with an account name or phone number and a password.

## Highlights

- Four learning areas: independent hospital visits, foreign-body airway-obstruction first aid, OSCE history taking with medical-record writing, and the Yixin wellbeing companion.
- A multi-agent loop for scenario creation, contextual participants, live coaching, stage progression, and scored review.
- Cursor-aware streaming voice input. Desktop users tap to record; mobile users hold to speak. Transcripts remain editable before sending.
- Optional, evidence-bounded voice-expression observations across multiple recordings in one message. They supplement the conversation and never override the user's final edited text.
- Responsive digital humans with state-based gestures and MiMo V2.5 text-to-speech, with browser speech fallback.
- Private history, favorites, pinning, ordering, deletion, and growth summaries.

## Stack and setup

The frontend uses Vue 3 and Vite; the backend uses FastAPI and MySQL. It connects to OpenAI-compatible LLM services and Xiaomi MiMo V2.5 voice services through protected backend endpoints. See the Chinese sections above for the complete local setup, environment variables, migrations, test commands, and deployment guidance.

This project is for education, practice, and demonstration only. It is not a substitute for emergency response, diagnosis, or professional clinical care.
