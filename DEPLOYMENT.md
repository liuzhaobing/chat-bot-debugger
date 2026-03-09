# 部署文档

## 快速开始

### 1. 环境准备

#### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 至少 20GB 磁盘空间

#### 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp worker/.env.example worker/.env

# 编辑配置（重要！）
vim worker/.env

# 必须修改的配置：
# - JWT_SECRET_KEY: 生成强密码
# - DATABASE_URL: 生产数据库连接
# - REDIS_URL: Redis 连接
# - CORS_ORIGINS: 允许的前端域名
```

### 3. 生成 JWT 密钥

```bash
# 生成安全的 JWT 密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 将生成的密钥填入 .env 文件的 JWT_SECRET_KEY
```

### 4. 构建镜像

```bash
# 构建所有服务
docker-compose -f docker-compose.prod.yml build

# 或单独构建
docker-compose -f docker-compose.prod.yml build worker
docker-compose -f docker-compose.prod.yml build backend
```

### 5. 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f worker
```

### 6. 数据库迁移

```bash
# Django 数据库迁移
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 7. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 健康检查
curl http://localhost/health

# WebSocket 测试（使用 wscat）
npm install -g wscat
wscat -c "ws://localhost/ws/agentic-test/test-session?token=YOUR_JWT_TOKEN"
```

## 生产环境配置

### 1. 使用 PostgreSQL

```yaml
# docker-compose.prod.yml 中已配置
# 修改 worker/.env:
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@postgres:5432/agentic_db
```

### 2. 配置 HTTPS

```bash
# 1. 获取 SSL 证书（Let's Encrypt）
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com

# 2. 复制证书到 nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# 3. 取消注释 nginx/conf.d/agentic.conf 中的 HTTPS 配置

# 4. 重启 Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 3. 配置域名

```bash
# 修改 nginx/conf.d/agentic.conf
server_name yourdomain.com;

# 修改 worker/.env
CORS_ORIGINS=https://yourdomain.com
ALLOWED_WS_ORIGINS=https://yourdomain.com
```

### 4. 性能优化

#### Worker 进程数

```bash
# 推荐：CPU 核心数 * 2 + 1
# 4核CPU -> 9个 workers

# 修改 worker/.env
GUNICORN_WORKERS=9
```

#### 数据库连接池

```bash
# 修改 worker/.env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

#### Redis 配置

```bash
# 修改 docker-compose.prod.yml
command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### 5. 监控配置

#### 日志聚合

```bash
# 使用 ELK Stack 或 Loki
# 日志已配置为 JSON 格式，便于解析

# 查看日志
docker-compose -f docker-compose.prod.yml logs --tail=100 -f worker
```

#### Prometheus 监控

```bash
# Worker 暴露 /metrics 端点
curl http://localhost:8001/metrics

# 配置 Prometheus 抓取
# prometheus.yml:
scrape_configs:
  - job_name: 'agentic-worker'
    static_configs:
      - targets: ['worker:8001']
```

## 扩展部署

### 水平扩展 Worker

```yaml
# docker-compose.prod.yml
services:
  worker:
    deploy:
      replicas: 3  # 启动3个实例
```

### 使用 Kubernetes

```bash
# 1. 构建镜像并推送到仓库
docker build -t your-registry/agentic-worker:v1.0.0 ./worker
docker push your-registry/agentic-worker:v1.0.0

# 2. 创建 Kubernetes 配置
# 参考 k8s/ 目录下的配置文件

# 3. 部署
kubectl apply -f k8s/
```

## 故障排查

### Worker 无法连接数据库

```bash
# 1. 检查数据库是否运行
docker-compose -f docker-compose.prod.yml ps postgres

# 2. 检查数据库连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d agentic_db

# 3. 检查 Worker 日志
docker-compose -f docker-compose.prod.yml logs worker | grep -i database
```

### WebSocket 连接失败

```bash
# 1. 检查 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 2. 检查 Worker 是否运行
curl http://localhost:8001/health

# 3. 检查 JWT Token 是否有效
# 使用 jwt.io 解码 token

# 4. 查看 Worker 日志
docker-compose -f docker-compose.prod.yml logs -f worker
```

### 性能问题

```bash
# 1. 检查资源使用
docker stats

# 2. 检查数据库连接池
docker-compose -f docker-compose.prod.yml logs worker | grep -i "pool"

# 3. 增加 Worker 数量
# 修改 worker/.env: GUNICORN_WORKERS=12

# 4. 重启服务
docker-compose -f docker-compose.prod.yml restart worker
```

## 备份与恢复

### 数据库备份

```bash
# 备份
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres agentic_db > backup_$(date +%Y%m%d).sql

# 恢复
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres agentic_db < backup_20260309.sql
```

### Redis 备份

```bash
# 备份
docker-compose -f docker-compose.prod.yml exec redis redis-cli SAVE
docker cp agentic-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb

# 恢复
docker cp redis_backup_20260309.rdb agentic-redis:/data/dump.rdb
docker-compose -f docker-compose.prod.yml restart redis
```

## 更新部署

### 滚动更新

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose -f docker-compose.prod.yml build worker

# 3. 滚动更新（零停机）
docker-compose -f docker-compose.prod.yml up -d --no-deps --build worker

# 4. 验证
curl http://localhost/health
```

### 回滚

```bash
# 1. 查看镜像历史
docker images | grep agentic-worker

# 2. 使用旧版本镜像
docker tag agentic-worker:old agentic-worker:latest

# 3. 重启服务
docker-compose -f docker-compose.prod.yml up -d worker
```

## 安全建议

### 1. 环境变量安全

```bash
# 不要将 .env 文件提交到 Git
echo ".env" >> .gitignore

# 使用 Docker Secrets（Swarm 模式）
docker secret create jwt_secret jwt_secret.txt
```

### 2. 网络隔离

```yaml
# docker-compose.prod.yml
# 数据库和 Redis 不暴露端口
postgres:
  # ports:  # 注释掉，只允许内部访问
  #   - "5432:5432"
```

### 3. 定期更新

```bash
# 更新基础镜像
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 监控告警

### 配置告警规则

```yaml
# Prometheus 告警规则
groups:
  - name: agentic_worker
    rules:
      - alert: HighWebSocketConnections
        expr: websocket_connections > 900
        for: 5m
        annotations:
          summary: "WebSocket 连接数过高"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_size - db_pool_available < 2
        for: 2m
        annotations:
          summary: "数据库连接池即将耗尽"
```

## 性能基准

### 预期性能指标

- WebSocket 并发连接：1000+
- 消息延迟：< 100ms (P99)
- 数据库查询：< 50ms (P95)
- CPU 使用率：< 70%
- 内存使用：< 2GB per worker

### 压力测试

```bash
# 使用 k6 进行 WebSocket 压力测试
k6 run --vus 100 --duration 30s websocket_test.js
```

## 联系支持

如有问题，请联系：
- Email: support@example.com
- Slack: #agentic-support
- 文档: https://docs.example.com
