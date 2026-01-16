<template>
  <div class="debug-container" v-if="model">
    <!-- Left Pane: Configuration -->
    <div class="config-pane">
      <div class="pane-header">
        <div class="header-left">
          <button class="back-btn" @click="$router.push('/')">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <h1>{{ model.display_name || model.name }}</h1>
          <span class="model-type-badge">{{ providerName }}</span>
        </div>
      </div>

      <div class="pane-body">
        <section class="config-section">
          <div class="section-title">模型信息</div>
          <div class="info-group">
            <label>模型名称</label>
            <div class="info-value">{{ model.name }}</div>
          </div>
          <div class="info-group">
            <label>显示名称</label>
            <div class="info-value">{{ model.display_name || model.name }}</div>
          </div>
          <div class="info-group">
            <label>提供商</label>
            <div class="info-value">{{ providerName }}</div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">系统提示词</div>
          <p class="section-hint">
            设置系统提示词来定义模型的行为和角色
          </p>
          <div class="prompt-editor-container">
            <textarea 
              v-model="systemPrompt" 
              class="prompt-textarea"
              placeholder="你是一个专业的助手..."
            ></textarea>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">模型参数</div>
          <div class="params-list">
            <div class="param-item">
              <div class="param-header">
                <label>Temperature</label>
                <span class="param-val">{{ temperature }}</span>
              </div>
              <input type="range" v-model.number="temperature" min="0" max="2" step="0.1" />
              <p class="param-hint">控制输出的随机性，值越高越随机</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <label>Top P</label>
                <span class="param-val">{{ topP }}</span>
              </div>
              <input type="range" v-model.number="topP" min="0" max="1" step="0.05" />
              <p class="param-hint">核采样参数，控制输出的多样性</p>
            </div>

            <div class="param-item">
              <div class="param-header">
                <label>Max Tokens</label>
                <span class="param-val">{{ maxTokens }}</span>
              </div>
              <input type="range" v-model.number="maxTokens" min="100" max="4000" step="100" />
              <p class="param-hint">最大输出token数量</p>
            </div>

            <div class="param-item checkbox-item">
              <label class="checkbox-label">
                <input type="checkbox" v-model="enableThinking" />
                <span>启用思考模式 (Enable Thinking)</span>
              </label>
              <p class="param-hint">启用后模型会展示推理过程（如支持）</p>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Right Pane: Debug Chat -->
    <div class="debug-pane">
      <div class="debug-header">
        <div class="debug-title">模型调试</div>
        <div class="debug-actions">
           <button class="clear-btn" @click="clearMessages" title="清空对话">
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
           </button>
        </div>
      </div>

      <div class="debug-messages" ref="msgScroll">
        <div v-if="messages.length === 0" class="empty-debug">
           <div class="model-avatar-large">
             <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
               <path d="M12 2L4 7v10l8 5 8-5V7l-8-5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
               <path d="M12 22V12m0 0l-8-5m8 5l8-5" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
             </svg>
           </div>
           <h3>{{ model.display_name || model.name }}</h3>
           <p>输入问题开始调试模型</p>
        </div>
        <message-item 
          v-for="(msg, index) in messages" 
          :key="index"
          :role="msg.role"
          :content="msg.content"
          :reasoning-content="msg.reasoning_content"
          :token-usage="msg.usage"
        />
        <div v-if="isStreaming" class="streaming-indicator">
           <span class="dot"></span>
           {{ streamingPhase === 'reasoning' ? '深度思考中...' : '生成回答中...' }}
        </div>
      </div>

      <div class="debug-input-area">
        <div class="input-card">
          <textarea 
            v-model="userInput" 
            placeholder="输入问题进行测试..." 
            @keydown.enter.prevent="sendTestMessage"
          ></textarea>
          <button class="send-btn" @click="sendTestMessage" :disabled="isStreaming || !userInput.trim()">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MessageItem from '../../../components/chat-completion/MessageItem.vue'

