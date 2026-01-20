<template>
  <div class="layout-container">
    <div class="panel-header">
      <div class="title">任务调试</div>
      <div class="actions">
        <!-- Actions if needed -->
      </div>
    </div>

    <div class="panel-content">
      <div class="debug-section">
        <div class="section-header">
          <label class="section-label">输入预览 (Prompt + Parameters)</label>
          <button class="copy-btn" @click="copyInputPreview" title="复制完整提示词">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            复制
          </button>
        </div>
        <div class="preview-box">
          <pre>{{ inputPreview }}</pre>
        </div>
      </div>

      <div class="debug-section">
        <label class="section-label">额外输入 (可选)</label>
        <textarea 
          v-model="additionalInput" 
          class="input-textarea"
          placeholder="在此输入额外内容，将附加在提示词之后..."
        ></textarea>
      </div>

      <div class="action-bar">
        <button 
          class="run-btn secondary" 
          @click="runApiDebug" 
          :disabled="isRunning"
        >
          <span>API 调试</span>
        </button>
        <button 
          class="run-btn" 
          @click="runTask" 
          :disabled="isRunning || !selectedModel"
        >
          <span v-if="isRunning" class="spinner-sm"></span>
          <span>{{ isRunning ? '运行中...' : '运行调试' }}</span>
        </button>
      </div>

      <div class="debug-section result-section">
        <label class="section-label">输出结果</label>
        <div class="result-box" :class="{ 'has-content': result }">
          <div v-if="!result && !isRunning" class="empty-placeholder">
            点击运行查看结果
          </div>
          <div v-else class="markdown-body">
            <!-- Simple pre for now, could be markdown renderer -->
            <div class="streaming-content">{{ result }}<span v-if="isRunning" class="cursor">|</span></div>
          </div>
          <div v-if="usage" class="usage-info">
             Tokens: {{ usage.total_tokens }} (Input: {{ usage.prompt_tokens }}, Output: {{ usage.completion_tokens }})
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'
import nunjucks from 'nunjucks'

