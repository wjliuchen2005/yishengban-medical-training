# Backend - 易生伴 FastAPI 后端

> **状态**：认证、三类训练场景、多智能体对话、阶段判断、OSCE 病历和评分接口已实现
> **框架**：FastAPI + SQLAlchemy + MySQL

## 📁 后端目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # MySQL 连接配置
│   ├── models.py            # SQLAlchemy ORM 模型
│   ├── schemas.py           # Pydantic 数据模型
│   ├── auth.py              # JWT 认证工具
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth/* 接口
│   │   ├── user.py          # /api/user/* 接口
│   │   ├── scene.py         # /api/scene/* 接口
│   │   ├── chat.py          # /api/chat/* 接口
│   │   └── result.py        # /api/result/* 接口
│   └── ai/
│       ├── __init__.py
│       ├── llm.py           # DeepSeek/OpenAI 兼容调用
│       ├── prompts.py       # 多智能体提示词与评分标准
│       └── scenario_generator.py # 动态情景生成与本地回退
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库连接（复制 .env.example 为 .env 并修改）
cp .env.example .env

# 3. 执行数据库脚本（参见 database/init.sql）

# 4. 启动服务
uvicorn app.main:app --reload --port 8000
```

## 📋 接口清单（前端已写好注释，对照实现）

| Method | Path | 功能 | 状态 |
|---|---|---|---|
| POST | `/api/auth/register` | 用户注册 | ✅ |
| POST | `/api/auth/login` | 用户登录 | ✅ |
| POST | `/api/auth/logout` | 退出登录 | ✅ |
| GET | `/api/auth/me` | 获取当前用户 | ✅ |
| GET | `/api/user/profile` | 获取用户信息 | ✅ |
| PUT | `/api/user/profile` | 修改用户信息 | ✅ |
| PUT | `/api/user/password` | 修改密码（验证原密码） | ✅ |
| POST | `/api/user/avatar` | 上传头像 | ✅ |
| GET | `/api/scene/list` | 场景列表 | ✅ |
| GET | `/api/scene/{id}` | 场景详情 | ✅ |
| POST | `/api/chat/start` | 生成情景并开始会话 | ✅ |
| POST | `/api/chat/message` | 多智能体对话与教练反馈 | ✅ |
| GET | `/api/chat/session/{id}` | 获取完整会话 | ✅ |
| POST | `/api/chat/restart-stage` | 重新开始当前阶段 | ✅ |
| POST | `/api/chat/record` | 保存 OSCE 病历记录 | ✅ |
| POST | `/api/chat/end` | 结束对话 | ✅ |
| GET | `/api/result/{sessionId}` | 获取评分和回放 | ✅ |
| POST | `/api/result/{sessionId}/share` | 获取站内成绩链接 | ✅ |

## 🔧 前端注释位置参考

所有前端的 API 调用都在 `frontend/src/api/` 目录下：
- `auth.js` - 认证相关
- `user.js` - 用户相关
- `scene.js` - 场景相关
- `chat.js` - 对话相关
- `result.js` - 评分相关

每个方法都写了 `@api` 注释，包含：
- 接口路径
- 请求参数
- 响应格式
- 调用示例

## 📝 前端约定

后端返回 JSON 格式：

```json
// 成功
{ "code": 0, "data": { ... } }
// 或直接返回（拦截器会兼容）
{ ... }

// 失败
{ "code": 1001, "message": "原密码错误" }
```

HTTP 状态码约定：
- 200 - 成功
- 400 - 请求参数错误
- 401 - 未登录/token 过期
- 403 - 无权限
- 404 - 资源不存在
- 500 - 服务器错误

## 🔑 认证机制

使用 JWT Token，存储在请求头的 `Authorization` 字段：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...
```
