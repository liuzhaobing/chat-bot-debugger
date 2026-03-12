<template>
  <div class="transcript-panel">
    <!-- 实时字幕区域 -->
    <div class="transcript-section">
      <div class="section-header">
        <h3>实时字幕</h3>
        <div class="header-actions">
          <button 
            class="btn-icon"
            @click="clearTranscript"
            title="清空字幕"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <div class="transcript-content" ref="transcriptContent">
        <div v-if="transcriptMessages.length === 0" class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
          <p>等待语音输入...</p>
        </div>
        
        <div
          v-for="message in transcriptMessages"
          :key="message.id"
          class="transcript-message"
          :class="{
            'is-user': message.type === 'user',
            'is-agent': message.type === 'agent',
            'is-partial': message.isPartial,
            'is-final': message.isFinal
          }"
        >
          <div class="message-avatar">
            <svg v-if="message.type === 'user'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
          <div class="message-info">
            <span class="message-sender">{{ message.type === 'user' ? '用户' : 'AI助手' }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-status">
            <div v-if="message.isPartial" class="status-indicator partial">
              <div class="typing-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            </div>
            <div v-else-if="message.isFinal" class="status-indicator final">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20,6 9,17 4,12"></polyline>
              </svg>
            </div>
          </div>
          <div class="message-content">
            <p>{{ message.content }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- AI日志区域 -->
    <div class="logs-section">
      <div class="section-header">
        <h3>AI日志</h3>
        <div class="header-actions">
          <button 
            class="btn-icon"
            @click="clearLogs"
            title="清空日志"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
            </svg>
          </button>
          <div class="log-filter">
            <select v-model="logFilter">
              <option value="all">全部</option>
              <option value="system">系统</option>
              <option value="audio">音频</option>
              <option value="ai">AI处理</option>
              <option value="error">错误</option>
            </select>
          </div>
        </div>
      </div>
      
      <div class="logs-content" ref="logsContent">
        <div v-if="filteredLogs.length === 0" class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14,2 14,8 20,8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10,9 9,9 8,9"></polyline>
          </svg>
          <p>暂无日志信息</p>
        </div>
        
        <div
          v-for="log in filteredLogs"
          :key="log.id"
          class="log-entry"
          :class="'log-' + log.level"
        >
          <div class="log-header">
            <div class="log-level-indicator" :class="'level-' + log.level"></div>
            <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
            <span class="log-category">{{ getCategoryLabel(log.category) }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="hasDetails(log.details)" class="log-content">
            <pre>{{ JSON.stringify(log.details, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TranscriptPanel',
  props: {
    transcriptMessages: {
      type: Array,
      default: () => []
    },
    logs: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      logFilter: 'all'
    }
  },
  computed: {
    filteredLogs() {
      if (this.logFilter === 'all') {
        return this.logs
      }
      return this.logs.filter(log => log.category === this.logFilter)
    }
  },
  watch: {
    transcriptMessages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom('transcript')
        })
      },
      deep: true
    },
    filteredLogs: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom('logs')
        })
      },
      deep: true
    }
  },
  methods: {
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      })
    },
    
    getCategoryLabel(category) {
      const labels = {
        'system': '系统',
        'audio': '音频',
        'ai': 'AI处理',
        'error': '错误',
        'websocket': 'WebSocket',
        'speech': '语音识别',
        'tts': '语音合成'
      }
      return labels[category] || category
    },

    hasDetails(details) {
      if (!details) return false
      if (Array.isArray(details)) return details.length > 0
      if (typeof details === 'object') return Object.keys(details).length > 0
      return false
    },
    
    clearTranscript() {
      this.$emit('clear-transcript')
    },
    
    clearLogs() {
      this.$emit('clear-logs')
    },
    
    scrollToBottom(type) {
      const element = type === 'transcript' ? this.$refs.transcriptContent : this.$refs.logsContent
      if (element) {
        element.scrollTop = element.scrollHeight
      }
    }
  }
}
</script>

<style scoped>
.transcript-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.transcript-section,
.logs-section {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.transcript-section {
  flex: 1.5;
  min-height: 300px;
}

.logs-section {
  flex: 1;
  min-height: 200px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon.active {
  background: var(--accent-blue);
  color: white;
}

.btn-icon svg {
  width: 16px;
  height: 16px;
}

.log-filter select {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
}

.log-filter select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

/* 内容区域 */
.transcript-content,
.logs-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
  min-height: 0;
}

.transcript-content::-webkit-scrollbar,
.logs-content::-webkit-scrollbar {
  width: 6px;
}

.transcript-content::-webkit-scrollbar-track,
.logs-content::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 3px;
}

.transcript-content::-webkit-scrollbar-thumb,
.logs-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.transcript-content::-webkit-scrollbar-thumb:hover,
.logs-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* 字幕消息 */
.transcript-message {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.transcript-message.is-user {
  background: rgba(79, 70, 229, 0.05);
  border-color: rgba(79, 70, 229, 0.2);
}

.transcript-message.is-agent {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.transcript-message.is-partial {
  opacity: 0.8;
  border-style: dashed;
}

.transcript-message.is-final {
  border-color: rgba(16, 185, 129, 0.4);
}

.message-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.transcript-message.is-user .message-avatar {
  background: rgba(79, 70, 229, 0.1);
  color: var(--accent-blue);
}

.transcript-message.is-agent .message-avatar {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.message-avatar svg {
  width: 14px;
  height: 14px;
}

.message-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.message-sender {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  font-size: 10px;
  color: var(--text-tertiary);
}

.message-status {
  flex-shrink: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.status-indicator.partial .typing-dots {
  display: flex;
  gap: 2px;
}

.typing-dots .dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dots .dot:nth-child(2) { animation-delay: -0.16s; }

.status-indicator.final {
  color: #059669;
}

.status-indicator.final svg {
  width: 14px;
  height: 14px;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-content p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
}

/* 日志条目 */
.log-entry {
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid var(--border-color);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.log-entry:hover {
  background: var(--bg-hover);
}

.log-entry.log-info {
  border-left-color: #3b82f6;
}

.log-entry.log-success {
  border-left-color: #10b981;
}

.log-entry.log-warning {
  border-left-color: #f59e0b;
}

.log-entry.log-error {
  border-left-color: #ef4444;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.log-level-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.log-level-indicator.level-info {
  background: #3b82f6;
}

.log-level-indicator.level-success {
  background: #10b981;
}

.log-level-indicator.level-warning {
  background: #f59e0b;
}

.log-level-indicator.level-error {
  background: #ef4444;
}

.log-timestamp {
  font-size: 10px;
  color: var(--text-tertiary);
  font-family: monospace;
}

.log-category {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.log-message {
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
}

.log-content {
  margin-top: 8px;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

.log-content pre {
  margin: 0;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}

/* 动画 */
@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .transcript-panel {
    gap: 12px;
  }
  
  .section-header {
    padding: 12px 16px;
  }
  
  .section-header h3 {
    font-size: 14px;
  }
  
  .transcript-content,
  .logs-content {
    padding: 12px;
  }
  
  .transcript-message {
    padding: 10px;
    margin-bottom: 12px;
  }

  .message-content p {
    font-size: 13px;
  }
  
  .log-entry {
    padding: 8px;
    margin-bottom: 10px;
  }

  .log-message {
    font-size: 12px;
  }
}
</style>