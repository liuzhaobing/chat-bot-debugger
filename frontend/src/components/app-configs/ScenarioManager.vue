<template>
  <div class="scenario-manager">
    <div class="header-actions">
      <h3>场景管理</h3>
      <button class="add-btn" @click="openEditModal()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        新建场景
      </button>
    </div>
    
    <div class="scenarios-list" v-if="scenarios.length">
      <div v-for="scenario in scenarios" :key="scenario.id" class="scenario-item">
        <div class="scenario-info">
          <div class="scenario-name">{{ scenario.name }}</div>
          <div class="scenario-desc" v-if="scenario.description">{{ scenario.description }}</div>
        </div>
        <div class="scenario-actions">
          <button class="action-btn load-btn" @click="loadScenario(scenario)" title="加载此场景参数">
            加载
          </button>
          <button class="action-btn edit-btn" @click="openEditModal(scenario)" title="编辑">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          </button>
          <button class="action-btn delete-btn" @click="deleteScenario(scenario)" title="删除">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      暂无场景，点击新建添加
    </div>

    <!-- Edit/Create Modal -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
        <div class="scenario-modal">
          <div class="modal-header">
            <h3>{{ editingId ? '编辑场景' : '新建场景' }}</h3>
            <button class="close-btn" @click="showModal = false">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>场景名称</label>
              <input v-model="formData.name" placeholder="请输入场景名称" />
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="formData.description" placeholder="场景描述（可选）" rows="2"></textarea>
            </div>
            <div class="form-group">
              <div class="label-row">
                <label>参数配置 (YAML)</label>
                <div class="yaml-actions">
                   <span class="yaml-hint">支持 YAML 格式输入</span>
                </div>
              </div>
              <textarea 
                v-model="formData.yamlInput" 
                class="yaml-editor" 
                placeholder="请输入 YAML 格式的参数配置..."
                rows="10"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn cancel" @click="showModal = false">取消</button>
            <button class="btn save" @click="saveScenario">保存</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios'
import yaml from 'js-yaml'

export default {
  name: 'ScenarioManager',
  props: {
    appId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      scenarios: [],
      showModal: false,
      editingId: null,
      formData: {
        name: '',
        description: '',
        yamlInput: ''
      }
    }
  },
  mounted() {
    this.fetchScenarios()
  },
  methods: {
    async fetchScenarios() {
      try {
        const res = await axios.get('/api/scenarios/', {
          params: { app_id: this.appId }
        })
        this.scenarios = res.data
      } catch (e) {
        console.error('Failed to fetch scenarios', e)
      }
    },
    openEditModal(scenario = null) {
      if (scenario) {
        this.editingId = scenario.id
        this.formData.name = scenario.name
        this.formData.description = scenario.description
        try {
          this.formData.yamlInput = yaml.dump(scenario.parameters)
        } catch (e) {
          this.formData.yamlInput = ''
        }
      } else {
        this.editingId = null
        this.formData.name = ''
        this.formData.description = ''
        this.formData.yamlInput = ''
      }
      this.showModal = true
    },
    async saveScenario() {
      if (!this.formData.name.trim()) {
        window.$message.error('场景名称不能为空')
        return
      }

      let parameters = {}
      if (this.formData.yamlInput.trim()) {
        try {
          parameters = yaml.load(this.formData.yamlInput)
          if (typeof parameters !== 'object' || parameters === null) {
              throw new Error('YAML must parse to an object')
          }
        } catch (e) {
          window.$message.error('YAML 格式错误: ' + e.message)
          return
        }
      }

      const payload = {
        app: this.appId,
        name: this.formData.name,
        description: this.formData.description,
        parameters: parameters
      }

      try {
        if (this.editingId) {
          await axios.patch(`/api/scenarios/${this.editingId}/`, payload)
          window.$message.success('场景更新成功')
        } else {
          await axios.post('/api/scenarios/', payload)
          window.$message.success('场景创建成功')
        }
        this.showModal = false
        this.fetchScenarios()
      } catch (e) {
        window.$message.error('保存失败: ' + (e.response?.data?.message || e.message))
      }
    },
    async deleteScenario(scenario) {
      if (!await window.$confirm({
        title: '删除场景',
        message: `确定要删除场景 "${scenario.name}" 吗？`,
        type: 'warning'
      })) return

      try {
        await axios.delete(`/api/scenarios/${scenario.id}/`)
        window.$message.success('删除成功')
        this.fetchScenarios()
      } catch (e) {
        window.$message.error('删除失败')
      }
    },
    loadScenario(scenario) {
      this.$emit('load-scenario', scenario.parameters)
      window.$message.success(`已加载场景: ${scenario.name}`)
    }
  }
}
</script>

<style scoped>
.scenario-manager {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-actions h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background-color: #f0f7ff;
  color: #1a73e8;
  border: 1px solid rgba(26, 115, 232, 0.2);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.add-btn:hover {
  background-color: #e6f1fc;
}

.scenarios-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scenario-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #edf2f7;
  transition: all 0.2s;
}

.scenario-item:hover {
  border-color: #dbe4ef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.scenario-info {
  flex: 1;
  min-width: 0;
}

.scenario-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
  margin-bottom: 2px;
}

.scenario-desc {
  color: #666;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scenario-actions {
  display: flex;
  gap: 6px;
  margin-left: 10px;
}

.action-btn {
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background-color: #e9ecef;
  color: #333;
}

.load-btn {
  font-size: 12px;
  padding: 4px 8px;
  background: #e6fffa;
  color: #2c7a7b;
  font-weight: 500;
}

.load-btn:hover {
  background: #b2f5ea;
}

.delete-btn:hover {
  background-color: #ffe3e3;
  color: #e03131;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 13px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px dashed #dee2e6;
}

/* Modal Styles */
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
  backdrop-filter: blur(2px);
}

.scenario-modal {
  background: white;
  width: 90%;
  max-width: 600px;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #4a5568;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4299e1;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.yaml-hint {
  font-size: 12px;
  color: #718096;
}

.yaml-editor {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #2d3748;
  background-color: #f7fafc;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn.cancel {
  background: white;
  border: 1px solid #e2e8f0;
  color: #4a5568;
}

.btn.cancel:hover {
  background: #f7fafc;
}

.btn.save {
  background: #4299e1;
  color: white;
}

.btn.save:hover {
  background: #3182ce;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
