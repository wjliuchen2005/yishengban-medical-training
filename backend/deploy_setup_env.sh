#!/bin/bash
# 服务器端 .env 配置生成脚本
# 使用方法: ./deploy_setup_env.sh

set -e

echo "=========================================="
echo "易生伴服务器环境配置向导"
echo "=========================================="
echo ""

# 检查是否在 backend 目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在 backend 目录下运行此脚本"
    exit 1
fi

# 读取配置
echo "请输入数据库配置："
read -p "数据库主机 [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "数据库端口 [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "数据库用户名 [yishengban]: " DB_USER
DB_USER=${DB_USER:-yishengban}

read -sp "数据库密码: " DB_PASSWORD
echo ""

read -p "数据库名 [yishengban]: " DB_NAME
DB_NAME=${DB_NAME:-yishengban}

echo ""
echo "生成 JWT 密钥..."
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
echo "✓ JWT_SECRET_KEY 已生成"

echo ""
echo "请输入 API Keys（智谱 GLM）："
echo "格式: key1,key2,key3（用逗号分隔，不要有空格）"
read -p "LLM_API_KEYS: " LLM_API_KEYS

read -p "LLM_BASE_URL [https://open.bigmodel.cn/api/paas/v4]: " LLM_BASE_URL
LLM_BASE_URL=${LLM_BASE_URL:-https://open.bigmodel.cn/api/paas/v4}

read -p "LLM_MODEL [glm-5.3-flash]: " LLM_MODEL
LLM_MODEL=${LLM_MODEL:-glm-5.3-flash}

echo ""
read -p "MiMo API Key: " MIMO_API_KEY

echo ""
echo "生产环境域名（CORS 配置）："
read -p "域名（例如: https://example.com）: " PRODUCTION_DOMAIN

# 生成 .env 文件
cat > .env << EOF
# MySQL 8.0
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

# JWT
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# OpenAI-compatible LLM provider - 多 key 负载均衡
LLM_API_KEYS=${LLM_API_KEYS}
LLM_BASE_URL=${LLM_BASE_URL}
LLM_MODEL=${LLM_MODEL}
LLM_REASONING_EFFORT=high
LLM_CHAT_REASONING_EFFORT=low

# Xiaomi MiMo V2.5 TTS
MIMO_API_KEY=${MIMO_API_KEY}
MIMO_TTS_ENABLED=true
MIMO_TTS_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_TTS_MODEL=mimo-v2.5-tts
MIMO_TTS_TIMEOUT_SECONDS=30

# Voice input
MIMO_ASR_BASE_URL=https://api.xiaomimimo.com/v1
VOICE_ASSESSMENT_MODEL=mimo-v2.5
MIMO_ASR_RMB_PER_HOUR=0.5
MIMO_AUDIO_INPUT_RMB_PER_MILLION=1
MIMO_AUDIO_OUTPUT_RMB_PER_MILLION=2

# Rating resilience
RATING_REQUEST_TIMEOUT_SECONDS=60
RATING_TASK_STALE_SECONDS=90

# CORS - 生产环境域名
CORS_ORIGINS=${PRODUCTION_DOMAIN}
EOF

# 设置安全权限
chmod 600 .env

echo ""
echo "=========================================="
echo "✓ .env 文件已生成"
echo "=========================================="
echo ""
echo "配置摘要:"
echo "  - 数据库: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "  - API Keys 数量: $(echo ${LLM_API_KEYS} | tr ',' '\n' | wc -l | xargs)"
echo "  - 模型: ${LLM_MODEL}"
echo "  - CORS: ${PRODUCTION_DOMAIN}"
echo "  - 文件权限: 600 (仅所有者可读写)"
echo ""
echo "下一步:"
echo "  1. 测试数据库连接: mysql -h ${DB_HOST} -u ${DB_USER} -p ${DB_NAME}"
echo "  2. 安装依赖: pip install -r requirements.txt"
echo "  3. 启动服务: uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo ""
