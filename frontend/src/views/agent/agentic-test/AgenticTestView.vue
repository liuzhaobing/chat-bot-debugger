<template>
  <div class="agentic-test-view">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 数字员工面板 -->
      <div class="employee-container">
        <SceneTestPanel
          ref="sceneTestPanel"
          :has-pending-test-cases="pendingTestCases.length > 0"
          :transcript-messages="transcriptMessages"
          :system-logs="systemLogs"
          :is-session-active="isSessionActive"
          :is-connecting="isConnecting"
          :session-duration="sessionDuration"
          :test-cases-with-status="testCasesWithStatus"
          :current-case-index="currentCaseIndex"
          :selected-case-index="selectedCaseIndex"
          :test-case-logs="testCaseLogs"
          :current-case-logs="currentCaseLogs"
          :test-completed="testCompleted"
          :test-report-data="testReportData"
          @start-session-with-config="handleStartSessionWithConfig"
          @reopen-test-case-popup="handleReopenTestCasePopup"
          @clear-transcript="clearTranscript"
          @clear-logs="clearLogs"
          @session-btn-click="handleVoiceAgentClick"
          @test-cases-confirm="confirmTestCases"
          @select-case="handleSelectCase"
          @view-report="handleViewReport"
        />
      </div>
    </div>

    <!-- 会话管理面板 - 悬浮显示 -->
    <div v-if="showMainInterface" class="session-overlay">
      <div class="session-panel">
        <div class="session-header">
          <h3>会话管理</h3>
          <button class="close-btn" @click="showMainInterface = false">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <SessionManager 
          @start-session="handleStartSession"
          @stop-session="handleStopSession"
        />
      </div>
    </div>

    <!-- VAD+ASR测试面板 -->
    <div v-if="showVadAsrTest" class="vad-asr-overlay">
      <div class="vad-asr-panel">
        <VadAsrTestPanel
          @close="showVadAsrTest = false"
        />
      </div>
    </div>

    <!-- 测试用例确认弹窗 - 已移动到 SceneTestPanel 左侧面板 -->
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import SessionManager from '@/components/agentic-test/SessionManager.vue'
import VadAsrTestPanel from '@/components/agentic-test/VadAsrTestPanel.vue'
import SceneTestPanel from '@/components/agentic-test/SceneTestPanel.vue'
import RealtimeAudioProcessor, { createAudioMessage } from '@/utils/realtimeAudioProcessor.js'
import { getAgenticTestWsUrl } from '@/config/worker.js'
import agenticTestService from '@/services/agenticTestService'

