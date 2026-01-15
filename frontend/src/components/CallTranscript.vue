<template>
  <div class="transcript-container">
    <div class="transcript-header">
      <h3>通话字幕</h3>
    </div>

    <div class="transcript-content" ref="transcriptContent">
      <div v-if="transcripts.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <p>暂无通话记录</p>
        <span>开始通话后，对话内容将显示在这里</span>
      </div>

      <div v-else class="transcript-list">
        <div 
          v-for="(item, index) in transcripts" 
          :key="index"
          class="transcript-item"
          :class="getParticipantClass(item.participant_id)"
        >
          <div class="message-wrapper">
            <div class="speaker-avatar">
              <svg v-if="isSipPhone(item.participant_id)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="transcript-footer">
      <div class="stats">
        <span class="stat-item">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          {{ transcripts.length }} 条消息
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CallTranscript',
  props: {
    transcripts: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    isSipPhone(participantId) {
      // 判断是否是 sip_phone (AI客服)
      return participantId && participantId.startsWith('sip_')
    },
    getParticipantClass(participantId) {
      // sip_phone (AI客服) 在左侧，phone (用户) 在右侧
      return this.isSipPhone(participantId) ? 'agent-message' : 'user-message'
    },
    getParticipantName(participantId) {
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
    scrollToBottom() {
      this.$nextTick(() => {
        const content = this.$refs.transcriptContent
        if (content) {
          content.scrollTop = content.scrollHeight
        }
      })
    }
  },
  watch: {
    transcripts: {
      handler() {
        this.scrollToBottom()
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.transcript-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.transcript-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-primary);
}

.transcript-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.transcript-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-secondary);
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

.message-text.interim {
  opacity: 0.6;
  font-style: italic;
}

.transcript-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-item svg {
  color: var(--text-tertiary);
}

/* 滚动条样式 */
.transcript-content::-webkit-scrollbar {
  width: 6px;
}

.transcript-content::-webkit-scrollbar-track {
  background: transparent;
}

.transcript-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

.transcript-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
