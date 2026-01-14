#!/bin/bash

# 应用类型系统快速启动脚本
# 用于快速部署和启动整个系统

set -e

echo "🚀 应用类型系统快速启动脚本"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python
echo -e "\n${YELLOW}[1/6] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python 3${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 已安装${NC}"

# 检查 Node.js
echo -e "\n${YELLOW}[2/6] 检查 Node.js 环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js 已安装${NC}"

# 后端设置
echo -e "\n${YELLOW}[3/6] 设置后端环境...${NC}"
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装 Python 依赖..."
pip install -q -r requirements.txt

# 运行迁移
echo "运行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 初始化应用类型
echo "初始化应用类型数据..."
python init_app_types.py

echo -e "${GREEN}✓ 后端环境设置完成${NC}"

# 前端设置
echo -e "\n${YELLOW}[4/6] 设置前端环境...${NC}"
cd ../frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装 Node.js 依赖..."
    npm install
else
    echo "Node.js 依赖已安装"
fi

echo -e "${GREEN}✓ 前端环境设置完成${NC}"

# 启动服务
echo -e "\n${YELLOW}[5/6] 启动服务...${NC}"

# 启动后端（后台运行）
cd ../backend
echo "启动后端服务 (http://localhost:8000)..."
source venv/bin/activate
python manage.py runserver > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端（后台运行）
cd ../frontend
echo "启动前端服务 (http://localhost:8080)..."
npm run serve > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

# 保存 PID
cd ..
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo -e "\n${GREEN}✓ 服务启动成功${NC}"

# 显示信息
echo -e "\n${YELLOW}[6/6] 服务信息${NC}"
echo "================================"
echo -e "${GREEN}后端服务:${NC} http://localhost:8000"
echo -e "${GREEN}前端服务:${NC} http://localhost:8080"
echo -e "${GREEN}API 文档:${NC} http://localhost:8000/api/"
echo ""
echo -e "${YELLOW}日志文件:${NC}"
echo "  - 后端: backend.log"
echo "  - 前端: frontend.log"
echo ""
echo -e "${YELLOW}停止服务:${NC}"
echo "  ./stop.sh"
echo ""
echo -e "${YELLOW}查看日志:${NC}"
echo "  tail -f backend.log"
echo "  tail -f frontend.log"
echo ""
echo -e "${GREEN}🎉 系统已启动！请访问 http://localhost:8080${NC}"
