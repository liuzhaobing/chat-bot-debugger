# 深度思考功能架构设计文档

## 1. 功能概述

### 1.1 核心需求
1. **深度思考开关**：在模型调试页面和聊天页面支持启用/禁用深度思考模式
2. **思考内容展示**：从 `delta.reasoning_content` 获取思考过程，从 `delta.content` 获取最终回答
3. **Token 使用量统计**：展示 `total_tokens`、`prompt_tokens`、`completion_tokens`
4. **消息操作**：支持复制助手回答、重试请求功能
5. **数据持久化**：数据库存储 `reasoning_content` 字段

### 1.2 影响范围
- **前端**：ModelDebugView.vue、ChatArea.vue、MessageItem.vue
- **后端**：Message 模型、ChatCompletionView、序列化器
- **数据库**：Message 表新增字段

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Vue.js)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  ModelDebugView.vue  │         │    ChatArea.vue      │     │
│  │  ┌────────────────┐  │         │  ┌────────────────┐  │     │
│  │  │ 深度思考开关    │  │         │  │ 深度思考开关    │  │     │
│  │  │ enable_thinking │  │         │  │ enable_thinking │  │     │
│  │  └────────────────┘  │         │  └────────────────┘  │     │
│  │  ┌────────────────┐  │         │  ┌────────────────┐  │     │
│  │  │ Token 统计显示  │  │         │  │ Token 统计显示  │  │     │
│  │  │ usage object   │  │         │  │ usage object   │  │     │
│  │  └────────────────┘  │         │  └────────────────┘  │     │
│  │  ┌────────────────┐  │         │  ┌────────────────┐  │     │
│  │  │ 复制/重试按钮   │  │         │  │ 复制/重试按钮   │  │     │
│  │  └────────────────┘  │         │  └────────────────┘  │     │
│  └──────────────────────┘         └──────────────────────┘     │
│              │                              │                   │
│              └──────────────┬───────────────┘                   │
│                             ▼                                   │
│                  ┌──────────────────────┐                       │
│                  │   MessageItem.vue    │                       │
│                  │  ┌────────────────┐  │                       │
│                  │  │ 思考内容展示    │  │                       │
│                  │  │ reasoning_content│                        │
│                  │  └────────────────┘  │                       │
│                  │  ┌────────────────┐  │                       │
│                  │  │ 最终回答展示    │  │                       │
│                  │  │ content        │  │                       │
│                  │  └────────────────┘  │                       │
│                  │  ┌────────────────┐  │                       │
│                  │  │ 复制/重试按钮   │  │                       │
│                  │  └────────────────┘  │                       │
│                  └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 层 (Django REST)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  POST /api/chat/completions                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Request Payload:                                        │    │
│  │ {                                                       │    │
│  │   "messages": [...],                                    │    │
│  │   "model": "gpt-4",                                     │    │
│  │   "stream": true,                                       │    │
│  │   "extra_body": {                                       │    │
│  │     "enable_thinking": true/false                       │    │
│  │   }                                                     │    │
│  │ }                                                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                             │                                   │
│                             ▼                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ChatCompletionView.post()                              │    │
│  │ 1. 解析 extra_body.enable_thinking                      │    │
│  │ 2. 转发到上游 LLM API                                   │    │
│  │ 3. 流式解析响应                                         │    │
│  │    - delta.reasoning_content → 思考内容                 │    │
│  │    - delta.content → 最终回答                           │    │
│  │    - usage → token 统计                                 │    │
│  │ 4. 保存到数据库 (Message 表)                            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  PATCH /api/conversations/{id}/messages/{msg_id}/retry         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 重试逻辑:                                               │    │
│  │ 1. 清空 assistant 消息的 content 和 reasoning_content   │    │
│  │ 2. 重新调用 LLM API                                     │    │
│  │ 3. 更新数据库记录                                       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据库层 (SQLite/PostgreSQL)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Message 表结构:                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ id (PK)                                                 │    │
│  │ conversation_id (FK)                                    │    │
│  │ role (user/assistant/system)                            │    │
│  │ content (TextField) - 最终回答内容                       │    │
│  │ reasoning_content (TextField, nullable) - 思考过程       │    │
│  │ token_usage (JSONField, nullable) - Token 统计          │    │
│  │   {                                                     │    │
│  │     "prompt_tokens": 100,                               │    │
│  │     "completion_tokens": 200,                           │    │
│  │     "total_tokens": 300                                 │    │
│  │   }                                                     │    │
│  │ created_at (DateTime)                                   │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    上游 LLM API (OpenAI Compatible)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  流式响应格式:                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ data: {                                                 │    │
│  │   "choices": [{                                         │    │
│  │     "delta": {                                          │    │
│  │       "reasoning_content": "思考中...",                  │    │
│  │       "content": "最终回答..."                           │    │
│  │     }                                                   │    │
│  │   }],                                                   │    │
│  │   "usage": {                                            │    │
│  │     "prompt_tokens": 100,                               │    │
│  │     "completion_tokens": 200,                           │    │
│  │     "total_tokens": 300                                 │    │
│  │   }                                                     │    │
│  │ }                                                       │    │
│  │ data: [DONE]                                            │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据流设计

