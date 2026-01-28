<template>
  <div class="iot-config-dropdown" :class="{ open: isOpen }">
    <button 
      class="config-trigger"
      @click="toggleDropdown"
      :class="{ 'has-config': isConfigValid }"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
      </svg>
      <span>IOT配置</span>
      <svg class="chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6,9 12,15 18,9"></polyline>
      </svg>
    </button>

    <div v-if="isOpen" class="config-dropdown">
      <div class="dropdown-header">
        <h4>IOT 配置</h4>
        <button class="close-btn" @click="closeDropdown">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="dropdown-content">
        <div class="config-form">
          <div class="form-group">
            <label>环境选择</label>
            <select v-model="localEnv" @change="saveConfig">
              <option value="test">测试环境 (api-test.myroki.com)</option>
              <option value="prod">生产环境 (api.myroki.com)</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>IOT Token</label>
            <input 
              v-model="localIotToken"
              type="password"
              placeholder="请输入IOT认证Token..."
              @blur="saveConfig"
            />
          </div>
          
          <div class="form-group">
            <label>Family ID</label>
            <input 
              v-model="localFamilyId"
              type="text"
              placeholder="请输入家庭ID..."
              @blur="saveConfig"
            />
          </div>
        </div>
        
        <div class="config-status">
          <div class="status-item" :class="{ valid: isEnvValid }">
            <div class="status-indicator"></div>
            <span>环境: {{ envDisplayName }}</span>
          </div>
          <div class="status-item" :class="{ valid: isTokenValid }">
            <div class="status-indicator"></div>
            <span>Token: {{ isTokenValid ? '已配置' : '未配置' }}</span>
          </div>
          <div class="status-item" :class="{ valid: isFamilyIdValid }">
            <div class="status-indicator"></div>
            <span>Family ID: {{ isFamilyIdValid ? '已配置' : '未配置' }}</span>
          </div>
        </div>
        
        <div class="config-actions">
          <button 
            class="btn btn-outline btn-sm"
            @click="testConnection"
            :disabled="!isConfigValid || isTestingConnection"
          >
            <svg v-if="isTestingConnection" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
            {{ isTestingConnection ? '测试中...' : '测试连接' }}
          </button>
          
          <button 
            class="btn btn-primary btn-sm"
            @click="loadDevices"
            :disabled="!isConfigValid || isLoadingDevices"
          >
            <svg v-if="isLoadingDevices" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
              <path d="M21 3v5h-5"></path>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
              <path d="M3 21v-5h5"></path>
            </svg>
            {{ isLoadingDevices ? '加载中...' : '加载设备' }}
          </button>
          
          <button 
            class="btn btn-outline btn-sm"
            @click="clearConfig"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
            </svg>
            清空配置
          </button>
        </div>
      </div>
    </div>

    <!-- 遮罩层 -->
    <div v-if="isOpen" class="dropdown-overlay" @click="closeDropdown"></div>
  </div>
</template>

