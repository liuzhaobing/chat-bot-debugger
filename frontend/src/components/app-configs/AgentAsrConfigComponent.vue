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

        <section class="config-section">
          <div class="section-title">
            系统提示词
            <div class="prompt-tools">
              <button class="optimize-btn" @click="optimizePrompt" title="优化提示词">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>
                <span>自动优化</span>
              </button>
            </div>
          </div>
          <p class="section-hint">
            定义ASR应用的行为和上下文理解能力，可以包含领域专业术语和识别规则
          </p>
          <div class="prompt-editor-container">
            <textarea 
              v-model="app.system_prompt" 
              class="prompt-textarea"
              placeholder="你是一个专业的语音识别助手，专门处理智能家居设备的语音指令..."
              @input="handlePromptInput"
            ></textarea>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">
            参数配置
            <button class="add-param-icon-btn" @click="openEditParamModal()" title="添加参数">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
          </div>
          <p class="section-hint">
            配置ASR应用的输入参数，支持音频数据、上下文信息等
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
            </div>
          </div>
          <div v-else class="empty-parameters">
            <button class="add-param-btn-large" @click="openEditParamModal()">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              点击添加参数
            </button>
            <p>定义ASR应用的输入参数结构</p>
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
            <div class="param-item">
              <div class="param-header">
                <label>Max Tokens</label>
                <span class="param-val">{{ currentMaxTokens }}</span>
              </div>
              <input type="range" v-model.number="currentMaxTokens" min="100" max="4000" step="100" />
            </div>
          </div>
        </section>

        <section class="config-section">
          <div class="section-title">Function Calling Schema</div>
          <p class="section-hint">
            此ASR应用可作为 Function Calling 工具或 MCP 工具使用
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

    <!-- Right Pane: ASR Testing -->
    <div class="debug-pane">
      <div class="debug-header">
        <div class="debug-title">🎙️ ASR 测试</div>
        <div class="debug-actions">
          <button class="clear-btn" @click="clearTestResults" title="清空测试结果">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>

      <div class="debug-messages" ref="msgScroll">
        <div v-if="testResults.length === 0" class="empty-debug">
          <div class="app-avatar-large" :style="{ backgroundColor: getIconColor(app.name) }">
            🎙️
          </div>
          <h3>{{ app.name }}</h3>
          <p>上传音频文件或录制语音来测试ASR识别效果</p>
        </div>
        
        <div v-for="(result, index) in testResults" :key="index" class="test-result-item">
          <div class="result-header">
            <div class="result-info">
              <span class="result-time">{{ formatTime(result.timestamp) }}</span>
              <span class="result-status" :class="result.status">{{ getStatusText(result.status) }}</span>
            </div>
            <div class="result-actions">
              <button class="play-audio-btn" @click="playAudio(result.audioData)" v-if="result.audioData" title="播放音频">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              </button>
            </div>
          </div>
          
          <div class="result-content">
            <div class="recognition-result" v-if="result.recognizedText">
              <label>识别结果:</label>
              <div class="result-text">{{ result.recognizedText }}</div>
            </div>
            <div class="error-message" v-if="result.error">
              <label>错误信息:</label>
              <span class="error-text">{{ result.error }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="isProcessing" class="processing-indicator">
          <span class="dot"></span>
          正在处理音频...
        </div>
      </div>

      <div class="debug-input-area">
        <div class="input-card">
          <div class="audio-input-section">
            <!-- 统一的音频文件预览区域 -->
            <div v-if="hasAudioFile" class="unified-audio-preview">
              <div class="audio-preview-card full-width">
                <div class="audio-preview-header">
                  <div class="audio-icon" :class="{ 'recording-icon': isRecordedAudio }">
                    <svg v-if="!isRecordedAudio" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M9 18V5l12-2v13"></path>
                      <circle cx="6" cy="18" r="3"></circle>
                      <circle cx="18" cy="16" r="3"></circle>
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                      <line x1="12" y1="19" x2="12" y2="23"></line>
                      <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                  </div>
                  <div class="audio-file-info">
                    <div class="file-name-row">
                      <span class="file-name" :title="currentAudioFileName">{{ currentAudioFileName }}</span>
                      <span class="file-format-badge" :class="{ 'recording-badge': isRecordedAudio }">
                        {{ currentAudioFormat.toUpperCase() }}
                      </span>
                    </div>
                    <div class="file-meta">
                      <span class="file-size">{{ currentAudioSize }}</span>
                      <span class="file-separator">•</span>
                      <span class="file-type" v-if="!isRecordedAudio">音频文件</span>
                      <span class="recording-duration" v-else>{{ formatDuration(recordingDuration) }}</span>
                    </div>
                  </div>
                </div>
                <div class="audio-preview-actions">
                  <button class="audio-action-btn play-btn" @click="playCurrentAudio" title="播放音频">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                  </button>
                  <button class="audio-action-btn delete-btn" @click="clearCurrentAudio" title="删除音频">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 6h18"></path>
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- 只有在没有音频文件时才显示输入选项 -->
            <div v-if="!hasAudioFile">
              <div class="input-tabs">
                <button 
                  class="tab-btn" 
                  :class="{ active: activeTab === 'upload' }"
                  @click="activeTab = 'upload'"
                >
                  📁 上传文件
                </button>
                <button 
                  class="tab-btn" 
                  :class="{ active: activeTab === 'record' }"
                  @click="activeTab = 'record'"
                >
                  🎙️ 录音
                </button>
              </div>
              
              <div v-if="activeTab === 'upload'" class="upload-section">
                <input 
                  type="file" 
                  ref="audioFileInput"
                  accept="audio/*"
                  @change="handleFileUpload"
                  style="display: none"
                />
                <button class="upload-btn-enhanced" @click="$refs.audioFileInput.click()">
                  <div class="upload-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </div>
                  <div class="upload-text">
                    <span class="upload-title">选择音频文件</span>
                    <span class="upload-subtitle">支持 WAV, MP3, FLAC, OPUS 格式</span>
                  </div>
                </button>
              </div>
              
              <div v-if="activeTab === 'record'" class="record-section">
                <button 
                  class="record-btn-enhanced" 
                  :class="{ recording: isRecording }"
                  @click="toggleRecording"
                >
                  <div class="record-icon" :class="{ recording: isRecording }">
                    <svg v-if="!isRecording" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                      <line x1="12" y1="19" x2="12" y2="23"></line>
                      <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                    </svg>
                  </div>
                  <div class="record-text">
                    <span class="record-title">{{ isRecording ? '停止录音' : '开始录音' }}</span>
                    <span class="record-subtitle" v-if="!isRecording">点击开始录制语音</span>
                    <span class="record-subtitle recording-time" v-else>录音时长: {{ formatDuration(recordingDuration) }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <div class="context-input">
            <label>上下文信息 (可选):</label>
            <textarea
              v-model="contextInput"
              placeholder="输入上下文信息，帮助提高识别准确度..."
              rows="2"
            ></textarea>
          </div>

          <button 
            class="test-btn" 
            @click="runAsrTest" 
            :disabled="isProcessing || (!selectedAudioFile && !recordedAudio)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            {{ isProcessing ? '处理中...' : '开始识别' }}
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
              <input v-model="editParamForm.name" placeholder="如: audio_data, context" />
            </div>
            <div class="input-group">
              <label>参数类型 <span class="required">*</span></label>
              <select v-model="editParamForm.type">
                <option value="string">string (字符串)</option>
                <option value="object">object (对象)</option>
                <option value="array">array (数组)</option>
                <option value="boolean">boolean (布尔值)</option>
              </select>
            </div>
            <div class="input-group">
              <label>参数描述 <span class="required">*</span></label>
              <textarea v-model="editParamForm.description" placeholder="描述此参数的用途"></textarea>
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
import ScenarioManager from './ScenarioManager.vue'
import AudioRecorder from '../../utils/audioRecorder.js'
import { mapState } from 'vuex'

export default {
  name: 'AgentAsrConfigComponent',
  components: { ModelSelector, ScenarioManager },
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
      saveStatus: '已保存',
      saveTimer: null,
      currentTemperature: 0.7,
      currentMaxTokens: 1000,
      currentProviderId: null,

      // 参数管理
      parameters: {
        type: 'object',
        properties: {},
        required: []
      },
      parameterTestValues: {},
      showEditParamModal: false,
      editingParam: null,
      editParamForm: {
        name: '',
        type: 'string',
        description: '',
        default: ''
      },
      
      // ASR 测试相关
      activeTab: 'upload',
      selectedAudioFile: null,
      recordedAudio: null,
      recordedAudioFormat: null,
      isRecording: false,
      recordingDuration: 0,
      recordingTimer: null,
      audioRecorder: null,
      audioChunks: [],
      contextInput: '',
      isProcessing: false,
      testResults: []
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
      return JSON.stringify(this.generateFunctionSchema(), null, 2)
    },
    parametersList() {
      if (!this.parameters.properties) return []
      return Object.entries(this.parameters.properties).map(([name, def]) => ({
        name,
        ...def,
        isRequired: this.parameters.required && this.parameters.required.includes(name)
      }))
    },
    // 统一音频文件管理的计算属性
    hasAudioFile() {
      return !!(this.selectedAudioFile || this.recordedAudio)
    },
    isRecordedAudio() {
      return !!this.recordedAudio
    },
    currentAudioFileName() {
      if (this.recordedAudio) {
        return `录音_${new Date().toLocaleTimeString()}.wav`
      }
      if (this.selectedAudioFile) {
        return this.truncateFileName(this.selectedAudioFile.name)
      }
      return ''
    },
    currentAudioFormat() {
      if (this.recordedAudio) {
        return this.recordedAudioFormat || 'wav'
      }
      if (this.selectedAudioFile) {
        return this._detectAudioFormat(this.selectedAudioFile)
      }
      return 'wav'
    },
    currentAudioSize() {
      const file = this.selectedAudioFile || this.recordedAudio
      return file ? this.formatFileSize(file.size) : '0 B'
    }
  },
  methods: {
    async fetchApp() {
      this.loading = true
      try {
        const res = await axios.get(`/api/apps/${this.appId}/`)
        this.app = res.data
        
        // 初始化模型配置
        if (!this.app.configuration) this.app.configuration = { temperature: 0.7, max_tokens: 1000 }
        this.currentTemperature = this.app.configuration.temperature || 0.7
        this.currentMaxTokens = this.app.configuration.max_tokens || 1000
        this.currentProviderId = this.app.provider_id || null
        
        // 初始化默认参数
        if (!this.app.parameters || !this.app.parameters.properties) {
          this.initializeDefaultParameters()
        } else {
          this.parameters = this.app.parameters
        }
        
        this.initializeTestValues()
      } catch (e) {
        window.$message.error('加载应用失败')
      } finally {
        this.loading = false
      }
    },
    
    initializeDefaultParameters() {
      this.parameters = {
        type: 'object',
        properties: {
          audio_data: {
            type: 'string',
            description: 'Base64编码的音频数据'
          },
          audio_format: {
            type: 'string',
            description: '音频格式 (wav, mp3, flac, opus)',
            default: 'wav'
          },
          language: {
            type: 'string',
            description: '识别语言代码',
            default: 'zh-CN'
          },
          context: {
            type: 'string',
            description: '上下文信息，帮助提高识别准确度'
          }
        },
        required: ['audio_data']
      }
    },
    
    initializeTestValues() {
      Object.keys(this.parameters.properties).forEach(paramName => {
        if (!this.parameterTestValues[paramName]) {
          const param = this.parameters.properties[paramName]
          this.$set(this.parameterTestValues, paramName, param.default || '')
        }
      })
    },
    
    handlePromptInput() {
      this.triggerAutoSavePrompt()
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
    
    async copyAppId() {
      try {
        await navigator.clipboard.writeText(this.app.id)
        window.$message.success('App ID 已复制')
      } catch (e) {
        window.$message.error('复制失败')
      }
    },
    
    async publishApp() {
      if (!this.app) return
      
      // 获取当前选择的模型和供应商
      const modelName = this.app.model_name
      const providerId = this.app.provider_id
      
      if (!modelName) {
        window.$message.warning('请选择一个模型')
        return
      }
      
      try {
        const payload = {
          name: this.app.name,
          description: this.app.description,
          system_prompt: this.app.system_prompt,
          provider_id: providerId,
          model_name: modelName,
          configuration: {
            temperature: this.currentTemperature,
            max_tokens: this.currentMaxTokens
          },
          parameters: this.parameters
        }
        
        await axios.post(`/api/apps/${this.app.id}/publish/`, payload)
        window.$message.success('ASR应用发布成功')
        this.saveStatus = '已发布'
      } catch (e) {
        const errorMsg = e.response?.data?.message || e.response?.data?.error || '发布失败'
        window.$message.error(errorMsg)
      }
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
      
      if ((!this.editingParam || this.editingParam !== this.editParamForm.name) && 
          this.parameters.properties[this.editParamForm.name]) {
        window.$message.error('参数名称已存在')
        return
      }
      
      if (this.editingParam && this.editingParam !== this.editParamForm.name) {
        this.$delete(this.parameters.properties, this.editingParam)
        const reqIndex = this.parameters.required.indexOf(this.editingParam)
        if (reqIndex > -1) {
          this.parameters.required.splice(reqIndex, 1)
          this.parameters.required.push(this.editParamForm.name)
        }
        if (this.parameterTestValues[this.editingParam]) {
           this.$set(this.parameterTestValues, this.editParamForm.name, this.parameterTestValues[this.editingParam])
           this.$delete(this.parameterTestValues, this.editingParam)
        }
      }
      
      this.$set(this.parameters.properties, this.editParamForm.name, {
        type: this.editParamForm.type,
        description: this.editParamForm.description || `参数 ${this.editParamForm.name}`,
        default: this.editParamForm.default
      })
      
      if (!this.parameterTestValues[this.editParamForm.name]) {
         this.$set(this.parameterTestValues, this.editParamForm.name, this.editParamForm.default || '')
      }
      
      this.showEditParamModal = false
      this.triggerAutoSavePrompt()
    },
    
    removeParameter(paramName) {
      this.$delete(this.parameters.properties, paramName)
      const index = this.parameters.required.indexOf(paramName)
      if (index > -1) {
        this.parameters.required.splice(index, 1)
      }
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
    
    copySchemaToClipboard() {
      const schema = this.formattedFunctionSchema
      
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
    
    handleLoadScenario(parameters) {
      if (!parameters) return
      Object.entries(parameters).forEach(([key, value]) => {
        this.$set(this.parameterTestValues, key, value)
      })
    },
    
    optimizePrompt() {
      window.$message.info('ASR提示词优化功能正在开发中...')
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
    
    // ASR 测试相关方法
    handleFileUpload(event) {
      const file = event.target.files[0]
      if (file) {
        // 清除录音数据
        this.clearRecordedAudio()
        this.selectedAudioFile = file
        window.$message.success(`已选择文件: ${file.name}`)
      }
    },
    
    async toggleRecording() {
      if (this.isRecording) {
        this.stopRecording()
      } else {
        await this.startRecording()
      }
    },
    
    async startRecording() {
      try {
        // 初始化录音器
        if (!this.audioRecorder) {
          this.audioRecorder = new AudioRecorder()
        }

        // 设置事件处理器
        this.audioRecorder.onStop = (audioBlob, format) => {
          // 清除文件上传数据
          this.clearSelectedAudio()
          this.recordedAudio = audioBlob
          this.recordedAudioFormat = format
          window.$message.success(`录音完成 (${format} 格式)`)
        }

        this.audioRecorder.onError = (error) => {
          window.$message.error('录音失败: ' + error.message)
          this.isRecording = false
          if (this.recordingTimer) {
            clearInterval(this.recordingTimer)
            this.recordingTimer = null
          }
        }

        // 开始录音
        await this.audioRecorder.startRecording()
        this.isRecording = true
        this.recordingDuration = 0
        
        this.recordingTimer = setInterval(() => {
          this.recordingDuration++
        }, 1000)
        
        window.$message.success('开始录音')
      } catch (error) {
        window.$message.error('无法访问麦克风: ' + error.message)
      }
    },
    
    stopRecording() {
      if (this.audioRecorder && this.isRecording) {
        this.audioRecorder.stopRecording()
        this.isRecording = false
        
        if (this.recordingTimer) {
          clearInterval(this.recordingTimer)
          this.recordingTimer = null
        }
      }
    },
    
    async runAsrTest() {
      if (this.isProcessing) return
      
      const audioFile = this.selectedAudioFile || this.recordedAudio
      if (!audioFile) {
        window.$message.warning('请先选择音频文件或录制语音')
        return
      }
      
      this.isProcessing = true
      const startTime = Date.now()
      
      try {
        // 转换音频为base64
        const audioBase64 = await this.fileToBase64(audioFile)
        
        // 构建请求参数
        const parameters = {
          audio_data: audioBase64,
          audio_format: this.recordedAudioFormat || this._detectAudioFormat(audioFile),
          language: 'zh-CN'
        }
        
        if (this.contextInput.trim()) {
          parameters.context = this.contextInput.trim()
        }
        
        // 调用ASR API
        const response = await axios.post(`/api/apps/${this.app.id}/invoke/`, {
          message: '',
          parameters: parameters
        })
        
        const processingTime = Date.now() - startTime
        
        if (response.data.status === 'success') {
          // 后端现在直接返回 recognized_text，不再是 JSON 字符串
          const recognizedText = response.data.content
          
          const result = {
            timestamp: new Date(),
            status: 'success',
            audioData: audioBase64,
            recognizedText: recognizedText,
            processingTime: processingTime
          }
          
          this.testResults.unshift(result)
          window.$message.success('ASR识别完成')
        } else {
          throw new Error(response.data.error || '识别失败')
        }
        
      } catch (error) {
        const result = {
          timestamp: new Date(),
          status: 'error',
          error: error.message || '识别失败',
          processingTime: Date.now() - startTime
        }
        
        this.testResults.unshift(result)
        window.$message.error('ASR识别失败: ' + error.message)
      } finally {
        this.isProcessing = false
        this.scrollToBottom()
      }
    },
    
    fileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const base64 = reader.result.split(',')[1]
          resolve(base64)
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    },
    
    playAudio(audioBase64) {
      try {
        const audio = new Audio(`data:audio/wav;base64,${audioBase64}`)
        audio.play()
      } catch (error) {
        window.$message.error('播放音频失败')
      }
    },
    
    _detectAudioFormat(file) {
      /**
       * 检测音频文件格式
       * @param {File|Blob} file - 音频文件或Blob对象
       * @returns {string} 音频格式
       */
      if (file.type) {
        // 从 MIME 类型推断格式
        if (file.type.includes('wav')) return 'wav'
        if (file.type.includes('webm')) return 'webm'
        if (file.type.includes('mp3')) return 'mp3'
        if (file.type.includes('mp4')) return 'mp4'
        if (file.type.includes('ogg')) return 'ogg'
        if (file.type.includes('flac')) return 'flac'
        if (file.type.includes('opus')) return 'opus'
      }
      
      // 从文件名推断格式（如果有的话）
      if (file.name) {
        const ext = file.name.split('.').pop().toLowerCase()
        if (['wav', 'webm', 'mp3', 'mp4', 'ogg', 'flac', 'opus'].includes(ext)) {
          return ext
        }
      }
      
      // 默认返回 wav
      return 'wav'
    },
    
    playSelectedAudio() {
      if (this.selectedAudioFile) {
        const url = URL.createObjectURL(this.selectedAudioFile)
        const audio = new Audio(url)
        audio.play().then(() => {
          // 播放完成后释放URL
          audio.addEventListener('ended', () => {
            URL.revokeObjectURL(url)
          })
        }).catch(error => {
          console.error('播放失败:', error)
          window.$message.error('播放音频失败')
          URL.revokeObjectURL(url)
        })
      }
    },
    
    playRecordedAudio() {
      if (this.recordedAudio) {
        const url = URL.createObjectURL(this.recordedAudio)
        const audio = new Audio(url)
        audio.play().then(() => {
          // 播放完成后释放URL
          audio.addEventListener('ended', () => {
            URL.revokeObjectURL(url)
          })
        }).catch(error => {
          console.error('播放失败:', error)
          window.$message.error('播放音频失败')
          URL.revokeObjectURL(url)
        })
      }
    },
    
    clearSelectedAudio() {
      this.selectedAudioFile = null
      // 清空文件输入框
      if (this.$refs.audioFileInput) {
        this.$refs.audioFileInput.value = ''
      }
      window.$message.info('已清除选择的文件')
    },
    
    clearRecordedAudio() {
      this.recordedAudio = null
      this.recordedAudioFormat = null
      this.recordingDuration = 0
      window.$message.info('已清除录音')
    },
    
    // 统一音频文件管理方法
    playCurrentAudio() {
      if (this.recordedAudio) {
        this.playRecordedAudio()
      } else if (this.selectedAudioFile) {
        this.playSelectedAudio()
      }
    },
    
    clearCurrentAudio() {
      if (this.recordedAudio) {
        this.clearRecordedAudio()
      } else if (this.selectedAudioFile) {
        this.clearSelectedAudio()
      }
    },
    
    truncateFileName(fileName, maxLength = 25) {
      if (fileName.length <= maxLength) return fileName
      const extension = fileName.split('.').pop()
      const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'))
      const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...'
      return truncatedName + '.' + extension
    },
    
    clearTestResults() {
      this.testResults = []
    },
    
    formatTime(date) {
      return date.toLocaleTimeString()
    },
    
    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    getStatusText(status) {
      const statusMap = {
        success: '成功',
        error: '失败',
        processing: '处理中'
      }
      return statusMap[status] || status
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.msgScroll
        if (el) el.scrollTop = el.scrollHeight
      })
    }
  },
  mounted() {
    this.fetchApp()
  },
  beforeDestroy() {
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer)
    }
    if (this.audioRecorder) {
      this.audioRecorder.cleanup()
    }
  }
}
</script>

