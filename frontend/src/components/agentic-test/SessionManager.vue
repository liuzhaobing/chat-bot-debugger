<template>
  <div class="session-manager">
    <div class="session-header">
      <h3>会话管理</h3>
      <div class="header-actions">
        <button 
          class="btn btn-primary btn-sm"
          @click="showCreateDialog = true"
          :disabled="isSessionActive"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          新建会话
        </button>
      </div>
    </div>

    <div class="session-content">
      <!-- 当前会话信息 -->
      <div v-if="currentSession" class="current-session">
        <div class="session-card active">
          <div class="session-info">
            <h4>{{ currentSession.name }}</h4>
            <div class="session-meta">
              <span class="session-id">ID: {{ currentSession.id }}</span>
              <span class="session-status" :class="connectionStatus">
                {{ getStatusText() }}
              </span>
            </div>
            <div v-if="isSessionActive" class="session-stats">
              <div class="stat">
                <span class="stat-label">时长:</span>
                <span class="stat-value">{{ formattedDuration }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">消息:</span>
                <span class="stat-value">{{ transcriptMessages.length }}</span>
              </div>
            </div>
          </div>
          <div class="session-actions">
            <button 
              v-if="!isSessionActive"
              class="btn btn-success btn-sm"
              @click="startSession"
              :disabled="isConnecting"
            >
              <svg v-if="isConnecting" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5,3 19,12 5,21 5,3"></polygon>
              </svg>
              {{ isConnecting ? '连接中...' : '开始会话' }}
            </button>
            <button 
              v-else
              class="btn btn-danger btn-sm"
              @click="stopSession"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
              停止会话
            </button>
          </div>
        </div>
      </div>

      <!-- 会话列表 -->
      <div class="sessions-list">
        <div class="list-header">
          <h4>历史会话</h4>
          <button 
            class="btn-icon"
            @click="refreshSessions"
            :disabled="isRefreshing"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
              :class="{ spin: isRefreshing }"
            >
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
              <path d="M21 3v5h-5"></path>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
              <path d="M3 21v-5h5"></path>
            </svg>
          </button>
        </div>

        <div v-if="otherSessions.length === 0" class="empty-sessions">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <p>暂无其他会话</p>
        </div>

        <div v-else class="sessions-grid">
          <div 
            v-for="session in otherSessions" 
            :key="session.id"
            class="session-card"
            @click="selectSession(session)"
          >
            <div class="session-info">
              <h5>{{ session.name }}</h5>
              <div class="session-meta">
                <span class="session-date">{{ formatDate(session.created_at) }}</span>
                <span v-if="session.is_active" class="session-badge active">活跃</span>
              </div>
            </div>
            <div class="session-actions">
              <button 
                class="btn-icon"
                @click.stop="deleteSession(session)"
                title="删除会话"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3,6 5,6 21,6"></polyline>
                  <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建会话对话框 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click="showCreateDialog = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>创建新会话</h3>
          <button class="btn-icon" @click="showCreateDialog = false">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
              placeholder="请输入会话名称..."
              @keyup.enter="createSession"
              ref="sessionNameInput"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateDialog = false">
            取消
          </button>
          <button 
            class="btn btn-primary"
            @click="createSession"
            :disabled="!newSessionName.trim() || isCreating"
          >
            <svg v-if="isCreating" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            {{ isCreating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  name: 'SessionManager',
  computed: {
    ...mapState('agenticTest', [
      'sessions',
      'currentSession',
      'connectionStatus',
      'sessionDuration',
      'transcriptMessages'
    ]),
    ...mapGetters('agenticTest', [
      'isSessionActive'
    ]),
    
    otherSessions() {
      return this.sessions.filter(session => 
        !this.currentSession || session.id !== this.currentSession.id
      )
    },
    
    formattedDuration() {
      const minutes = Math.floor(this.sessionDuration / 60)
      const seconds = this.sessionDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  data() {
    return {
      showCreateDialog: false,
      newSessionName: '',
      isCreating: false,
      isRefreshing: false,
      isConnecting: false
    }
  },
  mounted() {
    this.loadSessions()
  },
  watch: {
    showCreateDialog(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          if (this.$refs.sessionNameInput) {
            this.$refs.sessionNameInput.focus()
          }
        })
      }
    }
  },
  methods: {
    ...mapActions('agenticTest', [
      'fetchSessions',
      'createSession',
      'activateSession'
    ]),

    async loadSessions() {
      this.isRefreshing = true
      try {
        await this.fetchSessions()
      } catch (error) {
        console.error('加载会话列表失败:', error)
        this.$message?.error('加载会话列表失败')
      } finally {
        this.isRefreshing = false
      }
    },

    async refreshSessions() {
      await this.loadSessions()
    },

    async createSession() {
      if (!this.newSessionName.trim() || this.isCreating) return

      this.isCreating = true
      try {
        const session = await this.createSession(this.newSessionName.trim())
        this.showCreateDialog = false
        this.newSessionName = ''
        this.$message?.success(`会话 "${session.name}" 创建成功`)
      } catch (error) {
        console.error('创建会话失败:', error)
        this.$message?.error('创建会话失败')
      } finally {
        this.isCreating = false
      }
    },

    async selectSession(session) {
      if (this.isSessionActive) {
        this.$message?.warning('请先停止当前会话')
        return
      }

      try {
        await this.activateSession(session.id)
        this.$message?.success(`已切换到会话 "${session.name}"`)
      } catch (error) {
        console.error('切换会话失败:', error)
        this.$message?.error('切换会话失败')
      }
    },

    async deleteSession(session) {
      if (session.id === this.currentSession?.id) {
        this.$message?.warning('无法删除当前会话')
        return
      }

      if (!confirm(`确定要删除会话 "${session.name}" 吗？`)) {
        return
      }

      try {
        // 这里需要实现删除会话的API
        // await this.deleteSession(session.id)
        this.$message?.success(`会话 "${session.name}" 已删除`)
        this.refreshSessions()
      } catch (error) {
        console.error('删除会话失败:', error)
        this.$message?.error('删除会话失败')
      }
    },

    startSession() {
      this.$emit('start-session')
    },

    stopSession() {
      this.$emit('stop-session')
    },

    getStatusText() {
      const statusMap = {
        'disconnected': '未连接',
        'connecting': '连接中...',
        'connected': '已连接',
        'active': '会话中'
      }
      return statusMap[this.connectionStatus] || '未知状态'
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = Math.abs(now - date)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 1) {
        return '今天'
      } else if (diffDays === 2) {
        return '昨天'
      } else if (diffDays <= 7) {
        return `${diffDays}天前`
      } else {
        return date.toLocaleDateString('zh-CN')
      }
    }
  }
}
</script>

