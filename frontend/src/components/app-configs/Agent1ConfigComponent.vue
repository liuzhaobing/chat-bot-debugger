<template>
  <div class="debug-container" v-if="app">
    <!-- Left Pane: Configuration -->
    <div class="config-pane">
      <div class="pane-header">
        <div class="header-left">
          <button class="back-btn" @click="$router.push('/apps')">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div class="header-info">
            <div class="header-row-top">
              <h1>{{ app.name }}</h1>
              <span class="app-type-badge">{{ app.app_type_name }}</span>
            </div>
            <div class="header-row-bottom">
              <span class="app-id-badge">{{ app.id }}</span>
              <button class="copy-id-btn" @click="copyAppId" title="复制 App ID">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <span class="save-status">{{ saveStatus }}</span>
          <button class="publish-btn" @click="publishApp">发布</button>
        </div>
      </div>

      <div class="pane-body">
        <section class="config-section">
          <div class="section-title">应用基本信息</div>
          <div class="input-group app-name">
            <label>应用名称</label>
            <input v-model="app.name" placeholder="请输入应用名称" />
          </div>
          <div class="input-group">
            <label>应用描述</label>
            <textarea v-model="app.description" placeholder="请输入应用描述"></textarea>
          </div>
        </section>

        <!-- 执行模式选择器 -->
        <section class="config-section">
          <div class="section-title">执行模式</div>
          <p class="section-hint">
            选择应用的执行模式，不同模式适用于不同的使用场景
          </p>
          <div class="mode-selector">
            <div 
              class="mode-option" 
              :class="{ active: app.execution_mode === 'chat' }"
              @click="setExecutionMode('chat')"
            >
              <div class="mode-icon">💬</div>
              <div class="mode-info">
                <div class="mode-name">对话聊天式</div>
                <div class="mode-desc">支持多轮对话，适合助手、顾问类应用</div>
              </div>
            </div>
            <div 
              class="mode-option" 
              :class="{ active: app.execution_mode === 'task' }"
              @click="setExecutionMode('task')"
            >
              <div class="mode-icon">⚡</div>
              <div class="mode-info">
                <div class="mode-name">任务执行式</div>
                <div class="mode-desc">单次执行，适合翻译、生成、处理类应用</div>
              </div>
            </div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">
            {{ app.execution_mode === 'task' ? '任务提示词模板' : '系统提示词' }}
            <div class="prompt-tools">
              <button class="optimize-btn" @click="optimizePrompt" title="优化提示词">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>
                <span>自动优化</span>
              </button>
            </div>
          </div>
          <p class="section-hint">
            {{ promptSectionHint }}
          </p>
          <div class="prompt-editor-container">
            <textarea 
              v-model="app.system_prompt" 
              class="prompt-textarea"
              :placeholder="promptPlaceholder"
              @input="handlePromptInput"
            ></textarea>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">
            参数
            <button class="add-param-icon-btn" @click="openEditParamModal()" title="添加参数">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
          </div>
          <p class="section-hint" v-pre>
            系统会自动从提示词中检测 {{ variable }} 格式的参数，您也可以手动编辑参数配置
          </p>
          <div class="parameters-list" v-if="parametersList.length">
            <div v-for="param in parametersList" :key="param.name" class="parameter-item">
              <div class="param-header">
                <div class="param-name-type">
                  <span class="param-name">{{ param.name }}</span>
                  <span class="param-type">{{ param.type }}</span>
                  <span class="param-required" v-if="param.isRequired">必填</span>
                </div>
                <div class="param-actions-header">
                  <button class="edit-param-btn" @click="openEditParamModal(param.name)" title="编辑参数">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                  </button>
                  <button class="remove-param-btn" @click="removeParameter(param.name)" title="删除参数">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </button>
                </div>
              </div>
              
              <div class="param-description">
                <label>描述:</label>
                <span>{{ param.description }}</span>
              </div>
              
              <div class="param-test-value">
                <label>测试值:</label>
                <textarea
                  v-model="parameterTestValues[param.name]" 
                  :placeholder="`输入 ${param.name} 的测试值`"
                  class="test-value-input"
                />
              </div>
              
              <div class="param-footer">
                <label class="checkbox-label">
                  <input type="checkbox" :checked="param.isRequired" @change="toggleRequired(param.name)" />
                  <span>必填参数</span>
                </label>
              </div>
              <div class="param-footer">
                <div class="param-default" v-if="param.default">
                  <div class="param-default-header" @click="toggleDefaultExpand(param.name)">
                    <span class="label">默认值:</span>
                    <button class="toggle-expand-btn" v-if="param.default.length > 50">
                      {{ isDefaultExpanded(param.name) ? '收起' : '展开' }}
                    </button>
                  </div>
                  <div class="param-default-content" :class="{ 'collapsed': !isDefaultExpanded(param.name) && param.default.length > 50 }">
                    <code>{{ param.default }}</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-parameters">
            <button class="add-param-btn-large" @click="openEditParamModal()">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              点击添加参数
            </button>
            <p v-pre>或在提示词中使用 {{ variable }} 格式定义</p>
          </div>
        </section>

        <!-- 场景管理 -->
        <section class="config-section">
          <scenario-manager 
            v-if="app && app.id" 
            :app-id="app.id" 
            @load-scenario="handleLoadScenario" 
          />
        </section>

        <section class="config-section">
          <div class="section-title">模型配置</div>
          <div class="model-select-wrapper">
             <model-selector ref="modelSelector" v-model="appModel" />
          </div>
          <div class="params-list">
            <div class="param-item">
              <div class="param-header">
                <label>Temperature</label>
                <span class="param-val">{{ currentTemperature }}</span>
              </div>
              <input type="range" v-model.number="currentTemperature" min="0" max="2" step="0.1" />
            </div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">Function Calling Schema</div>
          <p class="section-hint">
            此应用可作为 Function Calling 工具或 MCP 工具使用
          </p>
          <div class="schema-preview-container">
            <button class="copy-schema-btn" @click="copySchemaToClipboard" title="复制到剪贴板">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span>复制</span>
            </button>
            <div class="schema-preview">
              <pre>{{ formattedFunctionSchema }}</pre>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Right Pane: Debug Chat or Task -->
    <task-debug-panel 
      v-if="isTaskMode"
      class="debug-pane"
      :app="app"
      :parameter-values="parameterTestValues"
      :temperature="currentTemperature"
    />

    <div v-else class="debug-pane">
      <div class="debug-header">
        <div class="debug-title">文本对话</div>
        <div class="debug-actions">
           <button class="clear-btn" @click="clearMessages" title="清空对话">
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
           </button>
        </div>
      </div>

      <div class="debug-messages" ref="msgScroll">
        <div v-if="messages.length === 0" class="empty-debug">
           <div class="app-avatar-large" :style="{ backgroundColor: getIconColor(app.name) }">
             {{ app.name[0].toUpperCase() }}
           </div>
           <h3>{{ app.name }}</h3>
           <p>输入问题开始调试您的应用</p>
        </div>
        <message-item 
          v-for="(msg, index) in messages" 
          :key="index"
          :role="msg.role"
          :content="msg.content"
          :reasoning-content="msg.reasoning_content"
          :token-usage="msg.usage"
        />
        <div v-if="isStreaming" class="streaming-indicator">
           <span class="dot"></span>
           思维中...
        </div>
      </div>

      <div class="debug-input-area">
        <div class="input-card">
          <textarea 
            v-model="userInput" 
            placeholder="输入问题进行测试..." 
            @keydown.enter.prevent="sendTestMessage"
          ></textarea>
          <button class="send-btn" @click="sendTestMessage" :disabled="isStreaming || !userInput.trim()">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑参数模态框 -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showEditParamModal" @click.self="showEditParamModal = false">
        <div class="param-modal">
          <div class="modal-header">
            <h3>编辑参数</h3>
            <button class="close-btn-modal" @click="showEditParamModal = false">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="input-group">
              <label>参数名称 <span class="required">*</span></label>
              <input v-model="editParamForm.name" placeholder="如: city, temperature" />
              <span class="hint-text" v-text="`在提示词中使用 {{ ${editParamForm.name} }} 引用此参数`"></span>
            </div>
            <div class="input-group">
              <label>参数类型 <span class="required">*</span></label>
              <select v-model="editParamForm.type">
                <option value="string">string (字符串)</option>
                <option value="number">number (小数)</option>
                <option value="integer">integer (整数)</option>
                <option value="boolean">boolean (布尔值)</option>
                <option value="array">array (数组)</option>
                <option value="object">object (对象/字典)</option>
              </select>
            </div>
            <div class="input-group">
              <label>参数描述 <span class="required">*</span></label>
              <textarea v-model="editParamForm.description" placeholder="描述此参数的用途，这将用于 Function Calling"></textarea>
              <span class="hint-text">清晰的描述有助于 LLM 正确理解和使用此参数</span>
            </div>
            <div class="input-group">
              <label>默认值</label>
              <textarea v-model="editParamForm.default" placeholder="可选，设置参数的默认值" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn-modal" @click="showEditParamModal = false">取消</button>
            <button class="save-btn-modal" @click="saveParamEdit">保存</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios'