export default {
  name: 'ModelDebugView',
  components: { MessageItem },
  data() {
    return {
      model: null,
      providerName: '',
      providerId: null,
      userInput: '',
      messages: [],
      isStreaming: false,
      streamingPhase: '', // 'reasoning' or 'content'
      
      // 配置参数
      systemPrompt: 'You are a helpful assistant.',
      temperature: 0.7,
      topP: 0.9,
      maxTokens: 1024,
      enableThinking: false
    }
  },
  methods: {
    async loadModel() {
      const modelName = this.$route.query.model
      const providerId = this.$route.query.provider
      
      if (!modelName || !providerId) {
        window.$message.error('缺少模型参数')
        this.$router.push('/')
        return
      }
      
      try {
        // 直接从后端获取 provider 信息，不依赖 Vuex
        const response = await fetch('/api/providers/')
        if (!response.ok) {
          throw new Error('Failed to fetch providers')
        }
        const providers = await response.json()
        
        const provider = providers.find(p => p.id === providerId)
        if (!provider) {
          window.$message.error('未找到提供商')
          this.$router.push('/')
          return
        }
        
        this.providerName = provider.name
        const model = provider.models.find(m => m.name === modelName)
        if (!model) {
          window.$message.error('未找到模型')
          this.$router.push('/')
          return
        }
        
        this.model = { ...model }
        this.providerId = providerId
      } catch (e) {
        window.$message.error('加载模型信息失败')
        this.$router.push('/')
      }
    },
    
    async sendTestMessage() {
      if (this.isStreaming || !this.userInput.trim()) return
      
      const userText = this.userInput.trim()
      this.userInput = ''
      this.messages.push({ role: 'user', content: userText })
      this.scrollToBottom()

      this.isStreaming = true
      let assistantMsg = { role: 'assistant', content: '', reasoning_content: '', usage: null }
      this.messages.push(assistantMsg)

      try {
        const payload = {
          provider_id: this.providerId,
          messages: [
            { role: 'system', content: this.systemPrompt },
            ...this.messages.slice(0, -1)
          ],
          model: this.model.name,
          temperature: this.temperature,
          top_p: this.topP,
          max_tokens: this.maxTokens,
          stream: true
        }

        payload.extra_body = {
          "enable_thinking": this.enableThinking
        }

        const response = await fetch('/api/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`Server Error (${response.status}): ${errorText}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()
          for (const line of lines) {
            const trimmed = line.trim()
            if (trimmed.startsWith('data: ')) {
              const jsonStr = trimmed.slice(6)
              if (jsonStr === '[DONE]') continue
              try {
                const data = JSON.parse(jsonStr)
                if (data.choices && data.choices[0].delta.reasoning_content) {
                  assistantMsg.reasoning_content += data.choices[0].delta.reasoning_content
                }
                if (data.choices && data.choices[0].delta.content) {
                  assistantMsg.content += data.choices[0].delta.content
                }
                // 收集 usage 信息（通常在最后一个 chunk）
                if (data.usage) {
                  assistantMsg.usage = data.usage
                }
              } catch (e) {
                // 忽略流式解析错误
              }
            }
          }
          this.scrollToBottom()
        }
      } catch (e) {
        assistantMsg.content = '出故障了: ' + e.message
      } finally {
        this.isStreaming = false
      }
    },
    
    clearMessages() {
      this.messages = []
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.msgScroll
        if (el) el.scrollTop = el.scrollHeight
      })
    }
  },
  mounted() {
    this.loadModel()
  }
}
</script>

<style scoped>
/* 复用应用调试的样式 */
.debug-container {
  display: flex;
  height: 100%;
  background-color: #f8fafc;
  overflow: hidden;
}

.config-pane {
  width: 50%;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

.pane-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.back-btn:hover { 
  background-color: #f1f5f9; 
}

.pane-header h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.model-type-badge {
  background-color: #f0f9ff;
  color: #0ea5e9;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.pane-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.section-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: -4px 0 0 0;
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.info-group label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
}

.info-value {
  font-size: 0.9rem;
  color: #1e293b;
  font-weight: 600;
}

.prompt-editor-container {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background-color: #fcfcfd;
}

.prompt-textarea {
  width: 100%;
  height: 200px;
  border: none;
  padding: 16px;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.6;
  background: transparent;
  outline: none;
  resize: vertical;
  color: #334155;
}

.params-list {
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-header label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}

.param-val {
  font-size: 0.85rem;
  color: #4f46e5;
  font-weight: 700;
}

.param-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: 0;
}

input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
}

input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
}

.checkbox-item {
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #475569;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #6366f1;
}

/* Debug Pane */
.debug-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
}

.debug-header {
  padding: 16px 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.debug-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.clear-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-btn:hover {
  background-color: #f1f5f9;
  color: #ef4444;
}

.debug-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-debug {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  padding-bottom: 100px;
}

.model-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  margin-bottom: 16px;
  background-color: #f5f3ff;
}

.empty-debug h3 {
  margin: 0 0 8px 0;
  color: #1e293b;
}

.debug-input-area {
  padding: 24px;
  background: linear-gradient(180deg, transparent 0%, #f8fafc 40%);
}

.input-card {
  max-width: 800px;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 12px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.input-card textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  resize: none;
  padding: 4px;
  line-height: 1.5;
  min-height: 24px;
}

.send-btn {
  background-color: #4f46e5;
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background-color: #4338ca;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.streaming-indicator {
  padding: 12px;
  font-size: 0.85rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 8px;
}

.streaming-indicator .dot {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0% { opacity: 0.2; }
  50% { opacity: 1; }
  100% { opacity: 0.2; }
}
</style>
