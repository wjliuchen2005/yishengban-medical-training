# 部署检查清单

## ✅ 本地测试完成

### 多 API Key 负载均衡
- ✓ 配置了 3 个智谱 GLM API key
- ✓ 轻量测试（5并发）: 100% 成功率，QPS: 2.09
- ✓ 高负载测试（20并发）: 100% 成功率，QPS: 4.69
- ✓ 平均响应时间: 0.21-0.48秒

### 代码修改
- ✓ `backend/app/ai/llm.py` - 添加多key轮询机制
- ✓ `backend/.env` - 配置 `LLM_API_KEYS`（3个key用逗号分隔）
- ✓ `backend/test_concurrent_api.py` - 并发测试脚本

---

## 🚀 服务器部署步骤

### 1. 准备服务器环境
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.10 python3-pip python3-venv mysql-server nginx git

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. 上传代码
```bash
# 方法1: Git 克隆
cd /var/www
sudo git clone <your-repo-url> yishengban
sudo chown -R $USER:$USER yishengban

# 方法2: SCP 上传（从本地执行）
scp -r /Users/liuchen/Claude\ Code/工作/aigc南医健康app/yilutong-medical-training-v2.1 user@server:/var/www/yishengban
```

### 3. 配置数据库
```bash
# 登录 MySQL
sudo mysql -u root -p

# 初始化数据库
mysql -u root -p < /var/www/yishengban/database/init.sql

# 创建专用用户（推荐）
CREATE USER 'yishengban'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON yishengban.* TO 'yishengban'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 配置后端环境变量
```bash
cd /var/www/yishengban/backend
cp .env.example .env
nano .env
```

**重要配置项：**
```bash
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=yishengban
DB_PASSWORD=strong_password_here
DB_NAME=yishengban

# JWT 密钥（生成新的）
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

# 多 API Key 配置（关键！）
LLM_API_KEYS=key1,key2,key3
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-5.3-flash

# MiMo 语音服务
MIMO_API_KEY=your_mimo_key

# CORS（生产域名）
CORS_ORIGINS=https://your-domain.com
```

### 5. 安装后端依赖
```bash
cd /var/www/yishengban/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. 构建前端
```bash
cd /var/www/yishengban/frontend
npm ci
npm run build
```

### 7. 配置 Systemd 服务
```bash
sudo nano /etc/systemd/system/yishengban.service
```

```ini
[Unit]
Description=Yishengban Medical Training Backend
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/yishengban/backend
Environment="PATH=/var/www/yishengban/backend/venv/bin"
ExecStart=/var/www/yishengban/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable yishengban
sudo systemctl start yishengban
sudo systemctl status yishengban
```

### 8. 配置 Nginx
```bash
sudo nano /etc/nginx/sites-available/yishengban
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /var/www/yishengban/frontend/dist;
    index index.html;

    # 限制并发连接（重要！）
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    limit_conn addr 10;

    # 限制请求速率
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # 静态资源（头像等）
    location /static {
        proxy_pass http://127.0.0.1:8000;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/yishengban /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. 配置 HTTPS（推荐）
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 服务器性能优化（2核2GB限制版）

### Uvicorn 配置
```bash
# 限制 workers 和并发
uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  --workers 1 \
  --limit-concurrency 15 \
  --timeout-keep-alive 30 \
  --backlog 50
```

### MySQL 优化
```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

```ini
[mysqld]
# 减少内存占用
innodb_buffer_pool_size = 256M
max_connections = 30
table_open_cache = 64
query_cache_size = 0
query_cache_type = 0
```

```bash
sudo systemctl restart mysql
```

### 启用 Swap（应急）
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 🔍 部署后验证

### 1. 健康检查
```bash
curl http://your-domain.com/api/health
# 预期: {"status":"ok"}
```

### 2. API 文档
访问: `https://your-domain.com/docs`

### 3. 多 Key 验证
```bash
# 查看日志确认多 key 加载
sudo journalctl -u yishengban -n 50
# 应该看到: "✓ LLM 配置: 3 个 API key"
```

### 4. 并发测试（服务器上）
```bash
cd /var/www/yishengban/backend
source venv/bin/activate
echo "2" | python test_concurrent_api.py
```

---

## ⚠️ 重要安全提示

### 必须完成
- [ ] 修改数据库密码
- [ ] 生成新的 JWT_SECRET_KEY
- [ ] 配置正确的 CORS_ORIGINS
- [ ] 启用 HTTPS
- [ ] 限制 SSH 登录（禁用 root，使用密钥）
- [ ] 配置防火墙（只开放 80/443/22）
- [ ] 定期备份数据库

### 文件权限
```bash
# .env 文件权限
sudo chmod 600 /var/www/yishengban/backend/.env
sudo chown www-data:www-data /var/www/yishengban/backend/.env

# 上传目录权限
sudo chown -R www-data:www-data /var/www/yishengban/backend/static
```

### 防火墙
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

---

## 📈 监控和维护

### 查看日志
```bash
# 后端服务日志
sudo journalctl -u yishengban -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 系统资源监控
```bash
# 实时监控
htop

# 内存使用
free -h

# 磁盘使用
df -h
```

### 数据库备份
```bash
# 每日自动备份
sudo crontab -e
```

```cron
0 2 * * * mysqldump -u yishengban -p'password' yishengban > /backup/yishengban_$(date +\%Y\%m\%d).sql
```

---

## 🎯 容量评估

### 当前配置（2核2GB + 3个API key）
- **理论最大并发**: 15-20人
- **推荐同时在线**: 10-15人
- **API请求QPS**: ~4-5
- **数据库连接池**: 20

### 如需支持更多用户
| 目标用户数 | CPU | 内存 | API Keys | 建议配置 |
|-----------|-----|------|----------|----------|
| 10-15人   | 2核 | 2GB  | 3个      | 当前配置 ✓ |
| 30-50人   | 4核 | 8GB  | 5-8个    | 升级服务器 |
| 50-100人  | 8核 | 16GB | 10-15个  | 独立数据库 |
| 100+人    | 16核 | 32GB | 20+个    | 负载均衡集群 |

---

## 📝 部署命令速查

```bash
# 重启服务
sudo systemctl restart yishengban

# 查看状态
sudo systemctl status yishengban

# 查看日志（最近50行）
sudo journalctl -u yishengban -n 50

# 实时日志
sudo journalctl -u yishengban -f

# 重新加载 Nginx
sudo nginx -t && sudo systemctl reload nginx

# 更新代码后
cd /var/www/yishengban
git pull
cd frontend && npm ci && npm run build
sudo systemctl restart yishengban
```
