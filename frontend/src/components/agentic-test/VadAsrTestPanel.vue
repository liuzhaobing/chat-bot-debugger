<template>
  <div class="vad-asr-test-panel">
    <div class="panel-header">
      <div class="header-left">
        <h3>VAD+ASR 测试调试</h3>
        <span class="app-id">App ID: 4f95e97b0ec641fab9772b68a81bcf4a</span>
      </div>
      <button class="close-btn" @click="$emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="panel-content">
      <!-- 控制区域 -->
      <div class="control-section">
        <div class="control-row">
          <div class="control-group">
            <label>连接状态</label>
            <div class="status-indicator" :class="connectionStatus">
              <div class="status-dot"></div>
              <span>{{ getStatusText() }}</span>
            </div>
          </div>
          
          <div class="control-group">
            <label>VAD敏感度</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                v-model="vadSensitivity"
                @input="updateVadSensitivity"
                class="sensitivity-slider"
              />
              <span class="slider-value">{{ vadSensitivity }}</span>
            </div>
          </div>
          
          <div class="control-group">
            <button 
              class="test-btn"
              :class="{ 
                'btn-success': !isTestActive,
                'btn-danger': isTestActive,
                'btn-connecting': isConnecting
              }"
              @click="toggleTest"
              :disabled="isConnecting"
            >
              <svg v-if="isConnecting" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
              </svg>
              <svg v-else-if="!isTestActive" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5,3 19,12 5,21 5,3"></polygon>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
              {{ getButtonText() }}
            </button>
          </div>
        </div>
      </div>

      <!-- 音频可视化区域 -->
      <div class="visualization-section">
        <div class="audio-visualizer">
          <div class="visualizer-header">
            <h4>音频可视化</h4>
            <div class="audio-stats">
              <span class="stat">音量: {{ Math.round(audioLevel * 100) }}%</span>
              <span class="stat" :class="{ active: isVoiceActive }">
                VAD: {{ isVoiceActive ? '检测到语音' : '静音' }}
              </span>
            </div>
          </div>
          
          <!-- 音频波形 -->
          <div class="waveform-container">
            <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
          </div>
          
          <!-- 音频级别指示器 -->
          <div class="level-indicator">
            <div class="level-bar">
              <div 
                class="level-fill" 
                :style="{ width: (audioLevel * 100) + '%' }"
                :class="{ active: isVoiceActive }"
              ></div>
            </div>
            <div class="level-labels">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 转录结果区域 -->
      <div class="transcript-section">
        <div class="transcript-header">
          <h4>转录结果</h4>
          <div class="transcript-controls">
            <button class="btn-sm" @click="clearTranscript">清空</button>
            <button class="btn-sm" @click="exportTranscript">导出</button>
          </div>
        </div>
        
        <div class="transcript-content" ref="transcriptContent">
          <div v-if="transcriptMessages.length === 0" class="empty-transcript">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
            <p>开始测试后，转录结果将显示在这里</p>
          </div>
          
          <div v-else class="transcript-messages">
            <div 
              v-for="message in transcriptMessages" 
              :key="message.id"
              class="transcript-message"
              :class="{ 
                partial: message.isPartial,
                final: message.isFinal,
                'low-confidence': message.confidence && message.confidence < 0.7
              }"
            >
              <div class="message-header">
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                <span v-if="message.confidence" class="message-confidence">
                  置信度: {{ Math.round(message.confidence * 100) }}%
                </span>
                <span class="message-type" :class="message.isPartial ? 'partial' : 'final'">
                  {{ message.isPartial ? '实时' : '最终' }}
                </span>
              </div>
              <div class="message-content">{{ message.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 调试日志区域 -->
      <div class="debug-section">
        <div class="debug-header">
          <h4>调试日志</h4>
          <div class="debug-controls">
            <button class="btn-sm" @click="clearLogs">清空日志</button>
            <button class="btn-sm" @click="exportLogs">导出日志</button>
          </div>
        </div>
        
        <div class="debug-content" ref="debugContent">
          <div v-if="debugLogs.length === 0" class="empty-logs">
            <p>暂无调试日志</p>
          </div>
          
          <div v-else class="debug-logs">
            <div 
              v-for="log in debugLogs" 
              :key="log.id"
              class="debug-log"
              :class="log.level"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-category">[{{ log.category }}]</span>
              <span class="log-message">{{ log.message }}</span>
              <div v-if="log.details" class="log-details">
                {{ JSON.stringify(log.details, null, 2) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VadAsrTestPanel',
  data() {
    return {
      // 连接状态
      connectionStatus: 'disconnected', // 'disconnected' | 'connecting' | 'connected' | 'active'
      isTestActive: false,
      isConnecting: false,
      
      // 音频处理
      audioContext: null,
      analyser: null,
      mediaStream: null,
      audioProcessor: null,
      dataArray: null,
      audioLevel: 0,
      isVoiceActive: false,
      vadSensitivity: 0.5,
      vadBuffer: [],
      voiceEndTimeout: null,
      audioPacketsSent: 0,
      
      // WebSocket
      websocket: null,
      
      // 数据
      transcriptMessages: [],
      debugLogs: [],
      
      // 可视化
      waveformCanvas: null,
      waveformContext: null,
      animationFrame: null,
      
      // 常量
      APP_ID: '4f95e97b0ec641fab9772b68a81bcf4a'
    }
  },
  mounted() {
    this.initializeCanvas()
    this.addDebugLog('system', 'info', 'VAD+ASR测试面板已初始化')
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    /**
     * 初始化画布
     */
    initializeCanvas() {
      this.$nextTick(() => {
        const canvas = this.$refs.waveformCanvas
        if (canvas) {
          this.waveformCanvas = canvas
          this.waveformContext = canvas.getContext('2d')
          
          // 设置画布尺寸
          const rect = canvas.getBoundingClientRect()
          canvas.width = rect.width * window.devicePixelRatio
          canvas.height = rect.height * window.devicePixelRatio
          this.waveformContext.scale(window.devicePixelRatio, window.devicePixelRatio)
          
          this.startWaveformAnimation()
        }
      })
    },

    /**
     * 开始/停止测试
     */
    async toggleTest() {
      if (this.isConnecting) return
      
      if (this.isTestActive) {
        await this.stopTest()
      } else {
        await this.startTest()
      }
    },

    /**
     * 开始测试
     */
    async startTest() {
      this.isConnecting = true
      this.connectionStatus = 'connecting'
      this.addDebugLog('system', 'info', '开始启动VAD+ASR测试...')
      
      try {
        // 1. 建立WebSocket连接
        await this.connectWebSocket()
        
        // 2. 初始化音频处理器
        await this.initializeAudioProcessor()
        
        // 3. 开始音频分析
        this.startAudioAnalysis()
        
        // 4. 更新状态
        this.isTestActive = true
        this.isConnecting = false
        this.connectionStatus = 'active'
        
        this.addDebugLog('system', 'success', 'VAD+ASR测试启动成功')
        
      } catch (error) {
        console.error('启动测试失败:', error)
        this.isConnecting = false
        this.connectionStatus = 'disconnected'
        this.addDebugLog('system', 'error', `启动测试失败: ${error.message}`)
        this.cleanup()
      }
    },

    /**
     * 停止测试
     */
    async stopTest() {
      this.addDebugLog('system', 'info', '正在停止VAD+ASR测试...')
      
      try {
        // 停止音频处理
        this.stopAudioAnalysis()
        
        // 断开WebSocket
        this.disconnectWebSocket()
        
        // 更新状态
        this.isTestActive = false
        this.connectionStatus = 'disconnected'
        this.audioLevel = 0
        this.isVoiceActive = false
        
        this.addDebugLog('system', 'success', 'VAD+ASR测试已停止')
        
      } catch (error) {
        console.error('停止测试失败:', error)
        this.addDebugLog('system', 'error', `停止测试失败: ${error.message}`)
      }
    },

    /**
     * 初始化音频处理器 - 使用类似dial电话客服的实时音频处理
     */
    async initializeAudioProcessor() {
      try {
        // 获取麦克风权限
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        })

        // 创建音频上下文
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
        
        if (this.audioContext.state === 'suspended') {
          await this.audioContext.resume()
        }

        // 创建分析器用于可视化
        this.analyser = this.audioContext.createAnalyser()
        this.analyser.fftSize = 2048
        this.analyser.smoothingTimeConstant = 0.8
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount)

        const source = this.audioContext.createMediaStreamSource(this.mediaStream)
        source.connect(this.analyser)

        // 创建音频处理器 - 模拟dial电话客服的方式
        const bufferSize = 256 // 16ms at 16kHz (256 samples = 16ms)
        this.audioProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1)
        
        this.audioProcessor.onaudioprocess = (e) => {
          if (!this.isTestActive) return
          
          const inputData = e.inputBuffer.getChannelData(0)
          
          // 计算音频级别用于可视化
          let sum = 0
          for (let i = 0; i < inputData.length; i++) {
            sum += Math.abs(inputData[i])
          }
          const average = sum / inputData.length
          this.audioLevel = Math.min(1, average * 10)
          
          // VAD检测
          this.detectVoiceActivity(average)
          
          // 转换为16位PCM字节数据 - 完全模拟dial电话客服
          const pcmData = new Int16Array(inputData.length)
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]))
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
          }
          
          // 转换为字节数组
          const audioBytes = new Uint8Array(pcmData.buffer)
          
          // 实时发送音频数据
          if (this.isWebSocketReady()) {
            this.sendRealTimeAudioData(audioBytes)
          }
        }
        
        source.connect(this.audioProcessor)
        this.audioProcessor.connect(this.audioContext.destination)
        
        this.addDebugLog('audio', 'success', '实时音频处理器初始化成功', {
          sampleRate: 16000,
          bufferSize: bufferSize,
          latency: `${bufferSize / 16000 * 1000}ms`
        })
        
      } catch (error) {
        this.addDebugLog('audio', 'error', '音频处理器初始化失败', { error: error.message })
        throw error
      }
    },

    /**
     * 连接WebSocket
     */
    async connectWebSocket() {
      return new Promise((resolve, reject) => {
        try {
          // 使用指定的app-id创建WebSocket连接
          const wsUrl = `ws://localhost:8000/ws/agentic-test/vad-asr-test/?app_id=${this.APP_ID}`
          
          this.websocket = new WebSocket(wsUrl)
          
          this.websocket.onopen = () => {
            this.connectionStatus = 'connected'
            this.addDebugLog('websocket', 'success', 'WebSocket连接已建立')
            resolve()
          }
          
          this.websocket.onmessage = (event) => {
            this.handleWebSocketMessage(event)
          }
          
          this.websocket.onclose = (event) => {
            this.addDebugLog('websocket', 'warning', `WebSocket连接已关闭: ${event.code}`)
          }
          
          this.websocket.onerror = (error) => {
            console.error('WebSocket错误:', error)
            this.addDebugLog('websocket', 'error', 'WebSocket连接错误')
            reject(new Error('WebSocket连接失败'))
          }
          
          // 连接超时
          setTimeout(() => {
            if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
              this.websocket.close()
              this.websocket = null
              reject(new Error('WebSocket连接超时'))
            }
          }, 10000)
          
        } catch (error) {
          reject(error)
        }
      })
    },

    /**
     * 断开WebSocket连接
     */
    disconnectWebSocket() {
      if (this.websocket) {
        try {
          this.websocket.close()
        } catch (error) {
          console.error('关闭WebSocket时出错:', error)
        }
        this.websocket = null
      }
    },

    /**
     * 检查WebSocket是否可用
     */
    isWebSocketReady() {
      return this.websocket && this.websocket.readyState === WebSocket.OPEN
    },

    /**
     * 处理WebSocket消息
     */
    handleWebSocketMessage(event) {
      try {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'transcript_partial':
            this.updatePartialTranscript(data.content, data.confidence)
            this.addDebugLog('asr', 'info', '收到部分转录结果', { 
              content: data.content, 
              confidence: data.confidence 
            })
            break
            
          case 'transcript_final':
            this.addTranscriptMessage(data.content, false, true, data.confidence)
            this.addDebugLog('asr', 'success', '收到最终转录结果', { 
              content: data.content, 
              confidence: data.confidence 
            })
            break
            
          case 'vad_status':
            this.addDebugLog('vad', 'info', `VAD状态: ${data.status}`, data.details)
            break
            
          case 'error':
            this.addDebugLog('error', 'error', data.message, data.details)
            break
            
          default:
            this.addDebugLog('websocket', 'info', '收到未知消息类型', data)
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
        this.addDebugLog('websocket', 'error', '消息解析失败')
      }
    },

    /**
     * 发送实时音频数据到服务器 - 模拟dial电话客服的方式
     */
    sendRealTimeAudioData(audioBytes) {
      if (!this.isWebSocketReady()) {
        return
      }
      
      try {
        // 转换为base64 - 与dial电话客服版本一致
        let binary = ''
        for (let i = 0; i < audioBytes.length; i++) {
          binary += String.fromCharCode(audioBytes[i])
        }
        const base64 = btoa(binary)
        
        // 消息格式与dial电话客服版本完全一致
        const message = {
          type: 'audio_data',
          timestamp: Math.floor(Date.now()),
          data: {
            audio_data: base64,
            sample_rate: 16000,
            channels: 1,
            format: 'pcm',  // 原始PCM格式，不是webm
            size: audioBytes.length
          },
          app_id: this.APP_ID
        }
        
        this.websocket.send(JSON.stringify(message))
        
        // 统计信息
        this.audioPacketsSent = (this.audioPacketsSent || 0) + 1
        
        // 每100个包记录一次日志，避免日志过多
        if (this.audioPacketsSent % 100 === 0) {
          this.addDebugLog('audio', 'info', `已发送${this.audioPacketsSent}个音频包`, {
            packetSize: audioBytes.length,
            format: 'pcm',
            sampleRate: 16000
          })
        }
        
      } catch (error) {
        console.error('发送实时音频数据失败:', error)
        this.addDebugLog('audio', 'error', '发送实时音频数据失败')
      }
    },

    /**
     * 检测语音活动 - 简化的VAD实现
     */
    detectVoiceActivity(audioLevel) {
      // 添加到VAD缓冲区
      this.vadBuffer = this.vadBuffer || []
      this.vadBuffer.push(audioLevel)
      if (this.vadBuffer.length > 10) {
        this.vadBuffer.shift()
      }

      // 计算平均音频级别
      const avgLevel = this.vadBuffer.reduce((sum, level) => sum + level, 0) / this.vadBuffer.length
      const threshold = this.vadSensitivity * 0.05

      // 判断语音活动
      if (avgLevel > threshold) {
        if (!this.isVoiceActive) {
          this.isVoiceActive = true
          this.addDebugLog('vad', 'info', '检测到语音开始', { level: avgLevel, threshold })
          this.addTranscriptMessage('', true, false)
        }
      } else if (avgLevel < threshold * 0.5) {
        if (this.isVoiceActive) {
          // 延迟触发语音结束事件
          if (this.voiceEndTimeout) {
            clearTimeout(this.voiceEndTimeout)
          }
          
          this.voiceEndTimeout = setTimeout(() => {
            if (this.isVoiceActive) {
              this.isVoiceActive = false
              this.addDebugLog('vad', 'info', '语音结束')
            }
          }, 500)
        }
      }
    },

    /**
     * 开始音频分析
     */
    startAudioAnalysis() {
      if (!this.analyser) return

      const analyze = () => {
        if (!this.isTestActive) return

        this.analyser.getByteFrequencyData(this.dataArray)
        
        requestAnimationFrame(analyze)
      }

      analyze()
    },

    /**
     * 停止音频分析
     */
    stopAudioAnalysis() {
      this.audioLevel = 0
      this.isVoiceActive = false
      
      if (this.voiceEndTimeout) {
        clearTimeout(this.voiceEndTimeout)
        this.voiceEndTimeout = null
      }
      
      // 停止媒体流
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
      
      // 断开音频处理器
      if (this.audioProcessor) {
        this.audioProcessor.disconnect()
        this.audioProcessor = null
      }
      
      // 关闭音频上下文
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close()
        this.audioContext = null
      }
    },

    /**
     * 更新VAD敏感度
     */
    updateVadSensitivity() {
      this.addDebugLog('vad', 'info', `VAD敏感度已更新: ${this.vadSensitivity}`)
    },

    /**
     * 添加转录消息
     */
    addTranscriptMessage(content, isPartial = false, isFinal = false, confidence = undefined) {
      const message = {
        id: Date.now() + Math.random(),
        content,
        isPartial,
        isFinal,
        confidence,
        timestamp: Date.now()
      }
      
      // 如果是部分消息，更新最后一条部分消息
      if (isPartial) {
        const lastIndex = this.transcriptMessages.length - 1
        const lastMessage = this.transcriptMessages[lastIndex]
        
        if (lastMessage && lastMessage.isPartial) {
          this.transcriptMessages.splice(lastIndex, 1, message)
        } else {
          this.transcriptMessages.push(message)
        }
      } else {
        this.transcriptMessages.push(message)
      }
      
      // 限制消息数量
      if (this.transcriptMessages.length > 50) {
        this.transcriptMessages = this.transcriptMessages.slice(-50)
      }
      
      // 自动滚动到底部
      this.$nextTick(() => {
        const content = this.$refs.transcriptContent
        if (content) {
          content.scrollTop = content.scrollHeight
        }
      })
    },

    /**
     * 更新部分转录
     */
    updatePartialTranscript(content, confidence) {
      this.addTranscriptMessage(content, true, false, confidence)
    },

    /**
     * 添加调试日志
     */
    addDebugLog(category, level, message, details = null) {
      const log = {
        id: Date.now() + Math.random(),
        category,
        level,
        message,
        details,
        timestamp: Date.now()
      }
      
      this.debugLogs.push(log)
      
      // 限制日志数量
      if (this.debugLogs.length > 100) {
        this.debugLogs = this.debugLogs.slice(-100)
      }
      
      // 自动滚动到底部
      this.$nextTick(() => {
        const content = this.$refs.debugContent
        if (content) {
          content.scrollTop = content.scrollHeight
        }
      })
    },

    /**
     * 开始波形动画
     */
    startWaveformAnimation() {
      const animate = () => {
        if (this.waveformCanvas && this.waveformContext) {
          this.drawWaveform()
        }
        this.animationFrame = requestAnimationFrame(animate)
      }
      animate()
    },

    /**
     * 绘制波形
     */
    drawWaveform() {
      const canvas = this.waveformCanvas
      const ctx = this.waveformContext
      const width = canvas.offsetWidth
      const height = canvas.offsetHeight
      
      // 清空画布
      ctx.clearRect(0, 0, width, height)
      
      if (this.analyser && this.isTestActive) {
        const timeData = this.getTimeDomainData()
        
        if (timeData) {
          // 绘制波形
          ctx.strokeStyle = this.isVoiceActive ? '#10b981' : '#6b7280'
          ctx.lineWidth = 2
          ctx.beginPath()
          
          const sliceWidth = width / timeData.length
          let x = 0
          
          for (let i = 0; i < timeData.length; i++) {
            const v = (timeData[i] - 128) / 128.0
            const y = (v * height / 2) + (height / 2)
            
            if (i === 0) {
              ctx.moveTo(x, y)
            } else {
              ctx.lineTo(x, y)
            }
            
            x += sliceWidth
          }
          
          ctx.stroke()
        }
      } else {
        // 绘制静态线
        ctx.strokeStyle = '#374151'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(0, height / 2)
        ctx.lineTo(width, height / 2)
        ctx.stroke()
      }
    },

    /**
     * 获取音频时域数据
     */
    getTimeDomainData() {
      if (!this.analyser) return null
      
      const timeData = new Uint8Array(this.analyser.fftSize)
      this.analyser.getByteTimeDomainData(timeData)
      return Array.from(timeData)
    },

    /**
     * 清空转录
     */
    clearTranscript() {
      this.transcriptMessages = []
      this.addDebugLog('system', 'info', '转录结果已清空')
    },

    /**
     * 清空日志
     */
    clearLogs() {
      this.debugLogs = []
    },

    /**
     * 导出转录结果
     */
    exportTranscript() {
      const content = this.transcriptMessages
        .filter(msg => msg.isFinal)
        .map(msg => `[${this.formatTime(msg.timestamp)}] ${msg.content}`)
        .join('\n')
      
      this.downloadFile('transcript.txt', content)
      this.addDebugLog('system', 'info', '转录结果已导出')
    },

    /**
     * 导出调试日志
     */
    exportLogs() {
      const content = this.debugLogs
        .map(log => `[${this.formatTime(log.timestamp)}] [${log.level.toUpperCase()}] [${log.category}] ${log.message}${log.details ? '\n' + JSON.stringify(log.details, null, 2) : ''}`)
        .join('\n')
      
      this.downloadFile('debug-logs.txt', content)
      this.addDebugLog('system', 'info', '调试日志已导出')
    },

    /**
     * 下载文件
     */
    downloadFile(filename, content) {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },

    /**
     * 格式化时间
     */
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      })
    },

    /**
     * 获取状态文本
     */
    getStatusText() {
      const statusMap = {
        'disconnected': '未连接',
        'connecting': '连接中...',
        'connected': '已连接',
        'active': '测试中'
      }
      return statusMap[this.connectionStatus] || '未知状态'
    },

    /**
     * 获取按钮文本
     */
    getButtonText() {
      if (this.isConnecting) return '连接中...'
      return this.isTestActive ? '停止测试' : '开始测试'
    },

    /**
     * 清理资源
     */
    cleanup() {
      // 停止动画
      if (this.animationFrame) {
        cancelAnimationFrame(this.animationFrame)
        this.animationFrame = null
      }
      
      // 停止音频分析
      this.stopAudioAnalysis()
      
      // 断开WebSocket
      this.disconnectWebSocket()
      
      // 重置状态
      this.isTestActive = false
      this.connectionStatus = 'disconnected'
      this.audioLevel = 0
      this.isVoiceActive = false
      this.audioPacketsSent = 0
    }
  }
}
</script>

