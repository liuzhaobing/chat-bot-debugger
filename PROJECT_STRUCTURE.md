# 项目结构详解

## 完整目录树

```
agentic-test-microservices/
│
├── 📁 backend/                          # Django Backend (HTTP 服务)
│   ├── 📁 agentic_test/                 # 原有模块
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py                    # Django Models
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── consumers.py                 # ⚠️ 待迁移到 Worker
│   │   ├── agent_loop.py                # ⚠️ 待迁移到 Worker
│   │   ├── services.py                  # ⚠️ 待迁移到 Worker
│   │   └── routing.py                   # ⚠️ 待删除
│   ├── 📁 core/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Django 配置
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py                      # ⚠️ 需修改，移除 WebSocket
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
│
├── 📁 worker/                           # FastAPI Worker (WebSocket 服务) ⭐ 新增
│   ├── 📁 app/
│   │   ├── __init__.py
│   │   ├── main.py                      # ⭐ FastAPI 应用入口
│   │   ├── config.py                    # ⭐ 配置管理 (Pydantic Settings)
│   │   ├── dependencies.py              # 依赖注入
│   │   │
│   │   ├── 📁 core/                     # 核心模块
│   │   │   ├── __init__.py
│   │   │   ├── database.py              # ⭐ SQLAlchemy Async 配置
│   │   │   ├── redis.py                 # Redis 连接管理
│   │   │   ├── security.py              # JWT 鉴权
│   │   │   └── logging.py               # ⭐ 结构化日志 (JSON)
│   │   │
│   │   ├── 📁 models/                   # SQLAlchemy Models (镜像 Django)
│   │   │   ├── __init__.py
│   │   │   ├── session.py               # AgenticTestSession
│   │   │   ├── log.py                   # AgenticTestLog
│   │   │   └── device.py                # DeviceStatus
│   │   │
│   │   ├── 📁 schemas/                  # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── websocket.py             # WebSocket 消息格式
│   │   │   ├── audio.py                 # 音频数据格式
│   │   │   └── device.py                # 设备状态格式
│   │   │
│   │   ├── 📁 services/                 # 业务逻辑服务
│   │   │   ├── __init__.py
│   │   │   ├── tts_service.py           # TTS 服务
│   │   │   ├── asr_service.py           # ASR 服务
│   │   │   ├── vad_service.py           # VAD 服务
│   │   │   ├── iot_service.py           # IoT 服务
│   │   │   ├── audio_processor.py       # 音频处理
│   │   │   └── agent_service.py         # Agent 循环逻辑
│   │   │
│   │   ├── 📁 websocket/                # WebSocket 处理
│   │   │   ├── __init__.py
│   │   │   ├── manager.py               # ⭐ 连接管理器 (核心)
│   │   │   ├── handlers.py              # 消息处理器
│   │   │   └── auth.py                  # WebSocket 鉴权
│   │   │
│   │   ├── 📁 routers/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── health.py                # ⭐ 健康检查
│   │   │   └── websocket.py             # ⭐ WebSocket 路由
│   │   │
│   │   └── 📁 utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── audio_utils.py           # 音频工具
│   │       └── trace.py                 # TraceID 生成
│   │
│   ├── 📁 tests/                        # 测试目录
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Pytest 配置
│   │   ├── test_websocket.py            # WebSocket 测试
│   │   ├── test_services.py             # 服务测试
│   │   └── test_database.py             # 数据库测试
│   │
│   ├── 📁 scripts/                      # 脚本目录
│   │   ├── check_models.py              # 检查模型一致性
│   │   └── migrate_check.py             # 迁移检查
│   │
│   ├── Dockerfile                       # ⭐ Docker 配置 (多阶段构建)
│   ├── requirements.txt                 # ⭐ Python 依赖
│   ├── .env.example                     # ⭐ 环境变量模板
│   ├── gunicorn.conf.py                 # ⭐ Gunicorn 配置
│   └── README.md                        # Worker 文档
│
├── 📁 frontend/                         # Vue.js Frontend
│   ├── 📁 src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── 📁 components/
│   │       └── 📁 agentic-test/
│   │           └── ...                  # ⚠️ 需适配新 WebSocket URL
│   ├── 📁 dist/                         # 构建输出
│   ├── package.json
│   └── vue.config.js
│
├── 📁 nginx/                            # Nginx 配置 ⭐ 新增
│   ├── nginx.conf                       # 主配置
│   └── 📁 conf.d/
│       └── agentic.conf                 # ⭐ 反向代理配置 (核心)
│
├── 📁 k8s/                              # Kubernetes 配置 (可选)
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
│
├── 📁 docs/                             # 文档目录
│   ├── api/                             # API 文档
│   ├── architecture/                    # 架构图
│   └── guides/                          # 使用指南
│
├── docker-compose.yml                   # 开发环境编排
├── docker-compose.prod.yml              # ⭐ 生产环境编排 (核心)
│
├── .gitignore
├── .dockerignore
│
├── ARCHITECTURE.md                      # ⭐ 架构设计文档
├── DEPLOYMENT.md                        # ⭐ 部署文档
├── QUICKSTART.md                        # ⭐ 快速开始
├── IMPLEMENTATION_SUMMARY.md            # ⭐ 实施总结
├── PROJECT_STRUCTURE.md                 # 本文件
├── README_MICROSERVICES.md              # ⭐ 项目 README
└── README.md                            # 原项目 README
```

