# 快速开始指南

## 5 分钟快速部署

### 前置条件
- Docker 20.10+
- Docker Compose 2.0+

### 步骤 1: 克隆项目

```bash
git clone <your-repo>
cd <project-directory>
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp worker/.env.example worker/.env

# 生成 JWT 密钥
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> worker/.env

# 编辑其他必要配置（可选）
vim worker/.env
```

### 步骤 3: 启动服务

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 步骤 4: 数据库迁移

```bash
# 运行 Django 迁移
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户（可选）
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 步骤 5: 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 健康检查
curl http://localhost/health

# 预期输出:
# {
#   "status": "healthy",
#   "app": "AgenticWorker",
#   "version": "1.0.0",
#   "database": "connected",
#   "redis": "connected",
#   "websocket": {
#     "total_connections": 0,
#     "max_connections": 1000
#   }
# }
```

### 步骤 6: 测试 WebSocket 连接

#### 使用浏览器控制台

```javascript
// 打开浏览器控制台 (F12)
const ws = new WebSocket('ws://localhost/ws/agentic-test/test-session-123?token=dev-token');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({
    type: 'ping',
    content: 'hello'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

#### 使用 wscat (命令行工具)

```bash
# 安装 wscat
npm install -g wscat

# 连接 WebSocket
wscat -c "ws://localhost/ws/agentic-test/test-session?token=dev-token"

# 发送消息
> {"type": "ping", "content": "hello"}

# 预期响应
< {"type": "pong", "content": "pong", "timestamp": 1234567890.123}
```

## 访问服务

- **前端**: http://localhost
- **Django Admin**: http://localhost/admin
- **Django API**: http://localhost/api
- **Worker Health**: http://localhost/health
- **Worker Docs**: http://localhost/docs (仅开发环境)
- **WebSocket**: ws://localhost/ws/agentic-test/{session_id}

## 常用命令

### 查看日志

```bash
# 所有服务
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart worker
```

### 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 停止并删除数据卷（危险！）
docker-compose -f docker-compose.prod.yml down -v
```

### 进入容器

```bash
# 进入 Worker 容器
docker-compose -f docker-compose.prod.yml exec worker bash

# 进入 Backend 容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 进入数据库容器
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d agentic_db
```

## 开发模式

### 启动 Worker 开发服务器

```bash
cd worker

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 启动开发服务器（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 启动 Backend 开发服务器

```bash
cd backend

# 激活虚拟环境
source venv/bin/activate

# 启动 Django 开发服务器
python manage.py runserver 0.0.0.0:8000
```

## 故障排查

### Worker 无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.prod.yml logs worker

# 常见问题：
# 1. 数据库连接失败 -> 检查 DATABASE_URL
# 2. Redis 连接失败 -> 检查 REDIS_URL
# 3. 端口被占用 -> 修改 docker-compose.prod.yml 中的端口映射
```

### WebSocket 连接失败

```bash
# 1. 检查 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 2. 检查 Worker 是否运行
curl http://localhost:8001/health

# 3. 查看 Worker 日志
docker-compose -f docker-compose.prod.yml logs -f worker | grep -i websocket
```

### 数据库连接错误

```bash
# 检查数据库是否运行
docker-compose -f docker-compose.prod.yml ps postgres

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -c "SELECT 1"

# 重启数据库
docker-compose -f docker-compose.prod.yml restart postgres
```

## 下一步

1. 阅读 [架构文档](ARCHITECTURE.md) 了解系统设计
2. 阅读 [部署文档](DEPLOYMENT.md) 了解生产环境配置
3. 阅读 [实施总结](IMPLEMENTATION_SUMMARY.md) 了解项目进度
4. 查看 [Worker README](worker/README.md) 了解 Worker 服务详情

## 获取帮助

- 查看日志: `docker-compose -f docker-compose.prod.yml logs -f`
- 健康检查: `curl http://localhost/health`
- 查看连接统计: `curl http://localhost/ws/stats`

## 许可证

MIT