import ModelSelector from '../model-square/ModelSelector.vue'
import MessageItem from '../chat-completion/MessageItem.vue'
import TaskDebugPanel from './TaskDebugPanel.vue'
import ScenarioManager from './ScenarioManager.vue'
import { mapState } from 'vuex'
import nunjucks from 'nunjucks'

export default {
  name: 'Agent1ConfigComponent',
  components: { ModelSelector, MessageItem, TaskDebugPanel, ScenarioManager },
  props: {
    appId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      app: null,
      loading: true,
      userInput: '',
      messages: [],
      isStreaming: false,
      saveStatus: '已保存',
      saveTimer: null,
      currentTemperature: 0.7,
      currentProviderId: null,
      
      // Function Calling Parameters 管理
      parameters: {
        type: 'object',
        properties: {},
        required: []
      },
      
      // 参数测试值（用于调试时填充）
      parameterTestValues: {},
      
      // 编辑参数的模态框
      showEditParamModal: false,
      editingParam: null,
      editParamForm: {
        name: '',
        type: 'string',
        description: '',
        default: ''
      },
      expandedDefaults: {}
    }
  },
  computed: {
    ...mapState('modelSquare', ['selectedModel']),
    appModel: {
      get() {
        if (!this.app) return null
        return {
          provider_id: this.app.provider_id,
          model_name: this.app.model_name
        }
      },
      set(val) {
        if (this.app && val) {
          this.app.provider_id = val.provider_id
          this.app.model_name = val.model_name
        }
      }
    },
    formattedFunctionSchema() {
      if (!this.app) return '{}'
      return JSON.stringify(this.app.get_function_schema || this.generateFunctionSchema(), null, 2)
    },
    parametersList() {
      // 将 parameters.properties 转换为数组用于展示
      if (!this.parameters.properties) return []
      return Object.entries(this.parameters.properties).map(([name, def]) => ({
        name,
        ...def,
        isRequired: this.parameters.required && this.parameters.required.includes(name)
      }))
    },
    // 根据执行模式动态显示提示词提示文本
    promptSectionHint() {
      if (!this.app) return ''
      return this.app.execution_mode === 'task'
        ? '编写任务模板，使用 {{ variable }} 定义参数，执行时将直接作为用户消息发送'
        : '编写应用的系统提示词，定义应用的行为和能力'
    },
    // 根据执行模式动态显示提示词占位符
    promptPlaceholder() {
      if (!this.app) return ''
      return this.app.execution_mode === 'task'
        ? '请将以下文本翻译成{{target_language}}:\n\n{{text}}'
        : '你是一个专业的助手...'
    },
    // 是否为任务执行模式
    isTaskMode() {
      return this.app && this.app.execution_mode === 'task'
    }
  },
  methods: {
    async fetchApp() {
      this.loading = true
      try {
        const res = await axios.get(`/api/apps/${this.appId}/`)
        this.app = res.data
        if (!this.app.configuration) this.app.configuration = { temperature: 0.7 }
        this.currentTemperature = this.app.configuration.temperature || 0.7
        this.currentProviderId = this.app.provider_id || null
        
        // 初始化 execution_mode（向后兼容旧应用）
        if (!this.app.execution_mode) {
          this.app.execution_mode = 'chat'
        }
        
        // 加载 parameters
        if (this.app.parameters && this.app.parameters.properties) {
          this.parameters = this.app.parameters
        } else {
          this.parameters = {
            type: 'object',
            properties: {},
            required: []
          }
        }
        
        // 解析 system_prompt 中的参数
        this.parseParametersFromPrompt()
        
        // 初始化测试值
        this.initializeTestValues()
      } catch (e) {
        window.$message.error('加载应用失败')
      } finally {
        this.loading = false
      }
    },
    
    handleLoadScenario(parameters) {
      if (!parameters) return
      
      // 更新参数测试值
      Object.entries(parameters).forEach(([key, value]) => {
        // 如果该参数在当前定义中存在，则更新值
        // 或者即使不存在也更新（视需求而定，这里选择直接更新，支持动态参数）
        this.$set(this.parameterTestValues, key, value)
      })
      
      // 如果有新的参数不在 parameters 定义中，是否要自动添加？
      // 暂时只更新值，不修改参数定义（Definition）
    },
    
    // 设置执行模式
    async setExecutionMode(mode) {
      if (this.app) {
        if (this.app.execution_mode === mode) return

        const confirmed = await window.$confirm({
          title: '切换执行模式',
          message: '切换模式可能会影响当前的调试上下文，确定要切换吗？',
          type: 'warning',
          confirmText: '切换'
        })

        if (confirmed) {
          this.app.execution_mode = mode
          // 切换模式时清空调试对话
          this.messages = []
          this.triggerAutoSavePrompt()
        }
      }
    },
    
    handlePromptInput() {
      this.parseParametersFromPrompt()
      this.triggerAutoSavePrompt()
    },
    
    async copyAppId() {
      try {
        await navigator.clipboard.writeText(this.app.id)
        window.$message.success('App ID 已复制')
      } catch (e) {
        window.$message.error('复制失败')
      }
    },
    
    parseParametersFromPrompt() {
      /**
       * 从 system_prompt 中自动解析参数
       * 改进版：排除 for 循环中的局部变量
       */
      const prompt = this.app.system_prompt || ''
      const detectedParams = new Set()
      const localVars = new Set()

      // 1. 先识别 for 循环产生的局部变量
      // 匹配 {% for item in list %} 或 {% for k, v in dict %}
      const loopDefRegex = /\{%\s*for\s+([a-zA-Z0-9_$,\s]+)\s+in\s+/g
      let match
      while ((match = loopDefRegex.exec(prompt)) !== null) {
        // match[1] 可能是 "item" 或 "key, value"
        const vars = match[1].split(',').map(s => s.trim())
        vars.forEach(v => {
          if (v) localVars.add(v)
        })
      }

      // 2. 匹配引用 {{ variable... }}
      const printRegex = /\{\{\s*([a-zA-Z0-9_$]+)/g
      while ((match = printRegex.exec(prompt)) !== null) {
        const varName = match[1]
        // 排除局部变量、保留字、已存在的
        if (varName !== 'super' && !localVars.has(varName)) {
           detectedParams.add(varName)
        }
      }

      // 3. 匹配循环源对象 {% for x in variable %}
      // 注意：循环源对象本身应该是参数
      const loopSourceRegex = /\{%\s*for\s+[\w,\s]+\s+in\s+([a-zA-Z0-9_$]+)/g
      while ((match = loopSourceRegex.exec(prompt)) !== null) {
        const sourceName = match[1]
        if (!localVars.has(sourceName)) {
           detectedParams.add(sourceName)
        }
      }

      // 为新检测到的参数添加默认配置
      detectedParams.forEach(paramName => {
        if (!this.parameters.properties[paramName]) {
          // 尝试根据名称推断类型
          let type = 'string'
          if (paramName.includes('list') || paramName.includes('array') || paramName.endsWith('s') || paramName.includes('messages')) {
             type = 'array'
          } else if (paramName.includes('obj') || paramName.includes('data') || paramName.includes('meta')) {
             type = 'object'
          }
          
          this.$set(this.parameters.properties, paramName, {
            type: type,
            description: `参数 ${paramName}`,
            default: ''
          })
        }
      })
      
      // 不删除未检测到的参数，保留用户手动配置
    },
    
    initializeTestValues() {
      // 初始化参数测试值
      Object.keys(this.parameters.properties).forEach(paramName => {
        if (!this.parameterTestValues[paramName]) {
          const param = this.parameters.properties[paramName]
          this.$set(this.parameterTestValues, paramName, param.default || '')
        }
      })
    },
    
    triggerAutoSavePrompt() {
      this.saveStatus = '保存中...'
      if (this.saveTimer) clearTimeout(this.saveTimer)
      this.saveTimer = setTimeout(async () => {
        try {
          await axios.patch(`/api/apps/${this.app.id}/auto_save_prompt/`, {
            system_prompt: this.app.system_prompt
          })
          this.saveStatus = '已保存'
        } catch (e) {
          this.saveStatus = '保存失败'
        }
      }, 2000)
    },
    
    // 参数管理方法
    openEditParamModal(paramName = null) {
      if (paramName) {
        const param = this.parameters.properties[paramName]
        this.editingParam = paramName
        this.editParamForm = {
          name: paramName,
          type: param.type || 'string',
          description: param.description || '',
          default: param.default || ''
        }
      } else {
        this.editingParam = null
        this.editParamForm = {
          name: '',
          type: 'string',
          description: '',
          default: ''
        }
      }
      this.showEditParamModal = true
    },
    
    saveParamEdit() {
      if (!this.editParamForm.name.trim()) {
        window.$message.error('参数名称不能为空')
        return
      }
      
      // 检查名称冲突
      if ((!this.editingParam || this.editingParam !== this.editParamForm.name) && 
          this.parameters.properties[this.editParamForm.name]) {
        window.$message.error('参数名称已存在')
        return
      }
      
      // 如果修改了参数名称，需要删除旧的
      if (this.editingParam && this.editingParam !== this.editParamForm.name) {
        this.$delete(this.parameters.properties, this.editingParam)
        // 更新 required 数组
        const reqIndex = this.parameters.required.indexOf(this.editingParam)
        if (reqIndex > -1) {
          this.parameters.required.splice(reqIndex, 1)
          this.parameters.required.push(this.editParamForm.name)
        }
        // 迁移测试值
        if (this.parameterTestValues[this.editingParam]) {
           this.$set(this.parameterTestValues, this.editParamForm.name, this.parameterTestValues[this.editingParam])
           this.$delete(this.parameterTestValues, this.editingParam)
        }
      }
      
      // 更新参数定义
      this.$set(this.parameters.properties, this.editParamForm.name, {
        type: this.editParamForm.type,
        description: this.editParamForm.description || `参数 ${this.editParamForm.name}`,
        default: this.editParamForm.default
      })
      
      // 初始化新参数的测试值
      if (!this.parameterTestValues[this.editParamForm.name]) {
         this.$set(this.parameterTestValues, this.editParamForm.name, this.editParamForm.default || '')
      }
      
      this.showEditParamModal = false
      this.triggerAutoSavePrompt()
    },
    
    removeParameter(paramName) {
      this.$delete(this.parameters.properties, paramName)
      // 从 required 中移除
      const index = this.parameters.required.indexOf(paramName)
      if (index > -1) {
        this.parameters.required.splice(index, 1)
      }
      // 删除测试值
      this.$delete(this.parameterTestValues, paramName)
      this.triggerAutoSavePrompt()
    },
    
    toggleRequired(paramName) {
      const index = this.parameters.required.indexOf(paramName)
      if (index > -1) {
        this.parameters.required.splice(index, 1)
      } else {
        this.parameters.required.push(paramName)
      }
      this.triggerAutoSavePrompt()
    },
    
    generateFunctionSchema() {
      return {
        type: 'function',
        function: {
          name: this.app.name,
          description: this.app.description,
          parameters: this.parameters
        }
      }
    },
    async publishApp() {
      if (!this.app) return
      
      // 获取当前选择的模型和供应商 (已通过 v-model 绑定到 this.app)
      const modelName = this.app.model_name
      const providerId = this.app.provider_id
      
      if (!modelName) {
        window.$message.warning('请选择一个模型')
        return
      }
      
      try {
        const payload = {
          execution_mode: this.app.execution_mode || 'chat',
          name: this.app.name,
          description: this.app.description,
          icon_url: this.app.icon_url,
          system_prompt: this.app.system_prompt,
          provider_id: providerId,
          model_name: modelName,
          configuration: {
            temperature: this.currentTemperature
          },
          parameters: this.parameters
        }
        
        await axios.post(`/api/apps/${this.app.id}/publish/`, payload)
        window.$message.success('应用发布成功')
        this.saveStatus = '已发布'
      } catch (e) {
        const errorMsg = e.response?.data?.message || e.response?.data?.error || '发布失败'
        window.$message.error(errorMsg)
      }
    },
    async sendTestMessage() {
      if (this.isStreaming || !this.userInput.trim()) return
      
      const modelName = this.app.model_name
      const providerId = this.app.provider_id
      if (!modelName) {
        window.$message.warning('请选择一个模型进行调试')
        return
      }

      const userText = this.userInput.trim()
      this.userInput = ''
      
      // Task 模式：每次执行前清空历史消息
      if (this.app.execution_mode === 'task') {
        this.messages = []
      }
      
      this.messages.push({ role: 'user', content: userText })
      this.scrollToBottom()

      this.isStreaming = true
      let assistantMsg = { role: 'assistant', content: '', reasoning_content: '', usage: null }
      this.messages.push(assistantMsg)

      try {
        // 使用测试值替换提示词中的参数
        // 使用 nunjucks 渲染模板，支持更复杂的 Jinja2 语法
        nunjucks.configure({ autoescape: false })
        const finalPrompt = nunjucks.renderString(this.app.system_prompt || '', this.parameterTestValues)

        let payload
        
        if (this.app.execution_mode === 'task') {
          // ========== 任务执行式 (Task Mode) ==========
          // 模板替换后 + 用户输入，作为单条 user 消息发送
          const taskMessage = finalPrompt ? `${finalPrompt}\n\n${userText}` : userText
          payload = {
            messages: [
              { role: 'user', content: taskMessage }
            ],
            provider_id: providerId,
            model: modelName,
            temperature: this.currentTemperature,
            stream: true
          }
        } else {
          // ========== 对话聊天式 (Chat Mode, 默认) ==========
          // system_prompt 作为 system 消息，支持多轮上下文
          payload = {
            messages: [
              { role: 'system', content: finalPrompt },
              ...this.messages.slice(0, -1)  // 不包含刚刚添加的空 assistant 消息
            ],
            provider_id: providerId,
            model: modelName,
            temperature: this.currentTemperature,
            stream: true
          }
        }

        const response = await fetch('/api/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`Server Error (${response.status}): ${errorText}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()
          for (const line of lines) {
            const trimmed = line.trim()
            if (trimmed.startsWith('data: ')) {
              const jsonStr = trimmed.slice(6)
              if (jsonStr === '[DONE]') continue
              try {
                const data = JSON.parse(jsonStr)
                if (data.choices && data.choices[0].delta.reasoning_content) {
                  assistantMsg.reasoning_content += data.choices[0].delta.reasoning_content
                }
                if (data.choices && data.choices[0].delta.content) {
                  assistantMsg.content += data.choices[0].delta.content
                }
                // 收集 usage 信息
                if (data.usage) {
                  assistantMsg.usage = data.usage
                }
              } catch (e) {
                // 忽略流式解析错误
              }
            }
          }
          this.scrollToBottom()
        }
      } catch (e) {
        assistantMsg.content = '出故障了: ' + e.message
      } finally {
        this.isStreaming = false
      }
    },
    clearMessages() {
      this.messages = []
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.msgScroll
        if (el) el.scrollTop = el.scrollHeight
      })
    },
    optimizePrompt() {
      window.$message.info('提示词优化功能正在开发中...')
    },
    getIconColor(name) {
      if (!name) return '#4f46e5'
      const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899', '#6366f1']
      let hash = 0
      for (let i = 0; i < name.length; i++) {
          hash = name.charCodeAt(i) + ((hash << 5) - hash)
      }
      return colors[Math.abs(hash) % colors.length]
    },
    
    copySchemaToClipboard() {
      const schema = this.formattedFunctionSchema
      
      // 使用现代 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(schema).then(() => {
          window.$message.success('Schema 已复制到剪贴板')
        }).catch(() => {
          this.fallbackCopyToClipboard(schema)
        })
      } else {
        this.fallbackCopyToClipboard(schema)
      }
    },
    
    fallbackCopyToClipboard(text) {
      // 降级方案：使用 textarea
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        window.$message.success('Schema 已复制到剪贴板')
      } catch (err) {
        window.$message.error('复制失败，请手动复制')
      }
      document.body.removeChild(textarea)
    },
    
    toggleDefaultExpand(paramName) {
      this.$set(this.expandedDefaults, paramName, !this.expandedDefaults[paramName])
    },
    
    isDefaultExpanded(paramName) {
      return !!this.expandedDefaults[paramName]
    }
  },
  mounted() {
    this.fetchApp()
  }
}
</script>