export default {
  name: 'TaskDebugPanel',
  props: {
    app: {
      type: Object,
      required: true
    },
    parameterValues: {
      type: Object,
      default: () => ({})
    },
    temperature: {
      type: Number,
      default: 0.7
    }
  },
  data() {
    return {
      additionalInput: '',
      result: '',
      isRunning: false,
      usage: null
    }
  },
  computed: {
    ...mapState('modelSquare', ['selectedModel']),
    inputPreview() {
      if (!this.app) return ''
      try {
        const context = this.parseParameters(true)
        nunjucks.configure({ autoescape: false })
        return nunjucks.renderString(this.app.system_prompt || '', context)
      } catch (e) {
        return `Rendering Error: ${e.message}\n\nRaw Template:\n${this.app.system_prompt}`
      }
    }
  },
  methods: {
    parseParameters(enhanceToString = false) {
      // Helper to parse parameter string values into JSON objects/arrays
      const context = {}
      
      const enhanceObjectWithToString = (obj) => {
          if (obj === null || typeof obj !== 'object') {
            return obj
          }
          if (Array.isArray(obj)) {
             obj.forEach((item, index) => {
               obj[index] = enhanceObjectWithToString(item)
             })
          } else {
             Object.keys(obj).forEach(key => {
               obj[key] = enhanceObjectWithToString(obj[key])
             })
          }
          // Override toString to return JSON
          Object.defineProperty(obj, 'toString', {
            value: function() {
              return JSON.stringify(this)
            },
            writable: true,
            configurable: true,
            enumerable: false 
          })
          return obj
      }

      Object.keys(this.parameterValues).forEach(key => {
        const val = this.parameterValues[key]
        try {
          if (val && typeof val === 'string' && (val.trim().startsWith('{') || val.trim().startsWith('[') || val.trim() === 'true' || val.trim() === 'false' || !isNaN(val))) {
             let parsed = JSON.parse(val)
             if (enhanceToString) {
               parsed = enhanceObjectWithToString(parsed)
             }
             context[key] = parsed
          } else {
             context[key] = val
          }
        } catch (e) {
          context[key] = val
        }
      })
      return context
    },

    async runApiDebug() {
      if (this.isRunning) return
      
      // API 调试使用的是应用保存的配置，不需要选择模型
      // 但需要提醒用户保存
      if (!this.app.id) return

      this.isRunning = true
      this.result = ''
      this.usage = null
      
      try {
        // 解析参数，确保传给后端的是对象而不是 JSON 字符串
        const parsedParams = this.parseParameters(false)
        
        const payload = {
          message: this.additionalInput || '', 
          parameters: parsedParams
        }
        
        const response = await axios.post(`/api/apps/${this.app.id}/invoke/`, payload)
        
        const data = response.data
        if (data.status === 'success') {
          this.result = data.content
          this.usage = data.usage
        } else {
          this.result = `API Error: ${data.error || 'Unknown error'}`
        }
      } catch (e) {
        const errorMsg = e.response?.data?.error || e.message
        // Format error nicely if it's a validation error
        if (typeof errorMsg === 'object') {
             this.result = `Validation Error: ${JSON.stringify(errorMsg, null, 2)}`
        } else {
             this.result = `Request Error: ${errorMsg}`
        }
      } finally {
        this.isRunning = false
      }
    },
    async runTask() {
      if (this.isRunning) return
      
      const modelName = this.selectedModel ? this.selectedModel.model_name : this.app.model_name
      const providerId = this.selectedModel ? this.selectedModel.provider_id : this.app.provider_id
      
      if (!modelName) {
        window.$message.warning('请选择一个模型进行调试')
        return
      }

      this.isRunning = true
      this.result = ''
      this.usage = null
      
      try {
        const userText = this.additionalInput.trim()
        const prompt = this.inputPreview
        const taskMessage = prompt ? (userText ? `${prompt}\n\n${userText}` : prompt) : userText

        const payload = {
          messages: [
            { role: 'user', content: taskMessage }
          ],
          provider_id: providerId,
          model: modelName,
          temperature: this.temperature,
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
                  this.result += data.choices[0].delta.content
                }
                if (data.usage) {
                  this.usage = data.usage
                }
              } catch (e) {
                // ignore
              }
            }
          }
        }
      } catch (e) {
        this.result = 'Error: ' + e.message
      } finally {
        this.isRunning = false
      }
    },
    copyInputPreview() {
      if (!this.inputPreview) return
      navigator.clipboard.writeText(this.inputPreview).then(() => {
        window.$message.success('已复制到剪贴板')
      }).catch(err => {
        window.$message.error('复制失败')
        console.error('Failed to copy text: ', err)
      })
    }
  }
}
</script>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8fafc;
}

.panel-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  min-height: 69px; /* Match left sidebar header height roughly */
}

.title {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.debug-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background-color: #f1f5f9;
  color: #4f46e5;
  border-color: #cbd5e1;
}

.preview-box {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  min-height: 200px;
  max-height: 300px;
  overflow-y: auto;
  resize: vertical;
}

.preview-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 0.875rem;
  color: #334155;
}

.input-textarea {
  width: 100%;
  height: 100px;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  font-size: 0.9rem;
}

.input-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  padding: 4px 0; /* Add some padding to ensure height */
  min-height: 48px; /* Ensure space for button */
  align-items: center;
  gap: 12px;
}

.run-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #6366f1;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.run-btn.secondary {
  background-color: #ffffff;
  color: #6366f1;
  border: 1px solid #6366f1;
}

.run-btn.secondary:hover {
  background-color: #e0e7ff;
}

.run-btn:hover {
  background-color: #4f46e5;
}

.run-btn:disabled {
  background-color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
}

.result-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.result-box {
  flex: 1;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  position: relative;
  overflow-y: auto;
}

.result-box .streaming-content {
    white-space: pre-wrap;
    word-break: break-word;
}

.empty-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-style: italic;
}

.streaming-content {
  color: #1e293b;
  line-height: 1.6;
}

.cursor {
  display: inline-block;
  width: 6px;
  height: 1em;
  background-color: #6366f1;
  margin-left: 2px;
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.usage-info {
  margin-top: 12px;
  font-size: 0.75rem;
  color: #64748b;
  text-align: right;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
