# 更新说明 - 修正版

## 🔄 主要变更

### 1. Function Calling 参数管理 ✅

**变更内容**:
- ❌ 删除 `variables` 字段（旧的变量管理方式）
- ❌ 删除 `function_schema` 字段（不再单独存储）
- ✅ 新增 `parameters` 字段（符合 OpenAI Function Calling 规范）
- ✅ 新增参数编辑界面，支持：
  - 参数名称
  - 参数类型（string, number, boolean, array, object）
  - 参数描述
  - 参数默认值
  - 必填/可选标记

**数据结构**:
```json
{
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "城市名称",
        "default": "北京"
      },
      "temperature": {
        "type": "number",
        "description": "温度值"
      }
    },
    "required": ["city"]
  }
}
```

**Function Calling Schema 生成**:
```json
{
  "type": "function",
  "function": {
    "name": "GetWeather",  // 使用应用名称（驼峰格式）
    "description": "获取天气信息",  // 使用应用描述
    "parameters": {  // 直接使用 parameters 字段
      "type": "object",
      "properties": {...},
      "required": [...]
    }
  }
}
```

### 2. 模型和供应商信息存储 ✅

**变更内容**:
- ✅ 新增 `provider_id` 字段 - 存储供应商ID
- ✅ 保留 `model_name` 字段 - 存储模型名称
- ✅ 发布时同时保存供应商和模型信息

**数据示例**:
```json
{
  "provider_id": 1,
  "model_name": "gpt-4",
  "configuration": {
    "temperature": 0.7
  }
}
```

### 3. 应用名称驼峰命名验证 ✅

**验证规则**:
- ✅ 必须以大写字母开头
- ✅ 只允许英文字母（大小写）
- ✅ 不允许空格
- ✅ 不允许标点符号和特殊字符

**有效示例**:
- ✅ `GetWeather`
- ✅ `FitnessCoach`
- ✅ `ASRRepairRequest`

**无效示例**:
- ❌ `get_weather` (不是驼峰格式)
- ❌ `Get Weather` (包含空格)
- ❌ `GetWeather!` (包含标点符号)
- ❌ `getWeather` (首字母小写)

### 4. 必填字段验证 ✅

**创建应用时**:
- ✅ 应用名称：必填，驼峰命名
- ✅ 应用描述：必填
- ✅ 应用类型：必填

**友好的错误提示**:
- "应用名称不能为空"
- "应用描述不能为空"
- "应用名称必须符合驼峰命名规范（如 GetWeather），只允许英文字母，必须以大写字母开头，不允许空格和标点符号"

## 📊 数据库变更

### 迁移文件
- `0009_update_app_parameters.py` - 更新 App 模型

### 字段变更

| 操作 | 字段 | 说明 |
|------|------|------|
| 重命名 | `variables` → `parameters` | 改为 Function Calling 参数格式 |
| 删除 | `function_schema` | 不再单独存储，动态生成 |
| 新增 | `provider_id` | 存储供应商ID |
| 修改 | `name` | 添加驼峰命名验证器 |

## 🔧 API 变更

### App 序列化器字段

**新增字段**:
```python
'provider_id',  # 供应商ID
'parameters',   # Function Calling 参数
```

**删除字段**:
```python
'variables',       # 旧的变量字段
'function_schema', # 不再单独存储
```

### 新增方法

**App 模型**:
```python
def get_function_schema(self):
    """动态生成 Function Calling Schema"""
    return {
        "type": "function",
        "function": {
            "name": self.name,  # 驼峰格式的应用名
            "description": self.description,
            "parameters": self.parameters
        }
    }
```

## 🎨 前端变更

### Agent1ConfigComponent.vue

**新增功能**:
1. **参数管理界面**
   - 参数列表展示
   - 添加参数按钮
   - 参数编辑（名称、类型、描述、默认值）
   - 必填/可选切换
   - 删除参数

2. **参数添加模态框**
   - 参数名称输入
   - 参数类型选择（下拉框）
   - 参数描述输入
   - 默认值输入

3. **供应商信息存储**
   - 保存 `provider_id`
   - 保存 `model_name`

**删除功能**:
- ❌ 变量自动识别（`{{variable}}`）
- ❌ 变量值设置

### AppsView.vue

**新增验证**:
1. 应用名称必填验证
2. 应用描述必填验证
3. 驼峰命名格式验证
4. 友好的错误提示

## 🚀 部署步骤

### 1. 停止服务
```bash
./stop.sh
```

### 2. 更新代码
```bash
git pull
```

