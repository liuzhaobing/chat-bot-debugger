<template>
  <div class="scene-test-panel">
    <!-- 主内容区域 - 使用过渡动画 -->
    <transition name="fade" mode="out-in">
      <!-- 聚合主页 - 4个角色合照 -->
      <div v-if="viewMode === 'group'" key="group" class="group-view">
        <!-- 右上角按钮组 -->
        <div class="top-right-buttons">
          <button class="icon-btn-header add-btn-header" @click="showHireModal = true" title="雇佣数字员工">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="8.5" cy="7" r="4"></circle>
              <line x1="20" y1="8" x2="20" y2="14"></line>
              <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
          </button>
        </div>

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

      <!-- 单个角色页面 - 左右布局 -->
      <div v-else key="single" class="single-view-split">
        <!-- 返回按钮 - 放在左侧面板顶部，与tab同行 -->
        <div class="left-panel">
          <!-- 顶部栏：返回按钮 + tab切换 -->
          <div class="left-panel-header">
            <button class="back-btn" @click="backToGroup" title="返回列表">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
              <span>返回</span>
            </button>

            <!-- 面板切换按钮 - 从右往左：头像、任务列表、派发任务 -->
            <div class="panel-switcher left-switcher">
              <!-- 派发任务按钮 - 火箭图标 -->
              <button
                v-if="currentEmployee"
                class="icon-btn-tab"
                @click="showDispatchModal = true"
                title="派发任务"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path>
                  <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path>
                  <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path>
                  <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path>
                </svg>
              </button>

              <!-- 重试任务按钮（失败时显示） -->
              <button
                v-if="currentTask && currentTask.status === 'failed'"
                class="icon-btn-tab warning"
                @click="retryTask(currentTask)"
                title="重试任务"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
              </button>

              <!-- 任务列表按钮 - 列表图标 -->
              <button :class="{ active: leftPanelContent === 'task-list' }" @click="leftPanelContent = 'task-list'" title="任务列表">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="8" y1="6" x2="21" y2="6"></line>
                  <line x1="8" y1="12" x2="21" y2="12"></line>
                  <line x1="8" y1="18" x2="21" y2="18"></line>
                  <line x1="3" y1="6" x2="3.01" y2="6"></line>
                  <line x1="3" y1="12" x2="3.01" y2="12"></line>
                  <line x1="3" y1="18" x2="3.01" y2="18"></line>
                </svg>
              </button>

              <!-- 角色头像按钮 -->
              <button
                class="avatar-tab-btn"
                :class="{ active: leftPanelContent === 'avatar', 'previewing': previewingVoiceId === currentEmployee?.tts_voice?.speaker }"
                @click="handleAvatarTabClick"
                title="点击查看角色，再次点击试听音色"
              >
                <div
                  class="avatar-tab-icon"
                  :style="{ background: currentEmployeeColor }"
                >
                  <span class="avatar-tab-text">{{ employeeNameShort }}</span>
                </div>
              </button>
            </div>
          </div>

          <!-- 内容区域 -->
          <div class="panel-content">
            <!-- 3D角色展示 -->
            <div v-if="leftPanelContent === 'avatar'" class="hero-showcase-compact">
              <template v-if="currentEmployee">
                <div class="hero-container-compact">
                  <Avatar3D
                    :animation-state="getAvatarState(currentTask?.status)"
                    :character-index="currentEmployee.avatar_index"
                    size="hero"
                  />
                </div>
              </template>
            </div>

            <!-- 任务列表 -->
            <div v-else-if="leftPanelContent === 'task-list'" class="task-list-panel">
              <div class="panel-title">任务列表</div>
              <div v-if="employeeTasksList.length === 0" class="empty-tasks-inline">
                <p>暂无任务</p>
              </div>
              <div v-else class="task-list-inline">
                <div
                  v-for="task in employeeTasksList"
                  :key="task.id"
                  class="task-item-inline"
                  :class="{ active: selectedTask?.id === task.id }"
                  @click="selectTaskInline(task)"
                >
                  <span class="task-name-inline">{{ task.name }}</span>
                  <span class="task-status-inline" :class="task.status">
                    {{ getStatusText(task.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：字幕/设备区 (70%) -->
        <div class="right-panel">
          <!-- 面板切换按钮 -->
          <div class="panel-switcher right-switcher">
            <button :class="{ active: rightPanelContent === 'transcript' }" @click="rightPanelContent = 'transcript'" title="字幕">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button :class="{ active: rightPanelContent === 'devices' }" @click="rightPanelContent = 'devices'" title="智能设备">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                <path d="M2 17l10 5 10-5"></path>
                <path d="M2 12l10 5 10-5"></path>
              </svg>
            </button>
            <!-- 测试用例设计按钮 - 靶心图标 -->
            <button
              :class="{ active: rightPanelContent === 'test-case-list' }"
              @click="rightPanelContent = 'test-case-list'"
              title="用例设计"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <circle cx="12" cy="12" r="6"></circle>
                <circle cx="12" cy="12" r="2"></circle>
              </svg>
            </button>
            <!-- 测试任务详情按钮 - 文件详情图标 -->
            <button
              v-if="selectedTaskForDetail"
              :class="{ active: rightPanelContent === 'task-detail' }"
              @click="rightPanelContent = 'task-detail'"
              title="任务详情"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <circle cx="10" cy="13" r="1"></circle>
                <circle cx="10" cy="17" r="1"></circle>
                <line x1="14" y1="13" x2="17" y2="13"></line>
                <line x1="14" y1="17" x2="17" y2="17"></line>
              </svg>
            </button>

            <!-- 会话状态按钮 - 右上角（独立样式，不受panel-switcher button影响） -->
            <button
              v-if="isConnecting || isSessionActive"
              class="session-status-btn"
              @click="handleSessionBtnClick"
              :class="{
                connected: isSessionActive,
                connecting: isConnecting
              }"
              title="点击停止会话"
            >
              <span class="status-dot"></span>
              <span v-if="isConnecting" class="status-text">连线中...</span>
              <span v-if="isSessionActive" class="status-text duration">{{ formattedSessionDuration }}</span>
            </button>
          </div>

          <!-- 内容区域 -->
          <div class="panel-content">
            <!-- 字幕/日志 -->
            <TranscriptPanel v-if="rightPanelContent === 'transcript'"
              :transcript-messages="transcriptMessages"
              :logs="systemLogs"
              @clear-transcript="$emit('clear-transcript')"
              @clear-logs="$emit('clear-logs')"
            />

            <!-- 智能设备（从弹窗移到这里） -->
            <div v-else-if="rightPanelContent === 'devices'" class="devices-panel-inline">
              <IOTConfigPanel ref="iotPanel" :hide-config="true" />
            </div>

            <!-- 测试用例设计（内嵌在右侧面板） -->
            <div v-else-if="rightPanelContent === 'test-case-list'" class="test-case-panel-inline">
              <TestCaseDesignPopup
                ref="testCaseDesignPopup"
                :visible="true"
                :initial-test-cases="initialTestCases"
                @confirm="handleTestCaseConfirm"
                @cancel="handleTestCaseCancel"
              />
            </div>

            <!-- 任务详情页 -->
            <div v-else-if="rightPanelContent === 'task-detail'" class="task-detail-panel">
              <!-- 有选中任务时显示详情 -->
              <template v-if="selectedTaskForDetail">
                <div class="task-detail-header">
                  <h3 class="task-detail-title">{{ selectedTaskForDetail.name }}</h3>
                  <span class="task-status-badge" :class="selectedTaskForDetail.status">
                    {{ getStatusText(selectedTaskForDetail.status) }}
                  </span>
                </div>

                <div class="task-detail-body">
                  <!-- 基本信息 -->
                  <div class="detail-section">
                    <h4>基本信息</h4>
                    <div class="detail-grid">
                      <div class="detail-item">
                        <span class="detail-label">任务ID</span>
                        <span class="detail-value">{{ selectedTaskForDetail.id }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">创建时间</span>
                        <span class="detail-value">{{ formatTime(selectedTaskForDetail.created_at) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">更新时间</span>
                        <span class="detail-value">{{ formatTime(selectedTaskForDetail.updated_at) }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">执行员工</span>
                        <span class="detail-value">{{ selectedTaskForDetail.employee?.name || '未配置' }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">TTS音色</span>
                        <span class="detail-value">{{ selectedTaskForDetail.employee?.tts_voice?.name || selectedTaskForDetail.tts_voice?.display_name || '未配置' }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">IOT协议</span>
                        <span class="detail-value">{{ selectedTaskForDetail.iot_protocol?.category || '未配置' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- PRD内容 -->
                  <div v-if="selectedTaskForDetail.prd_content" class="detail-section">
                    <h4>PRD/需求描述</h4>
                    <div class="prd-content">{{ selectedTaskForDetail.prd_content }}</div>
                  </div>

                  <!-- 测试报告 -->
                  <div v-if="selectedTaskForDetail.report_url || selectedTaskForDetail.report_data" class="detail-section">
                    <h4>测试报告</h4>

                    <!-- 报告概要统计 -->
                    <div v-if="selectedTaskForDetail.report_data?.case_statistics" class="report-summary">
                      <div class="summary-stat">
                        <span class="stat-num">{{ selectedTaskForDetail.report_data.case_statistics.total || 0 }}</span>
                        <span class="stat-label">总用例</span>
                      </div>
                      <div class="summary-stat passed">
                        <span class="stat-num">{{ selectedTaskForDetail.report_data.case_statistics.passed || 0 }}</span>
                        <span class="stat-label">通过</span>
                      </div>
                      <div class="summary-stat failed">
                        <span class="stat-num">{{ selectedTaskForDetail.report_data.case_statistics.failed || 0 }}</span>
                        <span class="stat-label">失败</span>
                      </div>
                      <div class="summary-stat rate">
                        <span class="stat-num">{{ selectedTaskForDetail.report_data.case_statistics.pass_rate || 0 }}%</span>
                        <span class="stat-label">通过率</span>
                      </div>
                    </div>

                    <!-- 查看详细报告按钮 -->
                    <button class="view-report-btn" @click="openReportForDetail">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                      </svg>
                      查看详细报告
                    </button>

                    <!-- 报告链接 -->
                    <div v-if="selectedTaskForDetail.report_url" class="detail-item" style="margin-top: 12px;">
                      <span class="detail-label">报告链接</span>
                      <a :href="selectedTaskForDetail.report_url" target="_blank" class="report-link">
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

                <!-- 测试报告详情（展开时显示） -->
                <div v-if="showReportInDetail" class="report-detail-inline">
                  <div class="report-detail-header">
                    <h4>详细报告</h4>
                    <button class="close-report-btn" @click="showReportInDetail = false">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                  <TestReportPanel
                    :report-data="reportDataForDetail"
                    :loading="reportLoadingForDetail"
                  />
                </div>
              </template>

              <!-- 没有选中任务时显示空状态 -->
              <template v-else>
                <div class="empty-task-detail">
                  <div class="empty-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                  </div>
                  <p class="empty-title">请选择一个任务</p>
                  <p class="empty-hint">在左侧任务列表中点击任务查看详情</p>
                </div>
              </template>
            </div>
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
import TranscriptPanel from './TranscriptPanel.vue'
import IOTConfigPanel from './IOTConfigPanel.vue'
import TestCaseDesignPopup from './TestCaseDesignPopup.vue'
import sceneTestService from '@/services/sceneTestService'

export default {
  name: 'SceneTestPanel',
  components: {
    Avatar3D,
    EmployeeGroup,
    HireEmployeeModal,
    TestReportPanel,
    TranscriptPanel,
    IOTConfigPanel,
    TestCaseDesignPopup
  },
  props: {
    hasPendingTestCases: {
      type: Boolean,
      default: false
    },
    transcriptMessages: {
      type: Array,
      default: () => []
    },
    systemLogs: {
      type: Array,
      default: () => []
    },
    // 会话状态
    isSessionActive: {
      type: Boolean,
      default: false
    },
    isConnecting: {
      type: Boolean,
      default: false
    },
    sessionDuration: {
      type: Number,
      default: 0
    }
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
      reportLoading: false,
      // 面板内容状态
      leftPanelContent: 'avatar', // 'avatar' | 'task-list'
      rightPanelContent: 'transcript', // 'devices' | 'transcript' | 'test-case-list' | 'task-detail'
      // 任务详情相关
      selectedTaskForDetail: null, // 用于右侧详情页展示的任务
      showReportInDetail: false, // 是否在任务详情页展开报告
      reportDataForDetail: null, // 任务详情页的报告数据
      reportLoadingForDetail: false, // 任务详情页报告加载状态
      // 测试用例设计相关
      initialTestCases: [] // 初始测试用例数据
    }
  },
  computed: {
    characterColors() {
      return {
        0: '#FF9F5A', // orange
        1: '#9B5DE5', // purple
        2: '#2D2D2D', // black
        3: '#F8E759'  // yellow
      }
    },
    currentEmployeeColor() {
      return this.characterColors[this.currentEmployee?.avatar_index] || '#667eea'
    },
    employeeNameShort() {
      const name = this.currentEmployee?.name || ''
      return name.length > 4 ? name.substring(0, 4) : name
    },
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
    },
    formattedSessionDuration() {
      const minutes = Math.floor(this.sessionDuration / 60)
      const seconds = this.sessionDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
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
    reopenTestCasePopup() {
      this.$emit('reopen-test-case-popup')
    },
    handleSessionBtnClick() {
      this.$emit('session-btn-click')
    },
    /**
     * 处理头像tab点击
     * - 如果当前不在角色页：切换到角色页
     * - 如果当前已在角色页：试听音色
     */
    handleAvatarTabClick() {
      if (this.leftPanelContent === 'avatar') {
        // 已在角色页，触发试听
        this.previewVoice()
      } else {
        // 不在角色页，切换到角色页
        this.leftPanelContent = 'avatar'
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
        job_instance_id: task.job_instance_id  // 关键：传递 job_instance_id
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
    selectTaskInline(task) {
      // 更新抽屉中选中的任务
      this.selectedTask = task
      // 设置详情页展示的任务
      this.selectedTaskForDetail = task
      // 关闭报告展开状态
      this.showReportInDetail = false
      // 切换到任务详情页
      this.rightPanelContent = 'task-detail'
    },
    /**
     * 在任务详情页中打开报告
     */
    openReportForDetail() {
      if (!this.selectedTaskForDetail) return

      // 如果已有报告数据，直接显示
      if (this.selectedTaskForDetail.report_data) {
        this.reportDataForDetail = this.selectedTaskForDetail.report_data
        this.showReportInDetail = true
        return
      }

      // 否则从服务器获取
      this.fetchReportForDetail()
    },
    async fetchReportForDetail() {
      if (!this.selectedTaskForDetail?.id) return

      this.reportLoadingForDetail = true
      this.showReportInDetail = true

      try {
        const data = await sceneTestService.getTaskReport(this.selectedTaskForDetail.id)
        this.reportDataForDetail = data.report_data || data

        // 更新本地任务数据
        if (this.selectedTaskForDetail && this.reportDataForDetail) {
          this.$set(this.selectedTaskForDetail, 'report_data', this.reportDataForDetail)
        }
      } catch (error) {
        console.error('获取测试报告失败:', error)
        window.$message?.error('获取测试报告失败')
        this.showReportInDetail = false
      } finally {
        this.reportLoadingForDetail = false
      }
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
    },
    /**
     * 测试用例确认
     */
    handleTestCaseConfirm(testCases) {
      this.$emit('test-cases-confirm', testCases)
    },
    /**
     * 测试用例取消
     */
    handleTestCaseCancel() {
      // 返回到字幕页面
      this.rightPanelContent = 'transcript'
    },
    /**
     * 重置测试用例面板
     */
    resetTestCasePanel() {
      this.initialTestCases = []
      if (this.$refs.testCaseDesignPopup) {
        this.$refs.testCaseDesignPopup.reset()
      }
    },
    /**
     * 切换到测试用例面板
     */
    switchToTestCasePanel() {
      this.rightPanelContent = 'test-case-list'
    },
    /**
     * 添加测试用例流式内容
     */
    addTestCaseChunk(chunk) {
      if (this.$refs.testCaseDesignPopup) {
        this.$refs.testCaseDesignPopup.addDesignChunk(chunk)
      }
    },
    /**
     * 设置测试用例生成完成
     */
    setTestCaseComplete(testCases) {
      this.initialTestCases = testCases
      if (this.$refs.testCaseDesignPopup) {
        this.$refs.testCaseDesignPopup.setDesignComplete(testCases)
      }
    }
  }
}
</script>

<style scoped>
.scene-test-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
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

/* 单个角色详情页 - 左右分栏布局 */
.single-view-split {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

/* 左侧面板 - 3D角色展示 (30%) */
.left-panel {
  width: 30%;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e8eef5 100%);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
}

/* 左侧面板顶部栏 - 返回按钮 + tab切换 */
.left-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.left-panel-header .panel-switcher {
  border-bottom: none;
  background: transparent;
  padding: 0;
}

.hero-showcase-compact {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.hero-container-compact {
  width: 100%;
  max-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 右侧面板 - 通话字幕 (70%) */
.right-panel {
  flex: 1;
  overflow: hidden;
  background: var(--bg-secondary, #f6f8fa);
  display: flex;
  flex-direction: column;
}

/* 面板切换按钮 */
.panel-switcher {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

/* 左侧面板切换按钮靠右对齐，避免被返回按钮遮挡 */
.panel-switcher.left-switcher {
  justify-content: flex-end;
}

.panel-switcher button {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-switcher button:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #374151;
}

.panel-switcher button.active {
  background: #3b82f6;
  color: #fff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

/* icon 样式的 tab 按钮 - 与普通按钮样式一致 */
.panel-switcher .icon-btn-tab {
  background: transparent;
  color: #6b7280;
}

.panel-switcher .icon-btn-tab:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #374151;
}

.panel-switcher .icon-btn-tab.warning {
  color: #ef4444;
}

.panel-switcher .icon-btn-tab.warning:hover {
  background: rgba(239, 68, 68, 0.08);
}

/* 头像 tab 按钮 */
.avatar-tab-btn {
  padding: 4px !important;
  width: auto !important;
  min-width: 36px;
  border-radius: 10px !important;
}

.avatar-tab-btn.active {
  background: rgba(59, 130, 246, 0.1) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.avatar-tab-btn.previewing {
  animation: avatar-pulse 1.5s ease infinite;
}

@keyframes avatar-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0);
  }
}

.avatar-tab-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

.avatar-tab-btn:hover .avatar-tab-icon {
  transform: scale(1.05);
}

.avatar-tab-btn:active .avatar-tab-icon {
  transform: scale(0.95);
}

.avatar-tab-text {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.02em;
}

/* 黄色背景需要深色文字 */
.avatar-tab-icon[style*="#F8E759"] .avatar-tab-text {
  color: #2D2D2D;
}

/* 会话状态按钮 - 右侧面板右上角（独立样式，优先级更高） */
.panel-switcher .session-status-btn {
  background: #000 !important;
  border-radius: 16px !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: white !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 6px 12px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  margin-left: auto !important;
  width: auto !important;
  height: auto !important;
}

.panel-switcher .session-status-btn:hover {
  transform: scale(1.03) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
  background: #000 !important;
}

.panel-switcher .session-status-btn.connected {
  border-color: rgba(16, 185, 129, 0.3) !important;
  animation: connected-glow 2s infinite !important;
}

.panel-switcher .session-status-btn.connecting {
  border-color: rgba(245, 158, 11, 0.3) !important;
  animation: connecting-glow 1s infinite !important;
}

.panel-switcher .session-status-btn .status-dot {
  width: 6px !important;
  height: 6px !important;
  border-radius: 50% !important;
  background: #6b7280 !important;
  transition: all 0.3s ease !important;
  flex-shrink: 0 !important;
}

.panel-switcher .session-status-btn.connected .status-dot {
  background: #10b981 !important;
  animation: dot-pulse 2s infinite !important;
}

.panel-switcher .session-status-btn.connecting .status-dot {
  background: #f59e0b !important;
  animation: dot-pulse 0.8s infinite !important;
}

.panel-switcher .session-status-btn .status-text {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  color: white !important;
}

.panel-switcher .session-status-btn .status-text.duration {
  color: #10b981 !important;
  font-weight: 600 !important;
}

@keyframes connected-glow {
  0%, 100% {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25), 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), 0 0 0 3px rgba(16, 185, 129, 0.15);
  }
}

@keyframes connecting-glow {
  0%, 100% {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25), 0 0 0 0 rgba(245, 158, 11, 0.4);
  }
  50% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), 0 0 0 3px rgba(245, 158, 11, 0.15);
  }
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 面板内容区域 */
.panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 任务列表面板 */
.task-list-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.task-list-inline {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.task-item-inline:hover {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.task-item-inline.active {
  background: rgba(59, 130, 246, 0.12);
  border-color: #3b82f6;
}

.task-name-inline {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a2e;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-status-inline {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
  margin-left: 8px;
}

.task-status-inline.pending {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
}

.task-status-inline.running {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.task-status-inline.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.task-status-inline.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.empty-tasks-inline {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 13px;
}

/* 测试用例设计面板（内嵌在右侧面板） */
.test-case-panel-inline {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary, #f6f8fa);
}

/* 覆盖 TestCaseDesignPopup 的弹窗样式，使其在内嵌时正常显示 */
.test-case-panel-inline >>> .test-case-popup-overlay {
  position: relative;
  background: transparent;
  backdrop-filter: none;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  animation: none;
  height: 100%;
}

.test-case-panel-inline >>> .test-case-popup {
  width: 100%;
  max-width: none;
  max-height: none;
  border-radius: 0;
  box-shadow: none;
  border: none;
  animation: none;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #fff);
}

.test-case-panel-inline >>> .popup-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.test-case-panel-inline >>> .popup-header h3 {
  font-size: 14px;
}

.test-case-panel-inline >>> .popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.test-case-panel-inline >>> .popup-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.test-case-panel-inline >>> .test-cases-table {
  font-size: 12px;
}

.test-case-panel-inline >>> .test-cases-table th,
.test-case-panel-inline >>> .test-cases-table td {
  padding: 8px 10px;
}

.test-case-panel-inline >>> .designing-status {
  padding: 40px;
}

/* 隐藏编辑弹窗的内层遮罩（编辑弹窗保持原样） */
.test-case-panel-inline >>> .edit-modal-overlay {
  position: fixed;
}

/* 智能设备面板（内嵌） */
.devices-panel-inline {
  flex: 1;
  overflow: hidden;
  background: var(--bg-secondary, #f6f8fa);
}

/* 任务详情面板 */
.task-detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-secondary, #f6f8fa);
}

.task-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.task-detail-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.task-status-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
}

.task-status-badge.pending { background: rgba(156, 163, 175, 0.1); color: #9ca3af; }
.task-status-badge.running { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.task-status-badge.completed { background: rgba(16, 185, 129, 0.1); color: #10b981; }
.task-status-badge.failed { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.task-status-badge.stopped { background: rgba(156, 163, 175, 0.1); color: #6b7280; }

.task-detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item .detail-label {
  font-size: 11px;
  color: #6b7280;
}

.detail-item .detail-value {
  font-size: 13px;
  color: #1a1a2e;
}

.prd-content {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 报告摘要 */
.report-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.summary-stat {
  background: #f9fafb;
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
  color: #6b7280;
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

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #3b82f6;
  text-decoration: none;
  font-size: 13px;
  transition: color 0.15s ease;
}

.report-link:hover {
  color: #60a5fa;
  text-decoration: underline;
}

/* 报告详情内嵌 */
.report-detail-inline {
  margin-top: 16px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.report-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.report-detail-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.close-report-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s ease;
}

.close-report-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #374151;
}

/* 空状态 */
.empty-task-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.empty-icon {
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-task-detail .empty-title {
  margin: 0 0 8px 0;
  font-size: 15px;
  font-weight: 500;
  color: #6b7280;
}

.empty-task-detail .empty-hint {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

/* 右上角按钮组 */
.top-right-buttons {
  position: absolute;
  top: 20px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.icon-btn-header {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: rgba(59, 130, 246, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #3b82f6;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-btn-header:hover {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.add-btn-header {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
}

.add-btn-header:hover {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

/* 返回按钮 */
.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s ease;
  border-radius: 6px;
}

.back-btn:hover {
  color: #333;
  background: rgba(0, 0, 0, 0.04);
}

.back-btn svg {
  width: 16px;
  height: 16px;
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
@media (max-width: 1200px) {
  .left-panel {
    width: 35%;
  }

  .panel-switcher button {
    width: 34px;
    height: 34px;
  }
}

@media (max-width: 900px) {
  .single-view-split {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    min-width: 0;
    min-height: 280px;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }

  .right-panel {
    flex: 1;
    min-height: 50vh;
  }

  .hero-showcase-compact {
    padding: 10px;
  }

  .hero-container-compact {
    max-width: 150px;
  }

  /* 平板上面板切换按钮更大 */
  .panel-switcher {
    padding: 10px 12px;
  }

  .panel-switcher button {
    width: 40px;
    height: 40px;
  }

  /* 左侧面板头部 */
  .left-panel-header {
    padding: 10px 12px;
  }

  .left-panel-header .panel-switcher button {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 600px) {
  /* 手机端优化 */

  /* 左侧面板头部 */
  .left-panel-header {
    padding: 10px 12px;
  }

  .back-btn {
    font-size: 12px;
    padding: 6px 8px;
  }

  /* 手机端面板切换按钮更大，便于触摸 */
  .panel-switcher {
    padding: 0;
    gap: 6px;
  }

  .panel-switcher button {
    width: 40px;
    height: 40px;
    border-radius: 10px;
  }

  .panel-switcher button svg {
    width: 20px;
    height: 20px;
  }

  /* 头像 tab 按钮手机端样式 */
  .avatar-tab-btn {
    min-width: 44px;
    padding: 5px !important;
  }

  .avatar-tab-icon {
    width: 34px;
    height: 34px;
  }

  .avatar-tab-text {
    font-size: 13px;
  }

  /* 会话状态按钮 */
  .session-status-btn {
    padding: 6px 10px;
    font-size: 11px;
  }

  /* 手机端左侧面板高度调整 */
  .left-panel {
    min-height: 250px;
    max-height: 35vh;
  }

  /* 手机端任务列表项更大 */
  .task-item-inline {
    padding: 12px 14px;
  }

  .task-name-inline {
    font-size: 14px;
  }

  /* 任务详情页响应式 */
  .task-detail-panel {
    padding: 12px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .report-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .summary-stat .stat-num {
    font-size: 18px;
  }

  /* 手机端测试用例面板 */
  .test-case-panel-inline >>> .popup-header {
    padding: 10px 12px;
  }

  .test-case-panel-inline >>> .popup-body {
    padding: 10px 12px;
  }

  .test-case-panel-inline >>> .popup-footer {
    padding: 10px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .test-case-panel-inline >>> .footer-left,
  .test-case-panel-inline >>> .footer-right {
    flex-wrap: wrap;
  }
}
</style>