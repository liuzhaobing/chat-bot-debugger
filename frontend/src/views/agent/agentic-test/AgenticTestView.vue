<template>
  <div class="agentic-test-view">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">厨电控制测试</h1>
        <span class="page-subtitle">Agentic Test 语音交互平台</span>
      </div>
      
      <div class="toolbar-center">
        <div class="panel-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activePanel === 'transcript' }"
            @click="switchPanel('transcript')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>通话字幕</span>
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activePanel === 'devices' }"
            @click="switchPanel('devices')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
            <span>智能设备</span>
          </button>
        </div>
      </div>
      
      <div class="toolbar-right">
        <!-- VAD+ASR测试按钮 -->
        <button 
          class="test-btn"
          @click="showVadAsrTest = true"
          title="VAD+ASR调试"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
          <span>VAD+ASR调试</span>
        </button>
        
        <!-- 语音会话按钮 -->
        <button 
          class="session-status-btn" 
          @click="handleVoiceAgentClick"
          :class="{ 
            connected: isSessionActive,
            connecting: isConnecting
          }"
        >
          <div class="status-dot"></div>
          <strong v-if="!isConnecting && !isSessionActive">对话调试</strong>
          <strong v-if="isConnecting">连线中...</strong>
          <strong v-if="isSessionActive" class="session-duration">{{ formattedSessionDuration }}</strong>
        </button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 通话字幕面板 -->
      <div v-if="activePanel === 'transcript'" class="transcript-container">
        <TranscriptPanel
          :transcript-messages="transcriptMessages"
          :logs="systemLogs"
          @clear-transcript="clearTranscript"
          @clear-logs="clearLogs"
        />
      </div>

      <!-- 智能设备面板 -->
      <div v-if="activePanel === 'devices'" class="devices-container">
        <div class="devices-content">
          <IOTConfigPanel ref="iotPanel" :hide-config="true" />
        </div>
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
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import IOTConfigPanel from '@/components/agentic-test/IOTConfigPanel.vue'
import TranscriptPanel from '@/components/agentic-test/TranscriptPanel.vue'
import SessionManager from '@/components/agentic-test/SessionManager.vue'
import VadAsrTestPanel from '@/components/agentic-test/VadAsrTestPanel.vue'
import RealtimeAudioProcessor, { createAudioMessage } from '@/utils/realtimeAudioProcessor.js'
import { getAgenticTestWsUrl } from '@/config/worker.js'
import agenticTestService from '@/services/agenticTestService'

