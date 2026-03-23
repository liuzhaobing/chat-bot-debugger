<template>
  <div class="test-case-detail-panel">
    <!-- 用例详情区域 -->
    <div class="case-detail-section">
      <div class="section-header">
        <h3 class="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          用例详情
        </h3>
        <span v-if="testCase" class="case-status-badge" :class="statusClass">
          {{ statusText }}
        </span>
      </div>

      <div class="detail-scroll-container">
        <div v-if="testCase" class="detail-content">
          <!-- 标题 -->
          <div class="detail-row">
            <span class="detail-label">标题</span>
            <span class="detail-value title">{{ testCase.title }}</span>
          </div>

          <!-- 前置条件 -->
          <div v-if="testCase.preconditions && testCase.preconditions.length" class="detail-block">
            <div class="block-title">前置条件</div>
            <ul class="condition-list">
              <li v-for="(cond, i) in testCase.preconditions" :key="i">{{ cond }}</li>
            </ul>
          </div>

          <!-- 测试步骤 -->
          <div class="detail-block">
            <div class="block-title">测试步骤</div>
            <div class="steps-list">
              <div
                v-for="(step, i) in testCase.steps"
                :key="i"
                class="step-item"
                :class="getStepClass(i)"
              >
                <div class="step-index">{{ i + 1 }}</div>
                <div class="step-content">
                  <span class="step-text">{{ step }}</span>
                  <span v-if="getStepResult(i)" class="step-result" :class="{ pass: getStepResult(i).is_pass, fail: !getStepResult(i).is_pass }">
                    {{ getStepResult(i).is_pass ? '通过' : '失败' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 预期结果 -->
          <div class="detail-block">
            <div class="block-title">预期结果</div>
            <ul class="result-list">
              <li v-for="(result, i) in testCase.expect_results" :key="i">{{ result }}</li>
            </ul>
          </div>

          <!-- 实际结果 - 始终显示 -->
          <div class="detail-block">
            <div class="block-title">实际执行结果</div>
            <div v-if="actualResults.length" class="actual-results">
              <div v-for="(result, i) in actualResults" :key="i" class="actual-result-item">
                {{ result }}
              </div>
            </div>
            <div v-else class="empty-actual-results">
              <span>暂无实际执行结果</span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-detail">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
          <p>请在左侧选择一个测试用例</p>
        </div>
      </div>
    </div>

    <!-- AI 日志区域 -->
    <div class="logs-section">
      <div class="section-header">
        <h3 class="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"></path>
          </svg>
          AI 日志
        </h3>
        <span class="log-count">{{ logs.length }} 条</span>
      </div>

      <div class="logs-content" ref="logsContainer">
        <div v-if="logs.length === 0" class="empty-logs">
          <p>暂无日志</p>
        </div>
        <div v-else class="logs-list">
          <div
            v-for="log in logs"
            :key="log.id"
            class="log-item"
            :class="[log.level, log.category]"
          >
            <div class="log-header-row">
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-category">[{{ log.category }}]</span>
              <span class="log-message">{{ log.message }}</span>
              <button
                v-if="hasDetails(log.details)"
                class="log-expand-btn"
                @click="toggleLogExpand(log.id)"
                :title="isLogExpanded(log.id) ? '收起详情' : '展开详情'"
              >
                <svg v-if="isLogExpanded(log.id)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9,18 15,12 9,6"></polyline>
                </svg>
              </button>
            </div>
            <!-- 展开的详情内容 -->
            <div v-if="hasDetails(log.details) && isLogExpanded(log.id)" class="log-details-content">
              <div class="log-details-header">
                <span class="details-label">详细信息</span>
                <button class="copy-btn" @click="copyLogDetails(log)" :title="copySuccessLogId === log.id ? '已复制' : '复制'">
                  <svg v-if="copySuccessLogId === log.id" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </button>
              </div>
              <pre>{{ formatDetails(log.details) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestCaseDetailPanel',
  props: {
    testCase: {
      type: Object,
      default: null
    },
    status: {
      type: String,
      default: 'NOT_RUN'
    },
    stepResults: {
      type: Array,
      default: () => []
    },
    actualResults: {
      type: Array,
      default: () => []
    },
    logs: {
      type: Array,
      default: () => []
    },
    isExecuting: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      expandedLogs: new Set(),
      copySuccessLogId: null
    }
  },
  computed: {
    statusClass() {
      // 如果正在执行，优先显示执行中状态
      if (this.isExecuting) {
        return 'executing'
      }
      const classMap = {
        'NOT_RUN': 'not-run',
        'PASS': 'pass',
        'FAIL': 'fail',
        'BLOCKED': 'blocked',
        'SKIPPED': 'skipped'
      }
      return classMap[this.status] || 'not-run'
    },
    statusText() {
      // 如果正在执行，优先显示执行中状态
      if (this.isExecuting) {
        return '执行中'
      }
      const textMap = {
        'NOT_RUN': '未执行',
        'PASS': '通过',
        'FAIL': '失败',
        'BLOCKED': '阻塞',
        'SKIPPED': '跳过'
      }
      return textMap[this.status] || '未执行'
    }
  },
  watch: {
    logs: {
      handler(newLogs) {
        if (newLogs && newLogs.length > 0) {
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    getStepClass(index) {
      const result = this.stepResults[index]
      if (!result) return ''
      return result.is_pass ? 'pass' : 'fail'
    },

    getStepResult(index) {
      return this.stepResults[index] || null
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    },

    scrollToBottom() {
      const container = this.$refs.logsContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    hasDetails(details) {
      if (!details) return false
      if (Array.isArray(details)) return details.length > 0
      if (typeof details === 'object') return Object.keys(details).length > 0
      return false
    },

    isLogExpanded(logId) {
      return this.expandedLogs.has(logId)
    },

    toggleLogExpand(logId) {
      if (this.expandedLogs.has(logId)) {
        this.expandedLogs.delete(logId)
      } else {
        this.expandedLogs.add(logId)
      }
      // 触发响应式更新
      this.expandedLogs = new Set(this.expandedLogs)
    },

    formatDetails(details) {
      return JSON.stringify(details, null, 2)
    },

    async copyLogDetails(log) {
      try {
        const content = JSON.stringify(log.details, null, 2)
        await navigator.clipboard.writeText(content)
        this.copySuccessLogId = log.id
        setTimeout(() => {
          this.copySuccessLogId = null
        }, 2000)
      } catch (err) {
        console.error('复制失败:', err)
      }
    }
  }
}
</script>

<style scoped>
.test-case-detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

/* 用例详情区域 */
.case-detail-section {
  flex: 0 0 auto;
  max-height: 50%;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #e5e7eb;
}

.detail-scroll-container {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(180deg, #fafbfc 0%, #f5f6f8 100%);
  border-bottom: 1px solid #e8eaed;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.section-title svg {
  color: #3b82f6;
}

.case-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
}

.case-status-badge.not-run {
  background: #e5e7eb;
  color: #6b7280;
}

.case-status-badge.pass {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.case-status-badge.fail {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.case-status-badge.blocked {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.case-status-badge.executing {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  animation: pulse-badge 1.5s ease-in-out infinite;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.detail-content {
  padding: 16px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  flex-shrink: 0;
  width: 60px;
}

.detail-value {
  font-size: 13px;
  color: #1a1a2e;
  flex: 1;
}

.detail-value.title {
  font-weight: 600;
}

.detail-block {
  margin-top: 16px;
}

.block-title {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.condition-list,
.result-list {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.8;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #d1d5db;
}

.step-item.pass {
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.step-item.fail {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.step-index {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  flex-shrink: 0;
}

.step-item.pass .step-index {
  background: #10b981;
  color: #fff;
}

.step-item.fail .step-index {
  background: #ef4444;
  color: #fff;
}

.step-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.step-text {
  font-size: 12px;
  color: #374151;
  line-height: 1.5;
}

.step-result {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.step-result.pass {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.step-result.fail {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.actual-results {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.actual-result-item {
  font-size: 12px;
  color: #4b5563;
  padding: 6px 10px;
  background: #f3f4f6;
  border-radius: 4px;
}

.empty-actual-results {
  font-size: 12px;
  color: #9ca3af;
  padding: 10px;
  background: #f9fafb;
  border-radius: 4px;
  text-align: center;
  border: 1px dashed #e5e7eb;
}

.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.empty-detail svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-detail p {
  margin: 0;
  font-size: 13px;
}

/* AI 日志区域 */
.logs-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.log-count {
  font-size: 11px;
  color: #9ca3af;
}

.logs-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #f5f6f8;
}

.empty-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
  font-size: 13px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-item {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  padding: 6px 8px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-left: 3px solid #d1d5db;
  margin-bottom: 4px;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-item.info {
  border-left-color: #3b82f6;
}

.log-item.success {
  border-left-color: #10b981;
}

.log-item.warning {
  border-left-color: #f59e0b;
}

.log-item.error {
  border-left-color: #ef4444;
}

.log-header-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.log-time {
  color: #9ca3af;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
  flex-shrink: 0;
}

.log-category {
  color: #6b7280;
  flex-shrink: 0;
  font-size: 11px;
}

.log-message {
  color: #374151;
  flex: 1;
  word-break: break-word;
}

.log-expand-btn {
  width: 26px;
  height: 26px;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.log-expand-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.log-expand-btn svg {
  width: 16px;
  height: 16px;
}

/* 展开的详情内容 */
.log-details-content {
  margin-top: 8px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.log-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.details-label {
  font-size: 10px;
  color: #6b7280;
  font-weight: 500;
}

.log-details-header .copy-btn {
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.log-details-header .copy-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.log-details-content pre {
  margin: 0;
  padding: 8px;
  background: #1f2937;
  color: #e5e7eb;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-item.success .log-message {
  color: #10b981;
}

.log-item.error .log-message {
  color: #ef4444;
}

.log-item.warning .log-message {
  color: #f59e0b;
}

.log-item.test .log-message {
  color: #3b82f6;
}
</style>