<style scoped>
/* 复用原有样式 */
.debug-container {
  display: flex;
  height: 100%;
  background-color: #f8fafc;
  overflow: hidden;
}

.config-pane {
  width: 50%;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

.pane-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.back-btn:hover { background-color: #f1f5f9; }

.pane-header h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.app-type-badge {
  background-color: #f5f3ff;
  color: #6366f1;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.save-status {
  font-size: 0.75rem;
  color: #94a3b8;
}

.publish-btn {
  background-color: #4f46e5;
  color: #ffffff;
  border: none;
  padding: 6px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.pane-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: -4px 0 0 0;
}

/* 执行模式选择器样式 */
.mode-selector {
  display: flex;
  gap: 12px;
}

.mode-option {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #ffffff;
}

.mode-option:hover {
  border-color: #c7d2fe;
  background-color: #fafafa;
}

.mode-option.active {
  border-color: #6366f1;
  background-color: #f5f3ff;
}

.mode-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.mode-info {
  flex: 1;
}

.mode-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #1e293b;
  margin-bottom: 4px;
}

.mode-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.4;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
}

.input-group input, .input-group textarea {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  color: #475569;
  background-color: #fcfcfd;
}

.prompt-editor-container {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background-color: #fcfcfd;
}

.prompt-tools {
  display: flex;
  align-items: center;
}

