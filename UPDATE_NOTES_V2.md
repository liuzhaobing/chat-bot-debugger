# 更新说明 V2 - 参数自动解析和增强编辑

## 🎯 本次更新内容

### 1. ✅ 恢复参数自动解析功能

**功能说明**:
- 系统会自动从 `system_prompt` 中检测 `{{parameter}}` 格式的参数
- 检测到新参数时自动添加到参数列表
- 为新参数设置默认配置（类型、描述等）

**解析逻辑**:
```javascript
// 正则表达式匹配 {{parameter_name}}
const regex = /\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}/g

// 示例提示词
"你是一个{{role}}，专门处理{{task}}相关的问题"

// 自动检测到参数: role, task
```

**自动配置**:
```json
{
  "role": {
    "type": "string",
    "description": "参数 role",
    "default": ""
  },
  "task": {
    "type": "string",
    "description": "参数 task",
    "default": ""
  }
}
```

### 2. ✅ 增强参数编辑界面

**新增功能**:

#### A. 参数类型编辑
- 支持 5 种数据类型：
  - `string` (字符串)
  - `number` (数字)
  - `boolean` (布尔值)
  - `array` (数组)
  - `object` (对象)

#### B. 参数描述编辑
- 可编辑参数描述
- 描述用于 Function Calling，帮助 LLM 理解参数用途
- 清晰的描述提示

#### C. 测试值输入框
- 每个参数都有独立的测试值输入框
- 测试值用于调试时替换提示词中的参数
- 实时预览效果

#### D. 必填参数标记
- 可切换参数的必填/可选状态
- 必填参数会显示红色标签
- 必填参数会添加到 `required` 数组

### 3. 🎨 界面优化

**参数卡片布局**:
```
┌─────────────────────────────────────────┐
│ parameter_name  [string]  [必填]  [编辑] [删除] │
├─────────────────────────────────────────┤
│ 描述: 参数的详细描述                      │
│ 测试值: [___输入测试值___]                │
│ ☑ 必填参数    默认值: "default"          │
└─────────────────────────────────────────┘
```

**编辑模态框**:
- 渐变色标题栏
- 清晰的字段分组
- 友好的提示文本
- 响应式设计

### 4. 🔄 工作流程

#### 创建应用流程
```
1. 编写 system_prompt
   "你是一个{{role}}，处理{{city}}的天气查询"
   
2. 系统自动检测参数
   ✓ 检测到: role, city
   
3. 自动创建参数配置
   ✓ role: { type: "string", description: "参数 role" }
   ✓ city: { type: "string", description: "参数 city" }
   
4. 编辑参数详情
   - 点击"编辑"按钮
   - 修改类型为 string
   - 完善描述: "用户的角色，如助手、顾问等"
   - 设置默认值: "助手"
   
5. 设置测试值
   - role: "天气助手"
   - city: "北京"
   
6. 调试测试
   - 系统使用测试值替换提示词
   - 实际发送: "你是一个天气助手，处理北京的天气查询"
```

## 📊 数据结构

### Parameters 完整格式
```json
{
  "type": "object",
  "properties": {
    "city": {
      "type": "string",
      "description": "城市名称，用于查询天气",
      "default": "北京"
    },
    "unit": {
      "type": "string",
      "description": "温度单位，celsius 或 fahrenheit",
      "default": "celsius"
    },
    "days": {
      "type": "number",
      "description": "预报天数，1-7天",
      "default": 3
    }
  },
  "required": ["city"]
}
```

### Function Calling Schema 生成
```json
{
  "type": "function",
  "function": {
    "name": "GetWeather",
    "description": "获取指定城市的天气信息",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名称，用于查询天气",
          "default": "北京"
        },
        "unit": {
          "type": "string",
          "description": "温度单位，celsius 或 fahrenheit",
          "default": "celsius"
        }
      },
      "required": ["city"]
    }
  }
}
```

## 🎯 使用示例

### 示例 1: 天气查询应用

**System Prompt**:
```
你是一个专业的天气助手。当用户询问{{city}}的天气时，你需要：
1. 确认城市名称
2. 询问需要查询的天数（默认{{days}}天）
3. 确认温度单位（{{unit}}）
```

**自动检测参数**:
- `city`
- `days`
- `unit`

**编辑参数**:
```javascript
// city
{
  type: "string",
  description: "要查询天气的城市名称",
  default: "北京"
}

// days
{
  type: "number",
  description: "预报天数，范围 1-7",
  default: 3
}

// unit
{
  type: "string",
  description: "温度单位，celsius 或 fahrenheit",
  default: "celsius"
}
```

**设置测试值**:
- city: "上海"
- days: 5
- unit: "celsius"

**调试效果**:
```
实际提示词:
"你是一个专业的天气助手。当用户询问上海的天气时，你需要：
1. 确认城市名称
2. 询问需要查询的天数（默认5天）
3. 确认温度单位（celsius）"
```

### 示例 2: 客服机器人

**System Prompt**:
```
你是{{company}}的客服代表{{agent_name}}。
你的职责是处理{{service_type}}相关的咨询。
工作时间：{{work_hours}}
```

