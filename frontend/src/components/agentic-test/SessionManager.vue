<template>
  <div class="session-manager">
    <div class="manager-header">
      <h3>测试会话</h3>
      <button class="btn btn-primary btn-sm" @click="showCreateModal = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        新建会话
      </button>
    </div>

    <div class="session-list">
      <div 
        v-for="session in sessions" 
        :key="session.id"
        class="session-item"
        :class="{ 
          active: currentSession && currentSession.id === session.id,
          connected: isConnected && currentSession && currentSession.id === session.id
        }"
        @click="selectSession(session)"
      >
        <div class="session-info">
          <div class="session-name">{{ session.name }}</div>
          <div class="session-meta">
            <span class="session-date">{{ formatDate(session.updated_at) }}</span>
            <span v-if="session.is_active" class="active-badge">活跃</span>
          </div>
        </div>
        <div class="session-actions">
          <button 
            class="btn-icon"
            @click.stop="connectToSession(session)"
            :disabled="isConnected && currentSession && currentSession.id === session.id"
            :title="isConnected && currentSession && currentSession.id === session.id ? '已连接' : '连接'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="sessions.length === 0" class="empty-sessions">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <p>暂无测试会话</p>
        <button class="btn btn-outline" @click="showCreateModal = true">
          创建第一个会话
        </button>
      </div>
    </div>

    <!-- 创建会话模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>创建新会话</h4>
          <button class="btn-close" @click="showCreateModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>会话名称</label>
            <input 
              v-model="newSessionName"
              type="text"
              placeholder="输入会话名称..."
              @keyup.enter="createSession"
              ref="sessionNameInput"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateModal = false">
            取消
          </button>
          <button 
            class="btn btn-primary"
            @click="createSession"
            :disabled="!newSessionName.trim()"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'SessionManager',
  data() {
    return {
      showCreateModal: false,
      newSessionName: ''
    }
  },
  computed: {
    ...mapState('agenticTest', [
      'sessions',
      'currentSession',
      'isConnected'
    ])
  },
  async mounted() {
    await this.fetchSessions()
  },
  methods: {
    ...mapActions('agenticTest', [
      'fetchSessions',
      'createSession',
      'activateSession',
      'connectWebSocket',
      'disconnectWebSocket'
    ]),
    
    selectSession(session) {
      // 选择会话但不自动连接
      this.$store.commit('agenticTest/SET_CURRENT_SESSION', session)
    },
    
    async connectToSession(session) {
      try {
        // 先断开现有连接
        if (this.isConnected) {
          await this.disconnectWebSocket()
        }
        
        // 激活会话
        await this.activateSession(session.id)
        
        // 建立WebSocket连接
        await this.connectWebSocket(session.id)
        
        this.$store.commit('agenticTest/SET_CURRENT_SESSION', session)
      } catch (error) {
        console.error('Failed to connect to session:', error)
        alert('连接会话失败，请重试')
      }
    },
    
    async createSession() {
      if (!this.newSessionName.trim()) return
      
      try {
        const session = await this.createSession(this.newSessionName)
        this.showCreateModal = false
        this.newSessionName = ''
        
        // 自动连接到新创建的会话
        await this.connectToSession(session)
      } catch (error) {
        console.error('Failed to create session:', error)
        alert('创建会话失败，请重试')
      }
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)
      
      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`
      
      return date.toLocaleDateString('zh-CN')
    }
  },
  watch: {
    showCreateModal(show) {
      if (show) {
        this.$nextTick(() => {
          this.$refs.sessionNameInput?.focus()
        })
      }
    }
  }
}
</script>

<style scoped>
.session-manager {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  height: 300px;
  display: flex;
  flex-direction: column;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.manager-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item.active {
  background: var(--bg-secondary);
  border-color: var(--accent-blue);
}

.session-item.connected {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.session-date {
  font-size: 12px;
  color: var(--text-tertiary);
}

.active-badge {
  padding: 2px 6px;
  background: #10b981;
  color: white;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.session-actions {
  display: flex;
  gap: 4px;
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

.btn-icon:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  text-align: center;
  padding: 20px;
}

.empty-sessions svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-sessions p {
  margin: 0 0 16px 0;
  font-size: 14px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-surface);
  border-radius: 12px;
  width: 400px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-close {
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
}

.btn-close:hover {
  background: var(--bg-hover);
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-primary {
  background: var(--accent-blue);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-blue-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover {
  background: var(--bg-hover);
}
</style>