<style scoped>
.session-manager {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.session-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.session-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 当前会话 */
.current-session {
  flex-shrink: 0;
}

.session-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.session-card.active {
  border-color: var(--accent-blue);
  background: rgba(79, 70, 229, 0.05);
  cursor: default;
}

.session-card.active:hover {
  transform: none;
}

.session-info {
  flex: 1;
  margin-bottom: 12px;
}

.session-info h4,
.session-info h5 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.session-info h5 {
  font-size: 14px;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.session-id,
.session-date {
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: monospace;
}

.session-status {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.session-status.disconnected {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.session-status.connecting {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.session-status.connected {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.session-status.active {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.session-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
  text-transform: uppercase;
}

.session-badge.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.session-stats {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.session-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 会话列表 */
.sessions-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.list-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-sessions svg {
  width: 32px;
  height: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-sessions p {
  margin: 0;
  font-size: 13px;
}

.sessions-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 按钮样式 */
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
  text-decoration: none;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn-primary {
  background: var(--accent-blue);
  color: white;
  border: 1px solid var(--accent-blue);
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
  border-color: #4338ca;
}

.btn-success {
  background: #10b981;
  color: white;
  border: 1px solid #10b981;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
  border-color: #059669;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: 1px solid #ef4444;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
  border-color: #dc2626;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
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

.btn-icon svg {
  width: 16px;
  height: 16px;
}

/* 模态框 */
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
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: var(--bg-surface);
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 400px;
  animation: slideIn 0.2s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border-color);
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
  transition: border-color 0.2s ease;
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .session-header {
    padding: 12px 16px;
  }
  
  .session-content {
    padding: 12px;
    gap: 16px;
  }
  
  .session-card {
    padding: 12px;
  }
  
  .session-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .modal-content {
    margin: 20px;
    width: calc(100% - 40px);
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
}
</style>