<template>
  <div class="voice-call-view">
    <div class="call-layout">
      <!-- 左侧：iPhone 通话界面 -->
      <div class="phone-section">
        <PhoneInterface
          :isConnected="isConnected"
          :isCallActive="isCallActive"
          :callDuration="callDuration"
          :agentState="agentState"
          :userState="userState"
          :audioLevel="currentAudioLevel"
          :activePanel="activePanel"
          :connecting="connecting"
          @mute-toggle="handleMuteToggle"
          @transcript-toggle="handleTranscriptToggle"
          @hangup="handleHangup"
          @connect="connectToServer"
          @toggle-sidebar="toggleSidebar"
          @switch-panel="switchPanel"
        />
      </div>

      <!-- 右侧：动态面板 -->
      <div class="panel-section" v-if="showPanel">
        <ScenarioPanel 
          v-if="activePanel === 'scenario'" 
          :testing="scenarioTesting"
          @test-scenario="handleScenarioTest"
          @error="handleError"
        />
        <TranscriptPanel v-if="activePanel === 'transcript'" :transcripts="transcripts" />
        <ConfigPanel 
          v-if="activePanel === 'config'" 
          :config="config"
          @update="handleConfigUpdate"
          @save="handleConfigSave"
        />
      </div>
    </div>
  </div>
</template>

<script>
import PhoneInterface from '../../../components/dial-agent/PhoneInterface.vue'
import ScenarioPanel from '../../../components/dial-agent/ScenarioPanel.vue'
import TranscriptPanel from '../../../components/dial-agent/TranscriptPanel.vue'
import ConfigPanel from '../../../components/dial-agent/ConfigPanel.vue'

