<template>
  <div class="test-case-list-panel">
    <!-- 顶部标题栏 -->
    <div class="panel-header">
      <div class="panel-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 11l3 3L22 4"></path>
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
        </svg>
        <span>测试用例</span>
        <span class="case-count">{{ testCasesWithStatus.length }}</span>
      </div>
      <!-- 统计摘要 -->
      <div class="stats-summary">
        <span class="stat passed" :title="'通过 ' + passedCount">{{ passedCount }}</span>
        <span class="stat failed" :title="'失败 ' + failedCount">{{ failedCount }}</span>
        <span class="stat blocked" :title="'阻塞 ' + blockedCount">{{ blockedCount }}</span>
      </div>
    </div>

    <!-- 用例列表 -->
    <div class="case-list">
      <div
        v-for="(caseStatus, index) in testCasesWithStatus"
        :key="caseStatus.testCase.id"
        class="case-item"
        :class="{
          active: index === selectedIndex,
          executing: index === currentIndex,
          [getStatusClass(caseStatus.status)]: true
        }"
        @click="handleSelectCase(index)"
      >
        <!-- 状态指示器 -->
        <div class="status-indicator" :class="getStatusClass(caseStatus.status)">
          <div v-if="index === currentIndex" class="pulse-ring"></div>
          <div class="status-dot"></div>
        </div>

        <!-- 用例信息 -->
        <div class="case-info">
          <div class="case-header-row">
            <span class="case-title">{{ getFirstLine(caseStatus.testCase.title) }}</span>
          </div>
          <div class="case-meta">
            <span class="case-id">{{ caseStatus.testCase.id }}</span>
            <span class="separator">·</span>
            <span class="case-type">{{ formatCaseType(caseStatus.testCase.type) }}</span>
          </div>
        </div>

        <!-- 右侧区域：步骤统计 + 状态标签 -->
        <div class="case-right-section">
          <span v-if="caseStatus.stepResults && caseStatus.stepResults.length > 0" class="step-summary">
            {{ getPassedStepCount(caseStatus.stepResults) }}/{{ caseStatus.stepResults.length }}
          </span>
          <div class="case-status-tag" :class="getStatusClass(caseStatus.status)">
            {{ getStatusLabel(caseStatus.status) }}
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="testCasesWithStatus.length === 0" class="empty-state">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 11l3 3L22 4"></path>
          <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
        </svg>
        <p>暂无测试用例</p>
      </div>
    </div>

    <!-- 测试报告概览 -->
    <div v-if="showReportSummary" class="report-summary-section">
      <div class="summary-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
        </svg>
        <span>测试报告</span>
      </div>
      <div class="summary-stats">
        <div class="summary-stat">
          <span class="stat-num">{{ reportStats.total }}</span>
          <span class="stat-label">总用例</span>
        </div>
        <div class="summary-stat passed">
          <span class="stat-num">{{ reportStats.passed }}</span>
          <span class="stat-label">通过</span>
        </div>
        <div class="summary-stat failed">
          <span class="stat-num">{{ reportStats.failed }}</span>
          <span class="stat-label">失败</span>
        </div>
        <div class="summary-stat rate">
          <span class="stat-num">{{ reportStats.pass_rate }}%</span>
          <span class="stat-label">通过率</span>
        </div>
      </div>
      <!-- 进度条 -->
      <div class="summary-progress">
        <div class="progress-bar">
          <div class="progress-fill passed-fill" :style="{ width: reportStats.pass_rate + '%' }"></div>
        </div>
      </div>
      <button class="view-report-btn" @click="handleViewReport">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        查看详细报告
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestCaseListPanel',
  props: {
    testCases: {
      type: Array,
      default: () => []
    },
    testCasesWithStatus: {
      type: Array,
      default: () => []
    },
    currentIndex: {
      type: Number,
      default: -1
    },
    selectedIndex: {
      type: Number,
      default: -1
    },
    testCompleted: {
      type: Boolean,
      default: false
    },
    reportData: {
      type: Object,
      default: null
    }
  },
  computed: {
    passedCount() {
      return this.testCasesWithStatus.filter(c => c.status === 'PASS').length
    },
    failedCount() {
      return this.testCasesWithStatus.filter(c => c.status === 'FAIL').length
    },
    blockedCount() {
      return this.testCasesWithStatus.filter(c => c.status === 'BLOCKED').length
    },
    showReportSummary() {
      return this.testCompleted && this.testCasesWithStatus.length > 0
    },
    reportStats() {
      if (this.reportData?.case_statistics) {
        return this.reportData.case_statistics
      }
      // 从 testCasesWithStatus 计算
      const total = this.testCasesWithStatus.length
      const passed = this.passedCount
      const failed = this.failedCount
      const passRate = total > 0 ? Math.round((passed / total) * 100) : 0
      return { total, passed, failed, pass_rate: passRate }
    }
  },
  methods: {
    handleSelectCase(index) {
      this.$emit('select-case', index)
    },

    handleViewReport() {
      this.$emit('view-report')
    },

    getFirstLine(title) {
      if (!title) return ''
      const firstLine = title.split('\n')[0]
      return firstLine.length > 28 ? firstLine.substring(0, 28) + '...' : firstLine
    },

    formatCaseType(type) {
      const typeMap = {
        'functional': '功能',
        'performance': '性能',
        'stability': '稳定',
        'compatibility': '兼容',
        'security': '安全',
        'usability': '易用'
      }
      return typeMap[type] || type || '功能'
    },

    getStatusClass(status) {
      const classMap = {
        'NOT_RUN': 'not-run',
        'PASS': 'pass',
        'FAIL': 'fail',
        'BLOCKED': 'blocked',
        'SKIPPED': 'skipped'
      }
      return classMap[status] || 'not-run'
    },

    getStatusLabel(status) {
      const labelMap = {
        'NOT_RUN': '待执行',
        'PASS': '通过',
        'FAIL': '失败',
        'BLOCKED': '阻塞',
        'SKIPPED': '跳过'
      }
      return labelMap[status] || '待执行'
    },

    getPassedStepCount(stepResults) {
      return stepResults.filter(s => s.is_pass).length
    }
  }
}
</script>

