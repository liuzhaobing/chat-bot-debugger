<template>
  <div class="transcript-panel">
    <div class="panel-header">
      <h3>通话字幕</h3>
    </div>

    <!-- 通话字幕区域 -->
    <div class="transcript-section" ref="transcriptContent" :style="showAILogs ? { height: transcriptHeight + 'px' } : {}">
      <div v-if="transcripts.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <p>暂无通话记录</p>
        <span>开始通话后，对话内容将显示在这里</span>
      </div>

      <div v-else class="transcript-list">
        <div 
          v-for="item in sortedTranscripts" 
          :key="`${item.segment_id}_${item.participant_id}`"
          class="transcript-item"
          :class="getParticipantClass(item.participant_id)"
        >
          <div class="message-wrapper">
            <div class="speaker-avatar">
              <svg v-if="item.participant_id === 'system'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
              </svg>
              <svg v-else-if="item.participant_id === 'ai_user'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4"></path>
                <path d="M21 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
                <path d="M3 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
                <path d="M12 21c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
                <path d="M12 3c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
              </svg>
              <svg v-else-if="isSipPhone(item.participant_id)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="speaker-name">{{ getParticipantName(item.participant_id) }}</span>
                <span class="message-time">{{ formatTime(item.timestamp) }}</span>
              </div>
              <div class="message-text" :class="{ interim: !item.is_final }">
                {{ item.text }}
                <span v-if="!item.is_final" class="typing-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 可拖拽的分隔条 -->
    <div 
      class="resizer" 
      @mousedown="startResize"
      v-if="showAILogs && !logCollapsed"
    >
      <div class="resizer-line"></div>
      <div class="resizer-handle">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="9" cy="12" r="1"/>
          <circle cx="9" cy="5" r="1"/>
          <circle cx="9" cy="19" r="1"/>
          <circle cx="15" cy="12" r="1"/>
          <circle cx="15" cy="5" r="1"/>
          <circle cx="15" cy="19" r="1"/>
        </svg>
      </div>
    </div>

    <!-- AI日志区域 - 只在场景测试时显示 -->
    <div 
      v-if="showAILogs" 
      class="ai-log-section" 
      :class="{ collapsed: logCollapsed }" 
      :style="logCollapsed ? {} : { height: logHeight + 'px' }"
    >
      <div class="log-header" @click="toggleLogCollapse">
        <div class="log-title">
          <div class="ai-indicator">
            <div class="ai-pulse"></div>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span>AI 执行日志</span>
          <div class="log-stats">{{ consoleLogs.length }} 条</div>
        </div>
        <button class="collapse-btn" :class="{ collapsed: logCollapsed }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      </div>

      <div v-if="!logCollapsed" class="log-content" ref="logContent">
        <div v-if="consoleLogs.length === 0" class="log-empty">
          <div class="empty-animation">
            <div class="pulse-ring"></div>
            <div class="pulse-ring pulse-ring-2"></div>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span>等待 AI 执行...</span>
        </div>

        <div v-else class="log-list">
          <div 
            v-for="(log, index) in sortedConsoleLogs" 
            :key="index"
            class="log-item"
            :class="getLogTypeClass(log.type)"
          >
            <div class="log-timeline">
              <div class="timeline-dot"></div>
              <div class="timeline-line" v-if="index < sortedConsoleLogs.length - 1"></div>
            </div>
            <div class="log-card">
              <div class="log-header-info">
                <div class="log-icon">
                  <svg v-if="log.type === 'status'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 6v6l4 2"/>
                  </svg>
                  <svg v-else-if="log.type === 'ai_user_query'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  <svg v-else-if="log.type === 'tts_audio'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  </svg>
                  <svg v-else-if="log.type === 'dial_response'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                  <svg v-else-if="log.type === 'judger_result'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 12l2 2 4-4"/>
                    <circle cx="12" cy="12" r="10"/>
                  </svg>
                  <svg v-else-if="log.type === 'error'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 16v-4"/>
                    <path d="M12 8h.01"/>
                  </svg>
                </div>
                <div class="log-meta">
                  <span class="log-type">{{ getLogTypeName(log.type) }}</span>
                  <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                </div>
              </div>
              <div class="log-message">{{ formatLogMessage(log) }}</div>
              <div v-if="log.data && Object.keys(log.data).length > 0 && shouldShowDetails(log)" class="log-details">
                <div class="details-content">{{ JSON.stringify(log.data, null, 2) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 折叠后的左下角按钮 -->
    <div v-if="showAILogs && logCollapsed" class="collapsed-log-button" @click="toggleLogCollapse">
      <div class="collapsed-button-content">
        <div class="ai-indicator small">
          <div class="ai-pulse"></div>
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          </svg>
        </div>
        <span>AI日志</span>
        <div class="log-count">{{ consoleLogs.length }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TranscriptPanel',
  props: {
    transcripts: {
      type: Array,
      default: () => []
    },
    consoleLogs: {
      type: Array,
      default: () => []
    },
    showAILogs: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      // 拖拽调整大小相关
      isResizing: false,
      startY: 0,
      startTranscriptHeight: 0,
      startLogHeight: 0,
      
      // 折叠状态
      logCollapsed: false,
      
      // 默认高度分配
      transcriptHeight: 300,
      logHeight: 200
    }
  },
  computed: {
    sortedTranscripts() {
      // 按照 createTime 排序，确保字幕按照实际对话顺序显示
      return [...this.transcripts].sort((a, b) => {
        return (a.createTime || 0) - (b.createTime || 0)
      })
    },
    sortedConsoleLogs() {
      // 按照时间戳排序控制台日志
      return [...this.consoleLogs].sort((a, b) => {
        return (a.timestamp || 0) - (b.timestamp || 0)
      })
    }
  },
  mounted() {
    // 初始化高度分配
    this.initializeHeights()
    
    // 添加全局鼠标事件监听器
    document.addEventListener('mousemove', this.handleMouseMove)
    document.addEventListener('mouseup', this.handleMouseUp)
    
    // 添加窗口resize监听器
    window.addEventListener('resize', this.initializeHeights)
  },
  beforeDestroy() {
    // 清理事件监听器
    document.removeEventListener('mousemove', this.handleMouseMove)
    document.removeEventListener('mouseup', this.handleMouseUp)
    window.removeEventListener('resize', this.initializeHeights)
  },
  methods: {
    // 初始化高度分配
    initializeHeights() {
      this.$nextTick(() => {
        const panelHeight = this.$el.clientHeight - 60 // 减去header的高度
        if (this.showAILogs) {
          this.transcriptHeight = Math.floor(panelHeight * 0.6) // 60%给字幕
          this.logHeight = Math.floor(panelHeight * 0.4) // 40%给日志
        } else {
          this.transcriptHeight = panelHeight // 全部给字幕
          this.logHeight = 200 // 默认日志高度
        }
      })
    },

    // 拖拽调整大小相关方法
    startResize(event) {
      this.isResizing = true
      this.startY = event.clientY
      this.startTranscriptHeight = this.transcriptHeight
      this.startLogHeight = this.logHeight
      
      // 防止文本选择
      event.preventDefault()
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'ns-resize'
    },

    handleMouseMove(event) {
      if (!this.isResizing) return

      const deltaY = event.clientY - this.startY
      const minHeight = 100 // 最小高度

      // 计算新的高度
      let newTranscriptHeight = this.startTranscriptHeight + deltaY
      let newLogHeight = this.startLogHeight - deltaY

      // 限制最小高度
      if (newTranscriptHeight < minHeight) {
        newTranscriptHeight = minHeight
        newLogHeight = this.startTranscriptHeight + this.startLogHeight - minHeight
      } else if (newLogHeight < minHeight) {
        newLogHeight = minHeight
        newTranscriptHeight = this.startTranscriptHeight + this.startLogHeight - minHeight
      }

      this.transcriptHeight = newTranscriptHeight
      this.logHeight = newLogHeight
    },

    handleMouseUp() {
      if (this.isResizing) {
        this.isResizing = false
        document.body.style.userSelect = ''
        document.body.style.cursor = ''
      }
    },

    // 折叠/展开日志区域
    toggleLogCollapse() {
      this.logCollapsed = !this.logCollapsed
      
      if (this.logCollapsed) {
        // 折叠时，将所有高度给字幕区域
        const totalHeight = this.transcriptHeight + this.logHeight
        this.transcriptHeight = totalHeight
      } else {
        // 展开时，重新分配高度
        this.initializeHeights()
      }
    },

    // 工具方法
    isSipPhone(participantId) {
      return participantId && participantId.startsWith('sip_')
    },
    getParticipantClass(participantId) {
      if (participantId === 'system') return 'system-message'
      if (participantId === 'ai_user') return 'ai-user-message'
      return this.isSipPhone(participantId) ? 'agent-message' : 'user-message'
    },
    getParticipantName(participantId) {
      if (participantId === 'system') return '系统'
      if (participantId === 'ai_user') return 'AI用户'
      return this.isSipPhone(participantId) ? 'AI客服' : '用户'
    },
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        hour12: false 
      })
    },
    formatLogTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        hour12: false 
      })
    },
    getLogTypeClass(type) {
      const typeMap = {
        'status': 'log-status',
        'ai_user_query': 'log-user',
        'tts_audio': 'log-audio',
        'dial_response': 'log-agent',
        'judger_result': 'log-judger',
        'error': 'log-error',
        'completed': 'log-success'
      }
      return typeMap[type] || 'log-info'
    },
    getLogTypeName(type) {
      const typeNames = {
        'status': '状态',
        'ai_user_query': 'AI用户',
        'tts_audio': 'TTS音频',
        'dial_response': '客服回复',
        'judger_result': '判断结果',
        'error': '错误',
        'completed': '完成'
      }
      return typeNames[type] || '信息'
    },
    formatLogMessage(log) {
      if (log.type === 'ai_user_query') {
        return `生成查询: ${log.data.query}`
      } else if (log.type === 'tts_audio') {
        return `音频合成完成 (${log.data.sample_rate}Hz)`
      } else if (log.type === 'dial_response') {
        return `客服回复: ${log.data.response}`
      } else if (log.type === 'judger_result') {
        return `判断结果: ${log.data.should_continue ? '继续' : '结束'} - ${log.data.reason}`
      } else if (log.type === 'status') {
        return log.data.message
      } else if (log.type === 'error') {
        return `错误: ${log.data.message}`
      } else if (log.type === 'completed') {
        return `测试完成 (共${log.data.total_rounds}轮)`
      }
      return log.message || JSON.stringify(log.data)
    },
    shouldShowDetails(log) {
      // 只对某些类型显示详细信息
      return ['judger_result', 'error'].includes(log.type)
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const transcriptContent = this.$refs.transcriptContent
        const logContent = this.$refs.logContent
        
        if (transcriptContent) {
          transcriptContent.scrollTop = transcriptContent.scrollHeight
        }
        if (logContent) {
          logContent.scrollTop = logContent.scrollHeight
        }
      })
    }
  },
  watch: {
    sortedTranscripts: {
      handler() {
        this.scrollToBottom()
      },
      deep: true
    },
    sortedConsoleLogs: {
      handler() {
        this.scrollToBottom()
      },
      deep: true
    },
    showAILogs: {
      handler() {
        this.initializeHeights()
      },
      immediate: true
    }
  }
}
</script>