<style scoped>
/* 复用 Agent1ConfigComponent 的基础样式 */
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

.pane-header h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.app-type-badge {
  background-color: #fef3c7;
  color: #d97706;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
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
  background-color: #d97706;
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

.input-group input, .input-group textarea, .input-group select {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  color: #475569;
  background-color: #fcfcfd;
}

.config-item label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
}

.config-item select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  background-color: #fcfcfd;
  cursor: pointer;
}

.toggle-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-right: 8px;
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
  background-color: #fef3c7;
  color: #d97706;
  border: 1px solid #fbbf24;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.optimize-btn:hover {
  background-color: #fde68a;
  border-color: #f59e0b;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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

/* 参数样式 */
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
  background-color: #fef3c7;
  color: #d97706;
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

.edit-param-btn, .remove-param-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-param-btn {
  color: #d97706;
}

.edit-param-btn:hover {
  background-color: #fef3c7;
}

.remove-param-btn {
  color: #94a3b8;
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
  border-color: #d97706;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.param-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
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

.add-param-btn-large {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  color: #d97706;
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
  border-color: #d97706;
  background-color: #fef3c7;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.2);
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
  border-color: #d97706;
  color: #d97706;
  background-color: #fef3c7;
  transform: scale(1.05);
}

/* 模型配置样式 */
.model-select-wrapper {
  margin-bottom: 16px;
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
  margin-bottom: 16px;
}

.param-item:last-child {
  margin-bottom: 0;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-header label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
}

.param-val {
  font-size: 0.85rem;
  color: #d97706;
  font-weight: 700;
  font-family: 'Monaco', 'Menlo', monospace;
}

.param-item input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
}