export default {
  name: 'VoiceCallView',
  components: {
    PhoneInterface,
    ScenarioPanel,
    TranscriptPanel,
    ConfigPanel
  },
  data() {
    return {
      // WebSocket 连接
      websocket: null,
      isConnected: false,
      connecting: false,
      isCallActive: false,
      
      // 音频相关
      audioContext: null,
      mediaStream: null,
      audioWorkletNode: null,
      isMuted: false,
      showTranscript: true,
      currentAudioLevel: 0,
      
      // 流式音频播放系统
      audioStreamQueue: [], // 音频数据流队列
      isPlayingAudio: false,
      audioStreamSource: null, // 当前音频流源
      nextStartTime: 0, // 下一个音频块的开始时间
      
      // 通话状态
      callDuration: 0,
      durationInterval: null,
      sessionId: null,
      
      // 状态管理
      agentState: '',
      userState: '',
      
      // 字幕数据
      transcripts: [],
      
      // 心跳机制
      heartbeatInterval: null,
      heartbeatIntervalTime: 25000, // 25秒
      
      // 右侧面板控制
      showPanel: true,
      activePanel: 'transcript', // 'scenario' | 'transcript' | 'config'
      
      // 场景测试相关
      scenarioTesting: false,
      currentScenario: null,
      scenarioEventSource: null,
      
      // 配置
      config: {
        serverUrl: 'ws://118.31.127.156:8000/ws/sessions/start',
        userId: '17744270115',
        agentType: 'robam_workflow',
        configTemplate: 'ai_telephone',
        welcomeMessage: '你好，欢迎致电名气，有什么可以帮您？',
        allowInterruptions: true,
        // 音频配置
        inputSampleRate: 16000,
        inputChannels: 1,
        outputSampleRate: 24000,
        outputChannels: 1,
        // 背景音乐配置
        backgroundMusic: {
          enabled: true,
          urls: ['https://roki-ai-ckb-prod.oss-accelerate.aliyuncs.com/static/test/office_background.wav'],
          volume: 0.05,
          loop: true,
          random: false
        },
        // 静默提醒配置
        idleReminderConfig: {
          enabled: true,
          reminderContentType: 'llm',
          message: '请问您还在吗？',
          intervalSeconds: 20,
          maxRemindCount: 2
        },
        // 插件配置
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
  },
  methods: {
    async checkMediaPermissions() {
      try {
        // 检查是否支持 getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          return { 
            success: false, 
            error: '您的浏览器不支持音频功能，请使用Chrome、Firefox或Edge浏览器，并确保使用HTTPS或localhost访问' 
          }
        }
        
        // 检查麦克风和扬声器权限
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } 
        })
        
        // 权限获取成功，停止测试流
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
    },
    
    async connectToServer() {
      if (this.connecting || this.isConnected) return
      
      this.connecting = true
      
      try {
        // 步骤1: 首先检查并请求麦克风权限
        console.log('步骤1: 检查麦克风权限...')
        const permissionCheck = await this.checkMediaPermissions()
        if (!permissionCheck.success) {
          alert(permissionCheck.error)
          console.error(permissionCheck.error)
          this.connecting = false
          return
        }
        
        // 步骤2: 启动音频采集
        console.log('步骤2: 启动音频采集...')
        await this.startAudioCapture()
        console.log('音频采集已就绪')
        
        // 步骤3: 连接 WebSocket
        console.log('步骤3: 连接 WebSocket...')
        this.websocket = new WebSocket(this.config.serverUrl)
        
        // 重新连接时清空字幕
        this.transcripts = []
        
        this.websocket.onopen = () => {
          console.log('WebSocket 已连接，发送初始化消息...')
          this.sendInitMessage()
          this.activePanel = 'transcript'
        }
        
        this.websocket.onmessage = (event) => {
          this.handleWebSocketMessage(JSON.parse(event.data))
        }
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error)
          alert('连接失败，请检查服务器地址')
          this.connecting = false
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
          
          // 只清空音频队列，保留字幕
          this.audioStreamQueue = []
          this.nextStartTime = 0
          this.isPlayingAudio = false
        }
        
      } catch (error) {
        console.error('Connection error:', error)
        alert('连接失败: ' + error.message)
        this.connecting = false
        this.stopAudioCapture()
      }
    },
    
    sendInitMessage() {
      // 生成会话ID和房间ID
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
          
          // 音频配置
          input_sample_rate: this.config.inputSampleRate,
          input_channels: this.config.inputChannels,
          output_sample_rate: this.config.outputSampleRate,
          output_channels: this.config.outputChannels,
          
          // 消息配置
          welcome_message: this.config.welcomeMessage,
          allow_interruptions: this.config.allowInterruptions,
          
          // 背景音乐配置
          background_music: {
            enabled: this.config.backgroundMusic.enabled,
            urls: this.config.backgroundMusic.urls,
            volume: this.config.backgroundMusic.volume,
            loop: this.config.backgroundMusic.loop,
            random: this.config.backgroundMusic.random
          },
          
          // 静默提醒配置
          idle_reminder_config: {
            enabled: this.config.idleReminderConfig.enabled,
            reminder_content_type: this.config.idleReminderConfig.reminderContentType,
            message: this.config.idleReminderConfig.message,
            interval_seconds: this.config.idleReminderConfig.intervalSeconds,
            max_remind_count: this.config.idleReminderConfig.maxRemindCount
          },
          
          // 插件配置
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
      console.log('init', initMessage)
      this.websocket.send(JSON.stringify(initMessage))
    },
    
    handleWebSocketMessage(message) {
      const { type, data, status } = message
      
      switch (type) {
        case 'init_ack':
          if (status === 'success') {
            console.log('初始化确认成功，等待会话启动...')
          } else {
            alert('初始化失败: ' + (message.message || '未知错误'))
            console.error('Init failed:', message)
            this.connecting = false
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
            // 音频采集已经在 connectToServer 中启动了，这里不需要再启动
            // 启动心跳
            this.startHeartbeat()
          } else {
            alert('会话启动失败: ' + (message.message || '未知错误'))
            console.error('Session start failed:', message)
            this.connecting = false
            this.stopAudioCapture()
          }
          break
          
        case 'user_state_changed':
          this.userState = data.new_state || ''
          break
          
        case 'agent_state_changed':
          this.agentState = data.new_state || ''
          break
          
        case 'transcription':
          this.handleTranscription(data)
          break
          
        case 'text_output':
          this.handleTextOutput(data)
          break
          
        case 'audio_output':
          this.handleAudioOutput(data)
          break
          
        case 'error':
          console.error('Server error:', data)
          alert('服务器错误: ' + (data.message || '未知错误'))
          break
          
        case 'heartbeat':
          // 心跳响应，静默处理
          break
          
        default:
          console.warn('Unknown message type:', type)
      }
    },
    
    handleTranscription(data) {
      console.log(data)
      const { text, final: is_final, participant_id, segment_id } = data
      
      // 查找是否已存在相同 segment_id 和 participant_id 的字幕
      const existingIndex = this.transcripts.findIndex(
        item => item.segment_id === segment_id && item.participant_id === participant_id
      )
      
      if (existingIndex !== -1) {
        // 更新已存在的字幕 - 直接替换文本
        this.$set(this.transcripts, existingIndex, {
          ...this.transcripts[existingIndex],
          text: text || this.transcripts[existingIndex].text, // 如果text为空，保留原文本
          is_final: is_final,
          updateTime: Date.now() // 更新时间戳用于排序
        })
      } else {
        // 添加新字幕（只有当text不为空时才添加）
        if (text && text.trim()) {
          this.transcripts.push({
            participant_id: participant_id,
            segment_id: segment_id,
            text: text,
            is_final: is_final,
            timestamp: new Date().toISOString(),
            createTime: Date.now(), // 创建时间戳用于排序
            updateTime: Date.now()
          })
        }
      }
    },
    
    handleTextOutput(data) {
      const { text, participant_id, segment_id } = data
      
      // 查找是否已存在相同 segment_id 和 participant_id 的字幕
      const existingIndex = this.transcripts.findIndex(
        item => item.segment_id === segment_id && item.participant_id === participant_id
      )
      
      if (existingIndex !== -1) {
        // 更新已存在的字幕 - 直接替换文本
        this.$set(this.transcripts, existingIndex, {
          ...this.transcripts[existingIndex],
          text: text || this.transcripts[existingIndex].text, // 如果text为空，保留原文本
          is_final: true,
          updateTime: Date.now() // 更新时间戳用于排序
        })
      } else {
        // 添加新字幕（只有当text不为空时才添加）
        if (text && text.trim()) {
          this.transcripts.push({
            participant_id: participant_id || 'sip_phone',
            segment_id: segment_id,
            text: text,
            is_final: true,
            timestamp: new Date().toISOString(),
            createTime: Date.now(), // 创建时间戳用于排序
            updateTime: Date.now()
          })
        }
      }
    },
    
    handleAudioOutput(data) {
      const { audio_data, sample_rate } = data
      
      // 立即解码并调度播放
      this.scheduleAudioChunk(audio_data, sample_rate || 24000)
    },
    
    async scheduleAudioChunk(base64Audio, sampleRate) {
      try {
        // 创建音频上下文（只创建一次）
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
          this.nextStartTime = this.audioContext.currentTime
        }
        
        // 确保音频上下文已恢复
        if (this.audioContext.state === 'suspended') {
          await this.audioContext.resume()
        }
        
        // 快速解码
        const binaryString = atob(base64Audio)
        const len = binaryString.length
        const bytes = new Uint8Array(len)
        
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }
        
        // 转换为 Float32Array
        const int16Array = new Int16Array(bytes.buffer)
        const float32Array = new Float32Array(int16Array.length)
        const scale = 1.0 / 32768.0
        
        for (let i = 0; i < int16Array.length; i++) {
          float32Array[i] = int16Array[i] * scale
        }
        
        // 创建 AudioBuffer
        const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, sampleRate)
        audioBuffer.getChannelData(0).set(float32Array)
        
        // 创建音频源并调度播放
        const source = this.audioContext.createBufferSource()
        source.buffer = audioBuffer
        
        // 添加增益节点
        const gainNode = this.audioContext.createGain()
        gainNode.gain.value = 1.0
        
        source.connect(gainNode)
        gainNode.connect(this.audioContext.destination)
        
        // 计算播放时间 - 关键：使用精确的时间调度
        const currentTime = this.audioContext.currentTime
        const bufferDuration = audioBuffer.duration
        
        // 如果 nextStartTime 已经过去，重置为当前时间
        if (this.nextStartTime < currentTime) {
          this.nextStartTime = currentTime
        }
        
        // 调度播放
        source.start(this.nextStartTime)
        
        // 更新下一个音频块的开始时间
        this.nextStartTime += bufferDuration
        
        // 保存引用以便清理
        this.audioStreamQueue.push(source)
        
        // 清理已播放的源
        source.onended = () => {
          const index = this.audioStreamQueue.indexOf(source)
          if (index > -1) {
            this.audioStreamQueue.splice(index, 1)
          }
        }
        
      } catch (error) {
        console.error('Error scheduling audio:', error)
      }
    },
    
    async startAudioCapture() {
      try {
        // 请求麦克风权限
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
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
        }
        
        // 确保音频上下文已恢复
        if (this.audioContext.state === 'suspended') {
          await this.audioContext.resume()
        }
        
        // 创建音频源
        const source = this.audioContext.createMediaStreamSource(this.mediaStream)
        
        // 创建 ScriptProcessor 用于捕获音频数据
        // 使用较小的 bufferSize 以降低延迟，但仍需要是 256 的倍数
        // 256 samples = 16ms @ 16kHz，接近 Python 的 10ms
        const bufferSize = 256
        const processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1)
        
        processor.onaudioprocess = (e) => {
          if (this.isMuted || !this.isConnected) return
          
          const inputData = e.inputBuffer.getChannelData(0)
          
          // 优化的音量检测
          let sum = 0
          const len = inputData.length
          for (let i = 0; i < len; i++) {
            sum += Math.abs(inputData[i])
          }
          const average = sum / len
          
          // 更新音频级别用于可视化
          this.currentAudioLevel = Math.min(1, average * 10)
          
          // 只有当音量超过阈值时才发送（与 Python 的 VAD 逻辑一致）
          if (average > 0.01) {
            // 优化的 PCM 转换
            const pcmData = new Int16Array(len)
            for (let i = 0; i < len; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]))
              pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
            }
            
            // 发送音频数据
            this.sendAudioData(pcmData)
          }
        }
        
        source.connect(processor)
        processor.connect(this.audioContext.destination)
        
        this.audioWorkletNode = processor
        
      } catch (error) {
        console.error('Error starting audio capture:', error)
        alert('无法访问麦克风: ' + error.message)
        throw error
      }
    },
    
    stopAudioCapture() {
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
      
      if (this.audioWorkletNode) {
        this.audioWorkletNode.disconnect()
        this.audioWorkletNode = null
      }
      
      // 停止所有已调度的音频
      this.audioStreamQueue.forEach(source => {
        try {
          source.stop()
        } catch (e) {
          // 忽略错误
        }
      })
      
      // 清空队列
      this.audioStreamQueue = []
      this.nextStartTime = 0
      this.isPlayingAudio = false
    },
    
    sendAudioData(pcmData) {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return
      
      // 转换为 base64
      const bytes = new Uint8Array(pcmData.buffer)
      let binary = ''
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i])
      }
      const base64 = btoa(binary)
      
      const message = {
        type: 'audio_input',
        timestamp: Date.now(),
        data: {
          audio_data: base64,
          sample_rate: 16000,
          channels: 1,
          format: 'pcm',
          size: bytes.length
        }
      }
      
      this.websocket.send(JSON.stringify(message))
    },
    
    disconnectFromServer() {
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
      
      this.isConnected = false
      this.isCallActive = false
      this.stopCallDuration()
      this.stopAudioCapture()
      this.stopHeartbeat()
      
      // 只清空音频队列，保留字幕
      this.audioStreamQueue = []
      this.nextStartTime = 0
      this.isPlayingAudio = false
    },
    
    handleMuteToggle(muted) {
      this.isMuted = muted
    },
    
    handleTranscriptToggle(show) {
      this.showTranscript = show
    },
    
    handleHangup() {
      // 如果正在进行场景测试，先停止测试
      if (this.scenarioTesting) {
        this.stopScenarioTest()
      }
      this.disconnectFromServer()
    },
    
    startCallDuration() {
      this.callDuration = 0
      this.durationInterval = setInterval(() => {
        this.callDuration++
      }, 1000)
    },
    
    stopCallDuration() {
      if (this.durationInterval) {
        clearInterval(this.durationInterval)
        this.durationInterval = null
      }
      this.callDuration = 0
    },
    
    // 心跳机制
    startHeartbeat() {
      // 清除已有的心跳
      this.stopHeartbeat()
      
      // 启动新的心跳定时器
      this.heartbeatInterval = setInterval(() => {
        this.sendHeartbeat()
      }, this.heartbeatIntervalTime)
      
      console.log('Heartbeat started')
    },
    
    stopHeartbeat() {
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval)
        this.heartbeatInterval = null
        console.log('Heartbeat stopped')
      }
    },
    
    sendHeartbeat() {
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        return
      }
      
      const heartbeatMessage = {
        type: 'heartbeat',
        timestamp: Date.now(),
        data: {
          client_time: Date.now(),
          session_id: this.sessionId
        }
      }
      
      try {
        this.websocket.send(JSON.stringify(heartbeatMessage))
        console.log('Heartbeat sent')
      } catch (error) {
        console.error('Failed to send heartbeat:', error)
      }
    },
    
    // 右侧面板控制
    toggleSidebar() {
      this.showPanel = !this.showPanel
    },
    
    switchPanel(panel) {
      this.activePanel = panel
      this.showPanel = true
    },
    
    handleConfigUpdate(newConfig) {
      // 实时更新配置（不保存）
      this.config = { ...newConfig }
    },
    
    handleConfigSave(newConfig) {
      this.config = { ...newConfig }
      console.log('Config saved:', this.config)
    },

    // 场景测试相关方法
    async handleScenarioTest(scenario) {
      if (this.scenarioTesting) {
        console.log('场景测试已在进行中')
        return
      }

      this.currentScenario = scenario
      this.scenarioTesting = true
      
      // 清空之前的字幕
      this.transcripts = []
      
      try {
        // 调用后端SSE接口开始场景测试
        const response = await fetch('/api/dial/scenario-test/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            scenario_id: scenario.id,
            app_id: '37ccee2a148f46199061c955fa70f9b7'
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        // 处理SSE流
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let reading = true

        while (reading) {
          const { done, value } = await reader.read()
          if (done) {
            reading = false
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          
          // 保留最后一个可能不完整的行
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                this.stopScenarioTest()
                return
              }

              try {
                const eventData = JSON.parse(data)
                this.handleScenarioTestEvent(eventData)
              } catch (e) {
                console.error('解析SSE数据失败:', e, 'data:', data)
              }
            }
          }
        }
      } catch (error) {
        console.error('场景测试失败:', error)
        this.handleError('场景测试启动失败: ' + error.message)
        this.scenarioTesting = false
      }
    },

    handleScenarioTestEvent(eventData) {
      const { type, data } = eventData

      switch (type) {
        case 'status':
          console.log('场景测试状态:', data.message)
          break

        case 'ai_user_query':
          // AI用户生成的查询
          this.transcripts.push({
            participant_id: 'ai_user',
            segment_id: `ai_user_${Date.now()}`,
            text: data.query,
            is_final: true,
            timestamp: new Date().toISOString(),
            createTime: Date.now(),
            updateTime: Date.now()
          })
          console.log('场景测试状态:', data.query)
          break

        case 'tts_audio':
          // TTS生成的音频，播放音频
          if (data.audio_data) {
            this.playTTSAudio(data.audio_data, data.sample_rate || 24000)
          }
          break

        case 'dial_response':
          // 电话客服的回复
          this.transcripts.push({
            participant_id: 'sip_phone',
            segment_id: `sip_phone_${Date.now()}`,
            text: data.response,
            is_final: true,
            timestamp: new Date().toISOString(),
            createTime: Date.now(),
            updateTime: Date.now()
          })
          break

        case 'judger_result':
          // 判断器结果
          console.log('判断器结果:', data)
          if (data.should_continue === false) {
            console.log('场景测试完成，原因:', data.reason)
            this.stopScenarioTest()
          }
          break

        case 'error':
          console.error('场景测试错误:', data.message)
          this.handleError('场景测试错误: ' + data.message)
          this.stopScenarioTest()
          break

        case 'completed':
          console.log('场景测试完成')
          this.addSystemMessage('场景测试已完成')
          this.stopScenarioTest()
          break

        default:
          console.log('未知事件类型:', type, data)
      }
    },

    async playTTSAudio(base64Audio, sampleRate) {
      try {
        // 创建音频上下文（如果还没有）
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        }

        // 确保音频上下文已恢复
        if (this.audioContext.state === 'suspended') {
          await this.audioContext.resume()
        }

        // 解码base64音频数据
        const binaryString = atob(base64Audio)
        const len = binaryString.length
        const bytes = new Uint8Array(len)
        
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }

        // 转换为Float32Array
        const int16Array = new Int16Array(bytes.buffer)
        const float32Array = new Float32Array(int16Array.length)
        const scale = 1.0 / 32768.0
        
        for (let i = 0; i < int16Array.length; i++) {
          float32Array[i] = int16Array[i] * scale
        }

        // 创建AudioBuffer
        const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, sampleRate)
        audioBuffer.getChannelData(0).set(float32Array)

        // 播放音频
        const source = this.audioContext.createBufferSource()
        source.buffer = audioBuffer
        source.connect(this.audioContext.destination)
        source.start()

      } catch (error) {
        console.error('播放TTS音频失败:', error)
      }
    },

    async stopScenarioTest() {
      if (!this.scenarioTesting) return

      this.scenarioTesting = false
      this.currentScenario = null

      try {
        // 调用后端接口停止场景测试
        await fetch('/api/dial/scenario-test/stop/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        })
      } catch (error) {
        console.error('停止场景测试失败:', error)
      }
    },

    handleError(message) {
      console.error(message)
      // 添加系统消息到字幕中
      this.addSystemMessage(`错误: ${message}`)
    },

    addSystemMessage(message) {
      // 添加系统消息到字幕显示
      this.transcripts.push({
        participant_id: 'system',
        segment_id: `system_${Date.now()}`,
        text: message,
        is_final: true,
        timestamp: new Date().toISOString(),
        createTime: Date.now(),
        updateTime: Date.now()
      })
    }
  },
  
  beforeDestroy() {
    this.stopHeartbeat()
    this.stopScenarioTest()
    this.disconnectFromServer()
  }
}
</script>

<style scoped>
.voice-call-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  position: relative;
}

.call-layout {
  flex: 1;
  display: flex;
  gap: 24px;
  padding: 24px;
  overflow: hidden;
}

.phone-section {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

@media (max-width: 1200px) {
  .call-layout {
    flex-direction: column;
  }
  
  .phone-section {
    flex: 0 0 auto;
  }
  
  .panel-section {
    flex: 1;
    min-height: 400px;
  }
}
</style>