**参数配置**:
```json
{
  "company": {
    "type": "string",
    "description": "公司名称",
    "default": "ABC科技"
  },
  "agent_name": {
    "type": "string",
    "description": "客服代表姓名",
    "default": "小智"
  },
  "service_type": {
    "type": "string",
    "description": "服务类型，如售前咨询、售后支持",
    "default": "售前咨询"
  },
  "work_hours": {
    "type": "string",
    "description": "工作时间",
    "default": "9:00-18:00"
  }
}
```

## 🔧 技术实现

### 前端核心方法

#### 1. 参数解析
```javascript
parseParametersFromPrompt() {
  const prompt = this.app.system_prompt || ''
  const regex = /\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}/g
  let match
  const detectedParams = new Set()
  
  while ((match = regex.exec(prompt)) !== null) {
    detectedParams.add(match[1])
  }
  
  // 为新参数添加默认配置
  detectedParams.forEach(paramName => {
    if (!this.parameters.properties[paramName]) {
      this.$set(this.parameters.properties, paramName, {
        type: 'string',
        description: `参数 ${paramName}`,
        default: ''
      })
    }
  })
}
```

#### 2. 参数编辑
```javascript
openEditParamModal(paramName) {
  const param = this.parameters.properties[paramName]
  this.editingParam = paramName
  this.editParamForm = {
    name: paramName,
    type: param.type || 'string',
    description: param.description || '',
    default: param.default || ''
  }
  this.showEditParamModal = true
}

saveParamEdit() {
  // 更新参数定义
  this.$set(this.parameters.properties, this.editParamForm.name, {
    type: this.editParamForm.type,
    description: this.editParamForm.description,
    default: this.editParamForm.default
  })
}
```

#### 3. 测试值替换
```javascript
async sendTestMessage() {
  // 使用测试值替换提示词中的参数
  let finalSystemPrompt = this.app.system_prompt || ''
  Object.keys(this.parameterTestValues).forEach(paramName => {
    const regex = new RegExp(`\\{\\{\\s*${paramName}\\s*\\}\\}`, 'g')
    finalSystemPrompt = finalSystemPrompt.replace(
      regex, 
      this.parameterTestValues[paramName] || ''
    )
  })
  
  // 发送请求...
}
```

## 🎨 UI/UX 改进

### 1. 参数卡片设计
- ✅ 白色背景，轻微阴影
- ✅ 清晰的视觉层次
- ✅ 分隔线区分不同区域
- ✅ 悬停效果

### 2. 编辑按钮
- ✅ 铅笔图标，直观易懂
- ✅ 悬停时高亮显示
- ✅ 紫色主题色

### 3. 测试值输入框
- ✅ 浅灰色背景
- ✅ 聚焦时高亮边框
- ✅ 占位符提示
- ✅ 全宽布局

### 4. 模态框设计
- ✅ 渐变色标题栏（紫色系）
- ✅ 白色主体内容
- ✅ 清晰的字段标签
- ✅ 友好的提示文本

## ⚠️ 注意事项

### 1. 参数命名规范
- 只支持字母、数字、下划线、连字符
- 建议使用小写字母和下划线
- 示例：`user_name`, `city`, `temperature`

### 2. 参数描述重要性
- 描述会用于 Function Calling
- 清晰的描述帮助 LLM 正确理解参数
- 建议包含：参数用途、取值范围、示例

### 3. 测试值 vs 默认值
- **测试值**: 仅用于调试，不会保存
- **默认值**: 保存在参数配置中，用于 Function Calling

### 4. 参数删除
- 删除参数不会影响提示词
- 如果提示词中仍使用该参数，会在下次编辑时重新检测

## 🚀 部署

无需额外部署步骤，前端代码已更新。刷新页面即可使用新功能。

## ✅ 测试清单

- [ ] 在提示词中添加 `{{parameter}}`
- [ ] 验证参数自动检测
- [ ] 点击编辑按钮
- [ ] 修改参数类型
- [ ] 修改参数描述
- [ ] 设置默认值
- [ ] 在测试值框中输入值
- [ ] 切换必填/可选
- [ ] 调试测试，验证参数替换
- [ ] 发布应用
- [ ] 获取 Function Schema，验证格式

## 📸 界面截图说明

根据您提供的截图，实现了以下功能：

1. ✅ **参数自动检测**: 从 system_prompt 解析 `{{parameter}}`
2. ✅ **参数类型选择**: 下拉框选择数据类型
3. ✅ **参数描述编辑**: 文本框编辑描述
4. ✅ **测试值输入**: 每个参数有独立的测试值输入框
5. ✅ **必填参数标记**: 复选框切换必填状态
6. ✅ **编辑按钮**: 铅笔图标，打开编辑模态框

## 🎉 总结

本次更新完善了参数管理功能，实现了：
- ✅ 自动参数检测
- ✅ 完整的参数编辑界面
- ✅ 测试值输入和替换
- ✅ 友好的用户体验

现在用户可以：
1. 在提示词中使用 `{{parameter}}` 定义参数
2. 系统自动检测并创建参数配置
3. 编辑参数的类型、描述、默认值
4. 设置测试值进行调试
5. 标记必填参数
6. 生成符合规范的 Function Calling Schema

---

**更新日期**: 2026-01-14  
**版本**: 2.1.0  
**重要性**: 🟢 中（功能增强，无破坏性变更）