.param-item input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #d97706;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(217, 119, 6, 0.3);
}

.param-item input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #d97706;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(217, 119, 6, 0.3);
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
  background-color: #d97706;
  border-color: #d97706;
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.3);
}

.schema-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.6;
}

/* Debug Pane - ASR 测试区域 */
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
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.empty-debug h3 {
    margin: 0 0 8px 0;
    color: #1e293b;
}

/* ASR 测试结果样式 */
.test-result-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-time {
  font-size: 0.85rem;
  color: #64748b;
}

.result-status {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.result-status.success {
  background-color: #dcfce7;
  color: #16a34a;
}

.result-status.error {
  background-color: #fee2e2;
  color: #dc2626;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.play-audio-btn {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  color: #d97706;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.play-audio-btn:hover {
  background: #fde68a;
  border-color: #f59e0b;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audio-info {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: #64748b;
}

.info-item {
  padding: 4px 8px;
  background-color: #f1f5f9;
  border-radius: 4px;
}

.recognition-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recognition-result label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
}

.result-text {
  padding: 12px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #1f2937;
}

.processing-time label {
  font-weight: 600;
  color: #374151;
}

.error-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-message label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #dc2626;
}

.error-text {
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.9rem;
}

.processing-indicator {
    padding: 12px;
    font-size: 0.85rem;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 8px;
}

