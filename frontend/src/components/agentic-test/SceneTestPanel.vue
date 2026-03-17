<template>
  <div class="scene-test-panel">
    <!-- 主内容区域 - 使用过渡动画 -->
    <transition name="fade" mode="out-in">
      <!-- 聚合主页 - 4个角色合照 -->
      <div v-if="viewMode === 'group'" key="group" class="group-view">
        <!-- 右上角新增按钮 -->
        <button class="add-employee-btn" @click="showHireModal = true" title="雇佣数字员工">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
        </button>

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
            <p class="empty-hint">点击右上角按钮雇佣数字员工</p>
          </div>

          <!-- 4个角色合照 -->
          <EmployeeGroup
            v-else
            @select="handleSelectEmployee"
          />
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
          <!-- 员工信息卡片 -->
          <div v-if="currentEmployee" class="employee-card">
            <div class="employee-avatar">
              <span class="avatar-letter">{{ currentEmployee.name?.charAt(0) || 'D' }}</span>
            </div>
            <div class="employee-details">
              <span class="employee-name">{{ currentEmployee.name }}</span>
              <span class="employee-voice">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                </svg>
                {{ currentEmployee.tts_voice?.name || '未配置音色' }}
              </span>
            </div>
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

            <!-- 重试任务（失败时显示） -->
            <button
              v-if="currentTask && currentTask.status === 'failed'"
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
      @task-created-and-start="handleTaskCreatedAndStart"
    />

    <!-- 派发任务弹窗 -->
    <HireEmployeeModal
      v-if="currentEmployee"
      :visible="showDispatchModal"
      :mode="'dispatch'"
      :employee="currentEmployee"
      @close="showDispatchModal = false"
      @task-created-and-start="handleTaskCreatedAndStart"
    />

    <!-- 任务详情抽屉 -->
    <div v-if="showDrawer" class="drawer-overlay" @click="closeDrawer">
      <div class="drawer-content task-drawer" @click.stop>
        <div class="drawer-header">
          <h3>{{ currentEmployee?.name }} 的任务列表</h3>
          <button class="close-btn" @click="closeDrawer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="drawer-body">
          <!-- 任务列表 -->
          <div class="task-list-section">
            <div v-if="employeeTasksList.length === 0" class="empty-tasks">
              <p>暂无任务</p>
            </div>
            <div v-else class="task-list">
              <div
                v-for="task in employeeTasksList"
                :key="task.id"
                class="task-item"
                :class="{ active: selectedTask?.id === task.id }"
                @click="selectTask(task)"
              >
                <div class="task-header">
                  <span class="task-name">{{ task.name }}</span>
                  <span class="task-status" :class="task.status">
                    {{ getStatusText(task.status) }}
                  </span>
                </div>
                <div class="task-meta">
                  <span>{{ formatTime(task.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 选中任务的详情 -->
          <div v-if="selectedTask" class="task-detail">
            <h4>任务详情</h4>
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
                <span class="detail-label">执行员工:</span>
                <span class="detail-value">{{ selectedTask.employee?.name || '未配置' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">TTS音色:</span>
                <span class="detail-value">{{ selectedTask.employee?.tts_voice?.name || selectedTask.tts_voice?.display_name || '未配置' }}</span>
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

            <div class="detail-section" v-if="selectedTask.report_url || selectedTask.report_data">
              <h4>测试报告</h4>

              <!-- 报告概要统计 -->
              <div v-if="selectedTask.report_data?.case_statistics" class="report-summary">
                <div class="summary-stat">
                  <span class="stat-num">{{ selectedTask.report_data.case_statistics.total || 0 }}</span>
                  <span class="stat-label">总用例</span>
                </div>
                <div class="summary-stat passed">
                  <span class="stat-num">{{ selectedTask.report_data.case_statistics.passed || 0 }}</span>
                  <span class="stat-label">通过</span>
                </div>
                <div class="summary-stat failed">
                  <span class="stat-num">{{ selectedTask.report_data.case_statistics.failed || 0 }}</span>
                  <span class="stat-label">失败</span>
                </div>
                <div class="summary-stat rate">
                  <span class="stat-num">{{ selectedTask.report_data.case_statistics.pass_rate || 0 }}%</span>
                  <span class="stat-label">通过率</span>
                </div>
              </div>

              <!-- 查看详细报告按钮 -->
              <button class="view-report-btn" @click="openReportPanel">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                查看详细报告
              </button>

              <!-- 报告链接（如果有外部链接） -->
              <div v-if="selectedTask.report_url" class="detail-row">
                <span class="detail-label">报告链接:</span>
                <a :href="selectedTask.report_url" target="_blank" class="report-link">
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

    <!-- 测试报告弹窗 -->
    <div v-if="showReportPanel" class="report-overlay" @click="closeReportPanel">
      <div class="report-drawer" @click.stop>
        <TestReportPanel
          :report-data="reportData"
          :loading="reportLoading"
          @close="closeReportPanel"
        />
      </div>
    </div>

  </div>
</template>

<script>
import Avatar3D from './Avatar3D.vue'
import EmployeeGroup from './EmployeeGroup.vue'
import HireEmployeeModal from './HireEmployeeModal.vue'
import TestReportPanel from './TestReportPanel.vue'
import sceneTestService from '@/services/sceneTestService'

export default {
  name: 'SceneTestPanel',
  components: {
    Avatar3D,
    EmployeeGroup,
    HireEmployeeModal,
    TestReportPanel
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
      previewingVoiceId: null,
      selectedTask: null,  // 选中的任务（用于任务列表抽屉）
      // 测试报告相关
      showReportPanel: false,
      reportData: null,
      reportLoading: false
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
    employeeTasksList() {
      if (!this.currentEmployee) return []
      return this.employeeTasks[this.currentEmployee.id] || []
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
        'failed': '任务失败',
        'stopped': '已停止'
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
      // 旧的事件处理，保留向后兼容
      if (this.currentEmployee && task.employee?.id === this.currentEmployee.id) {
        if (!this.employeeTasks[this.currentEmployee.id]) {
          this.$set(this.employeeTasks, this.currentEmployee.id, [])
        }
        this.employeeTasks[this.currentEmployee.id].unshift(task)
      }
      this.showDispatchModal = false
      window.$message?.success('任务已派发')
    },
    /**
     * 处理任务创建并启动事件
     * 派发任务后通过事件通知父组件启动会话
     */
    handleTaskCreatedAndStart({ task, employee }) {
      // 更新本地任务列表
      if (employee && task.employee?.id === employee.id) {
        if (!this.employeeTasks[employee.id]) {
          this.$set(this.employeeTasks, employee.id, [])
        }
        this.employeeTasks[employee.id].unshift(task)
      }
      this.showDispatchModal = false

      // 更新任务状态为 running
      this.updateTaskStatus(task.id, 'running')

      // 通过事件通知父组件启动会话
      const testerConfig = {
        name: task.name,
        prd_content: task.prd_content || '',
        tts_voice_id: employee?.tts_voice?.speaker || '',
        iot_protocol_id: task.iot_protocol?.id || '',
      }

      this.$emit('start-session-with-config', {
        testerConfig,
        task,
        employee
      })

      window.$message?.success('任务已派发，正在启动会话...')
    },
    /**
     * 获取 IOT 配置
     */
    getIOTConfigFromStorage() {
      return {
        token: localStorage.getItem('iot-token') || '',
        familyId: localStorage.getItem('family-id') || '',
        env: localStorage.getItem('iot-env') || 'test'
      }
    },
    /**
     * 更新本地任务状态
     */
    updateTaskStatus(taskId, status) {
      for (const empId in this.employeeTasks) {
        const tasks = this.employeeTasks[empId]
        const index = tasks.findIndex(t => t.id === taskId)
        if (index !== -1) {
          this.$set(tasks[index], 'status', status)
          break
        }
      }
    },
    retryTask(task) {
      console.log('重试任务:', task)
      window.$message?.info('重试功能开发中')
    },
    openTaskDrawer() {
      // 打开时重新加载任务列表
      if (this.currentEmployee) {
        this.loadEmployeeTasks(this.currentEmployee.id)
      }
      // 默认选中最新任务
      this.selectedTask = this.currentTask
      this.showDrawer = true
    },
    closeDrawer() {
      this.showDrawer = false
      this.selectedTask = null
    },
    selectTask(task) {
      this.selectedTask = task
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
    },
    // 测试报告相关方法
    openReportPanel() {
      if (!this.selectedTask) return

      // 如果已有报告数据，直接显示
      if (this.selectedTask.report_data) {
        this.reportData = this.selectedTask.report_data
        this.showReportPanel = true
        return
      }

      // 否则从服务器获取
      this.fetchReportData()
    },
    closeReportPanel() {
      this.showReportPanel = false
    },
    async fetchReportData() {
      if (!this.selectedTask?.id) return

      this.reportLoading = true
      this.showReportPanel = true

      try {
        const data = await sceneTestService.getTaskReport(this.selectedTask.id)
        this.reportData = data.report_data || data

        // 更新本地任务数据
        if (this.selectedTask && this.reportData) {
          this.$set(this.selectedTask, 'report_data', this.reportData)
        }
      } catch (error) {
        console.error('获取测试报告失败:', error)
        window.$message?.error('获取测试报告失败')
        this.showReportPanel = false
      } finally {
        this.reportLoading = false
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
  position: relative;
}

.group-view .hero-showcase {
  flex: 1;
}

/* 单个角色详情页 */
.single-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.single-view .hero-showcase {
  flex: 1;
  min-height: 0;
}

/* 右上角新增按钮 */
.add-employee-btn {
  position: absolute;
  top: 20px;
  right: 24px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: rgba(59, 130, 246, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: #3b82f6;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-employee-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 20px;
  left: 24px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s ease;
  z-index: 10;
}

.back-btn:hover {
  color: #333;
}

.back-btn svg {
  width: 16px;
  height: 16px;
}

/* 切换按钮 - 纯文字样式 */
.nav-btn {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s ease, color 0.2s ease;
  color: #666666;
  font-size: 26px;
  font-weight: 300;
  background: transparent;
  border: none;
  z-index: 10;
  padding: 0;
  opacity: 0;
}

.single-view:hover .nav-btn:not(:disabled) {
  opacity: 1;
}

.nav-btn:hover:not(:disabled) {
  color: #333333;
}

.nav-btn:disabled {
  opacity: 0;
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
  gap: 16px;
  padding: 12px 20px;
  margin: 0 auto 16px;
  width: fit-content;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.06),
    0 1px 2px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.group-info-bar {
  background: rgba(255, 255, 255, 0.7);
}

/* 员工信息卡片 */
.employee-card {
  display: flex;
  align-items: center;
  gap: 12px;
}

.employee-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.avatar-letter {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
}

.employee-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.employee-name {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  letter-spacing: 0.01em;
}

.employee-voice {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6e7681;
}

.employee-voice svg {
  opacity: 0.6;
}

/* 旧样式兼容 */
.employee-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
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

.status-badge.stopped {
  background: rgba(156, 163, 175, 0.1);
  color: #6b7280;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: rgba(59, 130, 246, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: #3b82f6;
}

.icon-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.icon-btn:active:not(:disabled) {
  transform: translateY(0);
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

/* 任务抽屉样式 */
.task-drawer {
  width: 640px;
  max-width: 90vw;
}

.task-drawer .drawer-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-list-section {
  flex-shrink: 0;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.task-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--bg-primary, #0d1117);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.task-item:hover {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.05);
}

.task-item.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #f0f6fc);
}

.task-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.task-status.pending {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
}

.task-status.running {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.task-status.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.task-status.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.task-status.stopped {
  background: rgba(156, 163, 175, 0.1);
  color: #6b7280;
}

.task-meta {
  font-size: 11px;
  color: var(--text-tertiary, #6e7681);
}

.empty-tasks {
  text-align: center;
  padding: 24px;
  color: var(--text-tertiary, #6e7681);
}

.task-detail {
  flex: 1;
  overflow-y: auto;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #30363d);
}

.task-detail h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #f0f6fc);
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

/* 测试报告摘要 */
.report-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.summary-stat {
  background: var(--bg-primary, #0d1117);
  border: 1px solid var(--border-color, #30363d);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.summary-stat .stat-num {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #60a5fa;
}

.summary-stat.passed .stat-num { color: #34d399; }
.summary-stat.failed .stat-num { color: #f87171; }
.summary-stat.rate .stat-num { color: #a78bfa; }

.summary-stat .stat-label {
  font-size: 11px;
  color: var(--text-tertiary, #6e7681);
  margin-top: 4px;
}

.view-report-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-report-btn:hover {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  transform: translateY(-1px);
}

.view-report-btn:active {
  transform: translateY(0);
}

/* 报告弹窗 */
.report-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1100;
  display: flex;
  justify-content: flex-end;
}

.report-drawer {
  width: 680px;
  max-width: 90vw;
  height: 100%;
  background: var(--bg-surface, #161b22);
  border-left: 1px solid var(--border-color, #30363d);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
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
    margin: 0 auto 12px;
    padding: 10px 14px;
    flex-direction: column;
    gap: 10px;
    width: auto;
  }

  .employee-card {
    width: 100%;
    justify-content: center;
  }

  .employee-avatar {
    width: 36px;
    height: 36px;
  }

  .action-buttons {
    gap: 8px;
    justify-content: center;
  }

  .icon-btn {
    width: 36px;
    height: 36px;
  }

  .back-btn {
    top: 12px;
    left: 12px;
    font-size: 13px;
  }

  .add-employee-btn {
    top: 12px;
    right: 12px;
    width: 40px;
    height: 40px;
  }
}
</style>