.optimize-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f5f3ff;
  color: #8b5cf6;
  border: 1px solid #ddd6fe;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.optimize-btn:hover {
  background-color: #ede9fe;
  border-color: #c4b5fd;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.optimize-btn svg {
  color: #7c3aed;
}

.prompt-textarea {
  width: 100%;
  height: 240px;
  border: none;
  padding: 16px;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.6;
  background: transparent;
  outline: none;
  resize: vertical;
  color: #334155;
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.variable-item label {
  width: 100px;
  font-size: 0.85rem;
  color: #475569;
  font-family: monospace;
}

.variable-value-textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #475569;
  background-color: #fcfcfd;
}

/* Parameters 样式 */
.add-param-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f5f3ff;
  color: #6366f1;
  border: 1px solid #ddd6fe;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.add-param-btn:hover {
  background-color: #ede9fe;
  border-color: #c4b5fd;
}

.parameters-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.parameter-item {
  padding: 20px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.param-name-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-name {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  font-family: 'Monaco', 'Menlo', monospace;
}

.param-type {
  font-size: 0.75rem;
  padding: 3px 10px;
  background-color: #e0e7ff;
  color: #4f46e5;
  border-radius: 6px;
  font-weight: 600;
}

.param-required {
  font-size: 0.75rem;
  padding: 3px 10px;
  background-color: #fee2e2;
  color: #ef4444;
  border-radius: 6px;
  font-weight: 600;
}

.param-actions-header {
  display: flex;
  gap: 8px;
}

.edit-param-btn {
  background: transparent;
  border: none;
  color: #6366f1;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-param-btn:hover {
  background-color: #f5f3ff;
}

.remove-param-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-param-btn:hover {
  background-color: #fee2e2;
  color: #ef4444;
}

.param-description {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
}

.param-description label {
  font-weight: 600;
  color: #475569;
  min-width: 50px;
}

.param-test-value {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-test-value label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  min-width: 60px;
}

.test-value-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  color: #475569;
  background-color: #f8fafc;
  transition: all 0.2s;
}

