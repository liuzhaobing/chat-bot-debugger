<template>
  <div class="scene-test-panel">
    <!-- 主内容区域 - 使用过渡动画 -->
    <transition name="fade" mode="out-in">
      <!-- 聚合主页 - 4个角色合照 -->
      <div v-if="viewMode === 'group'" key="group" class="group-view">
        <div class="hero-showcase">
          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-state">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <p>加载中...</p>
          </div>

          <!-- 空状态 -->
          <div v-else-if="employees.length === 0" class="empty-state">
            <div class="empty-avatar">
              <Avatar3D animation-state="idle" size="hero" />
            </div>
            <p class="empty-title">还没有雇佣数字员工</p>
            <p class="empty-hint">点击下方按钮雇佣数字员工</p>
          </div>

          <!-- 4个角色合照 -->
          <EmployeeGroup
            v-else
            @select="handleSelectEmployee"
          />
        </div>

        <!-- 底部操作栏 -->
        <div v-if="!isLoading" class="bottom-info-bar group-info-bar">
          <!-- 操作按钮组 -->
          <div class="action-buttons">
            <!-- 雇佣数字员工 -->
            <button class="icon-btn" @click="showHireModal = true" title="雇佣数字员工">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <line x1="20" y1="8" x2="20" y2="14"></line>
                <line x1="23" y1="11" x2="17" y2="11"></line>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 单个角色页面 -->
      <div v-else key="single" class="single-view">
        <div class="hero-showcase">
          <!-- 返回按钮 -->
          <button class="back-btn" @click="backToGroup" title="返回列表">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            <span>返回</span>
          </button>

          <!-- 角色展示 -->
          <template v-if="currentEmployee">
            <!-- 左切换按钮 -->
            <button
              class="nav-btn nav-prev"
              :disabled="currentIndex === 0"
              @click="prevEmployee"
              title="上一个"
            >
              &lt;
            </button>

            <!-- 3D角色容器 -->
            <div class="hero-container">
              <transition :name="slideDirection" mode="out-in">
                <div :key="currentEmployee.id" class="hero-wrapper">
                  <Avatar3D
                    :animation-state="getAvatarState(currentTask?.status)"
                    :character-index="currentEmployee.avatar_index"
                    size="hero"
                  />
                </div>
              </transition>
            </div>

            <!-- 右切换按钮 -->
            <button
              class="nav-btn nav-next"
              :disabled="currentIndex === employees.length - 1"
              @click="nextEmployee"
              title="下一个"
            >
              &gt;
            </button>
          </template>
        </div>

        <!-- 底部信息栏 -->
        <div class="bottom-info-bar">
          <!-- 员工信息 -->
          <div v-if="currentEmployee" class="employee-info">
            <span class="employee-name">{{ currentEmployee.name }}</span>
            <span class="employee-voice">{{ currentEmployee.tts_voice?.name || '未配置音色' }}</span>
          </div>

          <!-- 操作按钮组 -->
          <div class="action-buttons">
            <!-- 派发任务 -->
            <button
              v-if="currentEmployee"
              class="icon-btn"
              @click="showDispatchModal = true"
              title="派发任务"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="18" x2="12" y2="12"></line>
                <line x1="9" y1="15" x2="15" y2="15"></line>
              </svg>
            </button>

            <!-- 启动/暂停 -->
            <button
              v-if="currentTask && currentTask.status === 'pending'"
              class="icon-btn"
              @click="startTask(currentTask)"
              title="启动任务"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
            </button>
            <button
              v-else-if="currentTask && currentTask.status === 'running'"
              class="icon-btn icon-btn-warning"
              @click="pauseTask(currentTask)"
              title="暂停任务"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
              </svg>
            </button>
            <button
              v-else-if="currentTask && currentTask.status === 'failed'"
              class="icon-btn"
              @click="retryTask(currentTask)"
              title="重试任务"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
              </svg>
            </button>

            <!-- 查看任务 -->
            <button class="icon-btn" @click="openTaskDrawer" title="查看任务">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </button>

            <!-- 试听音色 -->
            <button
              v-if="currentEmployee"
              class="icon-btn"
              :disabled="previewingVoiceId === currentEmployee?.tts_voice?.speaker"
              @click="previewVoice"
              title="试听音色"
            >
              <svg v-if="previewingVoiceId === currentEmployee?.tts_voice?.speaker" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 雇佣数字员工弹窗 -->
    <HireEmployeeModal
      :visible="showHireModal"
      :mode="'hire'"
      @close="showHireModal = false"
      @created="handleEmployeeCreated"
    />

    <!-- 派发任务弹窗 -->
    <HireEmployeeModal
      v-if="currentEmployee"
      :visible="showDispatchModal"
      :mode="'dispatch'"
      :employee="currentEmployee"
      @close="showDispatchModal = false"
      @created="handleTaskCreated"
    />

    <!-- 任务详情抽屉 -->
    <div v-if="showDrawer" class="drawer-overlay" @click="closeDrawer">
      <div class="drawer-content" @click.stop>
        <div class="drawer-header">
          <h3>任务详情</h3>
          <button class="close-btn" @click="closeDrawer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div v-if="currentTask" class="drawer-body">
          <div class="detail-section">
            <div class="detail-row">
              <span class="detail-label">任务ID:</span>
              <span class="detail-value">{{ currentTask.id }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">任务名称:</span>
              <span class="detail-value">{{ currentTask.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态:</span>
              <span class="detail-value">
                <span class="status-badge" :class="currentTask.status">
                  {{ getStatusText(currentTask.status) }}
                </span>
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">创建时间:</span>
              <span class="detail-value">{{ formatTime(currentTask.created_at) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">更新时间:</span>
              <span class="detail-value">{{ formatTime(currentTask.updated_at) }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>配置信息</h4>
            <div class="detail-row">
              <span class="detail-label">执行员工:</span>
              <span class="detail-value">{{ currentTask.employee?.name || '未配置' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">TTS音色:</span>
              <span class="detail-value">{{ currentTask.employee?.tts_voice?.name || currentTask.tts_voice?.display_name || '未配置' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">IOT协议:</span>
              <span class="detail-value">{{ currentTask.iot_protocol?.category || '未配置' }}</span>
            </div>
          </div>

          <div class="detail-section" v-if="currentTask.prd_content">
            <h4>PRD/需求描述</h4>
            <div class="prd-content">{{ currentTask.prd_content }}</div>
          </div>

          <div class="detail-section" v-if="currentTask.report_url">
            <h4>测试报告</h4>
            <div class="detail-row">
              <span class="detail-label">报告链接:</span>
              <a :href="currentTask.report_url" target="_blank" class="report-link">
                点击下载
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
import Avatar3D from './Avatar3D.vue'
import EmployeeGroup from './EmployeeGroup.vue'
import HireEmployeeModal from './HireEmployeeModal.vue'
import sceneTestService from '@/services/sceneTestService'

export default {
  name: 'SceneTestPanel',
  components: {
    Avatar3D,
    EmployeeGroup,
    HireEmployeeModal
  },
  data() {
    return {
      viewMode: 'group', // 'group' | 'single'
      employees: [],
      employeeTasks: {}, // 员工任务缓存
      isLoading: false,
      currentIndex: 0,
      slideDirection: 'slide-left',
      showHireModal: false,
      showDispatchModal: false,
      showDrawer: false,
      previewingVoiceId: null
    }
  },
  computed: {
    currentEmployee() {
      if (this.employees.length === 0) return null
      return this.employees[this.currentIndex] || null
    },
    currentTask() {
      if (!this.currentEmployee) return null
      const tasks = this.employeeTasks[this.currentEmployee.id] || []
      return tasks.length > 0 ? tasks[0] : null
    },
    pendingCount() {
      let count = 0
      for (const empId in this.employeeTasks) {
        const tasks = this.employeeTasks[empId] || []
        count += tasks.filter(t => t.status === 'pending').length
      }
      return count
    }
  },
  mounted() {
    this.loadEmployees()
  },
  methods: {
    async loadEmployees() {
      this.isLoading = true
      try {
        this.employees = await sceneTestService.getDigitalEmployees()
        // 加载每个员工的最近任务
        for (const employee of this.employees) {
          this.loadEmployeeTasks(employee.id)
        }
      } catch (error) {
        console.error('加载数字员工失败:', error)
        window.$message?.error('加载数字员工失败')
      } finally {
        this.isLoading = false
      }
    },
    async loadEmployeeTasks(employeeId) {
      try {
        const tasks = await sceneTestService.getEmployeeTasks(employeeId)
        this.$set(this.employeeTasks, employeeId, tasks)
      } catch (error) {
        console.error('加载员工任务失败:', error)
      }
    },
    handleSelectEmployee(avatarIndex) {
      // 从合照点击进入单个角色页面
      // 尝试找到匹配该 avatar_index 的员工
      const matchingIndex = this.employees.findIndex(emp => emp.avatar_index === avatarIndex)
      if (matchingIndex !== -1) {
        this.currentIndex = matchingIndex
      } else {
        // 如果没有匹配的，默认显示第一个员工
        this.currentIndex = 0
      }
      this.viewMode = 'single'
    },
    backToGroup() {
      // 返回聚合主页
      this.viewMode = 'group'
    },
    getAvatarState(status) {
      if (status === 'running') return 'working'
      if (status === 'failed') return 'error'
      return 'idle'
    },
    getStatusText(status) {
      const statusMap = {
        'pending': '待命',
        'running': '工作中',
        'completed': '已完成',
        'failed': '任务失败'
      }
      return statusMap[status] || status
    },
    formatTime(timeStr) {
      if (!timeStr) return '-'
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN')
    },
    prevEmployee() {
      if (this.currentIndex > 0) {
        this.slideDirection = 'slide-right'
        this.currentIndex--
      }
    },
    nextEmployee() {
      if (this.currentIndex < this.employees.length - 1) {
        this.slideDirection = 'slide-left'
        this.currentIndex++
      }
    },
    handleEmployeeCreated(employee) {
      this.employees.push(employee)
      this.currentIndex = this.employees.length - 1
      this.showHireModal = false
      // 创建后自动进入单个角色页面
      this.viewMode = 'single'
      window.$message?.success('数字员工已雇佣')
    },
    handleTaskCreated(task) {
      if (this.currentEmployee && task.employee?.id === this.currentEmployee.id) {
        if (!this.employeeTasks[this.currentEmployee.id]) {
          this.$set(this.employeeTasks, this.currentEmployee.id, [])
        }
        this.employeeTasks[this.currentEmployee.id].unshift(task)
      }
      this.showDispatchModal = false
      window.$message?.success('任务已派发')
    },
    async startTask(task) {
      try {
        await sceneTestService.startTestTask(task.id)
        // 更新本地任务状态
        const tasks = this.employeeTasks[this.currentEmployee.id] || []
        const index = tasks.findIndex(t => t.id === task.id)
        if (index !== -1) {
          tasks[index].status = 'running'
        }
        window.$message?.success('任务已启动')
      } catch (error) {
        console.error('启动任务失败:', error)
        window.$message?.error('启动任务失败')
      }
    },
    pauseTask(task) {
      console.log('暂停任务:', task)
      window.$message?.info('暂停功能开发中')
    },
    retryTask(task) {
      console.log('重试任务:', task)
      window.$message?.info('重试功能开发中')
    },
    openTaskDrawer() {
      this.showDrawer = true
    },
    closeDrawer() {
      this.showDrawer = false
    },
    async previewVoice() {
      if (!this.currentEmployee?.tts_voice?.speaker) return
      const speaker = this.currentEmployee.tts_voice.speaker
      if (this.previewingVoiceId === speaker) return

      this.previewingVoiceId = speaker
      try {
        const audioBase64 = await sceneTestService.previewTTS(
          speaker,
          '你好，我是你的AI助手'
        )
        const audioBytes = atob(audioBase64)
        const audioArray = new Uint8Array(audioBytes.length)
        for (let i = 0; i < audioBytes.length; i++) {
          audioArray[i] = audioBytes.charCodeAt(i)
        }
        const audioBlob = new Blob([audioArray], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)

        const audio = new Audio(audioUrl)
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl)
          this.previewingVoiceId = null
        }
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl)
          this.previewingVoiceId = null
        }
        await audio.play()
      } catch (error) {
        console.error('TTS试听失败:', error)
        window.$message?.error('TTS试听失败')
        this.previewingVoiceId = null
      }
    }
  }
}
</script>

<style scoped>
.scene-test-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 48px);
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e8eef5 100%);
  color: var(--text-secondary, #8b949e);
}

/* 页面切换过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

/* 3D角色展示主区域 */
.hero-showcase {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.02) 0%, transparent 50%, rgba(59, 130, 246, 0.01) 100%);
  min-height: 400px;
  overflow: hidden;
}

/* group view 填满整个区域 */
.group-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.group-view .hero-showcase {
  flex: 1;
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 20px;
  left: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border-color, #30363d);
  border-radius: 20px;
  background: var(--bg-secondary, #21262d);
  color: var(--text-secondary, #8b949e);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
}

.back-btn:hover {
  background: var(--bg-hover, #30363d);
  color: var(--text-primary, #f0f6fc);
  border-color: rgba(59, 130, 246, 0.3);
}

/* 切换按钮 - 纯文字样式 */
.nav-btn {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.2s ease;
  color: #666666;
  font-size: 26px;
  font-weight: 300;
  background: transparent;
  border: none;
  z-index: 10;
  padding: 0;
}

.nav-btn:hover:not(:disabled) {
  color: #333333;
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-prev {
  left: 40px;
}

.nav-next {
  right: 40px;
}

/* 角色容器 */
.hero-container {
  width: 60%;
  height: 90%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 切换动画 */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter {
  transform: translateX(100px);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-100px);
  opacity: 0;
}

.slide-right-enter {
  transform: translateX(-100px);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(100px);
  opacity: 0;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
}

.empty-avatar {
  opacity: 0.3;
}

.empty-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary, #8b949e);
}

.empty-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-tertiary, #6e7681);
}

/* 底部信息栏 */
.bottom-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px 24px;
  background: transparent;
}

.group-info-bar {
  justify-content: center;
}

.employee-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.employee-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
}

.employee-voice {
  font-size: 12px;
  color: var(--text-tertiary, #6e7681);
}

/* 状态标签 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
}

.status-badge.running {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  gap: 12px;
}

.icon-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #60a5fa;
}

.icon-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.5);
  color: #93c5fd;
  transform: translateY(-2px);
}

.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.icon-btn-warning {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.08);
  color: #fbbf24;
}

.icon-btn-warning:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.5);
  color: #fcd34d;
}

/* 抽屉样式 */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.drawer-content {
  width: 400px;
  max-width: 90vw;
  height: 100%;
  background: var(--bg-surface, #161b22);
  border-left: 1px solid var(--border-color, #30363d);
  display: flex;
  flex-direction: column;
  animation: drawer-slide-in 0.2s ease;
}

@keyframes drawer-slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #30363d);
}

.drawer-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary, #8b949e);
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--bg-hover, #30363d);
  color: var(--text-primary, #f0f6fc);
}

.drawer-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color, #30363d);
}

.detail-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  width: 80px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
}

.detail-value {
  flex: 1;
  font-size: 12px;
  color: var(--text-primary, #f0f6fc);
}

.prd-content {
  padding: 12px;
  background: var(--bg-primary, #0d1117);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-primary, #f0f6fc);
  line-height: 1.6;
  white-space: pre-wrap;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #3b82f6;
  text-decoration: none;
  font-size: 12px;
  transition: color 0.15s ease;
}

.report-link:hover {
  color: #60a5fa;
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

/* 响应式布局 */
@media (max-width: 900px) {
  .nav-prev { left: 16px; }
  .nav-next { right: 16px; }
  .hero-container { width: 70%; }
}

@media (max-width: 600px) {
  .nav-btn {
    font-size: 24px;
  }

  .hero-container { width: 80%; }

  .bottom-info-bar {
    padding: 12px 16px 20px;
    flex-direction: column;
    gap: 12px;
  }

  .employee-info {
    text-align: center;
  }

  .action-buttons {
    gap: 8px;
  }

  .icon-btn {
    width: 40px;
    height: 40px;
  }

  .back-btn {
    top: 12px;
    left: 12px;
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style>