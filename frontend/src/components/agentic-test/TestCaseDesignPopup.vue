<template>
  <div class="test-case-popup-overlay" @click.self="handleCancel">
    <div class="test-case-popup">
      <div class="popup-header">
        <h3>测试用例设计</h3>
        <span class="case-count" v-if="testCases.length > 0">
          共 {{ testCases.length }} 条用例
        </span>
        <button class="close-btn" @click="handleCancel">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="popup-body">
        <!-- 正在设计状态（无用例时显示居中动画） -->
        <div v-if="isDesigning && testCases.length === 0" class="designing-status">
          <div class="spinner"></div>
          <span>正在设计测试用例...</span>
        </div>

        <!-- 测试用例表格 -->
        <div v-if="testCases.length > 0" class="test-cases-table-container">
          <table class="test-cases-table">
            <thead>
              <tr>
                <th class="col-index">#</th>
                <th class="col-id">用例编号</th>
                <th class="col-title">用例标题</th>
                <th class="col-type">测试类型</th>
                <th class="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(testCase, index) in testCases" :key="testCase.id || index">
                <td class="col-index">{{ index + 1 }}</td>
                <td class="col-id">
                  <span class="cell-text">{{ testCase.id }}</span>
                </td>
                <td class="col-title">
                  <span class="cell-text" :title="testCase.title">{{ testCase.title }}</span>
                </td>
                <td class="col-type">
                  <span class="type-tag" :class="getTypeClass(testCase.type)">
                    {{ getTypeLabel(testCase.type) }}
                  </span>
                </td>
                <td class="col-actions">
                  <div class="action-btns">
                    <button class="action-btn edit-btn" @click="editTestCase(index)" title="编辑">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </button>
                    <button class="action-btn delete-btn" @click="deleteTestCase(index)" title="删除">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 生成中动画（表格底部） -->
          <div v-if="isDesigning" class="generating-indicator">
            <div class="spinner-small"></div>
            <span>正在生成更多用例...</span>
          </div>
        </div>

        <!-- 原始内容预览（放在表格下方） -->
        <div v-if="showRawContent" class="raw-content">
          <div class="raw-content-header">
            <span>原始输出</span>
            <div class="raw-content-actions">
              <button class="copy-btn" @click="copyRawContent" title="复制">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <span v-if="copySuccess">{{ copySuccess }}</span>
              </button>
              <button @click="showRawContent = false">收起</button>
            </div>
          </div>
          <pre>{{ displayRawContent }}</pre>
        </div>

        <!-- 空状态（仅在非设计状态且无用例时显示） -->
        <div v-if="!isDesigning && testCases.length === 0" class="empty-state">
          <span>暂无测试用例</span>
        </div>
      </div>

      <div class="popup-footer">
        <div class="footer-left">
          <button class="add-btn" @click="addTestCase" :disabled="isDesigning">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加用例
          </button>
          <button v-if="testCases.length > 0" class="toggle-raw-btn" @click="showRawContent = !showRawContent">
            {{ showRawContent ? '隐藏原始输出' : '显示原始输出' }}
          </button>
        </div>
        <div class="footer-right">
          <button class="cancel-btn" @click="handleCancel">取消</button>
          <button
            class="confirm-btn"
            @click="handleConfirm"
            :disabled="isDesigning || testCases.length === 0"
          >
            确认并开始测试
          </button>
        </div>
      </div>

      <!-- 编辑弹窗 -->
      <div v-if="editingIndex !== null" class="edit-modal-overlay" @click.self="closeEditModal">
        <div class="edit-modal">
          <div class="edit-modal-header">
            <h4>编辑测试用例</h4>
            <button class="close-btn" @click="closeEditModal">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="edit-modal-body">
            <div class="form-group">
              <label>用例编号</label>
              <input v-model="editingCase.id" type="text" />
            </div>
            <div class="form-group">
              <label>所属模块</label>
              <input v-model="editingCase.module" type="text" />
            </div>
            <div class="form-group">
              <label>用例标题</label>
              <input v-model="editingCase.title" type="text" />
            </div>
            <div class="form-group">
              <label>测试类型</label>
              <select v-model="editingCase.type">
                <option value="Functional">功能测试</option>
                <option value="State">状态测试</option>
                <option value="EdgeCase">边界测试</option>
                <option value="Error">异常测试</option>
              </select>
            </div>
            <div class="form-group">
              <label>前置条件（每行一个）</label>
              <textarea v-model="editingCasePreconditionsText" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>测试步骤（每行一个）</label>
              <textarea v-model="editingCaseStepsText" rows="4"></textarea>
            </div>
            <div class="form-group">
              <label>预期结果（每行一个）</label>
              <textarea v-model="editingCaseExpectResultsText" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>设备GUID（每行一个）</label>
              <textarea v-model="editingCaseDeviceGuidsText" rows="2"></textarea>
            </div>
          </div>
          <div class="edit-modal-footer">
            <button class="cancel-btn" @click="closeEditModal">取消</button>
            <button class="confirm-btn" @click="saveEdit">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestCaseDesignPopup',
  props: {
    initialTestCases: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      testCases: [],
      rawContent: '',
      isDesigning: true,
      showRawContent: false,
      editingIndex: null,
      editingCase: null,
      copySuccess: '',
      // Streaming JSON parsing state
      jsonBuffer: '',
      inJsonArray: false,
      braceDepth: 0,
      currentObjectStart: -1,
      lastParsedIndex: 0  // 记录已解析到的位置
    }
  },
  computed: {
    displayRawContent() {
      // 如果有原始流式内容，直接返回
      if (this.rawContent) {
        return this.rawContent
      }
      // 否则返回测试用例的 JSON 格式
      return JSON.stringify(this.testCases, null, 2)
    },
    editingCasePreconditionsText: {
      get() {
        return (this.editingCase?.preconditions || []).join('\n')
      },
      set(val) {
        if (this.editingCase) {
          this.editingCase.preconditions = val.split('\n').filter(s => s.trim())
        }
      }
    },
    editingCaseStepsText: {
      get() {
        return (this.editingCase?.steps || []).join('\n')
      },
      set(val) {
        if (this.editingCase) {
          this.editingCase.steps = val.split('\n').filter(s => s.trim())
        }
      }
    },
    editingCaseExpectResultsText: {
      get() {
        return (this.editingCase?.expect_results || []).join('\n')
      },
      set(val) {
        if (this.editingCase) {
          this.editingCase.expect_results = val.split('\n').filter(s => s.trim())
        }
      }
    },
    editingCaseDeviceGuidsText: {
      get() {
        return (this.editingCase?.device_guids || []).join('\n')
      },
      set(val) {
        if (this.editingCase) {
          this.editingCase.device_guids = val.split('\n').filter(s => s.trim())
        }
      }
    }
  },
  mounted() {
    // 初始化测试用例
    if (this.initialTestCases.length > 0) {
      this.testCases = [...this.initialTestCases]
      this.isDesigning = false
    }
  },
  watch: {
    // 监听初始测试用例变化
    initialTestCases: {
      handler(newVal) {
        if (newVal && newVal.length > 0) {
          this.testCases = [...newVal]
          this.isDesigning = false
        }
      },
      deep: true
    }
  },
  methods: {
    /**
     * 获取类型显示标签
     */
    getTypeLabel(type) {
      const labels = {
        'Functional': '功能测试',
        'State': '状态测试',
        'EdgeCase': '边界测试',
        'Error': '异常测试',
        'Security': '安全测试',
        'Performance': '性能测试'
      }
      return labels[type] || type
    },

    /**
     * 获取类型样式类
     */
    getTypeClass(type) {
      const classes = {
        'Functional': 'type-functional',
        'State': 'type-state',
        'EdgeCase': 'type-edge',
        'Error': 'type-error',
        'Security': 'type-security',
        'Performance': 'type-performance'
      }
      return classes[type] || 'type-functional'
    },

    /**
     * 添加设计 chunk - 流式解析 JSON 并实时更新表格
     */
    addDesignChunk(chunk) {
      console.log('[StreamingJSON] Received chunk:', chunk.substring(0, 50) + '...')
      this.rawContent += chunk
      this.parseStreamingJson(chunk)
    },

    /**
     * 流式解析 JSON
     * 支持两种格式：
     * 1. 纯 JSON 数组: [{"id": "...", ...}, ...]
     * 2. Markdown 代码块: ```json\n[...\n]\n```
     */
    parseStreamingJson(chunk) {
      // 如果还没有开始解析 JSON 数组，先查找开始标记
      if (!this.inJsonArray) {
        // 尝试找到 JSON 数组开始
        const jsonStart = this.findJsonArrayStart(this.rawContent)
        if (jsonStart !== -1) {
          console.log('[StreamingJSON] Found array start at index:', jsonStart)
          this.inJsonArray = true
          this.jsonBuffer = this.rawContent.substring(jsonStart)
          this.braceDepth = 0
          this.currentObjectStart = -1
          this.lastParsedIndex = 0  // 重置解析位置
          // 重新解析缓冲区
          this.processJsonBuffer()
        }
      } else {
        // 已经在解析中，将新内容添加到缓冲区
        this.jsonBuffer += chunk
        this.processJsonBuffer()
      }
    },

    /**
     * 查找 JSON 数组的起始位置
     */
    findJsonArrayStart(content) {
      // 先尝试找 markdown 代码块中的 JSON
      const codeBlockMatch = content.match(/```(?:json)?\s*\n?\s*\[/)
      if (codeBlockMatch) {
        return content.indexOf('[', codeBlockMatch.index)
      }
      // 直接查找 JSON 数组开始 - 只要找到 [ 后面跟着 { 就开始
      for (let i = 0; i < content.length; i++) {
        if (content[i] === '[') {
          // 检查后面是否有 {（跳过空白）
          for (let j = i + 1; j < content.length; j++) {
            if (content[j] === '{') {
              return i
            }
            // 如果遇到 ] 说明是空数组，继续找
            if (content[j] === ']' && j === i + 1) {
              break
            }
            // 跳过空白字符
            if (!/\s/.test(content[j])) {
              break
            }
          }
        }
      }
      return -1
    },

    /**
     * 处理 JSON 缓冲区，提取完整的对象
     * 只处理新增的内容（从 lastParsedIndex 开始）
     */
    processJsonBuffer() {
      const len = this.jsonBuffer.length

      console.log('[StreamingJSON] Processing buffer, length:', len,
                  'lastParsedIndex:', this.lastParsedIndex,
                  'braceDepth:', this.braceDepth)

      let i = this.lastParsedIndex  // 从上次停止的位置继续

      while (i < len) {
        const char = this.jsonBuffer[i]

        // 处理字符串（需要跳过转义字符）
        if (char === '"') {
          i++
          while (i < len) {
            if (this.jsonBuffer[i] === '\\') {
              // 跳过转义字符
              i += 2
              continue
            }
            if (this.jsonBuffer[i] === '"') {
              i++
              break
            }
            i++
          }
          this.lastParsedIndex = i
          continue
        }

        if (char === '{') {
          if (this.braceDepth === 0) {
            this.currentObjectStart = i
            console.log('[StreamingJSON] Found object start at:', i)
          }
          this.braceDepth++
        } else if (char === '}') {
          this.braceDepth--
          if (this.braceDepth === 0 && this.currentObjectStart !== -1) {
            // 完整的对象已找到
            const objectStr = this.jsonBuffer.substring(this.currentObjectStart, i + 1)
            console.log('[StreamingJSON] Found complete object, length:', objectStr.length)
            this.tryParseAndAddObject(objectStr)
            this.currentObjectStart = -1

            // 清理已处理的缓冲区
            this.jsonBuffer = this.jsonBuffer.substring(i + 1)
            this.lastParsedIndex = 0
            // 找到完整对象后，重新开始处理剩余缓冲区
            this.processJsonBuffer()
            return
          }
        } else if (char === ']' && this.braceDepth === 0) {
          // 数组结束
          this.inJsonArray = false
          console.log('[StreamingJSON] Array ended')
          this.lastParsedIndex = i + 1
          break
        }

        i++
      }

      // 记录当前处理到的位置
      this.lastParsedIndex = i

      // 如果正在解析一个对象，需要保留从该对象开始的内容
      if (this.currentObjectStart > 0) {
        this.jsonBuffer = this.jsonBuffer.substring(this.currentObjectStart)
        this.lastParsedIndex = i - this.currentObjectStart
        this.currentObjectStart = 0
      }
    },

    /**
     * 尝试解析并添加单个 JSON 对象
     */
    tryParseAndAddObject(objectStr) {
      try {
        const obj = JSON.parse(objectStr)
        if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
          console.log('[StreamingJSON] Parsed complete object:', obj.id || 'unknown')
          this.addOrUpdateTestCase(obj)
        }
      } catch (e) {
        // 解析失败，可能是不完整的对象，忽略
        console.debug('[StreamingJSON] Parse failed (incomplete):', e.message)
      }
    },

    /**
     * 添加或更新测试用例
     */
    addOrUpdateTestCase(obj) {
      const testCase = this.normalizeTestCase(obj)

      // 检查是否已存在相同 ID 的用例
      const existingIndex = this.testCases.findIndex(tc => tc.id === testCase.id)

      if (existingIndex >= 0) {
        // 更新现有用例
        this.$set(this.testCases, existingIndex, testCase)
        console.log('[StreamingJSON] Updated test case:', testCase.id)
      } else {
        // 添加新用例 - 使用 push 是响应式的
        this.testCases.push(testCase)
        console.log('[StreamingJSON] Added test case:', testCase.id, 'Total:', this.testCases.length)
      }
      // 注意：isDesigning 状态由外部通过 setDesignComplete/setDesigning 控制，不在这里修改
    },

    /**
     * 标准化测试用例对象
     */
    normalizeTestCase(obj) {
      return {
        id: obj.id || `TC-${String(this.testCases.length + 1).padStart(3, '0')}`,
        module: obj.module || '',
        title: obj.title || obj.test_title || '',
        type: obj.type || 'Functional',
        preconditions: obj.preconditions || [],
        device_guids: obj.device_guids || [],
        steps: obj.steps || [],
        expect_results: obj.expect_results || obj.expected_results || [],
        actual_results: [],
        test_result: 'NotRun'
      }
    },

    /**
     * 设计完成
     */
    setDesignComplete(testCases) {
      this.testCases = testCases.map(tc => ({
        id: tc.id || '',
        module: tc.module || '',
        title: tc.title || '',
        type: tc.type || 'Functional',
        preconditions: tc.preconditions || [],
        device_guids: tc.device_guids || [],
        steps: tc.steps || [],
        expect_results: tc.expect_results || [],
        actual_results: [],
        test_result: 'NotRun'
      }))
      this.isDesigning = false
    },

    /**
     * 设置设计状态
     */
    setDesigning(status) {
      this.isDesigning = status
    },

    /**
     * 添加测试用例
     */
    addTestCase() {
      const newId = `TC-${String(this.testCases.length + 1).padStart(3, '0')}`
      this.testCases.push({
        id: newId,
        module: '',
        title: '新测试用例',
        type: 'Functional',
        preconditions: [],
        device_guids: [],
        steps: [],
        expect_results: [],
        actual_results: [],
        test_result: 'NotRun'
      })
    },

    /**
     * 删除测试用例
     */
    deleteTestCase(index) {
      if (confirm('确定要删除这个测试用例吗？')) {
        this.testCases.splice(index, 1)
      }
    },

    /**
     * 编辑测试用例
     */
    editTestCase(index) {
      this.editingIndex = index
      this.editingCase = JSON.parse(JSON.stringify(this.testCases[index]))
    },

    /**
     * 关闭编辑弹窗
     */
    closeEditModal() {
      this.editingIndex = null
      this.editingCase = null
    },

    /**
     * 保存编辑
     */
    saveEdit() {
      if (this.editingIndex !== null && this.editingCase) {
        this.$set(this.testCases, this.editingIndex, { ...this.editingCase })
        this.closeEditModal()
      }
    },

    /**
     * 确认
     */
    handleConfirm() {
      this.$emit('confirm', this.testCases)
    },

    /**
     * 取消
     */
    handleCancel() {
      this.$emit('cancel')
    },

    /**
     * 复制原始内容
     */
    async copyRawContent() {
      try {
        await navigator.clipboard.writeText(this.displayRawContent)
        this.copySuccess = '已复制'
        setTimeout(() => {
          this.copySuccess = ''
        }, 2000)
      } catch (err) {
        console.error('复制失败:', err)
        this.copySuccess = '复制失败'
        setTimeout(() => {
          this.copySuccess = ''
        }, 2000)
      }
    },

    /**
     * 重置状态
     */
    reset() {
      this.testCases = []
      this.rawContent = ''
      this.isDesigning = true
      this.showRawContent = false
      // 重置流式解析状态
      this.jsonBuffer = ''
      this.inJsonArray = false
      this.braceDepth = 0
      this.currentObjectStart = -1
      this.lastParsedIndex = 0
    }
  }
}
</script>

<style scoped>
/* ========== 弹窗动画 ========== */
.test-case-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.test-case-popup {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
  width: 90%;
  max-width: 900px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.popup-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.popup-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.case-count {
  font-size: 12px;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 12px;
}

.close-btn {
  margin-left: auto;
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

.close-btn svg {
  width: 16px;
  height: 16px;
}

.popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.designing-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--text-secondary);
  animation: pulseFade 1.5s ease-in-out infinite;
}

@keyframes pulseFade {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.raw-content {
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.raw-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-secondary);
  font-size: 12px;
  color: var(--text-tertiary);
}

.raw-content-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.raw-content-header button {
  background: none;
  border: none;
  color: var(--accent-blue);
  cursor: pointer;
  font-size: 12px;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: rgba(79, 70, 229, 0.1);
}

.copy-btn svg {
  width: 14px;
  height: 14px;
}

.raw-content pre {
  margin: 0;
  padding: 12px;
  font-size: 11px;
  font-family: monospace;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 180px;
  overflow-y: auto;
}

.test-cases-table-container {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.test-cases-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.test-cases-table th,
.test-cases-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.test-cases-table th {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  font-weight: 500;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.test-cases-table tbody tr:last-child td {
  border-bottom: none;
}

/* 表格行动画 */
.test-cases-table tbody tr {
  animation: rowSlideIn 0.3s ease-out;
  animation-fill-mode: both;
}

.test-cases-table tbody tr:nth-child(1) { animation-delay: 0.05s; }
.test-cases-table tbody tr:nth-child(2) { animation-delay: 0.1s; }
.test-cases-table tbody tr:nth-child(3) { animation-delay: 0.15s; }
.test-cases-table tbody tr:nth-child(4) { animation-delay: 0.2s; }
.test-cases-table tbody tr:nth-child(5) { animation-delay: 0.25s; }
.test-cases-table tbody tr:nth-child(n+6) { animation-delay: 0.3s; }

@keyframes rowSlideIn {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.test-cases-table tbody tr:hover {
  background: var(--bg-hover);
}

.test-cases-table td {
  color: var(--text-primary);
}

.col-index {
  width: 50px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
}

.col-id {
  width: 100px;
}

.col-title {
  min-width: 180px;
}

.col-type {
  width: 100px;
}

.col-actions {
  width: 80px;
  text-align: center;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.type-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.type-tag.type-functional {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.type-tag.type-state {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.type-tag.type-edge {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.type-tag.type-error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.type-tag.type-security {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.type-tag.type-performance {
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
}

/* 生成中动画 */
.generating-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 13px;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-tertiary);
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.edit-btn:hover {
  color: var(--accent-blue);
  background: rgba(79, 70, 229, 0.1);
}

.delete-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: var(--text-tertiary);
}

.popup-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.footer-left,
.footer-right {
  display: flex;
  gap: 10px;
}

.add-btn,
.toggle-raw-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  background: transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover,
.toggle-raw-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--text-tertiary);
}

.add-btn svg {
  width: 14px;
  height: 14px;
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn,
.confirm-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.confirm-btn {
  background: var(--accent-blue);
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: var(--accent-blue-hover);
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 编辑弹窗 */
.edit-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
  z-index: 2100;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.15s ease-out;
}

.edit-modal {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
  width: 90%;
  max-width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.edit-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
}

.edit-modal-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.edit-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

.form-group textarea {
  resize: vertical;
  min-height: 70px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.edit-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 18px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}
</style>