<style scoped>
.transcript-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 通话字幕区域 */
.transcript-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-secondary);
  min-height: 0;
}

/* 可拖拽的分隔条 */
.resizer {
  position: relative;
  height: 8px;
  background: var(--bg-primary);
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s ease;
}

.resizer:hover {
  background: var(--bg-hover);
}

.resizer-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
  transform: translateY(-50%);
}

.resizer-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  background: var(--bg-primary);
  border-radius: 4px;
  color: var(--text-tertiary);
  transition: all 0.2s ease;
}

.resizer:hover .resizer-handle {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

/* AI日志区域 */
.ai-log-section {
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.ai-log-section.collapsed {
  height: auto !important;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.log-header:hover {
  background: var(--bg-hover);
}

.log-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.ai-indicator {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  color: white;
}

.ai-pulse {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: aiPulse 2s infinite;
}

@keyframes aiPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2);
  }
}

.log-stats {
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.collapse-btn.collapsed {
  transform: rotate(180deg);
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  background: var(--bg-secondary);
}

.log-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
  color: var(--text-tertiary);
  text-align: center;
  gap: 16px;
}

.empty-animation {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-ring {
  position: absolute;
  width: 60px;
  height: 60px;
  border: 2px solid #667eea;
  border-radius: 50%;
  opacity: 0.6;
  animation: pulseRing 2s infinite;
}

.pulse-ring-2 {
  animation-delay: 1s;
}

@keyframes pulseRing {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.3;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.log-empty svg {
  color: #667eea;
  z-index: 1;
}

.log-empty span {
  font-size: 14px;
  font-weight: 500;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-item {
  display: flex;
  gap: 8px;
  animation: logSlideIn 0.4s ease-out;
}

@keyframes logSlideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.log-timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 1px;
}

.timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bg-primary);
  border: 2px solid #667eea;
  z-index: 1;
  transition: all 0.2s ease;
}

