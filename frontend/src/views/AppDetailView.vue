<template>
  <div class="debug-container" v-if="app">
    <!-- Left Pane: Configuration -->
    <div class="config-pane">
      <div class="pane-header">
        <div class="header-left">
          <button class="back-btn" @click="$router.push('/apps')">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <h1>{{ app.name }}</h1>
        </div>
        <div class="header-actions">
          <span class="save-status">{{ saveStatus }}</span>
          <button class="publish-btn" @click="saveAppData">发布</button>
        </div>
      </div>

      <div class="pane-body">
        <section class="config-section">
          <div class="section-title">应用基本信息</div>
          <div class="input-group app-name">
            <label>应用名称</label>
            <input v-model="app.name" placeholder="请输入应用名称" />
          </div>
          <div class="input-group">
            <label>应用描述</label>
            <textarea v-model="app.description" placeholder="请输入应用描述"></textarea>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">
            提示词
            <div class="prompt-tools">
              <button class="optimize-btn" @click="optimizePrompt" title="优化提示词">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>
                <span>自动优化</span>
              </button>
            </div>
          </div>
          <p class="section-hint" v-pre>
            使用 {{ variable }} 定义变量，系统将自动识别。
          </p>
          <div class="prompt-editor-container">
            <textarea 
              v-model="app.system_prompt" 
              class="prompt-textarea"
              placeholder="你是一个专业的助手..."
              @input="handlePromptInput"
            ></textarea>
          </div>
        </section>

        <section class="config-section" v-if="detectedVariables.length">
          <div class="section-title">变量设置</div>
          <div class="variables-list">
            <div v-for="v in detectedVariables" :key="v" class="variable-item">
              <label>{{ v }}</label>
              <textarea
                  v-model="variableValues[v]"
                  class="variable-value-textarea"
                  :placeholder="v + ' 的取值'"
                  @input="handlePromptInput"
              ></textarea>
            </div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">模型配置</div>
          <div class="model-select-wrapper">
             <model-selector ref="modelSelector" />
          </div>
          <div class="params-list">
            <div class="param-item">
              <div class="param-header">
                <label>Temperature</label>
                <span class="param-val">{{ app.configuration.temperature || 0.7 }}</span>
              </div>
              <input type="range" v-model.number="app.configuration.temperature" min="0" max="2" step="0.1" />
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Right Pane: Debug Chat -->
    <div class="debug-pane">
      <div class="debug-header">
        <div class="debug-title">文本对话</div>
        <div class="debug-actions">
           <button class="clear-btn" @click="clearMessages" title="清空对话">
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
           </button>
        </div>
      </div>

      <div class="debug-messages" ref="msgScroll">
        <div v-if="messages.length === 0" class="empty-debug">
           <div class="app-avatar-large" :style="{ backgroundColor: getIconColor(app.name) }">
             {{ app.name[0].toUpperCase() }}
           </div>
           <h3>{{ app.name }}</h3>
           <p>输入问题开始调试您的应用</p>
        </div>
        <message-item 
          v-for="(msg, index) in messages" 
          :key="index"
          :role="msg.role"
          :content="msg.content"
        />
        <div v-if="isStreaming" class="streaming-indicator">
           <span class="dot"></span>
           思维中...
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
import axios from 'axios'
import ModelSelector from '../components/ModelSelector.vue'
import MessageItem from '../components/MessageItem.vue'
import { mapState } from 'vuex'

