<template>
  <div class="scenario-panel">
    <div class="panel-header">
      <h3>场景选择</h3>
      <button class="btn-new" @click="showCreateModal = true">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        新建场景
      </button>
    </div>

    <div class="panel-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="scenarios.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="7" height="7" rx="1"></rect>
          <rect x="14" y="3" width="7" height="7" rx="1"></rect>
          <rect x="14" y="14" width="7" height="7" rx="1"></rect>
          <rect x="3" y="14" width="7" height="7" rx="1"></rect>
        </svg>
        <p>暂无场景</p>
        <span>点击上方按钮创建第一个场景</span>
      </div>

      <div v-else class="scenario-list">
        <div 
          v-for="scenario in scenarios" 
          :key="scenario.id" 
          class="scenario-item"
          :class="{ active: selectedScenario?.id === scenario.id }"
        >
          <div class="scenario-info">
            <h4>{{ scenario.name }}</h4>
            <p>{{ scenario.description || '暂无描述' }}</p>
            <div class="scenario-meta">
              <span class="time">{{ formatTime(scenario.updated_at) }}</span>
            </div>
          </div>
          <div class="scenario-actions">
            <button 
              class="btn-action btn-view" 
              @click="viewScenario(scenario)"
              title="查看详情"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
            <button 
              class="btn-action btn-edit" 
              @click="editScenario(scenario)"
              title="编辑场景"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button 
              class="btn-action btn-test" 
              @click="testScenario(scenario)"
              :disabled="testing"
              title="执行测试"
            >
              <svg v-if="!testing" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              <div v-else class="spinner-small"></div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑场景模态框 -->
    <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ showCreateModal ? '新建场景' : '编辑场景' }}</h3>
          <button class="btn-close" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>场景名称</label>
            <input 
              v-model="formData.name" 
              type="text" 
              placeholder="请输入场景名称"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>场景描述</label>
            <textarea 
              v-model="formData.description" 
              placeholder="请输入场景描述"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
          <div class="form-group">
            <label>场景参数</label>
            <textarea 
              ref="parametersTextarea"
              v-model="parametersText" 
              placeholder="请输入YAML格式的场景参数"
              class="form-textarea auto-resize"
              :class="{ 'error': yamlError }"
              rows="6"
              @input="handleParametersInput"
            ></textarea>
            <div v-if="yamlError" class="form-error">
              {{ yamlError }}
            </div>
            <div v-else class="form-hint">
              请输入有效的YAML格式，例如：<br>
              target: 需要达成的目标<br>
              first_input: 首轮query<br>
              role_features: 用户个性特征<br>
              conditions: 用户家的情况<br>
              end_rule: 结束规则
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-save" @click="saveScenario" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 查看场景详情模态框 -->
    <div v-if="showViewModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>场景详情</h3>
          <button class="btn-close" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-group">
            <label>场景名称</label>
            <div class="detail-value">{{ viewingScenario?.name }}</div>
          </div>
          <div class="detail-group">
            <label>场景描述</label>
            <div class="detail-value">{{ viewingScenario?.description || '暂无描述' }}</div>
          </div>
          <div class="detail-group">
            <label>场景参数</label>
            <pre class="detail-yaml">{{ formatYAML(viewingScenario?.parameters) }}</pre>
          </div>
          <div class="detail-group">
            <label>创建时间</label>
            <div class="detail-value">{{ formatTime(viewingScenario?.created_at) }}</div>
          </div>
          <div class="detail-group">
            <label>更新时间</label>
            <div class="detail-value">{{ formatTime(viewingScenario?.updated_at) }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import yaml from 'js-yaml'

export default {
  name: 'ScenarioPanel',
  props: {
    testing: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      // 固定的app-id
      appId: '37ccee2a148f46199061c955fa70f9b7',
      
      // 场景列表
      scenarios: [],
      selectedScenario: null,
      loading: false,
      
      // 模态框状态
      showCreateModal: false,
      showEditModal: false,
      showViewModal: false,
      
      // 表单数据
      formData: {
        name: '',
        description: '',
        parameters: {}
      },
      parametersText: '',
      saving: false,
      
      // 查看详情
      viewingScenario: null,
      editingScenario: null,
      
      // YAML 校验
      yamlError: null
    }
  },
  mounted() {
    this.loadScenarios()
  },
  methods: {
    async loadScenarios() {
      this.loading = true
      try {
        const response = await axios.get('/api/scenarios/', {
          params: { app_id: this.appId }
        })
        this.scenarios = response.data.results || response.data
      } catch (error) {
        console.error('加载场景失败:', error)
        this.$emit('error', '加载场景失败')
      } finally {
        this.loading = false
      }
    },

    viewScenario(scenario) {
      this.viewingScenario = scenario
      this.showViewModal = true
    },

    editScenario(scenario) {
      this.editingScenario = scenario
      this.formData = {
        name: scenario.name,
        description: scenario.description || '',
        parameters: scenario.parameters || {}
      }
      this.parametersText = this.formatYAML(scenario.parameters || {})
      this.yamlError = null
      this.showEditModal = true
      // 延迟执行自动缩放，确保DOM已更新
      this.$nextTick(() => {
        setTimeout(() => {
          this.autoResizeTextarea()
        }, 100)
      })
    },

    testScenario(scenario) {
      this.selectedScenario = scenario
      this.$emit('test-scenario', scenario)
    },

    async saveScenario() {
      if (!this.formData.name.trim()) {
        alert('请输入场景名称')
        return
      }

      // 验证YAML格式
      if (this.yamlError) {
        alert('请修正YAML格式错误后再保存')
        return
      }

      // 验证参数YAML格式
      let parameters = {}
      if (this.parametersText.trim()) {
        try {
          parameters = yaml.load(this.parametersText) || {}
        } catch (error) {
          this.yamlError = `YAML格式错误: ${error.message}`
          alert('场景参数格式错误，请输入有效的YAML格式')
          return
        }
      }

      this.saving = true
      try {
        const data = {
          app: this.appId,
          name: this.formData.name,
          description: this.formData.description,
          parameters: parameters
        }

        if (this.showEditModal && this.editingScenario) {
          // 编辑场景
          await axios.put(`/api/scenarios/${this.editingScenario.id}/`, data)
        } else {
          // 创建场景
          await axios.post('/api/scenarios/', data)
        }

        await this.loadScenarios()
        this.closeModal()
      } catch (error) {
        console.error('保存场景失败:', error)
        alert('保存场景失败')
      } finally {
        this.saving = false
      }
    },

    closeModal() {
      this.showCreateModal = false
      this.showEditModal = false
      this.showViewModal = false
      this.formData = { name: '', description: '', parameters: {} }
      this.parametersText = ''
      this.viewingScenario = null
      this.editingScenario = null
      this.yamlError = null
    },

    validateYaml() {
      if (!this.parametersText.trim()) {
        this.yamlError = null
        return
      }

      try {
        const parsed = yaml.load(this.parametersText)
        // 检查解析结果是否为对象
        if (parsed !== null && typeof parsed !== 'object') {
          this.yamlError = 'YAML内容必须是一个对象'
          return
        }
        this.yamlError = null
      } catch (error) {
        this.yamlError = `YAML格式错误: ${error.message}`
      }
    },

    handleParametersInput() {
      this.validateYaml()
      this.autoResizeTextarea()
    },

    autoResizeTextarea() {
      this.$nextTick(() => {
        const textarea = this.$refs.parametersTextarea
        if (textarea) {
          // 重置高度以获取正确的scrollHeight
          textarea.style.height = 'auto'
          // 设置最小高度（6行）和最大高度（20行）
          const minHeight = 6 * 24 // 6行 * 行高24px
          const maxHeight = 20 * 24 // 20行 * 行高24px
          const scrollHeight = textarea.scrollHeight
          
          if (scrollHeight > minHeight) {
            textarea.style.height = Math.min(scrollHeight, maxHeight) + 'px'
          } else {
            textarea.style.height = minHeight + 'px'
          }
        }
      })
    },

    formatTime(timeStr) {
      if (!timeStr) return ''
      return new Date(timeStr).toLocaleString('zh-CN')
    },

    formatYAML(obj) {
      if (!obj || Object.keys(obj).length === 0) return ''
      try {
        return yaml.dump(obj, {
          indent: 2,
          lineWidth: -1,
          noRefs: true,
          sortKeys: false
        })
      } catch (error) {
        console.error('YAML格式化失败:', error)
        return JSON.stringify(obj, null, 2)
      }
    },

    formatJSON(obj) {
      if (!obj) return '{}'
      return JSON.stringify(obj, null, 2)
    }
  }
}
</script>

