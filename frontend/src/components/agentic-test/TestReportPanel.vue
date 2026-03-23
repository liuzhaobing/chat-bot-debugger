<template>
  <div class="test-report-panel">
    <!-- 报告头部 - 仅在独立模式显示 -->
    <div v-if="showHeader" class="report-header">
      <h3>测试报告</h3>
      <button class="close-btn" @click="$emit('close')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
        <path d="M21 12a9 9 0 11-6.219-8.56"/>
      </svg>
      <span>加载报告中...</span>
    </div>

    <!-- 报告内容 -->
    <div v-else-if="reportData" class="report-content">
      <!-- 统计概览 -->
      <div class="stats-overview">
        <div class="stat-card total">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总用例</div>
        </div>
        <div class="stat-card passed">
          <div class="stat-value">{{ stats.passed }}</div>
          <div class="stat-label">通过</div>
        </div>
        <div class="stat-card failed">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-card rate">
          <div class="stat-value">{{ stats.pass_rate }}%</div>
          <div class="stat-label">通过率</div>
        </div>
      </div>

      <!-- 通过率进度条 -->
      <div class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: stats.pass_rate + '%' }"></div>
        </div>
        <div class="progress-labels">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>

      <!-- 其他统计 -->
      <div v-if="stats.blocked > 0 || stats.skipped > 0 || stats.not_run > 0" class="other-stats">
        <span v-if="stats.blocked > 0" class="stat-item blocked">
          <span class="dot"></span>阻塞 {{ stats.blocked }}
        </span>
        <span v-if="stats.skipped > 0" class="stat-item skipped">
          <span class="dot"></span>跳过 {{ stats.skipped }}
        </span>
        <span v-if="stats.not_run > 0" class="stat-item not-run">
          <span class="dot"></span>未执行 {{ stats.not_run }}
        </span>
      </div>

      <!-- 测试用例列表 -->
      <div class="test-cases-section">
        <div class="section-header">
          <h4>测试用例详情</h4>
          <div class="filter-tabs">
            <button
              :class="['filter-tab', { active: filterStatus === 'all' }]"
              @click="filterStatus = 'all'"
            >全部</button>
            <button
              :class="['filter-tab', { active: filterStatus === 'Pass' }]"
              @click="filterStatus = 'Pass'"
            >通过</button>
            <button
              :class="['filter-tab', { active: filterStatus === 'Fail' }]"
              @click="filterStatus = 'Fail'"
            >失败</button>
          </div>
        </div>

        <div class="test-cases-list">
          <div
            v-for="testCase in filteredTestCases"
            :key="testCase.id"
            class="test-case-item"
            :class="testCase.test_result.toLowerCase()"
            @click="toggleCaseDetail(testCase.id)"
          >
            <div class="case-header">
              <span class="case-status-icon">
                <svg v-if="testCase.test_result === 'Pass'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <svg v-else-if="testCase.test_result === 'Fail'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
              </span>
              <span class="case-id">{{ testCase.id }}</span>
              <span class="case-title">{{ testCase.title }}</span>
              <span class="case-type">{{ testCase.type }}</span>
              <svg class="expand-icon" :class="{ expanded: expandedCases.includes(testCase.id) }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>

            <!-- 展开详情 -->
            <div v-if="expandedCases.includes(testCase.id)" class="case-detail">
              <div class="detail-block">
                <div class="detail-label">前置条件</div>
                <ul class="detail-list">
                  <li v-for="(pre, idx) in testCase.preconditions" :key="idx">{{ pre }}</li>
                </ul>
              </div>
              <div class="detail-block">
                <div class="detail-label">预期结果</div>
                <ul class="detail-list">
                  <li v-for="(result, idx) in testCase.expect_results" :key="idx">{{ result }}</li>
                </ul>
              </div>
              <div v-if="testCase.actual_results && testCase.actual_results.length > 0" class="detail-block">
                <div class="detail-label">实际结果</div>
                <ul class="detail-list">
                  <li v-for="(result, idx) in testCase.actual_results" :key="idx">{{ result }}</li>
                </ul>
              </div>
              <div v-if="testCase.error_message" class="detail-block error">
                <div class="detail-label">错误信息</div>
                <div class="error-message">{{ testCase.error_message }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 缺陷列表 -->
      <div v-if="defects && defects.length > 0" class="defects-section">
        <div class="section-header">
          <h4>缺陷列表</h4>
          <span class="defect-count">{{ defects.length }}</span>
        </div>
        <div class="defects-list">
          <div v-for="defect in defects" :key="defect.id" class="defect-item" :class="defect.severity">
            <div class="defect-header">
              <span class="defect-id">{{ defect.id }}</span>
              <span class="defect-severity">{{ defect.severity }}</span>
              <span class="defect-status">{{ defect.status }}</span>
            </div>
            <div class="defect-description">{{ defect.description }}</div>
          </div>
        </div>
      </div>

      <!-- 会话信息 -->
      <div v-if="sessionInfo" class="session-info-section">
        <h4>执行信息</h4>
        <div class="session-info-grid">
          <div class="info-item">
            <span class="info-label">会话ID</span>
            <span class="info-value">{{ sessionInfo.session_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">执行时长</span>
            <span class="info-value">{{ formatDuration(sessionInfo.duration_seconds) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">测试环境</span>
            <span class="info-value">{{ sessionInfo.iot_env }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
      </svg>
      <p>暂无测试报告数据</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestReportPanel',
  props: {
    reportData: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    showHeader: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      filterStatus: 'all',
      expandedCases: []
    }
  },
  computed: {
    stats() {
      if (!this.reportData?.case_statistics) {
        return { total: 0, passed: 0, failed: 0, blocked: 0, skipped: 0, not_run: 0, pass_rate: 0 }
      }
      return this.reportData.case_statistics
    },
    testCases() {
      return this.reportData?.test_cases || []
    },
    defects() {
      return this.reportData?.defects || []
    },
    sessionInfo() {
      return this.reportData?.session_info || null
    },
    filteredTestCases() {
      if (this.filterStatus === 'all') {
        return this.testCases
      }
      return this.testCases.filter(tc => tc.test_result === this.filterStatus)
    }
  },
  methods: {
    toggleCaseDetail(caseId) {
      const index = this.expandedCases.indexOf(caseId)
      if (index === -1) {
        this.expandedCases.push(caseId)
      } else {
        this.expandedCases.splice(index, 1)
      }
    },
    formatDuration(seconds) {
      if (!seconds) return '-'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}分${secs}秒`
    }
  }
}
</script>

<style scoped>
.test-report-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-surface);
  color: var(--text-primary);
}

/* 头部 */
.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(180deg, #fafbfc 0%, #f5f6f8 100%);
}

.report-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 报告内容 */
.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 统计概览 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 1px solid var(--border-color);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.stat-card.total .stat-value { color: var(--accent-blue); }
.stat-card.passed .stat-value { color: #22c55e; }
.stat-card.failed .stat-value { color: #ef4444; }
.stat-card.rate .stat-value { color: #8b5cf6; }

/* 进度条 */
.progress-section {
  margin-bottom: 24px;
}

.progress-bar {
  height: 10px;
  background: var(--bg-secondary);
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #16a34a);
  border-radius: 5px;
  transition: width 0.5s ease;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 其他统计 */
.other-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.stat-item.blocked .dot { background: #f59e0b; }
.stat-item.skipped .dot { background: #8b5cf6; }
.stat-item.not-run .dot { background: #94a3b8; }

/* 测试用例列表 */
.test-cases-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.filter-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: 8px;
}

.filter-tab {
  padding: 6px 14px;
  font-size: 13px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s;
}

.filter-tab:hover {
  color: var(--text-primary);
}

.filter-tab.active {
  background: var(--bg-primary);
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.test-cases-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.test-case-item {
  background: var(--bg-secondary);
  border-radius: 10px;
  border-left: 4px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid var(--border-color);
}

.test-case-item:hover {
  background: var(--bg-hover);
}

.test-case-item.pass { border-left-color: #22c55e; }
.test-case-item.fail { border-left-color: #ef4444; }
.test-case-item.blocked { border-left-color: #f59e0b; }
.test-case-item.skipped { border-left-color: #8b5cf6; }
.test-case-item.notrun { border-left-color: #94a3b8; }

.case-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
}

.case-status-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.test-case-item.pass .case-status-icon { color: #22c55e; }
.test-case-item.fail .case-status-icon { color: #ef4444; }

.case-id {
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: monospace;
  min-width: 70px;
}

.case-title {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-type {
  font-size: 12px;
  padding: 3px 10px;
  background: var(--bg-primary);
  border-radius: 6px;
  color: var(--text-secondary);
}

.expand-icon {
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

/* 用例详情 */
.case-detail {
  padding: 0 16px 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
  padding-top: 14px;
}

.detail-block {
  margin-bottom: 14px;
}

.detail-block:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.detail-list {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.detail-list li {
  margin-bottom: 4px;
}

.detail-block.error .error-message {
  font-size: 14px;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* 缺陷列表 */
.defects-section {
  margin-bottom: 24px;
}

.defect-count {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.defects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.defect-item {
  background: var(--bg-secondary);
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
}

.defect-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.defect-id {
  font-size: 13px;
  font-family: monospace;
  color: var(--text-tertiary);
}

.defect-severity {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.defect-item.critical .defect-severity { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.defect-item.major .defect-severity { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.defect-item.normal .defect-severity { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.defect-item.minor .defect-severity { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

.defect-status {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-secondary);
}

.defect-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 会话信息 */
.session-info-section {
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.session-info-section h4 {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 600;
}

.session-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.info-value {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-tertiary);
}

.empty-state svg {
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 15px;
}
</style>