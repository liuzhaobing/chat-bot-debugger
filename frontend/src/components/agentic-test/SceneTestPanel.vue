<template>
  <div class="scene-test-panel">
    <div class="test-section">
      <!-- 顶部工具栏 -->
      <div class="stats-filter-bar">
        <div class="stats-tags">
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
        <div class="header-actions">
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

      <!-- 测试任务列表 -->
      <div class="tasks-content">
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
/* 主题变量 - 与IOTConfigPanel保持一致 */
:root {
  --bg-surface: #161b22;
  --bg-primary: #0d1117;
  --bg-secondary: #21262d;
  --bg-hover: #30363d;
  --border-color: #30363d;
  --text-primary: #f0f6fc;
  --text-secondary: #8b949e;
  --text-tertiary: #6e7681;
  --accent-blue: #58a6ff;
  --accent-green: #3fb950;
  --accent-red: #f85149;
  --accent-yellow: #f59e0b;
}

.scene-test-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 48px);
  min-height: 0;
  overflow: hidden;
  background: var(--bg-primary);
  color: var(--text-secondary);
  padding: 20px;
}

/* 测试区域 - 与IOTConfigPanel的devices-section保持一致 */
.test-section {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  overflow: hidden;
}

/* 统计和筛选栏 - 与IOTConfigPanel保持一致 */
.stats-filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 16px;
  flex-wrap: wrap;
}

.stats-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  min-width: 80px;
}

.stat-item:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.stat-item.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.stat-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.stat-item.active .stat-label {
  color: rgba(255, 255, 255, 0.9);
}

.stat-value {
  font-weight: 700;
  font-size: 16px;
  color: var(--text-primary);
}

.stat-item.active .stat-value {
  color: white;
}

.stat-running .stat-value {
  color: var(--accent-green);
}

.stat-running.active .stat-value {
  color: white;
}

.stat-completed .stat-value {
  color: var(--accent-blue);
}

.stat-completed.active .stat-value {
  color: white;
}

.stat-failed .stat-value {
  color: var(--accent-red);
}

.stat-failed.active .stat-value {
  color: white;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* 测试任务列表 */
.tasks-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
  max-height: none;
}

/* 自定义滚动条样式 */
.tasks-content::-webkit-scrollbar {
  width: 8px;
}

.tasks-content::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 4px;
}

.tasks-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.tasks-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
  gap: 16px;
  text-align: center;
}

.empty-state svg,
.loading-state svg {
  opacity: 0.5;
  margin-bottom: 12px;
}

.empty-state p,
.loading-state p {
  margin: 0;
  font-size: 14px;
}

/* 任务表格 */
.tasks-table {
  background: var(--bg-primary);
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr 1fr 1.5fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.th {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.task-row {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr 1fr 1.5fr 1fr;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.2s ease;
  position: relative;
}

.task-row:hover {
  background: rgba(88, 166, 255, 0.05);
  border-left: 3px solid var(--accent-blue);
}

.task-row:last-child {
  border-bottom: none;
}

.task-row.running {
  border-left: 3px solid var(--accent-green);
  background: rgba(63, 185, 80, 0.02);
}

.task-row.completed {
  border-left: 3px solid var(--accent-blue);
  background: rgba(88, 166, 255, 0.02);
}

.task-row.failed {
  border-left: 3px solid var(--accent-red);
  background: rgba(248, 81, 73, 0.02);
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
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.task-id {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.status-badge .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.status-badge.pending {
  background: rgba(139, 148, 158, 0.15);
  color: var(--text-secondary);
  border: 1px solid rgba(139, 148, 158, 0.3);
}

.status-badge.running {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
  border: 1px solid rgba(63, 185, 80, 0.3);
}

.status-badge.running .status-dot {
  animation: pulse 1.5s infinite;
}

.status-badge.completed {
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent-blue);
  border: 1px solid rgba(88, 166, 255, 0.3);
}

.status-badge.failed {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
  border: 1px solid rgba(248, 81, 73, 0.3);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.prd-preview {
  color: var(--text-secondary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  line-height: 1.4;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.tag-tts {
  background: rgba(155, 89, 182, 0.15);
  color: #bb8fce;
  border-color: rgba(155, 89, 182, 0.3);
}

.tag-iot {
  background: rgba(52, 152, 219, 0.15);
  color: #85c1e9;
  border-color: rgba(52, 152, 219, 0.3);
}

.tag-empty {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  border-color: var(--border-color);
}

.td-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.action-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  color: var(--text-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn-danger:hover {
  background: rgba(248, 81, 73, 0.2);
  border-color: var(--accent-red);
  color: var(--accent-red);
  box-shadow: 0 2px 4px rgba(248, 81, 73, 0.2);
}

.action-btn svg {
  transition: transform 0.2s ease;
}

.action-btn:hover svg {
  transform: scale(1.1);
}

/* 按钮样式 - 与IOTConfigPanel保持一致 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-primary);
  color: var(--text-primary);
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
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn-outline:hover:not(:disabled) {
  border-color: var(--text-secondary);
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 弹窗样式 - 与IOTConfigPanel保持一致 */
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
  padding: 20px;
}

.modal-content {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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

.close-btn {
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

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* 表单样式 - 与IOTConfigPanel保持一致 */
.form-group {
  margin-bottom: 20px;
  width: 100%;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group label .required {
  color: var(--accent-red);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s ease;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--text-tertiary);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.tts-selector {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.tts-select {
  flex: 1;
  min-width: 200px;
}

/* 详情弹窗 */
.detail-modal {
  max-width: 500px;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
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
  color: var(--text-primary);
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-value {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
}

.prd-content {
  padding: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--accent-blue);
  text-decoration: none;
  transition: text-decoration 0.2s ease;
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