### 3.1 启用深度思考流程

```
用户操作
   │
   ├─ 1. 切换深度思考开关 (enableThinking = true)
   │
   ▼
前端构建请求
   │
   ├─ 2. 构建 payload
   │     {
   │       "messages": [...],
   │       "extra_body": { "enable_thinking": true }
   │     }
   │
   ▼
后端处理
   │
   ├─ 3. ChatCompletionView 接收请求
   │     - 提取 extra_body.enable_thinking
   │     - 转发到上游 API
   │
   ▼
上游 LLM 响应
   │
   ├─ 4. 流式返回数据
   │     - delta.reasoning_content (思考过程)
   │     - delta.content (最终回答)
   │     - usage (token 统计)
   │
   ▼
前端实时渲染
   │
   ├─ 5. 解析 SSE 流
   │     - 思考内容 → 显示在思考区域
   │     - 最终回答 → 显示在回答区域
   │     - token 统计 → 显示在底部
   │
   ▼
数据库持久化
   │
   └─ 6. 保存 Message 记录
        - content: 最终回答
        - reasoning_content: 思考过程
        - token_usage: token 统计
```

### 3.2 重试功能流程

```
用户点击重试
   │
   ├─ 1. 触发 retryMessage(messageId)
   │
   ▼
前端处理
   │
   ├─ 2. 清空当前 assistant 消息的 content 和 reasoning_content
   │     - 保留消息 ID
   │     - 显示加载状态
   │
   ▼
后端 API 调用
   │
   ├─ 3. PATCH /api/conversations/{id}/messages/{msg_id}/retry
   │     - 获取历史消息上下文
   │     - 重新调用 LLM API
   │     - 使用相同的 enable_thinking 配置
   │
   ▼
流式响应
   │
   ├─ 4. 实时更新消息内容
   │     - reasoning_content 逐步填充
   │     - content 逐步填充
   │
   ▼
数据库更新
   │
   └─ 5. UPDATE Message SET
        content = '新回答',
        reasoning_content = '新思考过程',
        token_usage = {...}
      WHERE id = messageId
```

---

## 4. 数据库设计

### 4.1 Migration 脚本

```python
# backend/chat/migrations/0012_add_thinking_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0002_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reasoning_content',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='深度思考内容 (reasoning_content)'
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='token_usage',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='Token 使用统计 {prompt_tokens, completion_tokens, total_tokens}'
            ),
        ),
    ]
```

### 4.2 更新后的 Message 模型

```python
class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(help_text="最终回答内容")
    reasoning_content = models.TextField(
        blank=True, 
        null=True, 
        help_text="深度思考内容 (reasoning_content)"
    )
    token_usage = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Token 使用统计 {prompt_tokens, completion_tokens, total_tokens}"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
```

---

## 5. API 接口设计

### 5.1 聊天完成接口 (现有接口扩展)

**Endpoint**: `POST /api/chat/completions`

**Request Body**:
```json
{
  "conversation_id": 123,
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "解释量子纠缠"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "extra_body": {
    "enable_thinking": true
  }
}
```