## 文件说明

### ⭐ 核心文件（必读）

| 文件 | 描述 | 优先级 |
|------|------|--------|
| `worker/app/main.py` | FastAPI 应用入口，定义路由和中间件 | 🔴 高 |
| `worker/app/config.py` | 配置管理，使用 Pydantic Settings | 🔴 高 |
| `worker/app/core/database.py` | SQLAlchemy Async 配置，连接池管理 | 🔴 高 |
| `worker/app/websocket/manager.py` | WebSocket 连接管理器，核心逻辑 | 🔴 高 |
| `worker/app/routers/websocket.py` | WebSocket 路由和消息处理 | 🔴 高 |
| `worker/Dockerfile` | Docker 多阶段构建配置 | 🔴 高 |
| `nginx/conf.d/agentic.conf` | Nginx 反向代理配置 | 🔴 高 |
| `docker-compose.prod.yml` | 生产环境服务编排 | 🔴 高 |

### ⚠️ 待迁移文件

| 原文件 | 目标文件 | 状态 |
|--------|----------|------|
| `backend/agentic_test/consumers.py` | `worker/app/routers/websocket.py` | 🔄 进行中 |
| `backend/agentic_test/agent_loop.py` | `worker/app/services/agent_service.py` | 📋 待开始 |
| `backend/agentic_test/services.py` | `worker/app/services/*_service.py` | 📋 待开始 |
| `backend/agentic_test/models.py` | `worker/app/models/*.py` | 📋 待开始 |

### 📚 文档文件

| 文件 | 描述 | 适合人群 |
|------|------|----------|
| `QUICKSTART.md` | 5分钟快速开始 | 所有人 |
| `README_MICROSERVICES.md` | 项目总览 | 所有人 |
| `ARCHITECTURE.md` | 架构设计详解 | 架构师、开发者 |
| `DEPLOYMENT.md` | 生产环境部署 | 运维、DevOps |
| `IMPLEMENTATION_SUMMARY.md` | 实施进度总结 | 项目经理、开发者 |
| `worker/README.md` | Worker 服务文档 | 开发者 |

## 服务端口分配

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Nginx | 80 | HTTP | 反向代理入口 |
| Nginx | 443 | HTTPS | SSL 终止 |
| Django Backend | 8000 | HTTP | 内部端口，不对外暴露 |
| FastAPI Worker | 8001 | HTTP/WS | 内部端口，不对外暴露 |
| PostgreSQL | 5432 | TCP | 内部端口，不对外暴露 |
| Redis | 6379 | TCP | 内部端口，不对外暴露 |
| Prometheus | 9090 | HTTP | 监控指标（可选） |