.test-value-input:focus {
  border-color: #6366f1;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.param-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.param-default {
  font-size: 0.8rem;
  color: #94a3b8;
  width: 100%;
}

.param-default-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  cursor: pointer;
  user-select: none;
}

.param-default-header .label {
  font-weight: 600;
}

.toggle-expand-btn {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 0;
}

.toggle-expand-btn:hover {
  text-decoration: underline;
}

.param-default-content {
  background-color: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.param-default-content code {
  display: block;
  padding: 6px 8px;
  font-family: monospace;
  color: #475569;
  white-space: pre-wrap;
  word-break: break-all;
}

.param-default-content.collapsed code {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.param-actions {
  display: flex;
  gap: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #64748b;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.empty-parameters {
  padding: 48px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #94a3b8;
  background-color: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
  transition: all 0.2s;
}

.empty-parameters:hover {
  border-color: #cbd5e1;
  background-color: #f1f5f9;
}

.empty-parameters p {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
}

.add-param-btn-large {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  color: #6366f1;
  border: 1px solid #e2e8f0;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.add-param-btn-large:hover {
  border-color: #6366f1;
  background-color: #f5f3ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2);
}

.add-param-btn-large svg {
  width: 18px;
  height: 18px;
}

.add-param-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.add-param-icon-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: #f5f3ff;
  transform: scale(1.05);
}

/* 参数模态框样式 */
.param-modal {
  background: #ffffff;
  width: 540px;
  border-radius: 20px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.param-modal .modal-header {
  padding: 24px 28px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.param-modal .modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ffffff;
}

.param-modal .modal-header .close-btn {
  color: #ffffff;
  opacity: 0.9;
}

.param-modal .modal-header .close-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.2);
}

