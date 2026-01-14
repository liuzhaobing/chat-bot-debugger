# 应用类型系统实现指南

## 📋 功能概述

本次实现了以下核心功能：

1. **应用类型管理系统**
   - 新增 `AppType` 数据表，管理应用类型（Agent 1.0, Agent 2.0, Workflow 等）
   - 应用创建时必须选择类型
   - 支持类型的启用/禁用控制

2. **应用广场增强**
   - 应用卡片显示应用类型（替换"官方发布"）
   - 新增类型筛选器（全部、Agent 1.0、Agent 2.0 等）
   - 创建应用时选择类型

3. **Function Calling 支持**
   - 应用自动生成 Function Calling Schema
   - 可作为 MCP 工具或 Function Calling 候选项使用
   - 支持自定义 Schema

4. **应用详情页重构**
   - 根据应用类型动态加载配置组件
   - Agent 1.0 配置组件独立封装
   - 自动保存 system_prompt
   - 发布按钮保存完整配置（模型、参数等）

## 🏗️ 架构设计

### 数据库设计

#### AppType (应用类型表)
```sql
- id: 主键
- name: 显示名称 (如 "Agent 1.0")
- code: 代码标识 (如 "agent_1_0")
- description: 类型描述
- is_active: 是否启用
- sort_order: 排序权重
- created_at: 创建时间
```

#### App (应用表 - 新增字段)
```sql
- app_type_id: 外键 → AppType (必填)
- model_name: 使用的模型名称
- function_schema: Function Calling Schema (JSON)
- updated_at: 更新时间
```

### API 接口

#### 应用类型接口
- `GET /api/app-types/` - 获取应用类型列表
- `GET /api/app-types/?is_active=true` - 获取启用的类型

#### 应用接口（扩展）
- `GET /api/apps/?app_type=agent_1_0` - 按类型筛选应用
- `POST /api/apps/{id}/publish/` - 发布应用（保存完整配置）
- `PATCH /api/apps/{id}/auto_save_prompt/` - 自动保存提示词
- `GET /api/apps/{id}/function_schema/` - 获取 Function Calling Schema

## 🚀 部署步骤

### 1. 后端部署

#### 1.1 激活 Python 虚拟环境
```bash
cd backend
# 如果还没有虚拟环境，创建一个
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

#### 1.2 安装依赖
```bash
pip install -r requirements.txt
```

#### 1.3 运行数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 1.4 初始化应用类型数据
```bash
python init_app_types.py
```

#### 1.5 启动后端服务
```bash
python manage.py runserver
```

### 2. 前端部署

#### 2.1 安装依赖
```bash
cd frontend
npm install
```

#### 2.2 启动开发服务器
```bash
npm run serve
```

## 📝 使用说明

### 创建应用

1. 进入应用广场
2. 点击"在当前分组下新建应用"
3. 选择应用类型（目前仅 Agent 1.0 可用）
4. 填写应用名称和描述
5. 点击"立即创建"

### 配置应用（Agent 1.0）

1. 点击应用卡片进入详情页
2. 左侧配置面板：
   - 编辑应用基本信息
   - 编写系统提示词（支持 `{{variable}}` 变量）
   - 设置变量默认值
   - 选择模型和调整参数
   - 查看 Function Calling Schema
3. 右侧调试面板：
   - 输入测试问题
   - 实时查看对话效果
4. 点击"发布"按钮保存完整配置

### 自动保存机制

- **system_prompt**: 输入后 2 秒自动保存
- **其他字段**: 仅在点击"发布"按钮时保存
- **模型和参数**: 在发布时一并保存

### 类型筛选

在应用广场右侧，点击类型筛选器按钮：
- **全部**: 显示所有应用
- **Agent 1.0**: 仅显示 Agent 1.0 类型应用
- **Agent 2.0**: 暂未开放
- **Workflow**: 暂未开放

## 🔧 Function Calling 使用

### 自动生成的 Schema 格式

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

### 获取应用的 Function Schema

```bash
GET /api/apps/{app_id}/function_schema/
```

### 作为 MCP 工具使用

应用的 `function_schema` 字段可以直接用于 MCP 工具配置：

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "fitness_coach_app",
        "description": "...",
        "parameters": {...}
      }
    }
  ]
}
```