## URL 路由规则

| 路径 | 目标服务 | 说明 |
|------|----------|------|
| `/` | Frontend (Nginx) | 前端静态文件 |
| `/api/*` | Django Backend | RESTful API |
| `/admin/*` | Django Backend | Django Admin |
| `/static/*` | Django Backend | Django 静态文件 |
| `/media/*` | Django Backend | 媒体文件 |
| `/ws/*` | FastAPI Worker | WebSocket 连接 |
| `/health` | FastAPI Worker | 健康检查 |
| `/docs` | FastAPI Worker | API 文档（开发环境） |

## 数据流向

### HTTP 请求流

```
Client → Nginx → Django Backend → PostgreSQL
                                 → Redis
```

### WebSocket 连接流

```
Client → Nginx → FastAPI Worker → PostgreSQL (SQLAlchemy)
                                 → Redis
                                 → External Services (TTS/ASR/IoT)
```

### 认证流程

```
1. Client → Django Backend: POST /api/auth/login
2. Django Backend → PostgreSQL: 验证用户
3. Django Backend → Redis: 存储 Session/JWT
4. Django Backend → Client: 返回 JWT Token
5. Client → FastAPI Worker: WS /ws/...?token=xxx
6. FastAPI Worker → Redis: 验证 JWT
7. FastAPI Worker → Client: 建立 WebSocket 连接
```

## 环境变量配置

### Worker 环境变量 (`worker/.env`)

```bash
# 应用配置
APP_NAME=AgenticWorker
ENVIRONMENT=production
DEBUG=false

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=<生成的密钥>

# CORS
CORS_ORIGINS=https://yourdomain.com
```

### Backend 环境变量 (`backend/.env`)

```bash
# Django 配置
DJANGO_SETTINGS_MODULE=core.settings
SECRET_KEY=<Django密钥>

# 数据库
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Redis
REDIS_URL=redis://redis:6379/0
```

## 依赖关系

### Worker 核心依赖

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
gunicorn==23.0.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
redis[hiredis]==5.2.0
pydantic==2.10.3
python-jose[cryptography]==3.3.0
httpx==0.28.1
```

### Backend 核心依赖

```
django>=3.2,<4.0
djangorestframework
django-cors-headers
psycopg2-binary
redis
```

## 开发工作流

### 1. 本地开发

```bash
# 启动数据库和 Redis
docker-compose up -d postgres redis

# 启动 Backend
cd backend
python manage.py runserver

# 启动 Worker
cd worker
uvicorn app.main:app --reload
```

### 2. 测试

```bash
# Worker 测试
cd worker
pytest

# Backend 测试
cd backend
python manage.py test
```

### 3. 构建部署

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 监控与日志

### 日志位置

| 服务 | 日志位置 | 格式 |
|------|----------|------|
| Worker | `worker/logs/worker.log` | JSON |
| Backend | `backend/logs/django.log` | Text |
| Nginx | `/var/log/nginx/` | Text |
| PostgreSQL | Docker logs | Text |

### 监控指标

| 指标 | 端点 | 说明 |
|------|------|------|
| Worker 健康 | `/health` | 综合健康状态 |
| Worker 就绪 | `/ready` | Kubernetes 就绪探针 |
| Worker 存活 | `/live` | Kubernetes 存活探针 |
| WebSocket 统计 | `/ws/stats` | 连接统计 |
| Prometheus | `/metrics` | Prometheus 指标 |

## 下一步

1. 阅读 [QUICKSTART.md](QUICKSTART.md) 快速开始
2. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解架构
3. 参考 [DEPLOYMENT.md](DEPLOYMENT.md) 部署生产环境
4. 查看 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) 了解进度

---

**最后更新**: 2026-03-09  
**维护者**: Agentic Team