<style scoped>
.vad-asr-test-panel {
  background: var(--bg-surface);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 90vh;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  flex-shrink: 0;
}

.header-left h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-id {
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: monospace;
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

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 控制区域 */
.control-section {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
}

.control-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator.disconnected {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.status-indicator.connecting {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.status-indicator.connected {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-indicator.active {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sensitivity-slider {
  width: 100px;
}

.slider-value {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
  min-width: 24px;
}

.test-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-btn.btn-success {
  background: #10b981;
  color: white;
}

.test-btn.btn-success:hover:not(:disabled) {
  background: #059669;
}

.test-btn.btn-danger {
  background: #ef4444;
  color: white;
}

.test-btn.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.test-btn.btn-connecting {
  background: #f59e0b;
  color: white;
}

.test-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-btn svg {
  width: 14px;
  height: 14px;
}

/* 音频可视化区域 */
.visualization-section {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
}

.visualizer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.visualizer-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.audio-stats {
  display: flex;
  gap: 16px;
}

.stat {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--bg-secondary);
}

.stat.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.waveform-container {
  height: 80px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.level-indicator {
  margin-bottom: 8px;
}

.level-bar {
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}

.level-fill {
  height: 100%;
  background: #6b7280;
  transition: width 0.1s ease;
  border-radius: 4px;
}

.level-fill.active {
  background: #10b981;
}

.level-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-tertiary);
}

/* 转录结果区域 */
.transcript-section {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.transcript-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.transcript-controls {
  display: flex;
  gap: 8px;
}

.transcript-content {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.empty-transcript {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-transcript svg {
  width: 32px;
  height: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-transcript p {
  margin: 0;
  font-size: 13px;
}

.transcript-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transcript-message {
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border-left: 3px solid transparent;
}

.transcript-message.partial {
  border-left-color: #f59e0b;
  background: rgba(251, 191, 36, 0.05);
}

.transcript-message.final {
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.transcript-message.low-confidence {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 11px;
}

.message-time {
  color: var(--text-tertiary);
  font-family: monospace;
}

.message-confidence {
  color: var(--text-secondary);
}

.message-type {
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
  text-transform: uppercase;
}

.message-type.partial {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.message-type.final {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.message-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.4;
}

/* 调试日志区域 */
.debug-section {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.debug-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.debug-controls {
  display: flex;
  gap: 8px;
}

.debug-content {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.empty-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.debug-logs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.debug-log {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-family: monospace;
  background: var(--bg-secondary);
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.debug-log.info {
  border-left: 3px solid #3b82f6;
}

.debug-log.success {
  border-left: 3px solid #10b981;
}

.debug-log.warning {
  border-left: 3px solid #f59e0b;
}

.debug-log.error {
  border-left: 3px solid #ef4444;
}

.log-time {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.log-level {
  color: var(--text-secondary);
  font-weight: 600;
  flex-shrink: 0;
}

.log-category {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.log-message {
  color: var(--text-primary);
  flex: 1;
}

.log-details {
  width: 100%;
  margin-top: 4px;
  padding: 8px;
  background: var(--bg-primary);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 11px;
  white-space: pre-wrap;
  overflow-x: auto;
}

/* 按钮样式 */
.btn-sm {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-sm:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* 动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .panel-content {
    padding: 16px;
    gap: 16px;
  }
  
  .control-row {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .control-group {
    align-items: stretch;
  }
  
  .slider-container {
    justify-content: space-between;
  }
  
  .sensitivity-slider {
    flex: 1;
  }
  
  .audio-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .transcript-content,
  .debug-content {
    max-height: 200px;
  }
}
</style>