**Response (SSE Stream)**:
```
data: {"choices":[{"delta":{"reasoning_content":"首先，我需要理解量子纠缠的基本概念..."}}]}

data: {"choices":[{"delta":{"reasoning_content":"然后，我应该用通俗的语言解释..."}}]}

data: {"choices":[{"delta":{"content":"量子纠缠是指两个或多个粒子..."}}]}

data: {"choices":[{"delta":{"content":"之间存在一种特殊的关联..."}}]}

data: {"choices":[],"usage":{"prompt_tokens":50,"completion_tokens":150,"total_tokens":200}}

data: [DONE]
```

### 5.2 消息重试接口 (新增)

**Endpoint**: `PATCH /api/conversations/{conversation_id}/messages/{message_id}/retry`

**Request Body**:
```json
{
  "enable_thinking": true
}
```

**Response**: 同上 SSE Stream

---

## 6. 前端组件设计

### 6.1 MessageItem.vue 扩展

```vue
<template>
  <div class="message-item" :class="roleClass">
    <!-- 思考内容区域 (仅 assistant 且有 reasoning_content 时显示) -->
    <div v-if="role === 'assistant' && reasoningContent" class="thinking-section">
      <div class="thinking-header">
        <svg><!-- 思考图标 --></svg>
        <span>Deep thinking</span>
      </div>
      <div class="thinking-content">{{ reasoningContent }}</div>
    </div>

    <!-- 最终回答区域 -->
    <div class="message-content">
      <div class="content-text">{{ content }}</div>
    </div>

    <!-- 操作按钮 (仅 assistant 消息) -->
    <div v-if="role === 'assistant'" class="message-actions">
      <button @click="copyContent" title="复制">
        <svg><!-- 复制图标 --></svg>
      </button>
      <button @click="retryMessage" title="重试">
        <svg><!-- 重试图标 --></svg>
      </button>
    </div>

    <!-- Token 统计 (仅 assistant 消息且有 tokenUsage) -->
    <div v-if="role === 'assistant' && tokenUsage" class="token-usage">
      <span>Prompt: {{ tokenUsage.prompt_tokens }}</span>
      <span>Completion: {{ tokenUsage.completion_tokens }}</span>
      <span>Total: {{ tokenUsage.total_tokens }}</span>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    role: String,
    content: String,
    reasoningContent: String,
    tokenUsage: Object,
    messageId: Number
  },
  methods: {
    copyContent() {
      navigator.clipboard.writeText(this.content)
      this.$message.success('已复制到剪贴板')
    },
    retryMessage() {
      this.$emit('retry', this.messageId)
    }
  }
}
</script>
```

### 6.2 ModelDebugView.vue 关键修改

```javascript
data() {
  return {
    enableThinking: false,  // 深度思考开关
    lastTokenUsage: null,   // 最后一次 token 统计
    messages: []            // 消息列表，每条消息包含 reasoning_content
  }
},

methods: {
  async sendTestMessage() {
    // ... 构建 payload
    payload.extra_body = {
      enable_thinking: this.enableThinking
    }

    // 流式解析
    let assistantMsg = { 
      role: 'assistant', 
      content: '', 
      reasoning_content: '' 
    }
    
    for (const line of lines) {
      const data = JSON.parse(jsonStr)
      const delta = data.choices[0].delta
      
      // 解析思考内容
      if (delta.reasoning_content) {
        assistantMsg.reasoning_content += delta.reasoning_content
      }
      
      // 解析最终回答
      if (delta.content) {
        assistantMsg.content += delta.content
      }
      
      // 解析 token 统计
      if (data.usage) {
        this.lastTokenUsage = data.usage
      }
    }
  },

  retryMessage(messageId) {
    // 清空消息内容
    const msg = this.messages.find(m => m.id === messageId)
    msg.content = ''
    msg.reasoning_content = ''
    
    // 重新请求
    this.sendTestMessage()
  }
}
```

---

## 7. 样式设计规范

### 7.1 思考区域样式

```css
.thinking-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 3px solid #0ea5e9;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 8px;
}

.thinking-content {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #0c4a6e;
  white-space: pre-wrap;
}
```

### 7.2 Token 统计样式

```css
.token-usage {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 8px;
}

.token-usage span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.token-usage span::before {
  content: '•';
  color: #94a3b8;
}
```

### 7.3 操作按钮样式

```css
.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.message-actions button {
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.message-actions button:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #475569;
}
```

---

## 8. 状态管理 (Vuex)

### 8.1 State 扩展