.processing-indicator .dot {
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

/* 输入区域样式 */
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
  padding: 20px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.audio-input-section {
  margin-bottom: 16px;
}

.input-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #fef3c7;
  border-color: #fbbf24;
  color: #d97706;
}

.tab-btn:hover:not(.active) {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.upload-section, .record-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
}

.upload-btn-enhanced {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
}

.upload-btn-enhanced:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
}

.upload-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.upload-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.upload-subtitle {
  font-size: 13px;
  color: #64748b;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #ffffff;
  border: 1px solid #d97706;
  color: #d97706;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.upload-btn:hover {
  background: #fef3c7;
  transform: translateY(-1px);
}

.upload-hint {
  font-size: 0.8rem;
  color: #94a3b8;
  margin: 0;
}

.record-btn-enhanced {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #fef7f0 0%, #fef3ec 100%);
  border: 2px solid #fed7aa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
}

.record-btn-enhanced:hover {
  background: linear-gradient(135deg, #fef3ec 0%, #fde8d7 100%);
  border-color: #f59e0b;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.15);
}

.record-btn-enhanced.recording {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-color: #fca5a5;
  animation: recording-pulse 2s infinite;
}

@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }
}

.record-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  transition: all 0.3s ease;
}

.record-icon.recording {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  animation: recording-icon-pulse 1s infinite alternate;
}