<style scoped>
.test-case-list-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(180deg, #fafbfc 0%, #f5f6f8 100%);
  border-bottom: 1px solid #e8eaed;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.panel-title svg {
  color: #3b82f6;
}

.case-count {
  background: #e8eaed;
  color: #5f6368;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.stats-summary {
  display: flex;
  gap: 6px;
}

.stats-summary .stat {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  min-width: 24px;
  text-align: center;
}

.stats-summary .stat.passed {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.stats-summary .stat.failed {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.stats-summary .stat.blocked {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.case-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.case-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 4px;
  background: #fafbfc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 2px solid transparent;
  position: relative;
}

.case-item:hover {
  background: #f0f2f5;
}

.case-item.active {
  background: rgba(59, 130, 246, 0.06);
  border-color: #3b82f6;
}

.case-item.executing {
  background: rgba(59, 130, 246, 0.1);
  border-color: #3b82f6;
}

/* 状态指示器 */
.status-indicator {
  position: relative;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
  transition: all 0.2s ease;
}

.status-indicator.not-run .status-dot { background: #d1d5db; }
.status-indicator.pass .status-dot { background: #22c55e; }
.status-indicator.fail .status-dot { background: #ef4444; }
.status-indicator.blocked .status-dot { background: #f59e0b; }
.status-indicator.skipped .status-dot { background: #9ca3af; }

.status-indicator.executing .status-dot {
  background: #3b82f6;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.pulse-ring {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #3b82f6;
  animation: pulse-ring 1.2s ease-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}

/* 用例信息 */
.case-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.case-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
  font-size: 11px;
  color: #9ca3af;
}

.case-id {
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 10px;
}

.separator {
  color: #d1d5db;
}

.case-type {
  color: #6b7280;
}

/* 右侧区域 */
.case-right-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-shrink: 0;
}

.step-summary {
  font-size: 10px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

/* 右侧状态标签 */
.case-status-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  min-width: 42px;
  text-align: center;
}

.case-status-tag.not-run { background: #f3f4f6; color: #6b7280; }
.case-status-tag.pass { background: rgba(34, 197, 94, 0.12); color: #16a34a; }
.case-status-tag.fail { background: rgba(239, 68, 68, 0.12); color: #dc2626; }
.case-status-tag.blocked { background: rgba(245, 158, 11, 0.12); color: #d97706; }
.case-status-tag.skipped { background: rgba(156, 163, 175, 0.15); color: #6b7280; }

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  padding: 40px 20px;
}

.empty-state svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

/* 测试报告概览 */
.report-summary-section {
  border-top: 1px solid #e8eaed;
  padding: 14px;
  background: linear-gradient(180deg, #fafbfc 0%, #f5f6f8 100%);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.summary-header svg {
  color: #6b7280;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.summary-stat {
  background: #fff;
  border-radius: 8px;
  padding: 10px 8px;
  text-align: center;
  border: 1px solid #e8eaed;
}

.summary-stat .stat-num {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #3b82f6;
}

.summary-stat.passed .stat-num { color: #22c55e; }
.summary-stat.failed .stat-num { color: #ef4444; }
.summary-stat.rate .stat-num { color: #8b5cf6; }

.summary-stat .stat-label {
  display: block;
  font-size: 10px;
  color: #6b7280;
  margin-top: 2px;
}

.summary-progress {
  margin-bottom: 12px;
}

.progress-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.passed-fill {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.view-report-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-report-btn:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.view-report-btn:active {
  transform: translateY(0);
}
</style>