.timeline-line {
  position: absolute;
  top: 8px;
  width: 1px;
  height: calc(100% + 6px);
  background: linear-gradient(to bottom, #667eea, transparent);
  opacity: 0.3;
}

.log-card {
  flex: 1;
  background: var(--bg-primary);
  border-radius: 6px;
  padding: 8px 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.log-card:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
}

.log-header-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.log-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.log-meta {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-type {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
}

.log-time {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.log-message {
  font-size: 12px;
  line-height: 1.3;
  color: var(--text-primary);
  word-wrap: break-word;
  margin: 0;
}

.log-details {
  margin-top: 6px;
  padding: 6px;
  background: var(--bg-secondary);
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

.details-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 10px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.2;
}

/* 不同日志类型的样式 */
.log-status .log-icon {
  background: #eff6ff;
  color: #3b82f6;
}

.log-status .timeline-dot {
  border-color: #3b82f6;
}

.log-user .log-icon {
  background: #fef3c7;
  color: #f59e0b;
}

.log-user .timeline-dot {
  border-color: #f59e0b;
}

.log-audio .log-icon {
  background: #f3e8ff;
  color: #8b5cf6;
}

.log-audio .timeline-dot {
  border-color: #8b5cf6;
}

.log-agent .log-icon {
  background: #ecfdf5;
  color: #10b981;
}

.log-agent .timeline-dot {
  border-color: #10b981;
}

.log-judger .log-icon {
  background: #ecfeff;
  color: #06b6d4;
}

.log-judger .timeline-dot {
  border-color: #06b6d4;
}

.log-error .log-icon {
  background: #fef2f2;
  color: #ef4444;
}

.log-error .timeline-dot {
  border-color: #ef4444;
}

.log-success .log-icon {
  background: #f0fdf4;
  color: #22c55e;
}

.log-success .timeline-dot {
  border-color: #22c55e;
}

.log-info .log-icon {
  background: #f9fafb;
  color: #6b7280;
}

.log-info .timeline-dot {
  border-color: #6b7280;
}

/* 折叠后的左下角按钮 */
.collapsed-log-button {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  z-index: 10;
}

.collapsed-log-button:hover {
  background: var(--bg-hover);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.collapsed-button-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-indicator.small {
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.ai-indicator.small .ai-pulse {
  width: 4px;
  height: 4px;
  top: -1px;
  right: -1px;
}

.collapsed-button-content span {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.log-count {
  background: #667eea;
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

/* AI日志区域折叠状态 */
.ai-log-section.collapsed {
  display: none;
}

.transcript-section::-webkit-scrollbar,
.log-content::-webkit-scrollbar {
  width: 6px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  text-align: center;
  padding: 40px 20px;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

.empty-state span {
  font-size: 14px;
}

.transcript-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.transcript-item {
  display: flex;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.transcript-item.user-message {
  justify-content: flex-end;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.user-message .message-wrapper {
  flex-direction: row-reverse;
}

.speaker-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--text-secondary);
}

.user-message .speaker-avatar {
  background: #eef2ff;
  color: #4f46e5;
}

.agent-message .speaker-avatar {
  background: #f0fdf4;
  color: #10b981;
}

.ai-user-message .speaker-avatar {
  background: #fef3c7;
  color: #f59e0b;
}

.system-message .speaker-avatar {
  background: #f3f4f6;
  color: #6b7280;
}

.speaker-avatar svg {
  width: 20px;
  height: 20px;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.user-message .message-header {
  flex-direction: row-reverse;
}

.speaker-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.message-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  background: var(--bg-primary);
  color: var(--text-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.user-message .message-text {
  background: #eef2ff;
  color: #1e293b;
  border-bottom-right-radius: 4px;
}

.agent-message .message-text {
  background: var(--bg-primary);
  border-bottom-left-radius: 4px;
}

.ai-user-message .message-text {
  background: #fef3c7;
  color: #92400e;
  border-bottom-right-radius: 4px;
}

.system-message .message-text {
  background: #f3f4f6;
  color: #374151;
  border-radius: 8px;
  font-style: italic;
  text-align: center;
}

.message-text.interim {
  opacity: 0.85;
}

.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  margin-left: 4px;
}

.typing-dots .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.6;
  animation: typingDot 1.4s infinite;
}

.typing-dots .dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingDot {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.transcript-section::-webkit-scrollbar,
.log-content::-webkit-scrollbar {
  width: 6px;
}

.transcript-section::-webkit-scrollbar-track,
.log-content::-webkit-scrollbar-track {
  background: transparent;
}

.transcript-section::-webkit-scrollbar-thumb,
.log-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

.transcript-section::-webkit-scrollbar-thumb:hover,
.log-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
