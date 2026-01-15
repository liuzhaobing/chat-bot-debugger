<template>
  <div class="session-config-overlay" @click.self="close">
    <div class="config-panel">
      <div class="config-header">
        <h3>会话配置</h3>
        <button class="close-btn" @click="close">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="config-body">
        <div class="config-section">
          <h4>服务器配置</h4>
          <div class="form-group">
            <label>服务器地址</label>
            <input 
              v-model="localConfig.serverUrl" 
              type="text" 
              placeholder="ws://118.31.127.156:8000/ws/sessions/start"
            />
          </div>
        </div>

        <div class="config-section">
          <h4>用户信息</h4>
          <div class="form-group">
            <label>用户ID</label>
            <input 
              v-model="localConfig.userId" 
              type="text" 
              placeholder="17744270115"
            />
          </div>
          <div class="form-group">
            <label>房间ID</label>
            <input 
              v-model="localConfig.roomId" 
              type="text" 
              placeholder="自动生成"
              disabled
            />
          </div>
          <div class="form-group">
            <label>参与者ID</label>
            <input 
              v-model="localConfig.participantId" 
              type="text" 
              placeholder="自动生成"
              disabled
            />
          </div>
        </div>

        <div class="config-section">
          <h4>Agent配置</h4>
          <div class="form-group">
            <label>Agent类型</label>
            <select v-model="localConfig.agentType">
              <option value="robam_workflow">老板电器工作流</option>
              <option value="general">通用Agent</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="form-group">
            <label>配置模板</label>
            <select v-model="localConfig.configTemplate">
              <option value="ai_telephone">AI电话</option>
              <option value="voice_assistant">语音助手</option>
              <option value="customer_service">客户服务</option>
            </select>
          </div>
        </div>

        <div class="config-section">
          <h4>高级设置</h4>
          <div class="form-group">
            <label>欢迎消息</label>
            <textarea 
              v-model="localConfig.welcomeMessage" 
              rows="3"
              placeholder="你好，我是食神，欢迎致电老板电器。"
            ></textarea>
          </div>
          <div class="form-group">
            <label>系统提示</label>
            <textarea 
              v-model="localConfig.systemPrompt" 
              rows="3"
              placeholder="You are a helpful AI voice assistant."
            ></textarea>
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input 
                type="checkbox" 
                v-model="localConfig.allowInterruptions"
              />
              <span>允许打断</span>
            </label>
          </div>
        </div>
      </div>

      <div class="config-footer">
        <button class="btn btn-secondary" @click="reset">重置</button>
        <button class="btn btn-primary" @click="save">保存配置</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SessionConfig',
  props: {
    config: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      localConfig: {
        serverUrl: '',
        userId: '',
        roomId: '',
        participantId: '',
        agentType: 'robam_workflow',
        configTemplate: 'ai_telephone',
        welcomeMessage: '你好，我是食神，欢迎致电老板电器。',
        systemPrompt: 'You are a helpful AI voice assistant.',
        allowInterruptions: true
      }
    }
  },
  created() {
    // 初始化本地配置
    this.localConfig = { ...this.config }
  },
  methods: {
    close() {
      this.$emit('close')
    },
    save() {
      this.$emit('save', this.localConfig)
      this.close()
    },
    reset() {
      this.localConfig = {
        serverUrl: 'ws://118.31.127.156:8000/ws/sessions/start',
        userId: '17744270115',
        roomId: '',
        participantId: '',
        agentType: 'robam_workflow',
        configTemplate: 'ai_telephone',
        welcomeMessage: '你好，我是食神，欢迎致电老板电器。',
        systemPrompt: 'You are a helpful AI voice assistant.',
        allowInterruptions: true
      }
    }
  }
}
</script>

<style scoped>
.session-config-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.config-panel {
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.config-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.config-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.config-section {
  margin-bottom: 32px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  background: white;
  transition: all 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-group textarea {
  resize: vertical;
  min-height: 60px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.checkbox-group span {
  font-size: 14px;
  color: #1e293b;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e2e8f0;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.btn-secondary:hover {
  background: #e2e8f0;
  color: #475569;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

/* 滚动条样式 */
.config-body::-webkit-scrollbar {
  width: 6px;
}

.config-body::-webkit-scrollbar-track {
  background: transparent;
}

.config-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.config-body::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