export default {
  name: 'AgenticTestView',
  components: {
    SessionManager,
    VadAsrTestPanel,
    SceneTestPanel
  },
  computed: {
    ...mapState('agenticTest', [
      'isConnected',
      'currentSession',
      'logs',
      'audioData'
    ]),
    ...mapGetters('agenticTest', [
      'isConnectedAndReady'
    ]),
    
    formattedSessionDuration() {
      const minutes = Math.floor(this.sessionDuration / 60)
      const seconds = this.sessionDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  data() {
    return {
      // UI状态
      showMainInterface: false,
      showVadAsrTest: false,

      // 会话状态
      isSessionActive: false,
      isConnecting: false,
      connectionStatus: 'disconnected', // 'disconnected' | 'connecting' | 'connected' | 'active'
      sessionDuration: 0,
      sessionTimer: null,

      // 音频状态（使用统一的RealtimeAudioProcessor）
      audioProcessor: null,
      hasAudioActivity: false,
      currentAudioLevel: 0,
      isMuted: false,

      // 音频播放器（用于TTS播放）
      audioPlaybackContext: null,
      currentPlayingAudio: null,

      // 数据
      transcriptMessages: [],
      systemLogs: [],

      // IOT配置
      iotConfig: {
        token: '',
        familyId: '',
        env: 'test'
      },

      // 测试配置
      testerConfig: {
        name: '',
        prd_content: '',
        tts_voice_id: '',
        iot_protocol_id: ''
      },

      // 当前任务（用于关联测试报告）
      currentTask: null,

      // job_instance_id（用于 WebSocket session_id 和任务关联）
      jobInstanceId: null,

      // WebSocket
      websocket: null,
      reconnectAttempts: 0,
      maxReconnectAttempts: 3,
      reconnectTimeout: null,

      // 配置初始化状态
      isConfigInitialized: false,

      // 测试用例
      pendingTestCases: [],
      testCaseRawContent: '',
      isGeneratingTestCases: false,
      // 标记是否已经生成过测试用例（防止重连后重复生成）
      hasGeneratedTestCases: false,

      // 测试用例执行状态（测试用例导向UI）
      testCasesWithStatus: [],  // [{testCase, status, logs, stepResults}]
      currentCaseIndex: -1,     // 当前执行的用例索引
      selectedCaseIndex: -1,    // 用户选中的用例索引（用于查看详情）
      testCaseLogs: {},         // Map<caseId, Array<log>>
      currentCaseLogs: [],      // 当前执行用例的日志（用于实时显示）
      testCompleted: false,     // 测试是否已完成
      testReportData: null,     // 测试报告数据

      // 静默检测状态机
      silenceDetectionActive: false,   // 静默检测是否激活
      hasDetectedVoice: false,          // 是否已检测到用户说话
      silenceStartTime: null,           // 静默开始时间
      silenceThreshold: 1200,           // n/1000 秒静默阈值

      // 自适应阈值参数（基于噪音底噪估计）
      noiseFloor: 0.01,                 // 噪音底噪估计
      noiseFloorAlpha: 0.95,            // 底噪平滑系数（越大越平滑）
      signalMargin: 2.5,                // 信号余量倍数
      adaptiveThreshold: 0.025,         // 当前自适应阈值
      baseVolumeThreshold: 0.01,        // 基础阈值下限

      // 帧计数（替代时间戳防抖）
      speechFrames: 0,                  // 连续语音帧计数
      silenceFrames: 0,                 // 连续静音帧计数

      // 说话时长检测
      speechStartTime: null,            // 说话开始时间
      minSpeechDuration: 1000,          // 最小说话时长阈值（毫秒）
      actualSpeechDuration: 0,          // 实际说话时长

      // 频谱分析相关
      voiceEnergyRatioThreshold: 0.4,   // 人声能量占比阈值
      lastVoiceEnergyRatio: 0           // 最近一次人声能量占比（调试用）
    }
  },
  mounted() {
    // 不再在页面加载时初始化音频处理器
    // 只在用户点击对话调试按钮时才初始化和启动麦克风
    this.addSystemLog('system', 'info', '系统初始化完成，点击对话调试按钮开始会话')
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    ...mapActions('agenticTest', [
      'connectWebSocket',
      'disconnectWebSocket',
      'sendAudioData',
      'updateAudioFeatures'
    ]),

    /**
     * 重新打开测试用例确认弹窗
     */
    handleReopenTestCasePopup() {
      if (this.pendingTestCases.length > 0 && this.$refs.sceneTestPanel) {
        this.$refs.sceneTestPanel.switchToTestCasePanel()
      }
    },

    /**
     * 处理对话调调试按钮点击
     */
    handleVoiceAgentClick() {
      if (this.isConnecting) {
        return // 连接中时不响应点击
      }
      
      if (this.isSessionActive) {
        // 如果会话活跃，则停止会话
        this.handleStopSession()
      } else {
        // 如果会话未活跃，则开始会话
        this.handleStartSession()
      }
    },

    /**
     * 发送IOT配置到服务器
     */
    sendIOTConfigToServer() {
      if (!this.isWebSocketReady()) {
        return
      }
      
      try {
        // 从localStorage获取IOT配置
        const iotConfig = this.getIOTConfigFromStorage()
        
        if (iotConfig.token && iotConfig.familyId && iotConfig.env) {
          const message = {
            type: 'update_iot_config',
            config: iotConfig,
            timestamp: Date.now()
          }
          
          this.websocket.send(JSON.stringify(message))
          this.addSystemLog('iot', 'info', 'IOT配置已发送到服务器', iotConfig)
        } else {
          this.addSystemLog('iot', 'warning', 'IOT配置不完整，跳过发送')
        }
      } catch (error) {
        console.error('发送IOT配置失败:', error)
        this.addSystemLog('iot', 'error', '发送IOT配置失败')
      }
    },

    /**
     * 从localStorage获取IOT配置
     */
    getIOTConfigFromStorage() {
      return {
        token: localStorage.getItem('iot-token') || '',
        familyId: localStorage.getItem('family-id') || '',
        env: localStorage.getItem('iot-env') || 'test'
      }
    },

    /**
     * 发送 start_test 消息
     * 在配置初始化成功后调用
     */
    sendStartTest() {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        const startTestMessage = {
          type: 'start_test',
          query: '你好食神在吗',  // 初始查询
          timestamp: Date.now()
        }
        this.websocket.send(JSON.stringify(startTestMessage))
        this.addSystemLog('test', 'info', '已发送 start_test 消息')
      }
    },

    /**
     * 处理IOT配置变化
     */
    handleIOTConfigChange(config) {
      this.iotConfig = { ...config }
      this.addSystemLog('iot', 'info', 'IOT配置已更新')

      // 如果WebSocket已连接，立即发送更新的配置
      if (this.isWebSocketReady()) {
        this.sendIOTConfigToServer()
      }
    },

    /**
     * 检查WebSocket是否可用
     */
    isWebSocketReady() {
      try {
        return this.websocket && 
               this.websocket.readyState === WebSocket.OPEN &&
               typeof this.websocket.send === 'function'
      } catch (error) {
        console.error('WebSocket状态检查失败:', error)
        return false
      }
    },

    /**
     * 初始化音频处理器 - 使用统一的RealtimeAudioProcessor
     */
    async initializeAudioProcessor() {
      try {
        // 检查浏览器支持
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          const isSecure = window.isSecureContext
          const protocol = window.location.protocol
          const hostname = window.location.hostname

          let errorMsg = '浏览器不支持音频功能'
          if (!isSecure && hostname !== 'localhost' && hostname !== '127.0.0.1') {
            errorMsg = `需要 HTTPS 或 localhost 访问才能使用麦克风（当前: ${protocol}//${hostname}）`
          }

          throw new Error(errorMsg)
        }

        // 1. 先初始化音频播放上下文（扬声器权限）
        await this.initializeAudioPlaybackContext()

        // 2. 创建音频处理器实例
        this.audioProcessor = new RealtimeAudioProcessor({
          sampleRate: 16000,
          channelCount: 1,
          bufferSize: 256
        })

        // 设置回调函数
        this.audioProcessor.onAudioLevel = (level) => {
          this.currentAudioLevel = level
          this.hasAudioActivity = level > 0.02

          // 更新自适应阈值
          this.updateAdaptiveThreshold(level)

          // 静默检测逻辑
          if (this.silenceDetectionActive) {
            this.handleSilenceDetection(level)
          }
        }

        this.audioProcessor.onVoiceActivity = () => {
          // 语音活动状态变化不再打印日志，避免频繁刷屏
        }

        this.audioProcessor.onAudioData = (audioBytes) => {
          if (this.isWebSocketReady()) {
            this.sendRealTimeAudioData(audioBytes)
          }
        }

        this.audioProcessor.onError = (error) => {
          this.addSystemLog('error', 'error', `音频处理错误: ${error.message}`)
          this.handleAudioError('audio_error', error)
        }

        // 初始化麦克风
        const initialized = await this.audioProcessor.initialize()
        if (!initialized) {
          throw new Error('音频处理器初始化失败')
        }

        // 启动音频处理
        this.audioProcessor.start()

        this.addSystemLog('audio', 'success', '实时音频处理器初始化成功', {
          sampleRate: 16000,
          bufferSize: 256,
          latency: '16ms',
          playbackReady: !!this.audioPlaybackContext
        })

      } catch (error) {
        console.error('音频处理器初始化失败:', error)
        this.addSystemLog('system', 'error', '音频处理器初始化失败', { error: error.message })
        throw error
      }
    },

    /**
     * 初始化音频播放上下文（用于TTS播放）
     * 解决浏览器自动播放策略限制
     */
    async initializeAudioPlaybackContext() {
      try {
        // 创建用于播放的 AudioContext
        const AudioContextClass = window.AudioContext || window.webkitAudioContext
        this.audioPlaybackContext = new AudioContextClass({ sampleRate: 24000 })

        // 确保上下文处于运行状态（需要用户交互后才能激活）
        if (this.audioPlaybackContext.state === 'suspended') {
          await this.audioPlaybackContext.resume()
          this.addSystemLog('audio', 'info', '音频播放上下文已激活')
        }

        this.addSystemLog('audio', 'success', '音频播放上下文初始化成功', {
          state: this.audioPlaybackContext.state,
          sampleRate: this.audioPlaybackContext.sampleRate
        })

        return true
      } catch (error) {
        console.error('初始化音频播放上下文失败:', error)
        this.addSystemLog('audio', 'warning', `音频播放上下文初始化失败: ${error.message}`)
        return false
      }
    },

    /**
     * 释放音频播放上下文
     */
    async releaseAudioPlaybackContext() {
      try {
        // 停止当前播放的音频
        if (this.currentPlayingAudio) {
          this.currentPlayingAudio.pause()
          this.currentPlayingAudio = null
        }

        // 关闭音频上下文
        if (this.audioPlaybackContext && this.audioPlaybackContext.state !== 'closed') {
          await this.audioPlaybackContext.close()
          this.audioPlaybackContext = null
          this.addSystemLog('audio', 'info', '音频播放上下文已释放')
        }
      } catch (error) {
        console.error('释放音频播放上下文失败:', error)
      }
    },

    /**
     * 开始会话
     */
    async handleStartSession() {
      if (this.isConnecting || this.isSessionActive) return

      // 清空上次的字幕消息
      this.transcriptMessages = []

      this.isConnecting = true
      this.connectionStatus = 'connecting'
      this.addSystemLog('system', 'info', '正在启动会话...')

      try {
        // 1. 建立WebSocket连接
        await this.connectToWebSocket()

        // 2. 启动会话计时器
        this.startSessionTimer()

        // 3. 更新状态（注意：音频处理器延迟到用户确认测试用例后初始化）
        this.isSessionActive = true
        this.isConnecting = false
        this.connectionStatus = 'active'

        this.addSystemLog('system', 'success', '会话启动成功，等待测试用例确认...')
        this.addTranscriptMessage('system', '会话已开始，正在设计测试用例...', false, true)

      } catch (error) {
        console.error('启动会话失败:', error)
        this.isConnecting = false
        this.connectionStatus = 'disconnected'
        this.addSystemLog('system', 'error', `启动会话失败: ${error.message}`)

        // 清理资源
        this.cleanup()
      }
    },

    /**
     * 使用自定义配置启动会话（由 SceneTestPanel 派发任务时调用）
     * @param {Object} payload - 包含 testerConfig 和可选的 task 信息
     */
    async handleStartSessionWithConfig(payload) {
      if (this.isConnecting || this.isSessionActive) {
        window.$message?.warning('已有会话在运行中，请先停止当前会话')
        return
      }

      // 清空上次的字幕消息
      this.transcriptMessages = []

      // 重置测试用例生成标记（用户主动开始新测试）
      this.hasGeneratedTestCases = false

      // 设置测试配置
      if (payload.testerConfig) {
        this.testerConfig = { ...this.testerConfig, ...payload.testerConfig }
        this.addSystemLog('config', 'info', '已设置测试配置', payload.testerConfig)
      }

      // 保存任务信息（用于关联测试报告）
      if (payload.task) {
        this.currentTask = payload.task
        this.addSystemLog('task', 'info', `关联任务: ${payload.task.name}`, { task_id: payload.task.id, job_instance_id: payload.task.job_instance_id })
      }

      // 关键：保存 job_instance_id（用于 WebSocket session_id）
      if (payload.task?.job_instance_id) {
        this.jobInstanceId = payload.task.job_instance_id
        this.addSystemLog('session', 'info', `使用 job_instance_id 作为 session_id: ${this.jobInstanceId}`)
      }

      // 调用标准启动流程
      await this.handleStartSession()
    },

    /**
     * 停止会话
     */
    async handleStopSession() {
      if (!this.isSessionActive) return

      this.addSystemLog('system', 'info', '正在停止会话...')

      try {
        // 1. 发送停止测试消息到后端
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          const stopTestMessage = {
            type: 'stop_test',
            timestamp: Date.now()
          }
          this.websocket.send(JSON.stringify(stopTestMessage))
          this.addSystemLog('test', 'info', '已发送停止测试消息，等待后端处理...')
          // 不立即关闭连接，等待后端返回 test_stopped 消息
        } else {
          // 如果WebSocket已断开，直接清理
          this.cleanupAfterStop()
        }

      } catch (error) {
        console.error('停止会话失败:', error)
        this.addSystemLog('system', 'error', `停止会话失败: ${error.message}`)
        // 出错时也要清理
        this.cleanupAfterStop()
      }
    },

    /**
     * 停止后的清理工作
     */
    cleanupAfterStop() {
      // 1. 断开WebSocket
      this.disconnectFromWebSocket()

      // 2. 停止计时器
      this.stopSessionTimer()

      // 3. 清理音频资源（包括释放麦克风）
      this.cleanup()

      // 4. 更新状态
      this.isSessionActive = false
      this.connectionStatus = 'disconnected'
      this.hasAudioActivity = false
      this.currentAudioLevel = 0

      this.addSystemLog('system', 'success', '会话已停止，麦克风已释放')
      this.addTranscriptMessage('system', '会话已结束', false, true)
    },

    /**
     * 切换静音状态
     */
    handleToggleMute(muted) {
      this.isMuted = muted
      this.addSystemLog('audio', 'info', muted ? '麦克风已静音' : '麦克风已取消静音')
    },

    /**
     * 连接WebSocket
     */
    async connectToWebSocket() {
      // 清理现有连接
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }

      // 优先使用 jobInstanceId 作为 session_id（用于精确任务关联）
      // 如果没有 jobInstanceId，则使用 currentSession.id 或创建新会话
      let sessionId = this.jobInstanceId || this.currentSession?.id
      if (!sessionId) {
        this.addSystemLog('session', 'info', '正在创建新会话...')
        try {
          const session = await agenticTestService.createSession(`会话-${new Date().toLocaleString('zh-CN')}`)
          sessionId = session.id
          // 更新 Vuex store 中的 currentSession
          this.$store.commit('agenticTest/SET_CURRENT_SESSION', session)
          this.addSystemLog('session', 'success', `会话创建成功，ID: ${sessionId}`)
        } catch (error) {
          console.error('创建会话失败:', error)
          this.addSystemLog('session', 'error', '创建会话失败，使用默认 session')
          sessionId = 'default'
        }
      }

      // 连接到 Worker 服务的 WebSocket
      const wsUrl = getAgenticTestWsUrl(sessionId)

      return new Promise((resolve, reject) => {
        this.websocket = new WebSocket(wsUrl)

        this.websocket.onopen = () => {
          this.connectionStatus = 'connected'
          this.reconnectAttempts = 0
          this.isConfigInitialized = false
          this.addSystemLog('websocket', 'success', 'WebSocket连接已建立')

          // 连接建立后先发送 init_config 消息
          const iotConfig = this.getIOTConfigFromStorage()

          const initConfigMessage = {
            type: 'init_config',
            tester_config: {
              ...this.testerConfig,
              job_instance_id: this.jobInstanceId  // 关键：在 init_config 中传递 job_instance_id
            },
            iot_config: iotConfig,
            timestamp: Date.now()
          }
          this.websocket.send(JSON.stringify(initConfigMessage))
          this.addSystemLog('config', 'info', '已发送 init_config 消息', {
            tester_config: { ...this.testerConfig, job_instance_id: this.jobInstanceId },
            iot_config: { env: iotConfig.env, has_token: !!iotConfig.token }
          })

          // 连接已建立，resolve Promise
          resolve()
        }

        this.websocket.onmessage = (event) => {
          this.handleWebSocketMessage(event)
        }

        this.websocket.onclose = (event) => {
          this.addSystemLog('websocket', 'warning', `WebSocket连接已关闭: ${event.code}`)
          if (this.isSessionActive && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect()
          }
        }

        this.websocket.onerror = (error) => {
          console.error('WebSocket错误:', error)
          this.addSystemLog('websocket', 'error', 'WebSocket连接错误')
          reject(new Error('WebSocket连接失败'))
        }

        // 连接超时
        setTimeout(() => {
          try {
            if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
              this.websocket.close()
              this.websocket = null
              reject(new Error('WebSocket连接超时'))
            }
          } catch (error) {
            console.error('WebSocket超时检查错误:', error)
            reject(new Error('WebSocket连接超时'))
          }
        }, 10000)
      })
    },

    /**
     * 断开WebSocket连接
     */
    disconnectFromWebSocket() {
      // 停止静默检测
      this.stopSilenceDetection()

      if (this.websocket) {
        try {
          // 连接关闭前先发送stop_test
          if (this.websocket.readyState === WebSocket.OPEN) {
            const stopTestMessage = {
              type: 'stop_test',
              timestamp: Date.now()
            }
            this.websocket.send(JSON.stringify(stopTestMessage))
            this.addSystemLog('test', 'info', '已发送stop_test消息')
          }
          this.websocket.close()
        } catch (error) {
          console.error('关闭WebSocket时出错:', error)
        }
        this.websocket = null
      }

      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout)
        this.reconnectTimeout = null
      }
    },

    /**
     * 测试完成后关闭WebSocket连接
     * 发送close_connection消息通知服务端，然后关闭连接
     */
    async closeWebSocketAfterTest() {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        try {
          // 发送关闭连接消息通知服务端
          const closeMessage = {
            type: 'close_connection',
            timestamp: Date.now()
          }
          this.websocket.send(JSON.stringify(closeMessage))
          this.addSystemLog('websocket', 'info', '已发送关闭连接消息')
          // 关闭连接
          this.websocket.close()
        } catch (error) {
          console.error('关闭WebSocket时出错:', error)
        }
        this.websocket = null
      }
      this.isSessionActive = false
      this.isConfigInitialized = false

      // 关键：释放音频资源（麦克风和扬声器）
      await this.cleanupAudioResources()

      // 刷新 SceneTestPanel 的任务列表
      if (this.$refs.sceneTestPanel && this.currentTask?.employee?.id) {
        this.$refs.sceneTestPanel.loadEmployeeTasks(this.currentTask.employee.id)
      }
    },

    /**
     * 清理音频资源（麦克风和扬声器）
     */
    async cleanupAudioResources() {
      console.log('开始清理音频资源...')

      // 停止会话计时器
      this.stopSessionTimer()

      // 销毁音频处理器（释放麦克风）
      if (this.audioProcessor) {
        console.log('销毁音频处理器...')
        this.audioProcessor.destroy()
        this.audioProcessor = null
        this.addSystemLog('audio', 'info', '麦克风已释放')
      }

      // 释放音频播放上下文（释放扬声器）
      await this.releaseAudioPlaybackContext()

      // 重置音频相关状态
      this.hasAudioActivity = false
      this.currentAudioLevel = 0
      this.sessionDuration = 0
      this.isConnecting = false
      this.connectionStatus = 'disconnected'

      console.log('音频资源清理完成')
    },

    /**
     * 处理WebSocket消息
     */
    handleWebSocketMessage(event) {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'ping':
            // 响应心跳，防止被服务端断开
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
              this.websocket.send(JSON.stringify({ type: 'pong' }))
            }
            break

          case 'config_initialized':
            // 配置初始化成功
            this.isConfigInitialized = true
            this.addSystemLog('config', 'success', '配置初始化成功', data.metadata)
            // 只有在未生成过测试用例时才发送 start_test
            // 如果已经生成过（比如重连场景），则跳过
            if (!this.hasGeneratedTestCases) {
              this.sendStartTest()
            } else {
              this.addSystemLog('config', 'info', '测试用例已生成，跳过重新发送 start_test')
            }
            // 连接建立完成，resolve Promise
            break

          case 'transcript_partial':
            this.updatePartialTranscript(data.content)
            break

          case 'transcript_final':
            this.addTranscriptMessage('user', data.content, false, true)
            break

          case 'ai_response':
            this.addTranscriptMessage('agent', data.content, false, true)
            break

          case 'ai_response_partial':
            this.updatePartialAIResponse(data.content)
            break

          case 'audio_play':
            // 播放 TTS 音频
            this.playAudioFromBase64(data.content, data.metadata?.type)
            break

          case 'system_status':
            this.addSystemLog('ai', 'info', data.content)
            break

          case 'status':
          case 'log':
          case 'warning':
          case 'vad_status':
          case 'vad_result':
            // 系统状态类消息，记录日志
            this.addSystemLog('system', 'info', data.content, data.metadata)
            break

          case 'error':
            this.addSystemLog('error', 'error', data.content, data.metadata)
            break

          case 'test_cases_ready':
            // 测试用例准备就绪，即将开始执行
            var readyCasesCount = (data.content && data.content.count) || 0
            var readyTestCases = (data.content && data.content.test_cases) || []
            this.addSystemLog('system', 'success', '测试用例准备就绪，共 ' + readyCasesCount + ' 个用例', readyTestCases)
            // 可以在这里更新 UI 显示测试用例列表
            this.$emit('test-cases-ready', readyTestCases)
            break

          case 'test_case_generation_started':
            // 开始设计测试用例，打开确认弹窗
            this.isGeneratingTestCases = true
            this.pendingTestCases = []
            this.testCaseRawContent = ''
            // 重置弹窗状态并切换到测试用例面板
            if (this.$refs.sceneTestPanel) {
              this.$refs.sceneTestPanel.resetTestCasePanel()
              this.$refs.sceneTestPanel.switchToTestCasePanel()
            }
            this.addSystemLog('system', 'info', '开始设计测试用例...')
            break

          case 'test_case_stream':
            // 流式测试用例内容，追加到弹窗
            var streamContent = (data.content && data.content.content) || data.content || ''
            if (streamContent) {
              this.testCaseRawContent += streamContent
              // 确保弹窗已挂载后再添加内容
              if (this.$refs.sceneTestPanel) {
                this.$refs.sceneTestPanel.addTestCaseChunk(streamContent)
              }
            }
            break

          case 'test_cases_generated':
            // 测试用例生成完成，解析并填充表格
            var generatedCases = (data.content && data.content.test_cases) || []
            if (generatedCases.length > 0 && this.$refs.sceneTestPanel) {
              this.pendingTestCases = generatedCases
              // 初始化测试用例状态数组
              this.initTestCasesWithStatus(generatedCases)
              this.$refs.sceneTestPanel.setTestCaseComplete(generatedCases)
            }
            this.isGeneratingTestCases = false
            // 标记测试用例已生成，防止重连后重复生成
            this.hasGeneratedTestCases = true
            this.addSystemLog('system', 'success', `测试用例生成完成，共 ${generatedCases.length} 个用例`)
            break

          case 'test_cases_ready_for_confirm':
            // 测试用例已准备好，等待用户确认
            var confirmCases = (data.content && data.content.test_cases) || []
            var confirmCount = (data.content && data.content.count) || confirmCases.length

            // 切换到测试用例面板
            if (this.$refs.sceneTestPanel) {
              this.$refs.sceneTestPanel.switchToTestCasePanel()
              this.$nextTick(() => {
                if (confirmCases.length > 0) {
                  this.pendingTestCases = confirmCases
                  // 初始化测试用例状态数组
                  this.initTestCasesWithStatus(confirmCases)
                  this.$refs.sceneTestPanel.setTestCaseComplete(confirmCases)
                }
              })
            }
            this.isGeneratingTestCases = false
            // 标记测试用例已生成，防止重连后重复生成
            this.hasGeneratedTestCases = true
            this.addSystemLog('system', 'info', `测试用例准备就绪，共 ${confirmCount} 个用例，等待确认...`)
            break

          case 'test_completed':
            // 测试完成，显示报告摘要并关闭连接
            var content = data.content || {}
            // 重置当前用例索引，停止动画
            this.currentCaseIndex = -1
            // 添加详细的测试报告日志到当前用例日志
            this.addSystemLog('system', 'success', '========================================')
            this.addSystemLog('system', 'success', '测试报告概要')
            this.addSystemLog('system', 'info', `总用例数: ${content.total_cases || 0}`)
            this.addSystemLog('system', 'success', `通过: ${content.passed || 0}`)
            this.addSystemLog('system', 'error', `失败: ${content.failed || 0}`)
            this.addSystemLog('system', 'info', `通过率: ${content.pass_rate || 0}%`)
            this.addSystemLog('system', 'success', '========================================')
            // 设置测试完成状态和报告数据
            this.testCompleted = true
            // 规范化报告数据格式，确保包含 case_statistics 和 test_cases
            this.testReportData = {
              ...content,
              // 如果后端没有 case_statistics，从顶层字段构建
              case_statistics: content.case_statistics || {
                total: content.total_cases || 0,
                passed: content.passed || 0,
                failed: content.failed || 0,
                blocked: content.blocked || 0,
                skipped: content.skipped || 0,
                not_run: content.not_run || 0,
                pass_rate: content.pass_rate || 0
              },
              // 如果后端没有 test_cases，从 testCasesWithStatus 构建
              test_cases: content.test_cases || this.testCasesWithStatus.map(cs => ({
                id: cs.testCase.id,
                title: cs.testCase.title,
                type: cs.testCase.type || 'functional',
                preconditions: cs.testCase.preconditions || [],
                expect_results: cs.testCase.expect_results || [],
                actual_results: cs.testCase.actual_results || [],
                test_result: cs.status === 'PASS' ? 'Pass' : (cs.status === 'FAIL' ? 'Fail' : cs.status),
                error_message: cs.errorMessage || '',
                step_results: cs.stepResults || []
              }))
            }
            // 延迟关闭连接，给日志渲染一点时间
            setTimeout(() => {
              this.closeWebSocketAfterTest()
            }, 1000)
            break

          case 'current_case_changed':
            // 当前用例变化
            var caseIndex = data.content?.case_index ?? -1
            var caseId = data.content?.case_id
            var caseTitle = data.content?.title
            var previousCaseIndex = this.currentCaseIndex
            console.log('[current_case_changed] caseIndex:', caseIndex, 'caseId:', caseId, 'previousCaseIndex:', previousCaseIndex)
            this.currentCaseIndex = caseIndex
            // 自动选择当前执行的用例
            if (caseIndex >= 0) {
              this.selectedCaseIndex = caseIndex
            }
            // 只有用例真正切换时才清空日志（从有效索引切换到另一个有效索引）
            // 从 -1 到 0（首次进入）不清空，保留已添加的日志
            if (previousCaseIndex >= 0 && previousCaseIndex !== caseIndex) {
              this.currentCaseLogs = []
            }
            this.addSystemLog('test', 'info', `开始执行用例 ${caseIndex + 1}: ${caseTitle}`)
            break

          case 'step_result_update':
            // 步骤结果更新
            var stepData = data.content || {}
            this.updateStepResult(stepData)
            this.addSystemLog('test', stepData.is_pass ? 'success' : 'warning',
              `步骤 ${stepData.step_index + 1}: ${stepData.is_pass ? '通过' : '失败'}`)
            break

          case 'case_completed':
            // 用例完成
            var completedData = data.content || {}
            console.log('[case_completed] 收到数据:', completedData)
            console.log('[case_completed] currentCaseIndex:', this.currentCaseIndex)
            console.log('[case_completed] testCasesWithStatus:', this.testCasesWithStatus.map((c, i) => ({
              index: i,
              testCaseId: c.testCase.id,
              status: c.status
            })))
            this.updateCaseStatus(completedData)
            this.addSystemLog('test', 'success',
              `用例完成: ${completedData.title} - ${completedData.test_result}`)
            break

          case 'test_stopped':
            // 后端确认停止测试，执行清理
            this.addSystemLog('system', 'success', '后端确认停止，正在关闭连接...')
            this.cleanupAfterStop()
            break

          case 'connection_closing':
            this.addSystemLog('websocket', 'info', '服务端确认关闭连接')
            break

          case 'server_close':
            this.addSystemLog('websocket', 'warning', '服务端超时关闭连接')
            break

          default:
            console.log('未知消息类型:', data.type, data)
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
        this.addSystemLog('websocket', 'error', '消息解析失败')
      }
    },

    /**
     * 播放 Base64 编码的音频 - 使用 AudioContext 直接播放 PCM 数据
     * 参考 dial-agent 的实现
     */
    async playAudioFromBase64(base64Audio, audioType = 'tts') {
      if (!base64Audio) {
        this.addSystemLog('audio', 'warning', '音频数据为空，跳过播放')
        return
      }

      try {
        // 停止之前播放的音频
        if (this.currentPlayingAudio) {
          try {
            this.currentPlayingAudio.stop()
          } catch (e) {
            // 忽略已停止的错误
          }
          this.currentPlayingAudio = null
        }

        // 确保音频播放上下文存在且处于运行状态
        if (!this.audioPlaybackContext) {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext
          this.audioPlaybackContext = new AudioContextClass({ sampleRate: 24000 })
        }

        if (this.audioPlaybackContext.state === 'suspended') {
          await this.audioPlaybackContext.resume()
        }

        // 解码 base64 音频数据
        const binaryString = atob(base64Audio)
        const len = binaryString.length
        const bytes = new Uint8Array(len)

        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }

        // 检测是否是 WAV 格式（有 RIFF 头）
        const isWav = len >= 12 &&
          bytes[0] === 0x52 && bytes[1] === 0x49 &&
          bytes[2] === 0x46 && bytes[3] === 0x46

        let float32Array
        let sampleRate = 24000

        if (isWav) {
          // WAV 格式：解析头部获取采样率和数据偏移
          const view = new DataView(bytes.buffer)
          let dataOffset = 12
          let dataLength = 0

          // 查找 fmt 和 data 块
          while (dataOffset < len - 8) {
            const chunkId = String.fromCharCode(
              bytes[dataOffset], bytes[dataOffset + 1],
              bytes[dataOffset + 2], bytes[dataOffset + 3]
            )
            const chunkSize = view.getUint32(dataOffset + 4, true)

            if (chunkId === 'fmt ') {
              // 获取采样率 (位于 fmt 块偏移 12 处)
              sampleRate = view.getUint32(dataOffset + 12, true)
            } else if (chunkId === 'data') {
              dataLength = chunkSize
              break
            }

            dataOffset += 8 + chunkSize
          }

          // 确保数据长度是偶数（Int16 需要）
          dataLength = Math.floor(dataLength / 2) * 2

          if (dataLength > 0) {
            // 从 WAV 文件中提取 PCM 数据
            const pcmBytes = bytes.slice(dataOffset + 8, dataOffset + 8 + dataLength)
            const pcmData = new Int16Array(pcmBytes.buffer)

            // 转换 Int16 PCM 到 Float32
            float32Array = new Float32Array(pcmData.length)
            const scale = 1.0 / 32768.0
            for (let i = 0; i < pcmData.length; i++) {
              float32Array[i] = pcmData[i] * scale
            }
          }
        } else {
          // 假设是原始 PCM 数据，确保长度是偶数
          const alignedLen = Math.floor(len / 2) * 2
          const pcmData = new Int16Array(bytes.buffer, 0, alignedLen / 2)

          // 转换 Int16 PCM 到 Float32
          float32Array = new Float32Array(pcmData.length)
          const scale = 1.0 / 32768.0
          for (let i = 0; i < pcmData.length; i++) {
            float32Array[i] = pcmData[i] * scale
          }
        }

        if (!float32Array || float32Array.length === 0) {
          throw new Error('无法解析音频数据')
        }

        // 创建 AudioBuffer
        const audioBuffer = this.audioPlaybackContext.createBuffer(
          1, // 单声道
          float32Array.length,
          sampleRate
        )
        audioBuffer.getChannelData(0).set(float32Array)

        // 播放音频
        const source = this.audioPlaybackContext.createBufferSource()
        source.buffer = audioBuffer
        source.connect(this.audioPlaybackContext.destination)

        this.addSystemLog('audio', 'info', `开始播放${audioType === 'tts' ? 'TTS' : '音频'}`, {
          sampleRate,
          duration: (float32Array.length / sampleRate).toFixed(2) + 's'
        })

        source.onended = () => {
          this.addSystemLog('audio', 'info', '音频播放完成')
          this.currentPlayingAudio = null

          // 通知后端 TTS 播放结束
          if (this.isWebSocketReady()) {
            const message = {
              type: 'tts_playback_ended',
              timestamp: Date.now()
            }
            this.websocket.send(JSON.stringify(message))
            this.addSystemLog('audio', 'info', '已通知后端 TTS 播放结束')
          }

          // 新增：启动静默检测
          this.startSilenceDetection()
        }

        source.start()
        this.currentPlayingAudio = source

      } catch (error) {
        console.error('播放音频失败:', error)
        this.addSystemLog('audio', 'error', `播放音频失败: ${error.message}`)
        this.currentPlayingAudio = null
      }
    },

    /**
     * 发送实时音频数据到服务器 - 使用统一的消息格式
     */
    sendRealTimeAudioData(audioBytes) {
      if (!this.isWebSocketReady()) {
        return
      }
      
      try {
        // 使用统一的消息创建函数
        const message = createAudioMessage(audioBytes, {
          sampleRate: 16000,
          channels: 1,
          format: 'pcm',
          sessionId: this.currentSession?.id || this.session_id
        })
        
        this.websocket.send(JSON.stringify(message))
        
      } catch (error) {
        console.error('发送实时音频数据失败:', error)
        this.addSystemLog('audio', 'error', '发送实时音频数据失败')
      }
    },

    /**
     * 尝试重连
     */
    attemptReconnect() {
      this.reconnectAttempts++
      this.addSystemLog('websocket', 'info', `尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      this.reconnectTimeout = setTimeout(async () => {
        try {
          await this.connectToWebSocket()
        } catch (error) {
          console.error('重连失败:', error)
          if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.addSystemLog('websocket', 'error', '重连失败，会话将停止')
            this.handleStopSession()
          }
        }
      }, 2000 * this.reconnectAttempts) // 递增延迟
    },

    /**
     * 开始会话计时器
     */
    startSessionTimer() {
      this.sessionDuration = 0
      this.sessionTimer = setInterval(() => {
        this.sessionDuration++
      }, 1000)
    },

    /**
     * 停止会话计时器
     */
    stopSessionTimer() {
      if (this.sessionTimer) {
        clearInterval(this.sessionTimer)
        this.sessionTimer = null
      }
    },

    /**
     * 添加字幕消息
     */
    addTranscriptMessage(type, content, isPartial = false, isFinal = false) {
      const message = {
        id: Date.now() + Math.random(),
        type,
        content,
        isPartial,
        isFinal,
        timestamp: Date.now()
      }
      
      // 如果是部分消息，更新最后一条相同类型的消息
      if (isPartial) {
        const lastIndex = this.transcriptMessages.length - 1
        const lastMessage = this.transcriptMessages[lastIndex]
        
        if (lastMessage && lastMessage.type === type && lastMessage.isPartial) {
          this.transcriptMessages.splice(lastIndex, 1, message)
        } else {
          this.transcriptMessages.push(message)
        }
      } else {
        this.transcriptMessages.push(message)
      }
      
      // 限制消息数量 - 减少到更合理的数量
      if (this.transcriptMessages.length > 30) {
        this.transcriptMessages = this.transcriptMessages.slice(-30)
      }
    },

    /**
     * 更新部分转录
     */
    updatePartialTranscript(content) {
      this.addTranscriptMessage('user', content, true, false)
    },

    /**
     * 更新部分AI回复
     */
    updatePartialAIResponse(content) {
      this.addTranscriptMessage('agent', content, true, false)
    },

    /**
     * 添加系统日志
     */
    addSystemLog(category, level, message, details = null) {
      const log = {
        id: Date.now() + Math.random(),
        category,
        level,
        message,
        details,
        timestamp: Date.now()
      }

      // 1. 添加到全局日志（用于 TranscriptPanel）
      this.systemLogs.push(log)

      // 2. 直接添加到当前用例日志（用于实时显示）- 这是关键！
      // Vue 2 能正确追踪数组的 push 操作
      this.currentCaseLogs.push(log)

      // 3. 同时存储到 testCasesWithStatus（用于历史查看）
      // 使用 currentCaseIndex，但如果还是 -1（尚未收到 current_case_changed），则使用 0（第一个用例）
      const targetCaseIndex = this.currentCaseIndex >= 0 ? this.currentCaseIndex : 0
      if (targetCaseIndex >= 0 && this.testCasesWithStatus[targetCaseIndex]) {
        const currentCase = this.testCasesWithStatus[targetCaseIndex]
        const currentLogs = currentCase.logs || []
        this.$set(this.testCasesWithStatus, targetCaseIndex, {
          ...currentCase,
          logs: [...currentLogs, log]
        })
      }

      // 限制日志数量
      if (this.systemLogs.length > 50) {
        this.systemLogs = this.systemLogs.slice(-50)
      }
    },

    /**
     * 清空字幕
     */
    clearTranscript() {
      this.transcriptMessages = []
      this.addSystemLog('system', 'info', '字幕已清空')
    },

    /**
     * 清空日志
     */
    clearLogs() {
      this.systemLogs = []
    },

    /**
     * 获取状态文本
     */
    getStatusText() {
      const statusMap = {
        'disconnected': '未连接',
        'connecting': '连接中...',
        'connected': '已连接',
        'active': '会话中'
      }
      return statusMap[this.connectionStatus] || '未知状态'
    },

    /**
     * 处理音频错误
     */
    handleAudioError(errorType, error) {
      switch (errorType) {
        case 'microphone_permission_denied':
          this.$message?.error('麦克风权限被拒绝，请允许访问麦克风')
          break
        case 'recording_error':
          this.$message?.error('录制过程中发生错误')
          break
        default:
          this.$message?.error(`音频处理错误: ${errorType} - ${error?.message || '未知错误'}`)
      }
    },

    /**
     * 确认测试用例
     * 发送 test_case_confirm 消息到服务端，并初始化音频处理器
     */
    async confirmTestCases(testCases) {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        // 使用用户修改后的测试用例初始化状态数组
        this.initTestCasesWithStatus(testCases)

        // 1. 立即切换到测试用例执行视图（确保能接收后续的WebSocket消息）
        if (this.$refs.sceneTestPanel) {
          this.$refs.sceneTestPanel.switchToTestExecutionView()
          // 默认选中第一个用例
          this.selectedCaseIndex = 0
        }
        // 清空当前用例日志，准备接收新用例的日志
        this.currentCaseLogs = []

        // 2. 初始化音频处理器（用户确认后才开始采集音频）
        try {
          await this.initializeAudioProcessor()
          this.addSystemLog('audio', 'success', '音频处理器初始化成功，麦克风已激活')
        } catch (error) {
          console.error('音频处理器初始化失败:', error)
          this.addSystemLog('audio', 'error', `音频处理器初始化失败: ${error.message}`)
          // 即使音频初始化失败，也继续执行测试
        }

        // 3. 发送确认消息到服务端（包含用户修改后的测试用例）
        const confirmMessage = {
          type: 'test_case_confirm',
          timestamp: Date.now(),
          test_cases: testCases  // 包含用户修改后的测试用例
        }
        this.websocket.send(JSON.stringify(confirmMessage))
        this.addSystemLog('system', 'success', `已确认 ${testCases.length} 个测试用例，开始执行...`)
        this.addTranscriptMessage('system', '测试用例已确认，请开始说话...', false, true)
      } else {
        this.addSystemLog('websocket', 'error', 'WebSocket 未连接，无法确认测试用例')
      }
    },

    /**
     * 取消测试用例确认
     */
    cancelTestCaseConfirm() {
      // 切换回字幕面板
      if (this.$refs.sceneTestPanel) {
        this.$refs.sceneTestPanel.rightPanelContent = 'transcript'
      }
      this.addSystemLog('system', 'info', '已取消测试用例确认')

      // 停止会话
      if (this.isSessionActive) {
        this.handleStopSession()
      }
    },

    /**
     * 清理资源
     */
    async cleanup() {
      console.log('开始清理资源...')

      // 停止静默检测
      this.stopSilenceDetection()

      // 停止会话计时器
      this.stopSessionTimer()

      // 断开WebSocket
      this.disconnectFromWebSocket()

      // 销毁音频处理器（释放麦克风）
      if (this.audioProcessor) {
        console.log('销毁音频处理器...')
        this.audioProcessor.destroy()
        this.audioProcessor = null
      }

      // 释放音频播放上下文（释放扬声器）
      await this.releaseAudioPlaybackContext()

      // 重置状态
      this.isSessionActive = false
      this.isConnecting = false
      this.connectionStatus = 'disconnected'
      this.hasAudioActivity = false
      this.currentAudioLevel = 0
      this.sessionDuration = 0

      console.log('资源清理完成')
    },

    /**
     * 静默检测控制方法
     */
    startSilenceDetection() {
      // 重置状态
      this.silenceDetectionActive = true
      this.hasDetectedVoice = false
      this.silenceStartTime = null
      this.speechFrames = 0
      this.silenceFrames = 0
      this.speechStartTime = null
      this.actualSpeechDuration = 0
      // 不重置 noiseFloor，保留已学习的噪音底噪
      this.addSystemLog('audio', 'info',
        `开始静默检测，当前阈值: ${this.adaptiveThreshold.toFixed(4)}`)
    },

    stopSilenceDetection() {
      this.silenceDetectionActive = false
      this.hasDetectedVoice = false
      this.silenceStartTime = null
      this.speechFrames = 0
      this.silenceFrames = 0
      this.speechStartTime = null
      this.actualSpeechDuration = 0
    },

    handleSilenceDetection(level) {
      // 基础音量检测
      const hasVoiceByLevel = level >= this.adaptiveThreshold

      // 频谱分析：使用 RealtimeAudioProcessor 的人声能量占比计算
      const voiceEnergyRatio = this.audioProcessor?.calculateVoiceEnergyRatio?.() || 0
      this.lastVoiceEnergyRatio = voiceEnergyRatio  // 保存用于调试
      const hasVoiceBySpectrum = voiceEnergyRatio >= this.voiceEnergyRatioThreshold

      // 综合判断：音量达标 + 频谱符合人声特征
      const hasVoice = hasVoiceByLevel && hasVoiceBySpectrum

      if (!this.hasDetectedVoice) {
        // 阶段1：等待用户说话开始（帧计数防抖）
        if (hasVoice) {
          this.speechFrames++
          this.silenceFrames = 0
          // 连续3帧语音确认说话开始
          if (this.speechFrames >= 3) {
            this.hasDetectedVoice = true
            this.speechStartTime = Date.now()  // 记录说话开始时间
            this.actualSpeechDuration = 0
            this.addSystemLog('audio', 'info', '检测到用户说话')
          }
        } else {
          // 短暂噪音，重置帧计数
          this.speechFrames = 0
        }
      } else {
        // 阶段2：用户正在说话
        if (hasVoice) {
          // 用户还在说话，更新说话时长
          this.actualSpeechDuration = Date.now() - this.speechStartTime
          this.silenceStartTime = null
          this.silenceFrames = 0
        } else {
          // 用户静默中
          this.silenceFrames++
          if (!this.silenceStartTime) {
            this.silenceStartTime = Date.now()
          }
          const silenceDuration = Date.now() - this.silenceStartTime

          // 先检查说话时长是否足够
          if (this.actualSpeechDuration < this.minSpeechDuration) {
            // 说话时长不足，等待更长时间确认是否真的结束
            if (silenceDuration >= 500) {  // 500ms 确认说话结束
              // 说话时长不足，重置状态等待新的说话
              this.addSystemLog('audio', 'info',
                `说话时长不足 ${(this.actualSpeechDuration / 1000).toFixed(1)}s < ${(this.minSpeechDuration / 1000)}s，重置检测`)
              this.hasDetectedVoice = false
              this.speechStartTime = null
              this.actualSpeechDuration = 0
              this.silenceStartTime = null
              this.speechFrames = 0
              this.silenceFrames = 0
            }
          } else {
            // 说话时长足够，等待静默阈值后触发识别
            if (silenceDuration >= this.silenceThreshold) {
              this.addSystemLog('audio', 'info',
                `说话时长 ${(this.actualSpeechDuration / 1000).toFixed(1)}s，检测到${this.silenceThreshold / 1000}秒静默，触发识别`)
              this.sendSilenceDetected()
              this.stopSilenceDetection()  // 停止检测，避免重复发送
            }
          }
        }
      }
    },

    sendSilenceDetected() {
      if (!this.isWebSocketReady()) return
      const message = {
        type: 'silence_detected',
        timestamp: Date.now()
      }
      this.websocket.send(JSON.stringify(message))
    },

    /**
     * 更新自适应阈值 - 基于噪音底噪估计算法
     * 参考：ITU-T G.729 Annex B
     */
    updateAdaptiveThreshold(level) {
      // 仅在未检测到说话时更新噪音底噪
      if (!this.hasDetectedVoice) {
        // 一阶IIR滤波器平滑
        this.noiseFloor = this.noiseFloorAlpha * this.noiseFloor +
                          (1 - this.noiseFloorAlpha) * level
      }

      // 动态计算语音阈值 = 噪音底噪 * 信号余量
      this.adaptiveThreshold = Math.max(
        this.baseVolumeThreshold,
        this.noiseFloor * this.signalMargin
      )
    },

    /**
     * 更新步骤结果
     */
    updateStepResult(stepData) {
      const { case_id, step_index, is_pass, actual_result } = stepData
      const index = this.testCasesWithStatus.findIndex(c => c.testCase.id === case_id)
      if (index >= 0) {
        const caseStatus = this.testCasesWithStatus[index]
        if (!caseStatus.stepResults) {
          caseStatus.stepResults = []
        }
        // 使用 $set 确保响应式
        this.$set(caseStatus.stepResults, step_index, {
          is_pass,
          actual_result,
          timestamp: Date.now()
        })
      }
    },

    /**
     * 更新用例状态
     */
    updateCaseStatus(completedData) {
      const { case_id, test_result, step_pass_results, actual_results } = completedData
      console.log('[updateCaseStatus] case_id:', case_id, 'test_result:', test_result)

      // 先尝试用 case_id 匹配
      let index = this.testCasesWithStatus.findIndex(c => c.testCase.id === case_id)
      console.log('[updateCaseStatus] 通过case_id查找结果:', index)

      // 如果用 case_id 找不到，尝试用 currentCaseIndex
      if (index < 0 && this.currentCaseIndex >= 0 && this.currentCaseIndex < this.testCasesWithStatus.length) {
        index = this.currentCaseIndex
        console.log('[updateCaseStatus] 使用currentCaseIndex:', index)
      }

      if (index >= 0) {
        // 规范化状态值（确保是大写格式）
        let normalizedStatus = (test_result || 'NOT_RUN').toUpperCase()
        // 处理可能的变体
        const statusMap = {
          'PASS': 'PASS',
          'PASSED': 'PASS',
          'FAIL': 'FAIL',
          'FAILED': 'FAIL',
          'BLOCKED': 'BLOCKED',
          'SKIPPED': 'SKIPPED',
          'NOT_RUN': 'NOT_RUN',
          'NOTRUN': 'NOT_RUN'
        }
        normalizedStatus = statusMap[normalizedStatus] || normalizedStatus
        console.log('[updateCaseStatus] 规范化状态:', normalizedStatus)

        // 创建新数组以确保 Vue 2 响应式更新
        const newTestCasesWithStatus = [...this.testCasesWithStatus]
        newTestCasesWithStatus[index] = {
          ...newTestCasesWithStatus[index],
          status: normalizedStatus,
          stepResults: step_pass_results?.map((is_pass, i) => ({
            is_pass,
            actual_result: actual_results?.[i] || '',
            timestamp: Date.now()
          })) || [],
          actual_results: actual_results || []
        }
        this.testCasesWithStatus = newTestCasesWithStatus
        console.log('[updateCaseStatus] 更新完成, 新状态:', this.testCasesWithStatus[index].status)
      } else {
        console.warn('[updateCaseStatus] 未找到匹配的用例!')
      }

      // 用例完成后，自动切换到下一个用例
      if (this.currentCaseIndex >= 0 && this.currentCaseIndex < this.testCasesWithStatus.length - 1) {
        this.selectedCaseIndex = this.currentCaseIndex + 1
      }
    },

    /**
     * 初始化测试用例状态数组
     */
    initTestCasesWithStatus(testCases) {
      this.testCasesWithStatus = testCases.map(tc => ({
        testCase: tc,
        status: 'NOT_RUN',
        logs: [],           // 每个用例的日志数组（用于历史查看）
        stepResults: []
      }))
      // 清空实时日志
      this.currentCaseLogs = []
      // 重置测试状态
      this.testCompleted = false
      this.testReportData = null
      // 重置用例索引
      this.currentCaseIndex = -1
      this.selectedCaseIndex = -1
    },

    /**
     * 获取选中用例的日志
     */
    getSelectedCaseLogs() {
      if (this.selectedCaseIndex < 0 || !this.testCasesWithStatus[this.selectedCaseIndex]) {
        return []
      }
      const caseId = this.testCasesWithStatus[this.selectedCaseIndex].testCase.id
      return this.testCaseLogs[caseId] || []
    },

    /**
     * 处理用例选择事件
     */
    handleSelectCase(index) {
      this.selectedCaseIndex = index
    },

    /**
     * 处理查看报告事件
     */
    handleViewReport() {
      // 通知 SceneTestPanel 显示详细报告
      if (this.$refs.sceneTestPanel) {
        this.$refs.sceneTestPanel.showDetailedReport(this.testReportData)
      }
    }
  }
}
</script>

<style scoped>
.agentic-test-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  position: relative;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding: 12px;
  overflow: hidden;
}

.employee-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 会话管理面板 - 悬浮覆盖层 */
.session-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}

.session-panel {
  background: var(--bg-surface);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.session-header h3 {
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
  border-radius: 8px;
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

/* VAD+ASR测试面板 - 悬浮覆盖层 */
.vad-asr-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}

.vad-asr-panel {
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .session-panel {
    width: 95%;
    max-height: 90vh;
  }

  .session-header {
    padding: 16px 20px;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 10px;
  }
}
</style>