@keyframes recording-icon-pulse {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(1.05);
  }
}

.record-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.record-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.record-subtitle {
  font-size: 13px;
  color: #64748b;
}

.recording-time {
  color: #ef4444;
  font-weight: 500;
}

.context-input {
  margin-bottom: 16px;
}

.context-input label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.context-input textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}

.context-input textarea:focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.test-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.test-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px -3px rgba(217, 119, 6, 0.4);
}

.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 音频预览卡片样式 */
.unified-audio-preview {
  margin-bottom: 16px;
}

.audio-preview-card {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.audio-preview-card.full-width {
  width: 100%;
  margin-top: 0;
}

.audio-preview-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.recording-preview {
  background: linear-gradient(135deg, #fef7f0 0%, #fef3ec 100%);
  border-color: #fed7aa;
}

.audio-preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.audio-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.recording-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.audio-file-info {
  flex: 1;
  min-width: 0;
}

.file-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.file-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-format-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: #3b82f6;
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.recording-badge {
  background: #f59e0b;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.file-separator {
  color: #cbd5e1;
}

.recording-duration {
  color: #f59e0b;
  font-weight: 500;
}

.audio-preview-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.audio-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.audio-action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: currentColor;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.audio-action-btn:hover::before {
  opacity: 0.1;
}

.audio-action-btn:active {
  transform: scale(0.95);
}

.audio-action-btn.play-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.audio-action-btn.play-btn:hover {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  transform: translateY(-1px);
}

.audio-action-btn.delete-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.audio-action-btn.delete-btn:hover {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

/* 模态框样式 */
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
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.param-modal .modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #ffffff;
}

.close-btn-modal {
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

.close-btn-modal:hover {
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

.param-modal .input-group select {
  width: 100%;
  cursor: pointer;
  transition: all 0.2s;
}

.param-modal .input-group select:focus {
  border-color: #d97706;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
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
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
  transition: all 0.3s;
  box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.3);
}

.save-btn-modal:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(217, 119, 6, 0.4);
}

.required {
  color: #ef4444;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>