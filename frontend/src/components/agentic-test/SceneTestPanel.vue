<template>
  <div class="scene-test-panel">
    <!-- 顶部工具栏 -->
    <div class="panel-header">
      <div class="header-left">
        <h2 class="panel-title">场景测试</h2>
        <span class="panel-subtitle">测试任务管理与报告</span>
      </div>
      <div class="header-right">
        <button 
          class="btn btn-primary"
          @click="showCreateModal = true"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          创建测试任务
        </button>
      </div>
    </div>

    <!-- 统计栏 -->
    <div class="stats-bar">
      <div class="stat-item" :class="{ active: filterStatus === 'all' }" @click="filterStatus = 'all'">
        <span class="stat-label">全部任务</span>
        <span class="stat-value">{{ testTasks.length }}</span>
      </div>
      <div class="stat-item stat-running" :class="{ active: filterStatus === 'running' }" @click="filterStatus = 'running'">
        <span class="stat-label">运行中</span>
        <span class="stat-value">{{ runningCount }}</span>
      </div>
      <div class="stat-item stat-completed" :class="{ active: filterStatus === 'completed' }" @click="filterStatus = 'completed'">
        <span class="stat-label">已完成</span>
        <span class="stat-value">{{ completedCount }}</span>
      </div>
      <div class="stat-item stat-failed" :class="{ active: filterStatus === 'failed' }" @click="filterStatus = 'failed'">
        <span class="stat-label">失败</span>
        <span class="stat-value">{{ failedCount }}</span>
      </div>
    </div>

    <!-- 测试任务列表 -->
    <div class="tasks-container">
      <div v-if="isLoading" class="loading-state">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <p>加载中...</p>
      </div>

      <div v-else-if="filteredTasks.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 11l3 3L22 4"></path>
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
        </svg>
        <p>{{ filterStatus === 'all' ? '暂无测试任务，点击上方按钮创建' : '没有符合条件的任务' }}</p>
      </div>

      <div v-else class="tasks-table">
        <div class="table-header">
          <div class="th th-name">任务名称</div>
          <div class="th th-status">状态</div>
          <div class="th th-prd">PRD/需求</div>
          <div class="th th-tts">TTS音色</div>
          <div class="th th-iot">IOT协议</div>
          <div class="th th-time">创建时间</div>
          <div class="th th-actions">操作</div>
        </div>
        
        <div class="table-body">
          <div 
            v-for="task in filteredTasks" 
            :key="task.id"
            class="task-row"
            :class="{ 
              running: task.status === 'running',
              completed: task.status === 'completed',
              failed: task.status === 'failed'
            }"
          >
            <div class="td td-name">
              <div class="task-name">{{ task.name }}</div>
              <div class="task-id">ID: {{ task.id.slice(0, 8) }}</div>
            </div>
            <div class="td td-status">
              <span class="status-badge" :class="task.status">
                <span class="status-dot"></span>
                {{ getStatusText(task.status) }}
              </span>
            </div>
            <div class="td td-prd">
              <div class="prd-preview" :title="task.prd_content">
                {{ task.prd_content ? task.prd_content.slice(0, 30) + '...' : '未配置' }}
              </div>
            </div>
            <div class="td td-tts">
              <span v-if="task.tts_voice" class="tag tag-tts">
                {{ task.tts_voice.display_name || task.tts_voice.speaker }}
              </span>
              <span v-else class="tag tag-empty">未配置</span>
            </div>
            <div class="td td-iot">
              <span v-if="task.iot_protocol" class="tag tag-iot">
                {{ task.iot_protocol.category }}
              </span>
              <span v-else class="tag tag-empty">未配置</span>
            </div>
            <div class="td td-time">
              {{ formatTime(task.created_at) }}
            </div>
            <div class="td td-actions">
              <button 
                v-if="task.status === 'completed' && task.report_url"
                class="action-btn"
                @click="downloadReport(task)"
                title="下载测试报告"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
              </button>
              <button 
                class="action-btn"
                @click="viewTaskDetail(task)"
                title="查看详情"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </button>
              <button 
                class="action-btn action-btn-danger"
                @click="deleteTask(task)"
                title="删除任务"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="m19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建测试任务弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal-content create-task-modal" @click.stop>
        <div class="modal-header">
          <h3>创建测试任务</h3>
          <button class="close-btn" @click="showCreateModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <!-- 任务名称 -->
          <div class="form-group">
            <label>任务名称 <span class="required">*</span></label>
            <input 
              v-model="newTask.name"
              type="text"
              placeholder="请输入测试任务名称..."
            />
          </div>

          <!-- PRD/需求输入 -->
          <div class="form-group">
            <label>产品PRD或需求描述</label>
            <textarea 
              v-model="newTask.prd_content"
              rows="4"
              placeholder="请输入产品PRD文档内容或一句话需求描述..."
            ></textarea>
          </div>

          <!-- TTS音色选择 -->
          <div class="form-group">
            <label>TTS音色选择</label>
            <div class="tts-selector">
              <select v-model="newTask.tts_voice_id" class="tts-select">
                <option value="">请选择TTS音色</option>
                <option v-for="voice in ttsVoices" :key="voice.id" :value="voice.id">
                  {{ voice.display_name || voice.speaker }}
                </option>
              </select>
              <button 
                class="btn btn-outline btn-sm"
                @click="previewTTS"
                :disabled="!newTask.tts_voice_id || isPreviewing"
              >
                <svg v-if="isPreviewing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                  <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                {{ isPreviewing ? '试听中...' : '试听' }}
              </button>
            </div>
            <p class="form-hint">试听文本："你好，我是你的烹饪伙伴食神"</p>
          </div>

          <!-- IOT设备协议选择 -->
          <div class="form-group">
            <label>IOT设备协议</label>
            <select v-model="newTask.iot_protocol_id" class="protocol-select">
              <option value="">请选择设备协议</option>
              <option v-for="protocol in deviceProtocols" :key="protocol.id" :value="protocol.id">
                {{ protocol.category }} - {{ protocol.id }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateModal = false">取消</button>
          <button 
            class="btn btn-primary"
            @click="createTask"
            :disabled="!canCreate || isCreating"
          >
            <svg v-if="isCreating" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            {{ isCreating ? '创建中...' : '创建任务' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
      <div class="modal-content detail-modal" @click.stop>
        <div class="modal-header">
          <h3>任务详情</h3>
          <button class="close-btn" @click="showDetailModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div v-if="selectedTask" class="modal-body">
          <div class="detail-section">
            <div class="detail-row">
              <span class="detail-label">任务ID:</span>
              <span class="detail-value">{{ selectedTask.id }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">任务名称:</span>
              <span class="detail-value">{{ selectedTask.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态:</span>
              <span class="detail-value">
                <span class="status-badge" :class="selectedTask.status">
                  {{ getStatusText(selectedTask.status) }}
                </span>
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">创建时间:</span>
              <span class="detail-value">{{ formatTime(selectedTask.created_at) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">更新时间:</span>
              <span class="detail-value">{{ formatTime(selectedTask.updated_at) }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>配置信息</h4>
            <div class="detail-row">
              <span class="detail-label">TTS音色:</span>
              <span class="detail-value">{{ selectedTask.tts_voice?.display_name || '未配置' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">IOT协议:</span>
              <span class="detail-value">{{ selectedTask.iot_protocol?.category || '未配置' }}</span>
            </div>
          </div>

          <div class="detail-section" v-if="selectedTask.prd_content">
            <h4>PRD/需求描述</h4>
            <div class="prd-content">{{ selectedTask.prd_content }}</div>
          </div>

          <div class="detail-section" v-if="selectedTask.report_url">
            <h4>测试报告</h4>
            <div class="detail-row">
              <span class="detail-label">报告链接:</span>
              <a :href="selectedTask.report_url" target="_blank" class="report-link">
                点击下载
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import sceneTestService from '@/services/sceneTestService'

export default {
  name: 'SceneTestPanel',
  data() {
    return {
      testTasks: [],
      isLoading: false,
      filterStatus: 'all',
      showCreateModal: false,
      showDetailModal: false,
      selectedTask: null,
      isCreating: false,
      isPreviewing: false,
      ttsVoices: [],
      deviceProtocols: [],
      newTask: {
        name: '',
        prd_content: '',
        tts_voice_id: '',
        iot_protocol_id: ''
      }
    }
  },
  computed: {
    filteredTasks() {
      if (this.filterStatus === 'all') {
        return this.testTasks
      }
      return this.testTasks.filter(task => task.status === this.filterStatus)
    },
    runningCount() {
      return this.testTasks.filter(t => t.status === 'running').length
    },
    completedCount() {
      return this.testTasks.filter(t => t.status === 'completed').length
    },
    failedCount() {
      return this.testTasks.filter(t => t.status === 'failed').length
    },
    canCreate() {
      return this.newTask.name.trim().length > 0
    }
  },
  mounted() {
    this.loadTasks()
    this.loadTTSVoices()
    this.loadDeviceProtocols()
  },
  methods: {
    async loadTasks() {
      this.isLoading = true
      try {
        this.testTasks = await sceneTestService.getTestTasks()
      } catch (error) {
        console.error('加载测试任务失败:', error)
        this.$message?.error?.('加载测试任务失败') || alert('加载测试任务失败')
      } finally {
        this.isLoading = false
      }
    },
    async loadTTSVoices() {
      try {
        this.ttsVoices = await sceneTestService.getTTSVoices()
      } catch (error) {
        console.error('加载TTS音色失败:', error)
      }
    },
    async loadDeviceProtocols() {
      try {
        this.deviceProtocols = await sceneTestService.getDeviceProtocols()
      } catch (error) {
        console.error('加载设备协议失败:', error)
      }
    },
    async createTask() {
      this.isCreating = true
      try {
        const task = await sceneTestService.createTestTask({
          name: this.newTask.name,
          prd_content: this.newTask.prd_content,
          tts_voice_id: this.newTask.tts_voice_id || null,
          iot_protocol_id: this.newTask.iot_protocol_id || null
        })
        this.testTasks.unshift(task)
        this.showCreateModal = false
        this.resetNewTask()
        this.$message?.success?.('测试任务创建成功') || alert('测试任务创建成功')
      } catch (error) {
        console.error('创建测试任务失败:', error)
        this.$message?.error?.('创建测试任务失败') || alert('创建测试任务失败')
      } finally {
        this.isCreating = false
      }
    },
    async previewTTS() {
      if (!this.newTask.tts_voice_id) return
      
      this.isPreviewing = true
      try {
        const audioUrl = await sceneTestService.previewTTS(
          this.newTask.tts_voice_id,
          '你好，我是你的烹饪伙伴食神'
        )
        const audio = new Audio(audioUrl)
        audio.play()
      } catch (error) {
        console.error('TTS试听失败:', error)
        this.$message?.error?.('TTS试听失败') || alert('TTS试听失败')
      } finally {
        this.isPreviewing = false
      }
    },
    async deleteTask(task) {
      if (!confirm(`确定要删除任务 "${task.name}" 吗？`)) return
      
      try {
        await sceneTestService.deleteTestTask(task.id)
        this.testTasks = this.testTasks.filter(t => t.id !== task.id)
        this.$message?.success?.('任务已删除') || alert('任务已删除')
      } catch (error) {
        console.error('删除任务失败:', error)
        this.$message?.error?.('删除任务失败') || alert('删除任务失败')
      }
    },
    downloadReport(task) {
      if (task.report_url) {
        window.open(task.report_url, '_blank')
      }
    },
    viewTaskDetail(task) {
      this.selectedTask = task
      this.showDetailModal = true
    },
    resetNewTask() {
      this.newTask = {
        name: '',
        prd_content: '',
        tts_voice_id: '',
        iot_protocol_id: ''
      }
    },
    getStatusText(status) {
      const statusMap = {
        'pending': '待执行',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败'
      }
      return statusMap[status] || status
    },
    formatTime(timeStr) {
      if (!timeStr) return '-'
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.scene-test-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0d1117;
  color: #c9d1d9;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #30363d;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #f0f6fc;
  margin: 0;
}

.panel-subtitle {
  font-size: 13px;
  color: #8b949e;
}

.stats-bar {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #30363d;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 24px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}

.stat-item:hover {
  border-color: #58a6ff;
}

.stat-item.active {
  border-color: #58a6ff;
  background: rgba(88, 166, 255, 0.1);
}

.stat-label {
  font-size: 12px;
  color: #8b949e;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #f0f6fc;
}

.stat-running.active .stat-value,
.stat-running:hover .stat-value {
  color: #3fb950;
}

.stat-completed.active .stat-value,
.stat-completed:hover .stat-value {
  color: #58a6ff;
}

.stat-failed.active .stat-value,
.stat-failed:hover .stat-value {
  color: #f85149;
}

.tasks-container {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8b949e;
  gap: 16px;
}

.empty-state svg {
  opacity: 0.5;
}

.tasks-table {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr 1fr 1.5fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  background: #21262d;
  border-bottom: 1px solid #30363d;
}

.th {
  font-size: 12px;
  font-weight: 600;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-body {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.task-row {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr 1fr 1.5fr 1fr;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #30363d;
  transition: background 0.2s;
}

.task-row:hover {
  background: rgba(88, 166, 255, 0.05);
}

.task-row:last-child {
  border-bottom: none;
}

.td {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.td-name {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.task-name {
  font-weight: 500;
  color: #f0f6fc;
}

.task-id {
  font-size: 11px;
  color: #6e7681;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #21262d;
  color: #8b949e;
}

.status-badge .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-badge.pending {
  background: rgba(139, 148, 158, 0.15);
  color: #8b949e;
}

.status-badge.running {
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
}

.status-badge.running .status-dot {
  animation: pulse 1.5s infinite;
}

.status-badge.completed {
  background: rgba(88, 166, 255, 0.15);
  color: #58a6ff;
}

.status-badge.failed {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.prd-preview {
  color: #8b949e;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.tag-tts {
  background: rgba(155, 89, 182, 0.15);
  color: #bb8fce;
}

.tag-iot {
  background: rgba(52, 152, 219, 0.15);
  color: #85c1e9;
}

.tag-empty {
  background: #21262d;
  color: #6e7681;
}

.td-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: #21262d;
  color: #8b949e;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #30363d;
  color: #f0f6fc;
}

.action-btn-danger:hover {
  background: rgba(248, 81, 73, 0.2);
  color: #f85149;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn svg {
  flex-shrink: 0;
}

.btn-primary {
  background: #238636;
  border-color: #238636;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #2ea043;
  border-color: #2ea043;
}

.btn-outline {
  background: transparent;
  border-color: #30363d;
  color: #c9d1d9;
}

.btn-outline:hover:not(:disabled) {
  border-color: #8b949e;
  background: #21262d;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #30363d;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #f0f6fc;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #8b949e;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #30363d;
  color: #f0f6fc;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #30363d;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #c9d1d9;
}

.form-group label .required {
  color: #f85149;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #f0f6fc;
  font-size: 13px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #58a6ff;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #6e7681;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #6e7681;
}

.tts-selector {
  display: flex;
  gap: 12px;
}

.tts-select {
  flex: 1;
}

/* 详情弹窗 */
.detail-modal {
  max-width: 500px;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #30363d;
}

.detail-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #f0f6fc;
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 13px;
  color: #8b949e;
}

.detail-value {
  flex: 1;
  font-size: 13px;
  color: #c9d1d9;
}

.prd-content {
  padding: 12px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-size: 13px;
  color: #c9d1d9;
  line-height: 1.6;
  white-space: pre-wrap;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #58a6ff;
  text-decoration: none;
}

.report-link:hover {
  text-decoration: underline;
}

/* 动画 */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
