/**
 * Dial Agent 独立服务
 * 处理与后端的WebSocket连接和音频处理
 */
class DialAgentService {
  constructor() {
    this.websocket = null
    this.isConnected = false
    this.connecting = false
    this.isCallActive = false
    
    // 音频相关
    this.audioContext = null
    this.mediaStream = null
    this.audioWorkletNode = null
    this.isMuted = false
    this.currentAudioLevel = 0
    
    // 流式音频播放系统
    this.audioStreamQueue = []
    this.isPlayingAudio = false
    this.audioStreamSource = null
    this.nextStartTime = 0
    
    // 通话状态
    this.callDuration = 0
    this.durationInterval = null
    this.sessionId = null
    
    // 状态管理
    this.agentState = ''
    this.userState = ''
    
    // 心跳机制
    this.heartbeatInterval = null
    this.heartbeatIntervalTime = 25000 // 25秒
    
    // 事件监听器
    this.eventListeners = {}
    
    // 默认配置
    this.config = {
      serverUrl: 'ws://118.31.127.156:8000/ws/sessions/start',
      userId: '17744270115',
      agentType: 'robam_workflow',
      configTemplate: 'ai_telephone',
      welcomeMessage: '你好，欢迎致电名气，有什么可以帮您？',
      allowInterruptions: true,
      inputSampleRate: 16000,
      inputChannels: 1,
      outputSampleRate: 24000,
      outputChannels: 1,
      backgroundMusic: {
        enabled: true,
        urls: ['https://roki-ai-ckb-prod.oss-accelerate.aliyuncs.com/static/test/office_background.wav'],
        volume: 0.05,
        loop: true,
        random: false
      },
      idleReminderConfig: {
        enabled: true,
        reminderContentType: 'llm',
        message: '请问您还在吗？',
        intervalSeconds: 20,
        maxRemindCount: 2
      },
      pluginConfigs: {
        sileroVad: {
          minSpeechDuration: 0.05,
          minSilenceDuration: 0.25,
          prefixPaddingDuration: 0.5,
          maxBufferedSpeech: 60.0,
          activationThreshold: 0.4,
          sampleRate: 16000,
          intermediateResultInterval: 320
        }
      }
    }
  }

