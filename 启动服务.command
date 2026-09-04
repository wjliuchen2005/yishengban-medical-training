#!/bin/bash
# =====================================================
# “易”生伴 - macOS 一键启动脚本（双击本文件即可）
#
# 会依次：
#   1. 检查并启动 MySQL（Homebrew 版，root 无密码）
#   2. 检查后端虚拟环境和依赖（缺失时自动安装）
#   3. 启动后端 API（端口 8000）
#   4. 启动前端页面（端口 5173，自动打开浏览器）
#
# 停止服务：关闭本终端窗口，或按 Ctrl+C
# =====================================================
cd "$(dirname "$0")" || exit 1

echo "=========================================="
echo "  “易”生伴 - 高校健康教育多智能体情境训练"
echo "=========================================="

# ---------- 1. MySQL ----------
echo "[1/4] 检查 MySQL ..."
if mysqladmin -u root status >/dev/null 2>&1; then
    echo "  ✓ MySQL 已在运行"
else
    if command -v brew >/dev/null 2>&1; then
        echo "  启动 MySQL（brew services）..."
        brew services start mysql
        # 等待就绪（最多 15 秒）
        for i in $(seq 1 15); do
            mysqladmin -u root status >/dev/null 2>&1 && break
            sleep 1
        done
    fi
    if mysqladmin -u root status >/dev/null 2>&1; then
        echo "  ✓ MySQL 已启动"
    else
        echo "  ✗ MySQL 启动失败！请手动执行: brew services start mysql"
        echo "    然后重新双击本脚本"
        read -n 1 -s -r -p "按任意键退出..."
        exit 1
    fi
fi

# 检查数据库是否已初始化（首次使用时自动导入）
if ! mysql -u root -e "USE yishengban" >/dev/null 2>&1; then
    echo "  首次使用：导入 database/init.sql ..."
    mysql -u root < "database/init.sql" >/dev/null 2>&1 && echo "  ✓ 数据库初始化完成（测试账号 test/123456）"
fi

# ---------- 2. 后端依赖 ----------
echo "[2/4] 检查后端环境 ..."
if [ ! -d backend/venv ]; then
    echo "  首次使用：创建虚拟环境并安装依赖（约1-2分钟）..."
    cd backend && python3 -m venv venv && ./venv/bin/pip install -q -r requirements.txt && cd ..
fi
if [ ! -f backend/.env ]; then
    echo "  ✗ 缺少 backend/.env 配置文件（数据库/大模型 API 配置），无法启动"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi
echo "  ✓ 后端环境就绪"

# ---------- 3. 后端 API ----------
echo "[3/4] 启动后端 API（端口 8000）..."
backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# 等待后端就绪（最多 30 秒）
for i in $(seq 1 30); do
    curl -s http://localhost:8000/api/health >/dev/null 2>&1 && break
    sleep 1
done
if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "  ✓ 后端已启动 http://localhost:8000/docs"
else
    echo "  ✗ 后端启动失败，请查看上方报错信息"
    kill $BACKEND_PID 2>/dev/null
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# ---------- 4. 前端 ----------
echo "[4/4] 启动前端页面（端口 5173）..."
if [ ! -d frontend/node_modules ]; then
    echo "  首次使用：安装前端依赖（约1-2分钟）..."
    cd frontend && npm install --no-audit --no-fund && cd ..
fi

# Ctrl+C / 关闭窗口时同时停掉后端
trap 'kill $BACKEND_PID 2>/dev/null; exit 0' INT TERM EXIT

sleep 3 && open http://localhost:5173
cd frontend && npx vite --port 5173
