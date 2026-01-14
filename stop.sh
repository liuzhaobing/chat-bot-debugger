#!/bin/bash

# 停止服务脚本

set -e

echo "🛑 停止应用类型系统服务..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 停止后端
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null || echo "后端进程已停止"
    rm backend.pid
    echo -e "${GREEN}✓ 后端已停止${NC}"
else
    echo -e "${YELLOW}未找到后端 PID 文件${NC}"
fi

# 停止前端
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID 2>/dev/null || echo "前端进程已停止"
    rm frontend.pid
    echo -e "${GREEN}✓ 前端已停止${NC}"
else
    echo -e "${YELLOW}未找到前端 PID 文件${NC}"
fi

# 清理可能残留的进程
echo -e "\n${YELLOW}清理残留进程...${NC}"
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "vue-cli-service serve" 2>/dev/null || true

echo -e "\n${GREEN}✓ 所有服务已停止${NC}"
