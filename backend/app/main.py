"""
FastAPI 主入口
==============

启动命令：uvicorn app.main:app --reload --port 8000

所有接口的实现规范参见 frontend/src/api/ 下的注释。

注意：数据库表需要在启动 uvicorn 之前用 database/init.sql 建好。
启动 uvicorn 时不会自动建表，也不会自动连数据库（只有请求时才会连）。
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ⭐ 已启用的路由（auth/user/scene/chat/result/psych 全部实现）
from app.routers import auth, user, scene, chat, result, psych

app = FastAPI(
    title="“易”生伴 API",
    description="高校学生医疗急救对话训练系统 - 后端 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置：生产环境通过 CORS_ORIGINS 明确列出 HTTPS 域名。
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """根路径"""
    return {"message": "“易”生伴 API 已启动", "docs": "/docs"}


@app.get("/api/health")
def health():
    """健康检查（不连数据库）"""
    return {"status": "ok"}


# =====================================================
# 已启用的路由
# =====================================================
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(scene.router)
app.include_router(chat.router)
app.include_router(result.router)
app.include_router(psych.router)

# =====================================================
# 静态文件：头像上传目录（/static/avatars/xxx.png）
# =====================================================
from fastapi.staticfiles import StaticFiles

_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
os.makedirs(os.path.join(_static_dir, "avatars"), exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
