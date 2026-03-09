# FastAPI Worker Service

企业级 WebSocket 服务，专门处理高并发实时连接和异步任务。

## 目录结构

```
worker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy 数据库配置
│   │   ├── redis.py            # Redis 连接管理
│   │   ├── security.py         # JWT 鉴权
│   │   └── logging.py          # 结构化日志
│   │
│   ├── models/                 # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── session.py          # AgenticTestSession
│   │   ├── log.py              # AgenticTestLog
│   │   └── device.py           # DeviceStatus
│   │
│   ├── schemas/                # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── websocket.py        # WebSocket 消息格式
│   │   ├── audio.py            # 音频数据格式
│   │   └── device.py           # 设备状态格式
│   │
│   ├── services/               # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── tts_service.py      # TTS 服务
│   │   ├── asr_service.py      # ASR 服务
│   │   ├── vad_service.py      # VAD 服务
│   │   ├── iot_service.py      # IoT 服务
│   │   └── audio_processor.py  # 音频处理
│   │
│   ├── websocket/              # WebSocket 处理
│   │   ├── __init__.py
│   │   ├── manager.py          # 连接管理器
│   │   ├── handlers.py         # 消息处理器
│   │   └── auth.py             # WebSocket 鉴权
│   │
│   ├── routers/                # API 路由
│   │   ├── __init__.py
│   │   ├── health.py           # 健康检查
│   │   └── websocket.py        # WebSocket 路由
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── audio_utils.py      # 音频工具
│       └── trace.py            # TraceID 生成
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_websocket.py
│   └── test_services.py
│
├── scripts/                    # 脚本目录
│   ├── check_models.py         # 检查模型一致性
│   └── migrate_check.py        # 迁移检查
│
├── Dockerfile                  # Docker 配置
├── docker-compose.yml          # Docker Compose
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量示例
├── gunicorn.conf.py            # Gunicorn 配置
└── README.md                   # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd worker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 3. 启动开发服务器

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 或使用 FastAPI CLI
fastapi dev app/main.py --port 8001
```

### 4. 启动生产服务器

```bash
# 使用 Gunicorn + Uvicorn Workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5
```

## Docker 部署

### 构建镜像

```bash
docker build -t agentic-worker:latest .
```

### 运行容器

```bash
docker run -d \
  --name agentic-worker \
  -p 8001:8001 \
  --env-file .env \
  agentic-worker:latest
```

### Docker Compose

```bash
docker-compose up -d
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## WebSocket 连接

```javascript
// 连接示例
const ws = new WebSocket('ws://localhost:8001/ws/agentic-test/{session_id}?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({
    type: 'start_test',
    query: '打开油烟机',
    iot_config: { token: 'xxx', familyId: 'yyy', env: 'test' }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 健康检查

```bash
curl http://localhost:8001/health
```

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_websocket.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 性能优化

### 1. 数据库连接池

```python
# config.py
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

### 2. Redis 连接池

```python
# config.py
REDIS_MAX_CONNECTIONS = 50
```

### 3. Worker 数量

```bash
# 推荐：CPU 核心数 * 2 + 1
gunicorn --workers 9 ...
```

## 监控与日志

### 结构化日志

所有日志以 JSON 格式输出，包含 TraceID：

```json
{
  "timestamp": "2026-03-09T10:30:00Z",
  "level": "INFO",
  "trace_id": "abc123",
  "message": "WebSocket connected",
  "session_id": "uuid-xxx",
  "user_id": "user-123"
}
```

### Prometheus 指标

访问 `/metrics` 获取 Prometheus 格式的指标。

## 故障排查

### WebSocket 连接失败

1. 检查 JWT Token 是否有效
2. 检查 Redis 连接
3. 查看日志：`docker logs agentic-worker`

### 数据库连接错误

1. 检查数据库配置
2. 确认数据库可访问
3. 检查连接池配置

### 性能问题

1. 增加 Worker 数量
2. 优化数据库查询
3. 启用 Redis 缓存

## 开发指南

### 添加新的 WebSocket 消息类型

1. 在 `schemas/websocket.py` 定义 Schema
2. 在 `websocket/handlers.py` 添加处理器
3. 在 `websocket/manager.py` 注册路由

### 添加新的外部服务

1. 在 `services/` 创建服务类
2. 实现异步方法
3. 添加错误处理和重试逻辑

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交代码
4. 创建 Pull Request

## License

MIT