.param-modal .modal-header .close-btn-modal {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #ffffff;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.param-modal .modal-header .close-btn-modal:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: rotate(90deg);
}

.param-modal .modal-body {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 500px;
  overflow-y: auto;
}

.param-modal .input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-modal .input-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #334155;
}

.param-modal .input-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  color: #475569;
  background-color: #fcfcfd;
  cursor: pointer;
  transition: all 0.2s;
}

.param-modal .input-group select:focus {
  border-color: #6366f1;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.param-modal .input-group textarea {
  min-height: 80px;
  resize: vertical;
}

.hint-text {
  font-size: 0.8rem;
  color: #94a3b8;
  font-style: italic;
}

.param-modal .modal-footer {
  padding: 20px 28px;
  background-color: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #e2e8f0;
}

.cancel-btn-modal {
  padding: 10px 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #64748b;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.cancel-btn-modal:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
}

.save-btn-modal {
  padding: 10px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.3s;
  box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.3);
}

.save-btn-modal:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);
}

.required {
  color: #ef4444;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(8px);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

.params-list {
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-header {
  display: flex;
  justify-content: space-between;
}

.param-header label {
  font-size: 0.85rem;
  font-weight: 600;
}

.param-val {
  font-size: 0.85rem;
  color: #4f46e5;
  font-weight: 700;
}

.schema-preview-container {
  position: relative;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
}

.copy-schema-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  z-index: 10;
}

.copy-schema-btn:hover {
  background-color: #6366f1;
  border-color: #6366f1;
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
}

.copy-schema-btn svg {
  width: 14px;
  height: 14px;
}

.schema-preview {
  background-color: #f8fafc;
  overflow-x: auto;
}

.schema-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.6;
}