export default {
  name: 'AppDebugView',
  components: { ModelSelector, MessageItem },
  data() {
    return {
      app: null,
      loading: true,
      userInput: '',
      messages: [],
      isStreaming: false,
      detectedVariables: [],
      variableValues: {},
      saveStatus: '已保存',
      saveTimer: null
    }
  },
  computed: {
    ...mapState(['selectedModel'])
  },
  methods: {
    async fetchApp() {
      this.loading = true
      try {
        const id = this.$route.params.id
        const res = await axios.get(`/api/apps/${id}/`)
        this.app = res.data
        if (!this.app.configuration) this.app.configuration = { temperature: 0.7 }
        this.parseVariables()
      } catch (e) {
        window.$message.error('加载应用失败')
      } finally {
        this.loading = false
      }
    },
    handlePromptInput() {
      this.parseVariables()
      this.triggerAutoSave()
    },
    parseVariables() {
      const prompt = this.app.system_prompt || ''
      const regex = /\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}/g
      let match
      const vars = new Set()
      while ((match = regex.exec(prompt)) !== null) {
        vars.add(match[1])
      }
      this.detectedVariables = Array.from(vars)
      // Initialize values if not present
      this.detectedVariables.forEach(v => {
        if (this.variableValues[v] === undefined) {
          this.variableValues[v] = ''
        }
      })
    },
    triggerAutoSave() {
      this.saveStatus = '保存中...'
      if (this.saveTimer) clearTimeout(this.saveTimer)
      this.saveTimer = setTimeout(() => {
        this.saveAppData()
      }, 2000)
    },
    async saveAppData() {
      if (!this.app) return
      try {
        await axios.patch(`/api/apps/${this.app.id}/`, {
          name: this.app.name,
          description: this.app.description,
          system_prompt: this.app.system_prompt,
          configuration: this.app.configuration,
          variables: this.detectedVariables.map(v => ({ name: v, default: this.variableValues[v] }))
        })
        this.saveStatus = '已保存'
      } catch (e) {
        this.saveStatus = '保存失败'
      }
    },
    async sendTestMessage() {
      if (this.isStreaming || !this.userInput.trim()) return
      if (!this.selectedModel) {
        window.$message.warning('请选择一个模型进行调试')
        return
      }

      const userText = this.userInput.trim()
      this.userInput = ''
      this.messages.push({ role: 'user', content: userText })
      this.scrollToBottom()

      this.isStreaming = true
      let assistantMsg = { role: 'assistant', content: '' }
      this.messages.push(assistantMsg)

      try {
        // Substitute variables in system prompt
        let finalSystemPrompt = this.app.system_prompt || ''
        Object.keys(this.variableValues).forEach(v => {
          const regex = new RegExp(`\\{\\{\\s*${v}\\s*\\}\\}`, 'g')
          finalSystemPrompt = finalSystemPrompt.replace(regex, this.variableValues[v])
        })

        const payload = {
          messages: [
            { role: 'system', content: finalSystemPrompt },
            ...this.messages.slice(0, -1)
          ],
          model: this.selectedModel.model_name,
          temperature: this.app.configuration.temperature,
          stream: true
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
                if (data.choices && data.choices[0].delta.content) {
                  assistantMsg.content += data.choices[0].delta.content
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
    },
    optimizePrompt() {
      window.$message.info('提示词优化功能正在开发中...')
    },
    getIconColor(name) {
      if (!name) return '#4f46e5'
      const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899', '#6366f1']
      let hash = 0
      for (let i = 0; i < name.length; i++) {
          hash = name.charCodeAt(i) + ((hash << 5) - hash)
      }
      return colors[Math.abs(hash) % colors.length]
    }
  },
  mounted() {
    this.fetchApp()
  }
}
</script>

<style scoped>
.debug-container {
  display: flex;
  height: 100%;
  background-color: #f8fafc;
  overflow: hidden;
}

/* Config Pane */
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

.back-btn:hover { background-color: #f1f5f9; }

.pane-header h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.save-status {
  font-size: 0.75rem;
  color: #94a3b8;
}

.publish-btn {
  background-color: #4f46e5;
  color: #ffffff;
  border: none;
  padding: 6px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: -4px 0 0 0;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
}

.input-group input, .input-group textarea {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  color: #475569;
  background-color: #fcfcfd;
}

.prompt-editor-container {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background-color: #fcfcfd;
}

.prompt-tools {
  display: flex;
  align-items: center;
}

.optimize-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f5f3ff;
  color: #8b5cf6;
  border: 1px solid #ddd6fe;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.optimize-btn:hover {
  background-color: #ede9fe;
  border-color: #c4b5fd;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.optimize-btn svg {
  color: #7c3aed;
}

.prompt-textarea {
  width: 100%;
  height: 240px;
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

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.variable-item label {
  width: 100px;
  font-size: 0.85rem;
  color: #475569;
  font-family: monospace;
}

.variable-value-textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #475569;
  background-color: #fcfcfd;
}

.params-list {
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-header {
  display: flex;
  justify-content: space-between;
}

.param-header label {
  font-size: 0.85rem;
  font-weight: 600;
}

.param-val {
  font-size: 0.85rem;
  color: #4f46e5;
  font-weight: 700;
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

.app-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 16px;
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