```javascript
state: {
  messages: [],
  enableThinking: false,  // 全局深度思考开关
  currentTokenUsage: null
}
```

### 8.2 Actions 扩展

```javascript
actions: {
  async sendMessage({ commit, state }, { messages, enableThinking }) {
    const payload = {
      messages,
      extra_body: { enable_thinking: enableThinking }
    }
    
    // 流式请求处理
    const response = await fetch('/api/chat/completions', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    
    // 解析 SSE 流
    // ...
  },

  async retryMessage({ commit, state }, { messageId, enableThinking }) {
    const response = await fetch(
      `/api/conversations/${conversationId}/messages/${messageId}/retry`,
      {
        method: 'PATCH',
        body: JSON.stringify({ enable_thinking: enableThinking })
      }
    )
    
    // 流式更新消息
    // ...
  }
}
```

---

## 9. 错误处理

### 9.1 前端错误处理

```javascript
try {
  // 流式请求
} catch (error) {
  if (error.name === 'AbortError') {
    // 用户取消请求
    this.$message.info('请求已取消')
  } else if (error.response?.status === 429) {
    // 速率限制
    this.$message.error('请求过于频繁，请稍后再试')
  } else {
    // 其他错误
    this.$message.error(`请求失败: ${error.message}`)
  }
}
```

### 9.2 后端错误处理

```python
try:
    response = requests.post(
        f"{provider.base_url}/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
        timeout=60
    )
    response.raise_for_status()
except requests.Timeout:
    return Response({"error": "上游 API 超时"}, status=504)
except requests.HTTPError as e:
    return Response({"error": f"上游 API 错误: {e}"}, status=502)
except Exception as e:
    return Response({"error": f"服务器内部错误: {e}"}, status=500)
```

---

## 10. 性能优化

### 10.1 前端优化
- **虚拟滚动**: 消息列表超过 100 条时使用虚拟滚动
- **防抖处理**: 重试按钮添加 1 秒防抖
- **流式渲染**: 使用 `requestAnimationFrame` 优化 DOM 更新

### 10.2 后端优化
- **数据库索引**: 为 `conversation_id` 和 `created_at` 添加索引
- **连接池**: 使用连接池管理上游 API 请求
- **缓存**: 对 token 统计进行短期缓存

---

## 11. 测试计划

### 11.1 单元测试
- Message 模型的 CRUD 操作
- 序列化器的字段验证
- 流式解析逻辑

### 11.2 集成测试
- 完整的聊天流程（启用/禁用深度思考）
- 重试功能的端到端测试
- Token 统计的准确性验证

### 11.3 UI 测试
- 思考内容的实时渲染
- 复制功能的剪贴板验证
- 按钮样式的一致性检查

---

## 12. 部署清单

### 12.1 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 12.2 前端构建
```bash
cd frontend
npm run build
```

### 12.3 环境变量
```env
# 上游 API 超时设置
LLM_API_TIMEOUT=60

# 流式响应缓冲区大小
STREAM_BUFFER_SIZE=1024
```

---

## 13. 监控与日志

### 13.1 关键指标
- 深度思考模式的使用率
- Token 消耗统计
- 重试请求的频率
- 流式响应的延迟

### 13.2 日志记录
```python
import logging

logger = logging.getLogger(__name__)

# 记录深度思考请求
logger.info(f"Deep thinking enabled: {enable_thinking}, model: {model_name}")

# 记录 token 使用
logger.info(f"Token usage: {usage}")

# 记录重试操作
logger.info(f"Message retry: conversation_id={conv_id}, message_id={msg_id}")
```

---

## 14. 未来扩展

### 14.1 短期计划
- 支持思考内容的折叠/展开
- 添加思考时长统计
- 支持导出对话（包含思考过程）

### 14.2 长期计划
- 思考过程的可视化（思维导图）
- 多轮思考的链式展示
- 思考质量评分系统

---

## 15. 参考资料

- OpenAI API 文档: https://platform.openai.com/docs/api-reference
- Server-Sent Events (SSE) 规范: https://html.spec.whatwg.org/multipage/server-sent-events.html
- Django Streaming Response: https://docs.djangoproject.com/en/stable/ref/request-response/#streaminghttpresponse
- Vue.js 组件通信: https://vuejs.org/guide/components/events.html
