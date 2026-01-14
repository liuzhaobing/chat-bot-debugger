# Chat Bot Debugger - 应用类型系统

一个支持多种应用类型（Agent 1.0, Agent 2.0, Workflow）的智能对话应用平台，具备完整的应用管理、调试和 Function Calling 支持。

## 🚀 快速开始

### 一键启动
```bash
./start.sh
```

### 访问系统
- **前端**: http://localhost:8080
- **后端**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/

### 停止服务
```bash
./stop.sh
```

## ✨ 核心功能

### 1. 应用类型管理
- ✅ **Agent 1.0**: 基于 Prompt 的快速对话应用
- ⏳ **Agent 2.0**: 强化 React 和 Function Call 能力（待实现）
- ⏳ **Workflow**: 自定义工作流编排（待实现）

### 2. 应用广场
- 📱 应用分类管理
- 🔍 类型筛选器（全部、Agent 1.0、Agent 2.0、Workflow）
- 🎨 应用卡片展示（显示应用类型）
- ➕ 快速创建应用

### 3. 应用配置（Agent 1.0）
- 📝 系统提示词编辑（支持 `{{variable}}` 变量）
- 🎛️ 模型选择和参数配置
- 💾 自动保存提示词（2秒防抖）
- 🚀 发布按钮保存完整配置
- 🔧 Function Calling Schema 预览

### 4. 实时调试
- 💬 右侧调试面板
- ⚡ 流式响应
- 🧪 变量替换测试

### 5. Function Calling 支持
- 🔌 自动生成 Function Calling Schema
- 🛠️ 可作为 MCP 工具使用
- 📋 符合 OpenAI Function Calling 规范

## 📚 文档

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 系统架构图和流程图 |
| [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) | 安全审计报告（评分 6.4/10） |
| [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) | 实现和部署指南 |
| [README_IMPLEMENTATION.md](./README_IMPLEMENTATION.md) | 实现总结（4900+ 行代码） |

## 🏗️ 技术栈

### 后端
- **Django 3.2+** - Web 框架
- **Django REST Framework** - API 框架
- **SQLite** - 数据库
- **Python 3.8+** - 编程语言

### 前端
- **Vue.js 2.x** - 前端框架
- **Vuex** - 状态管理
- **Axios** - HTTP 客户端
- **Vue Router** - 路由管理

## 📦 安装部署

### 前置要求
- Python 3.8+
- Node.js 14+
- npm 或 yarn

### 后端部署
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python init_app_types.py
python manage.py runserver
```

### 前端部署
```bash
cd frontend
npm install
npm run serve
```

## 🎯 使用指南

### 创建应用
1. 进入应用广场
2. 点击"在当前分组下新建应用"
3. 选择应用类型（目前仅 Agent 1.0 可用）
4. 填写应用名称和描述
5. 点击"立即创建"

### 配置应用
1. 点击应用卡片进入详情页
2. 编辑系统提示词（自动保存）
3. 设置变量默认值
4. 选择模型和调整参数
5. 点击"发布"保存完整配置

### 调试应用
1. 在右侧调试面板输入测试问题
2. 查看实时响应
3. 调整配置后重新测试

## 🔒 安全性

### 已实现
- ✅ SQL 注入防护（Django ORM）
- ✅ XSS 防护（Vue.js 自动转义）
- ✅ CSRF 防护（Django 中间件）
- ✅ 数据验证（DRF 序列化器）

### 待改进
- ⚠️ 用户认证系统（高优先级）
- ⚠️ API 限流（中优先级）
- ⚠️ 操作日志（中优先级）

详见 [SECURITY_AUDIT.md](./SECURITY_AUDIT.md)

## 📊 项目统计

- **代码行数**: 4900+
- **文件数量**: 13 个核心文件
- **文档页数**: 50+
- **安全评分**: 6.4/10

## 🎓 代码规范

- **后端**: Google Python Style Guide + PEP 8
- **前端**: Vue.js Style Guide
- **注释**: 详细的中文注释
- **API**: RESTful 设计原则

## 🛠️ API 接口

### 应用类型
```
GET    /api/app-types/              # 获取应用类型列表
GET    /api/app-types/?is_active=true  # 获取启用的类型
```

### 应用管理
```
GET    /api/apps/                   # 获取应用列表
POST   /api/apps/                   # 创建应用
GET    /api/apps/{id}/              # 获取应用详情
PATCH  /api/apps/{id}/              # 更新应用
DELETE /api/apps/{id}/              # 删除应用
```

### 应用操作
```
POST   /api/apps/{id}/publish/      # 发布应用
PATCH  /api/apps/{id}/auto_save_prompt/  # 自动保存提示词
GET    /api/apps/{id}/function_schema/   # 获取 Function Schema
```

### 筛选参数
```
?category=1                         # 按分类筛选
?app_type=agent_1_0                 # 按类型筛选
?search=keyword                     # 搜索应用
```

## 🔧 Function Calling 示例

### 自动生成的 Schema
```json
{
  "type": "function",
  "function": {
    "name": "fitness_coach",
    "description": "Personalized fitness and nutrition advice.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "用户的输入问题或请求"
        }
      },
      "required": ["query"]
    }
  }
}
```

### 使用方式
```python
# 获取应用的 Function Schema
response = requests.get('http://localhost:8000/api/apps/1/function_schema/')
schema = response.json()

# 用于 OpenAI Function Calling
completion = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...],
    functions=[schema]
)
```

## 🐛 故障排查

### 问题：迁移失败
```bash
rm backend/chat/migrations/0006_*.py
rm backend/chat/migrations/0007_*.py
rm backend/chat/migrations/0008_*.py
python manage.py makemigrations
python manage.py migrate
```

### 问题：应用类型为空
```bash
python backend/init_app_types.py
```

### 问题：前端无法连接后端
1. 检查后端是否运行：http://localhost:8000
2. 检查 CORS 配置
3. 查看浏览器控制台错误

## 📈 后续计划

### 短期（1-2周）
- [ ] 实现用户认证系统
- [ ] 添加操作日志
- [ ] 配置 API 限流

### 中期（1个月）
- [ ] 实现 Agent 2.0 配置组件
- [ ] 增强输入验证
- [ ] 添加单元测试

### 长期（3个月）
- [ ] 实现 Workflow 配置组件
- [ ] 添加安全监控
- [ ] 性能优化

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证

## 📞 联系方式

- 架构文档：[ARCHITECTURE.md](./ARCHITECTURE.md)
- 安全审计：[SECURITY_AUDIT.md](./SECURITY_AUDIT.md)
- 实现指南：[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)

---

**实现日期**: 2026-01-14  
**版本**: 1.0.0  
**架构师**: AI 全栈架构师