export default {
  name: 'AgenticTestView',
  components: {
    IOTConfigPanel,
    TranscriptPanel,
    SessionManager,
    VadAsrTestPanel
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
      activePanel: 'transcript', // 'transcript' | 'devices'
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

      // WebSocket
      websocket: null,
      reconnectAttempts: 0,
      maxReconnectAttempts: 3,
      reconnectTimeout: null
    }
  },
  mounted() {
    // 不再在页面加载时初始化音频处理器
    // 只在用户点击对话调试按钮时才初始化和启动麦克风
    this.addSystemLog('system', 'info', '系统初始化完成，点击对话调试按钮开始会话')
    
    // 启动定时清理机制，每5分钟清理一次过多的数据
    this.cleanupInterval = setInterval(() => {
      this.performPeriodicCleanup()
    }, 5 * 60 * 1000) // 5分钟
  },
  beforeDestroy() {
    // 清理定时器
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval)
    }
    
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
     * 面板切换
     */
    switchPanel(panel) {
      this.activePanel = panel
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
     * 处理加载设备请求
     */
    handleLoadDevices(config) {
      this.addSystemLog('iot', 'info', '开始加载设备列表...', { config })
      // 这里可以触发IOTConfigPanel的加载设备方法
      // 通过事件总线或者ref来调用
      this.$nextTick(() => {
        // 如果IOTConfigPanel有暴露的方法，可以直接调用
        const iotPanel = this.$refs.iotPanel
        if (iotPanel && typeof iotPanel.loadDevices === 'function') {
          iotPanel.loadDevices()
        }
      })
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
      
      this.isConnecting = true
      this.connectionStatus = 'connecting'
      this.addSystemLog('system', 'info', '正在启动会话...')
      
      try {
        // 1. 建立WebSocket连接
        await this.connectToWebSocket()
        
        // 2. 初始化并启动音频处理器
        await this.initializeAudioProcessor()
        
        // 3. 启动会话计时器
        this.startSessionTimer()
        
        // 4. 更新状态
        this.isSessionActive = true
        this.isConnecting = false
        this.connectionStatus = 'active'
        this.activePanel = 'transcript' // 自动切换到字幕面板
        
        this.addSystemLog('system', 'success', '会话启动成功，麦克风已激活')
        this.addTranscriptMessage('system', '会话已开始，请开始说话...', false, true)
        
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
     * 停止会话
     */
    async handleStopSession() {
      if (!this.isSessionActive) return
      
      this.addSystemLog('system', 'info', '正在停止会话...')
      
      try {
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
        
      } catch (error) {
        console.error('停止会话失败:', error)
        this.addSystemLog('system', 'error', `停止会话失败: ${error.message}`)
      }
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

      // 确保有有效的 session，如果没有则创建新的
      let sessionId = this.currentSession?.id
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
          this.addSystemLog('websocket', 'success', 'WebSocket连接已建立')

          // 连接建立后立即发送start_test（已包含iot_config，无需单独发送update_iot_config）
          const iotConfig = this.getIOTConfigFromStorage()
          const startTestMessage = {
            type: 'start_test',
            query: '我的家庭圈有哪些一体机？',
            iot_config: iotConfig,
            timestamp: Date.now()
          }
          this.websocket.send(JSON.stringify(startTestMessage))
          this.addSystemLog('test', 'info', '已发送start_test消息', iotConfig)

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
     * 处理WebSocket消息
     */
    handleWebSocketMessage(event) {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
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
     * 定期清理数据，防止内存泄漏
     */
    performPeriodicCleanup() {
      const now = Date.now()
      const maxAge = 15 * 60 * 1000 // 15分钟
      
      // 清理过期的转录消息
      this.transcriptMessages = this.transcriptMessages.filter(msg => 
        now - msg.timestamp < maxAge
      )
      
      // 清理过期的系统日志
      this.systemLogs = this.systemLogs.filter(log => 
        now - log.timestamp < maxAge
      )
      
      // 强制限制数量（双重保险）
      if (this.transcriptMessages.length > 20) {
        this.transcriptMessages = this.transcriptMessages.slice(-20)
      }
      
      if (this.systemLogs.length > 30) {
        this.systemLogs = this.systemLogs.slice(-30)
      }
      
      this.addSystemLog('system', 'info', '执行定期数据清理', {
        transcriptCount: this.transcriptMessages.length,
        systemLogCount: this.systemLogs.length
      })
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
      
      this.systemLogs.push(log)
      
      // 限制日志数量 - 减少到更合理的数量
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
     * 清理资源
     */
    async cleanup() {
      console.log('开始清理资源...')

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

/* 顶部工具栏 - 参考dial-agent样式 */
.top-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.panel-tabs {
  display: flex;
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: var(--text-tertiary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.tab-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
  transition: left 0.5s ease;
}

.tab-btn:hover::before {
  left: 100%;
}

.tab-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
  transform: translateY(-1px);
}

.tab-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  font-weight: 600;
  box-shadow: 
    0 4px 12px rgba(59, 130, 246, 0.3),
    0 2px 4px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 50%);
  border-radius: 8px;
  pointer-events: none;
}

.tab-btn.active:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  box-shadow: 
    0 6px 16px rgba(59, 130, 246, 0.4),
    0 2px 6px rgba(59, 130, 246, 0.3);
  transform: translateY(-2px);
}

.tab-btn svg {
  width: 16px;
  height: 16px;
  transition: all 0.3s ease;
}

.tab-btn.active svg {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* VAD+ASR测试按钮 */
.test-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent-blue);
}

.test-btn svg {
  width: 14px;
  height: 14px;
}

/* 会话状态按钮 - 类似dial-agent的灵动岛样式 */
.session-status-btn {
  background: #000;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  font-size: 12px;
  font-weight: 500;
  min-width: 80px;
  justify-content: center;
}

.session-status-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.session-status-btn.connected {
  background: #000;
  border-color: rgba(16, 185, 129, 0.3);
  animation: connected-glow 2s infinite;
}

.session-status-btn.connecting {
  background: #000;
  border-color: rgba(245, 158, 11, 0.3);
  animation: connecting-glow 1s infinite;
}

.session-status-btn.connected .status-dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

.session-status-btn.connecting .status-dot {
  background: #f59e0b;
  animation: pulse 0.8s infinite;
}

.session-status-btn .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  transition: all 0.3s ease;
}

.session-status-btn .session-duration {
  color: #10b981;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-weight: 600;
}

@keyframes connected-glow {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), 0 0 0 4px rgba(16, 185, 129, 0.2);
  }
}

@keyframes connecting-glow {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 0 0 rgba(245, 158, 11, 0.4);
  }
  50% {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), 0 0 0 4px rgba(245, 158, 11, 0.2);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding: 12px 20px;
  overflow: hidden;
}

.transcript-container,
.devices-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.devices-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.devices-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.devices-content {
  flex: 1;
  overflow: hidden;
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
  .toolbar-left {
    display: none;
  }
  
  .toolbar-center {
    justify-content: flex-start;
  }
  
  .main-content {
    padding: 16px 20px;
  }
}

@media (max-width: 768px) {
  .top-toolbar {
    padding: 16px 20px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .tab-btn {
    padding: 10px 16px;
    font-size: 13px;
  }
  
  .tab-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .session-panel {
    width: 95%;
    max-height: 90vh;
  }
  
  .session-header {
    padding: 16px 20px;
  }
}

@media (max-width: 480px) {
  .top-toolbar {
    padding: 12px 16px;
  }
  
  .main-content {
    padding: 12px 16px;
  }
  
  .tab-btn {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .tab-btn span {
    display: none;
  }
  
  .session-status-btn {
    padding: 6px 12px;
    font-size: 11px;
    min-width: 60px;
  }
  
  .devices-header h2 {
    font-size: 18px;
  }
}
</style>