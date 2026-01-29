#!/bin/bash
cd "$(dirname "$0")"

# 初始化conda
eval "$(conda shell.bash hook)"

# 激活环境
conda activate chat-bot-debugger

# 设置Django配置
export DJANGO_SETTINGS_MODULE=core.settings

# 启动服务
python -m uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --reload