## 🔒 安全性说明

### 已实现的安全措施

1. **SQL 注入防护**: 使用 Django ORM，自动参数化查询
2. **XSS 防护**: Vue.js 自动转义输出
3. **数据验证**: 
   - Function Schema 格式验证
   - 应用类型有效性验证
   - 必填字段验证

### 建议的安全增强

1. **用户认证**: 添加用户系统，限制应用编辑权限
2. **API 限流**: 防止恶意请求
3. **输入清理**: 对用户输入进行更严格的清理和验证

## 📂 文件结构

### 后端新增/修改文件

```
backend/
├── chat/
│   ├── models.py                          # 新增 AppType 模型，扩展 App 模型
│   ├── serializers.py                     # 新增类型序列化器
│   ├── views.py                           # 新增类型视图和发布接口
│   ├── urls.py                            # 新增类型路由
│   └── migrations/
│       ├── 0006_apptype_and_app_extensions.py
│       ├── 0007_populate_app_types.py
│       └── 0008_make_app_type_required.py
└── init_app_types.py                      # 数据初始化脚本
```

### 前端新增/修改文件

```
frontend/
└── src/
    ├── components/
    │   └── app-configs/
    │       └── Agent1ConfigComponent.vue  # Agent 1.0 配置组件
    └── views/
        ├── AppsView.vue                   # 新增类型筛选器
        └── AppDetailView.vue              # 重构为动态组件加载
```

## 🎯 后续扩展

### Agent 2.0 实现

1. 创建 `Agent2ConfigComponent.vue`
2. 实现 React 和 Function Call 逻辑
3. 在 `AppDetailView.vue` 中注册组件
4. 更新 `AppType` 的 `is_active` 为 `true`

### Workflow 实现

1. 创建 `WorkflowConfigComponent.vue`
2. 实现工作流编排界面
3. 扩展 `App` 模型添加工作流配置字段
4. 在 `AppDetailView.vue` 中注册组件

## 🐛 故障排查

### 问题：迁移失败

**解决方案**:
```bash
# 删除旧的迁移文件（如果有冲突）
rm backend/chat/migrations/0006_*.py
rm backend/chat/migrations/0007_*.py
rm backend/chat/migrations/0008_*.py

# 重新生成迁移
python manage.py makemigrations
python manage.py migrate
```

### 问题：应用类型为空

**解决方案**:
```bash
# 运行初始化脚本
python backend/init_app_types.py
```

### 问题：前端无法获取应用类型

**解决方案**:
1. 检查后端是否正常运行
2. 检查 API 路由是否正确注册
3. 查看浏览器控制台错误信息

## 📞 技术支持

如有问题，请检查：
1. 后端日志: `python manage.py runserver` 输出
2. 前端控制台: 浏览器开发者工具
3. 数据库状态: `python manage.py dbshell`

## 📄 代码规范

本实现遵循以下规范：
- **Google Python Style Guide** (后端)
- **Vue.js Style Guide** (前端)
- **RESTful API 设计原则**
- **详细的中文注释**

## ✅ 功能清单

- [x] AppType 数据表设计和实现
- [x] App 模型扩展（app_type, model_name, function_schema）
- [x] 应用类型 API 接口
- [x] 应用广场类型筛选器
- [x] 应用卡片显示类型
- [x] 创建应用时选择类型
- [x] Agent1ConfigComponent 组件
- [x] AppDetailView 动态组件加载
- [x] system_prompt 自动保存
- [x] 发布按钮保存完整配置
- [x] Function Calling Schema 生成
- [x] 数据迁移脚本
- [x] 初始化脚本
- [x] 文档和部署指南

## 🎉 总结

本次实现完成了应用类型系统的完整架构，为后续扩展 Agent 2.0 和 Workflow 奠定了基础。系统设计遵循了模块化、可扩展的原则，代码质量符合 Google 编程规范，并包含详细的中文注释。