### 3. 运行迁移
```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

### 4. 启动服务
```bash
./start.sh
```

## ⚠️ 注意事项

### 数据迁移

**现有应用的处理**:
1. `variables` 字段会自动重命名为 `parameters`
2. 如果现有应用的 `variables` 是数组格式，需要手动转换为 parameters 格式
3. `function_schema` 字段会被删除，改为动态生成

**建议操作**:
```python
# 如果有现有应用，建议运行以下脚本转换数据
from chat.models import App

for app in App.objects.all():
    # 如果 parameters 是旧的数组格式，转换为新格式
    if isinstance(app.parameters, list):
        properties = {}
        required = []
        for var in app.parameters:
            if isinstance(var, dict) and 'name' in var:
                properties[var['name']] = {
                    'type': 'string',
                    'description': var.get('description', f"参数 {var['name']}"),
                    'default': var.get('default', '')
                }
        app.parameters = {
            'type': 'object',
            'properties': properties,
            'required': required
        }
        app.save()
```

### 应用名称

**现有应用名称检查**:
- 如果现有应用名称不符合驼峰命名规范，需要手动修改
- 建议在迁移前检查所有应用名称

```python
from chat.models import App
import re

pattern = r'^[A-Z][a-zA-Z]*$'
for app in App.objects.all():
    if not re.match(pattern, app.name):
        print(f"应用 {app.id}: {app.name} 不符合驼峰命名规范")
```

## 📝 使用示例

### 创建应用

```javascript
// 前端创建应用
const appData = {
  name: "GetWeather",  // 驼峰命名
  description: "获取天气信息",  // 必填
  app_type: 1,  // Agent 1.0
  category: 1
}

await axios.post('/api/apps/', appData)
```

### 配置参数

```javascript
// 添加参数
const parameters = {
  type: 'object',
  properties: {
    city: {
      type: 'string',
      description: '城市名称',
      default: '北京'
    },
    unit: {
      type: 'string',
      description: '温度单位',
      default: 'celsius'
    }
  },
  required: ['city']
}
```

### 发布应用

```javascript
// 发布时保存完整配置
const publishData = {
  name: "GetWeather",
  description: "获取天气信息",
  system_prompt: "你是一个天气助手...",
  provider_id: 1,  // 供应商ID
  model_name: "gpt-4",  // 模型名称
  configuration: {
    temperature: 0.7
  },
  parameters: {
    type: 'object',
    properties: {...},
    required: [...]
  }
}

await axios.post(`/api/apps/${appId}/publish/`, publishData)
```

### 获取 Function Schema

```javascript
// 获取应用的 Function Calling Schema
const response = await axios.get(`/api/apps/${appId}/function_schema/`)

// 返回格式
{
  "type": "function",
  "function": {
    "name": "GetWeather",
    "description": "获取天气信息",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名称",
          "default": "北京"
        }
      },
      "required": ["city"]
    }
  }
}
```

## 🎯 优势

### 1. 符合标准
- ✅ 完全符合 OpenAI Function Calling 规范
- ✅ 可直接用于 MCP 工具配置
- ✅ 参数定义更加规范和灵活

### 2. 更好的用户体验
- ✅ 可视化参数编辑界面
- ✅ 支持多种参数类型
- ✅ 友好的错误提示
- ✅ 驼峰命名规范保证一致性

### 3. 更强的扩展性
- ✅ 参数支持复杂类型（array, object）
- ✅ 可以添加更多参数属性（enum, pattern 等）
- ✅ 动态生成 Schema，避免数据冗余

## 📞 问题排查

### 问题1: 迁移失败
```bash
# 解决方案
python manage.py migrate chat 0008  # 回退到上一个版本
python manage.py migrate  # 重新迁移
```

### 问题2: 现有应用名称不符合规范
```python
# 批量修改应用名称
from chat.models import App

# 示例：将 "get weather" 改为 "GetWeather"
app = App.objects.get(name="get weather")
app.name = "GetWeather"
app.save()
```

### 问题3: parameters 格式错误
```python
# 重置为默认格式
app.parameters = {
    'type': 'object',
    'properties': {},
    'required': []
}
app.save()
```

## ✅ 测试清单

- [ ] 创建新应用（驼峰命名）
- [ ] 创建应用时验证必填字段
- [ ] 创建应用时验证驼峰命名
- [ ] 添加参数
- [ ] 编辑参数
- [ ] 删除参数
- [ ] 切换必填/可选
- [ ] 选择模型和供应商
- [ ] 发布应用
- [ ] 获取 Function Schema
- [ ] 验证 Schema 格式正确

---

**更新日期**: 2026-01-14  
**版本**: 2.0.0  
**重要性**: 🔴 高（包含数据库结构变更）