  // 事件监听器管理
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = []
    }
    this.eventListeners[event].push(callback)
  }

  off(event, callback) {
    if (this.eventListeners[event]) {
      const index = this.eventListeners[event].indexOf(callback)
      if (index > -1) {
        this.eventListeners[event].splice(index, 1)
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(callback => callback(data))
    }
  }

  // 更新配置
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig }
  }

  // 获取当前状态
  getState() {
    return {
      isConnected: this.isConnected,
      connecting: this.connecting,
      isCallActive: this.isCallActive,
      callDuration: this.callDuration,
      agentState: this.agentState,
      userState: this.userState,
      isMuted: this.isMuted,
      currentAudioLevel: this.currentAudioLevel,
      sessionId: this.sessionId
    }
  }

  // 检查媒体权限
  async checkMediaPermissions() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        return { 
          success: false, 
          error: '您的浏览器不支持音频功能，请使用Chrome、Firefox或Edge浏览器，并确保使用HTTPS或localhost访问' 
        }
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      stream.getTracks().forEach(track => track.stop())
      return { success: true }
    } catch (error) {
      console.error('Media permission error:', error)
      
      let message = '无法访问麦克风'
      if (error.name === 'NotAllowedError') {
        message = '麦克风权限被拒绝，请在浏览器设置中允许访问麦克风'
      } else if (error.name === 'NotFoundError') {
        message = '未检测到麦克风设备'
      } else if (error.name === 'NotReadableError') {
        message = '麦克风正在被其他应用使用'
      } else if (error.name === 'NotSupportedError') {
        message = '浏览器不支持音频功能，请使用HTTPS或localhost访问'
      }
      
      return { success: false, error: message }
    }
  }

  // 连接到服务器
  async connect() {
    if (this.connecting || this.isConnected) return
    
    this.connecting = true
    this.emit('connecting', true)
    
    try {
      // 检查麦克风权限
      const permissionCheck = await this.checkMediaPermissions()
      if (!permissionCheck.success) {
        this.emit('error', permissionCheck.error)
        this.connecting = false
        this.emit('connecting', false)
        return
      }
      
      // 启动音频采集
      await this.startAudioCapture()
      
      // 连接 WebSocket
      this.websocket = new WebSocket(this.config.serverUrl)
      
      this.websocket.onopen = () => {
        console.log('WebSocket 已连接，发送初始化消息...')
        this.sendInitMessage()
      }
      
      this.websocket.onmessage = (event) => {
        this.handleWebSocketMessage(JSON.parse(event.data))
      }
      
      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', '连接失败，请检查服务器地址')
        this.connecting = false
        this.emit('connecting', false)
        this.stopAudioCapture()
      }
      
      this.websocket.onclose = () => {
        console.log('WebSocket 连接已关闭')
        this.isConnected = false
        this.isCallActive = false
        this.connecting = false
        this.stopCallDuration()
        this.stopAudioCapture()
        this.stopHeartbeat()
        
        this.emit('disconnected')
        this.emit('connecting', false)
        this.emit('callStateChanged', false)
        
        // 清空音频队列
        this.audioStreamQueue = []
        this.nextStartTime = 0
        this.isPlayingAudio = false
      }
      
    } catch (error) {
      console.error('Connection error:', error)
      this.emit('error', '连接失败: ' + error.message)
      this.connecting = false
      this.emit('connecting', false)
      this.stopAudioCapture()
    }
  }

  // 断开连接
  disconnect() {
    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }
    
    this.isConnected = false
    this.isCallActive = false
    this.stopCallDuration()
    this.stopAudioCapture()
    this.stopHeartbeat()
    
    this.emit('disconnected')
    this.emit('callStateChanged', false)
    
    // 清空音频队列
    this.audioStreamQueue = []
    this.nextStartTime = 0
    this.isPlayingAudio = false
  }

  // 切换静音
  toggleMute() {
    this.isMuted = !this.isMuted
    this.emit('muteChanged', this.isMuted)
    return this.isMuted
  }

  // 发送初始化消息
  sendInitMessage() {
    const sessionId = `DIAL${Date.now()}_myroki_test_com`
    const roomId = `room_${Date.now()}`
    const agentUserId = `sip_${this.config.userId}`
    
    const initMessage = {
      type: 'init',
      config: {
        room_id: roomId,
        session_id: sessionId,
        user_id: this.config.userId,
        agent_user_id: agentUserId,
        agent_type: this.config.agentType,
        config_template: this.config.configTemplate,
        input_sample_rate: this.config.inputSampleRate,
        input_channels: this.config.inputChannels,
        output_sample_rate: this.config.outputSampleRate,
        output_channels: this.config.outputChannels,
        welcome_message: this.config.welcomeMessage,
        allow_interruptions: this.config.allowInterruptions,
        background_music: {
          enabled: this.config.backgroundMusic.enabled,
          urls: this.config.backgroundMusic.urls,
          volume: this.config.backgroundMusic.volume,
          loop: this.config.backgroundMusic.loop,
          random: this.config.backgroundMusic.random
        },
        idle_reminder_config: {
          enabled: this.config.idleReminderConfig.enabled,
          reminder_content_type: this.config.idleReminderConfig.reminderContentType,
          message: this.config.idleReminderConfig.message,
          interval_seconds: this.config.idleReminderConfig.intervalSeconds,
          max_remind_count: this.config.idleReminderConfig.maxRemindCount
        },
        plugin_configs: {
          silero_vad: {
            min_speech_duration: this.config.pluginConfigs.sileroVad.minSpeechDuration,
            min_silence_duration: this.config.pluginConfigs.sileroVad.minSilenceDuration,
            prefix_padding_duration: this.config.pluginConfigs.sileroVad.prefixPaddingDuration,
            max_buffered_speech: this.config.pluginConfigs.sileroVad.maxBufferedSpeech,
            activation_threshold: this.config.pluginConfigs.sileroVad.activationThreshold,
            sample_rate: this.config.pluginConfigs.sileroVad.sampleRate,
            intermediate_result_interval: this.config.pluginConfigs.sileroVad.intermediateResultInterval
          }
        }
      }
    }
    
    this.websocket.send(JSON.stringify(initMessage))
  }

  // 处理WebSocket消息
  handleWebSocketMessage(message) {
    const { type, data, status } = message
    
    switch (type) {
      case 'init_ack':
        if (status === 'success') {
          console.log('初始化确认成功，等待会话启动...')
        } else {
          this.emit('error', '初始化失败: ' + (message.message || '未知错误'))
          this.connecting = false
          this.emit('connecting', false)
          this.stopAudioCapture()
        }
        break
        
      case 'session_started':
        if (status === 'success') {
          console.log('会话启动成功')
          this.sessionId = message.session_id
          this.isConnected = true
          this.connecting = false
          this.isCallActive = true
          this.startCallDuration()
          this.startHeartbeat()
          
          this.emit('connected')
          this.emit('connecting', false)
          this.emit('callStateChanged', true)
        } else {
          this.emit('error', '会话启动失败: ' + (message.message || '未知错误'))
          this.connecting = false
          this.emit('connecting', false)
          this.stopAudioCapture()
        }
        break
        
      case 'user_state_changed':
        this.userState = data.new_state || ''
        this.emit('userStateChanged', this.userState)
        break
        
      case 'agent_state_changed':
        this.agentState = data.new_state || ''
        this.emit('agentStateChanged', this.agentState)
        break
        
      case 'transcription':
        this.emit('transcription', data)
        break
        
      case 'text_output':
        this.emit('textOutput', data)
        break
        
      case 'audio_output':
        this.handleAudioOutput(data)
        break
        
      case 'error':
        console.error('Server error:', data)
        this.emit('error', '服务器错误: ' + (data.message || '未知错误'))
        break
        
      case 'heartbeat':
        // 心跳响应，静默处理
        break
        
      default:
        console.warn('Unknown message type:', type)
    }
  }

  // 处理音频输出
  handleAudioOutput(data) {
    const { audio_data, sample_rate } = data
    this.scheduleAudioChunk(audio_data, sample_rate || 24000)
  }

  // 调度音频块播放
  async scheduleAudioChunk(base64Audio, sampleRate) {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        this.nextStartTime = this.audioContext.currentTime
      }
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }
      
      // 解码音频 - 优化解码过程
      const binaryString = atob(base64Audio)
      const len = binaryString.length
      const bytes = new Uint8Array(len)
      
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      // 转换为Float32Array - 改进转换精度
      const int16Array = new Int16Array(bytes.buffer)
      const float32Array = new Float32Array(int16Array.length)
      
      for (let i = 0; i < int16Array.length; i++) {
        // 使用更精确的转换
        float32Array[i] = int16Array[i] / 32768.0
      }
      
      const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, sampleRate)
      audioBuffer.getChannelData(0).set(float32Array)
      
      const source = this.audioContext.createBufferSource()
      source.buffer = audioBuffer
      
      // 添加增益控制
      const gainNode = this.audioContext.createGain()
      gainNode.gain.value = 1.0
      
      source.connect(gainNode)
      gainNode.connect(this.audioContext.destination)
      
      // 改进时间调度 - 减少音频间隙
      const currentTime = this.audioContext.currentTime
      const bufferDuration = audioBuffer.duration
      
      // 如果nextStartTime太远或已过期，重置
      if (this.nextStartTime < currentTime || this.nextStartTime > currentTime + 0.5) {
        this.nextStartTime = currentTime + 0.01 // 小延迟避免点击声
      }
      
      source.start(this.nextStartTime)
      this.nextStartTime += bufferDuration
      
      // 清理管理
      this.audioStreamQueue.push(source)
      
      source.onended = () => {
        const index = this.audioStreamQueue.indexOf(source)
        if (index > -1) {
          this.audioStreamQueue.splice(index, 1)
        }
      }
      
      // 限制队列大小，防止内存泄漏
      if (this.audioStreamQueue.length > 50) {
        const oldSource = this.audioStreamQueue.shift()
        try {
          oldSource.stop()
        } catch (e) {
          // 忽略已停止的源
        }
      }
      
    } catch (error) {
      console.error('Error scheduling audio:', error)
    }
  }

  // 启动音频采集 - 完全模拟Python版本
  async startAudioCapture() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
      }
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }
      
      const source = this.audioContext.createMediaStreamSource(this.mediaStream)
      
      // Python版本：chunk_size = int(16000 * 10 / 1000) = 160 samples
      // 但Web Audio API需要2的幂次方，所以使用256 (16ms)
      const bufferSize = 256
      const processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1)
      
      processor.onaudioprocess = (e) => {
        if (this.isMuted || !this.isConnected) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        
        // 计算音频级别用于可视化
        let sum = 0
        for (let i = 0; i < inputData.length; i++) {
          sum += Math.abs(inputData[i])
        }
        const average = sum / inputData.length
        this.currentAudioLevel = Math.min(1, average * 10)
        this.emit('audioLevelChanged', this.currentAudioLevel)
        
        // 转换为16位PCM字节数据 - 完全模拟Python版本
        const pcmData = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]))
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        
        // 转换为字节数组 - 模拟Python的bytes类型
        const audioBytes = new Uint8Array(pcmData.buffer)
        
        // 模拟Python的回调：audio_callback(audio_data, True)
        // Python版本总是传递has_voice=True
        this.onAudioRecorded(audioBytes, true)
      }
      
      source.connect(processor)
      processor.connect(this.audioContext.destination)
      
      this.audioWorkletNode = processor
      
    } catch (error) {
      console.error('Error starting audio capture:', error)
      throw error
    }
  }

  // 完全模拟Python的音频录制回调
  onAudioRecorded(audioData, hasVoice) {
    // Python版本：if self.connected and has_voice:
    // Python版本总是传递has_voice=True，所以实际上总是发送
    if (this.isConnected && hasVoice) {
      // Python版本：将音频数据放入队列，由异步任务处理
      // JavaScript版本：直接发送（因为JavaScript是单线程的）
      this.sendAudioData(audioData)
    }
  }

  // 停止音频采集
  stopAudioCapture() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }
    
    if (this.audioWorkletNode) {
      this.audioWorkletNode.disconnect()
      this.audioWorkletNode = null
    }
    
    this.audioStreamQueue.forEach(source => {
      try {
        source.stop()
      } catch (e) {
        // 忽略错误
      }
    })
    
    this.audioStreamQueue = []
    this.nextStartTime = 0
    this.isPlayingAudio = false
  }

  // 发送音频数据 - 完全模拟Python版本
  sendAudioData(audioBytes) {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return
    
    // 转换为base64 - 与Python版本一致
    let binary = ''
    for (let i = 0; i < audioBytes.length; i++) {
      binary += String.fromCharCode(audioBytes[i])
    }
    const base64 = btoa(binary)
    
    // 消息格式与Python版本完全一致
    const message = {
      type: 'audio_input',
      timestamp: Math.floor(Date.now()), // Python: int(time.time() * 1000)
      data: {
        audio_data: base64,
        sample_rate: 16000, // self.recorder.sample_rate
        channels: 1,        // self.recorder.channels
        format: 'pcm',      // 与Python版本一致
        size: audioBytes.length // len(audio_data)
      }
    }
    
    try {
      this.websocket.send(JSON.stringify(message))
      // Python版本会更新统计信息，这里暂时注释
      // this.stats.messages_sent += 1
      // this.stats.audio_chunks_sent += 1
    } catch (error) {
      console.error('Failed to send audio:', error)
      // this.stats.errors += 1
    }
  }

  // 开始通话计时
  startCallDuration() {
    this.callDuration = 0
    this.durationInterval = setInterval(() => {
      this.callDuration++
      this.emit('callDurationChanged', this.callDuration)
    }, 1000)
  }

  // 停止通话计时
  stopCallDuration() {
    if (this.durationInterval) {
      clearInterval(this.durationInterval)
      this.durationInterval = null
    }
    this.callDuration = 0
  }

  // 启动心跳
  startHeartbeat() {
    this.stopHeartbeat()
    
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat()
    }, this.heartbeatIntervalTime)
  }

  // 停止心跳
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  // 发送心跳 - 完全模拟Python版本
  sendHeartbeat() {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      return
    }
    
    // 心跳消息格式与Python版本完全一致
    const heartbeatMessage = {
      type: 'heartbeat',
      timestamp: Date.now() / 1000, // Python: time.time()
      data: {
        client_time: Date.now() / 1000, // Python: time.time()
        session_id: this.sessionId
        // Python版本还包含client_stats，这里简化
      }
    }
    
    try {
      this.websocket.send(JSON.stringify(heartbeatMessage))
      console.debug('发送心跳消息')
    } catch (error) {
      console.error('发送心跳失败:', error)
    }
  }

  // 销毁服务
  destroy() {
    this.stopHeartbeat()
    this.disconnect()
    this.eventListeners = {}
  }
}

// 创建单例实例
const dialAgentService = new DialAgentService()

export default dialAgentService