<script>
export default {
  name: 'IOTConfigDropdown',
  data() {
    return {
      isOpen: false,
      localIotToken: '',
      localFamilyId: '',
      localEnv: 'test',
      isTestingConnection: false,
      isLoadingDevices: false
    }
  },
  computed: {
    isEnvValid() {
      return this.localEnv && ['test', 'prod'].includes(this.localEnv)
    },
    
    envDisplayName() {
      return this.localEnv === 'prod' ? '生产环境' : '测试环境'
    },
    
    isTokenValid() {
      return this.localIotToken && this.localIotToken.trim().length > 0
    },
    
    isFamilyIdValid() {
      return this.localFamilyId && this.localFamilyId.trim().length > 0
    },
    
    isConfigValid() {
      return this.isEnvValid && this.isTokenValid && this.isFamilyIdValid
    }
  },
  mounted() {
    this.loadConfig()
    // 点击外部关闭下拉框
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    toggleDropdown() {
      this.isOpen = !this.isOpen
    },
    
    closeDropdown() {
      this.isOpen = false
    },
    
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.isOpen = false
      }
    },
    
    loadConfig() {
      // 从localStorage加载配置
      const savedToken = localStorage.getItem('iot-token')
      const savedFamilyId = localStorage.getItem('family-id')
      const savedEnv = localStorage.getItem('iot-env')
      
      if (savedToken) {
        this.localIotToken = savedToken
      }
      
      if (savedFamilyId) {
        this.localFamilyId = savedFamilyId
      }
      
      if (savedEnv && ['test', 'prod'].includes(savedEnv)) {
        this.localEnv = savedEnv
      }
      
      this.emitConfig()
    },
    
    saveConfig() {
      // 保存到localStorage
      if (this.localIotToken.trim()) {
        localStorage.setItem('iot-token', this.localIotToken.trim())
      } else {
        localStorage.removeItem('iot-token')
      }
      
      if (this.localFamilyId.trim()) {
        localStorage.setItem('family-id', this.localFamilyId.trim())
      } else {
        localStorage.removeItem('family-id')
      }
      
      if (this.localEnv && ['test', 'prod'].includes(this.localEnv)) {
        localStorage.setItem('iot-env', this.localEnv)
      } else {
        localStorage.removeItem('iot-env')
      }
      
      this.emitConfig()
    },
    
    emitConfig() {
      this.$emit('config-change', {
        token: this.localIotToken.trim(),
        familyId: this.localFamilyId.trim(),
        env: this.localEnv
      })
    },
    
    async testConnection() {
      if (!this.isConfigValid) return
      
      this.isTestingConnection = true
      
      try {
        const response = await fetch('/api/agentic-test/iot/test-connection/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            iot_token: this.localIotToken.trim(),
            family_id: this.localFamilyId.trim(),
            env: this.localEnv
          })
        })
        
        const result = await response.json()
        
        if (response.ok && result.success) {
          this.$message?.success(`IOT连接测试成功，发现 ${result.device_count || 0} 个设备`)
        } else {
          this.$message?.error(`IOT连接测试失败: ${result.error || '未知错误'}`)
        }
      } catch (error) {
        console.error('IOT connection test failed:', error)
        this.$message?.error('IOT连接测试失败，请检查配置')
      } finally {
        this.isTestingConnection = false
      }
    },
    
    async loadDevices() {
      if (!this.isConfigValid) return
      
      this.isLoadingDevices = true
      
      try {
        this.$emit('load-devices', {
          token: this.localIotToken.trim(),
          familyId: this.localFamilyId.trim(),
          env: this.localEnv
        })
        
        // 关闭下拉框
        this.closeDropdown()
        
        this.$message?.success('开始加载设备列表...')
      } catch (error) {
        console.error('Load devices failed:', error)
        this.$message?.error('加载设备失败')
      } finally {
        // 延迟重置状态，给用户一些视觉反馈
        setTimeout(() => {
          this.isLoadingDevices = false
        }, 1000)
      }
    },
    
    clearConfig() {
      this.localIotToken = ''
      this.localFamilyId = ''
      this.localEnv = 'test'
      
      // 清除localStorage
      localStorage.removeItem('iot-token')
      localStorage.removeItem('family-id')
      localStorage.removeItem('iot-env')
      
      this.emitConfig()
      this.$message?.success('IOT配置已清空')
    }
  }
}
</script>

<style scoped>
.iot-config-dropdown {
  position: relative;
  display: inline-block;
}

.config-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.config-trigger:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent-blue);
}

.config-trigger.has-config {
  border-color: #10b981;
  color: #059669;
}

.config-trigger.has-config:hover {
  background: rgba(16, 185, 129, 0.05);
}

.config-trigger svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.chevron {
  transition: transform 0.2s ease;
}

.iot-config-dropdown.open .chevron {
  transform: rotate(180deg);
}

.config-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  width: 320px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.dropdown-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.close-btn svg {
  width: 14px;
  height: 14px;
}

.dropdown-content {
  padding: 20px;
}

.config-form {
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.config-status {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-item.valid {
  color: #059669;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  transition: background-color 0.2s ease;
}

.status-item.valid .status-indicator {
  background: #10b981;
}

.config-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 11px;
}

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.btn svg {
  flex-shrink: 0;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}

/* 动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .config-dropdown {
    width: 280px;
    right: -20px;
  }
  
  .dropdown-header,
  .dropdown-content {
    padding: 16px;
  }
  
  .config-actions {
    flex-direction: column;
  }
  
  .config-actions .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>