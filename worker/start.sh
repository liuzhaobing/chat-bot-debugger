#!/bin/bash
# Worker Service 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量 (使用 source 避免 JSON 数组解析问题)
if [ -f .env ]; then
    set -a
    source <(grep -v '^#' .env | grep -v '^\s*$')
    set +a
fi

# 默认配置
HOST=${WORKER_HOST:-0.0.0.0}
PORT=${WORKER_PORT:-8001}
WORKERS=${GUNICORN_WORKERS:-4}
# 转换为小写 (uvicorn 要求小写)
LOG_LEVEL=$(echo ${LOG_LEVEL:-info} | tr '[:upper:]' '[:lower:]')

echo "========================================"
echo "  Agentic Worker Service"
echo "========================================"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"
echo "========================================"

# 检查是否使用开发模式
if [ "$ENVIRONMENT" = "development" ] || [ "$DEBUG" = "true" ]; then
    echo "Starting in DEVELOPMENT mode..."
    exec uvicorn app.main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level $LOG_LEVEL
else
    echo "Starting in PRODUCTION mode..."
    exec gunicorn app.main:app \
        --workers $WORKERS \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind $HOST:$PORT \
        --timeout 120 \
        --graceful-timeout 30 \
        --keep-alive 5 \
        --log-level $LOG_LEVEL \
        --access-logfile - \
        --error-logfile -
fi