/* Debug Pane */
.debug-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
}

.debug-header {
  padding: 16px 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.debug-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.clear-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
}

.debug-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-debug {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  padding-bottom: 100px;
}

.app-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 16px;
}

.empty-debug h3 {
    margin: 0 0 8px 0;
    color: #1e293b;
}

.debug-input-area {
  padding: 24px;
  background: linear-gradient(180deg, transparent 0%, #f8fafc 40%);
}

.input-card {
  max-width: 800px;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 12px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.input-card textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  resize: none;
  padding: 4px;
  line-height: 1.5;
  min-height: 24px;
}

.send-btn {
  background-color: #4f46e5;
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.streaming-indicator {
    padding: 12px;
    font-size: 0.85rem;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 8px;
}

.streaming-indicator .dot {
    width: 6px;
    height: 6px;
    background: #94a3b8;
    border-radius: 50%;
    animation: blink 1.5s infinite;
}

@keyframes blink {
    0% { opacity: 0.2; }
    50% { opacity: 1; }
    100% { opacity: 0.2; }
}
/* New Header Styles */
.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-row-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-row-bottom {
  display: flex;
  align-items: center;
  gap: 6px;
}

.app-id-badge {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 11px;
  color: #a0aec0;
  letter-spacing: 0.02em;
}

.copy-id-btn {
  padding: 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #cbd5e0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: color 0.2s;
}

.copy-id-btn:hover {
  color: #718096;
  background-color: #f7fafc;
}
</style>
