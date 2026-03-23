<template>
  <div class="floating-transcript-container">
    <!-- 悬浮按钮 -->
    <div
      v-if="!isOpen"
      class="floating-btn"
      @click="toggleOpen"
      :class="{ 'has-messages': transcriptMessages.length > 0 }"
      :style="{ background: `linear-gradient(135deg, ${employeeColor}, ${darkenColor(employeeColor)})` }"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span v-if="transcriptMessages.length > 0" class="message-badge">{{ transcriptMessages.length }}</span>
    </div>

    <!-- 悬浮窗 - 手机样式 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="floating-window">
        <!-- 头部 -->
        <div class="window-header" :style="{ background: `linear-gradient(135deg, ${employeeColor}, ${darkenColor(employeeColor)})` }">
          <div class="header-left">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="window-title">实时字幕</span>
          </div>
          <div class="header-actions">
            <button class="action-btn close-btn" @click="toggleOpen" title="关闭">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="window-content" ref="transcriptContent">
          <div v-if="transcriptMessages.length === 0" class="empty-state">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
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
            class="message-item"
            :class="{
              'is-user': message.type === 'user',
              'is-agent': message.type === 'agent',
              'is-partial': message.isPartial
            }"
            :style="message.type === 'agent' ? { borderLeftColor: employeeColor } : {}"
          >
            <div class="message-header">
              <span class="message-sender">{{ message.type === 'user' ? '食神' : '模拟用户' }}</span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div class="message-body">
              <p>{{ message.content }}</p>
              <div v-if="message.isPartial" class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'FloatingTranscript',
  props: {
    transcriptMessages: {
      type: Array,
      default: () => []
    },
    employeeColor: {
      type: String,
      default: '#3b82f6'
    }
  },
  data() {
    return {
      isOpen: false
    }
  },
  watch: {
    transcriptMessages: {
      handler(newMessages) {
        if (newMessages && newMessages.length > 0) {
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      },
      deep: true
    }
  },
  methods: {
    toggleOpen() {
      this.isOpen = !this.isOpen
      if (this.isOpen) {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },

    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },

    scrollToBottom() {
      const container = this.$refs.transcriptContent
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    // 颜色变暗处理
    darkenColor(hex) {
      if (!hex || hex.length < 4) return hex
      // 移除 # 前缀
      hex = hex.replace('#', '')
      // 处理简写形式如 #abc
      if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
      }
      const r = Math.max(0, parseInt(hex.substring(0, 2), 16) - 30)
      const g = Math.max(0, parseInt(hex.substring(2, 4), 16) - 30)
      const b = Math.max(0, parseInt(hex.substring(4, 6), 16) - 30)
      return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.floating-transcript-container {
  position: relative;
}

/* 悬浮按钮 */
.floating-btn {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
}

.floating-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(59, 130, 246, 0.5);
}

.floating-btn.has-messages {
  animation: pulse-btn 2s ease-in-out infinite;
}

@keyframes pulse-btn {
  0%, 100% { box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 4px 30px rgba(59, 130, 246, 0.6); }
}

.message-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

/* 悬浮窗 - 手机样式 */
.floating-window {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 320px;
  max-width: calc(100vw - 40px);
  height: 480px;
  max-height: calc(100vh - 100px);
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1001;
}

.window-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  border-radius: 20px 20px 0 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.window-title {
  font-size: 14px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.window-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f8fafc;
  /* 隐藏滚动条但保留滚动能力 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.window-content::-webkit-scrollbar {
  display: none; /* Chrome/Safari/Opera */
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
}

.empty-state svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

/* 消息样式 */
.message-item {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.message-item.is-user {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  border-left: 3px solid #3b82f6;
}

.message-item.is-agent {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-left: 3px solid #22c55e;
}

.message-item.is-partial {
  opacity: 0.8;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.message-sender {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.message-time {
  font-size: 10px;
  color: #94a3b8;
}

.message-body {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.message-body p {
  margin: 0;
  font-size: 13px;
  color: #1e293b;
  line-height: 1.5;
  flex: 1;
}

.typing-indicator {
  display: flex;
  gap: 3px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
  animation: typing 1.4s ease-in-out infinite;
}

.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 过渡动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 响应式 */
@media (max-width: 400px) {
  .floating-window {
    width: calc(100vw - 20px);
    right: 10px;
    bottom: 10px;
    height: calc(100vh - 80px);
    border-radius: 16px;
  }

  .window-header {
    border-radius: 16px 16px 0 0;
  }
}
</style>