<style scoped>
<style scoped>
<style scoped>
.scenario-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-new {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-secondary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
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

.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scenario-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.scenario-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.scenario-item.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.scenario-info {
  flex: 1;
  min-width: 0;
}

.scenario-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scenario-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scenario-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scenario-meta .time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.scenario-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 16px;
}

.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-view {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.btn-view:hover {
  background: #3b82f6;
  color: white;
}

.btn-edit {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.btn-edit:hover {
  background: #f59e0b;
  color: white;
}

.btn-test {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.btn-test:hover:not(:disabled) {
  background: #10b981;
  color: white;
}

.btn-test:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
  background: var(--bg-primary);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-input.error,
.form-textarea.error {
  border-color: #ef4444;
  background-color: #fef2f2;
}

.form-textarea {
  resize: vertical;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #64748b; /* 调整字体颜色为更淡的颜色 */
  line-height: 24px; /* 设置固定行高用于计算 */
}

.form-textarea.auto-resize {
  resize: none; /* 禁用手动拖拽调整大小 */
  overflow-y: auto; /* 当内容超过最大高度时显示滚动条 */
  transition: height 0.2s ease; /* 添加高度变化的过渡动画 */
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-error {
  margin-top: 6px;
  font-size: 12px;
  color: #ef4444;
  background-color: #fef2f2;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #fecaca;
}

.detail-group {
  margin-bottom: 20px;
}

.detail-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.detail-value {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.detail-yaml {
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  white-space: pre-wrap;
  overflow-x: auto;
  margin: 0;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.btn-cancel,
.btn-save {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: var(--bg-hover, #f3f4f6);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: var(--border-color);
}

.btn-save {
  background: #3b82f6;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #2563eb;
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
