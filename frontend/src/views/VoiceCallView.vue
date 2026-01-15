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
          @mute-toggle="handleMuteToggle"
          @transcript-toggle="handleTranscriptToggle"
          @hangup="handleHangup"
          @connect="connectToServer"
          @toggle-sidebar="toggleSidebar"
          @open-settings="openSettings"
        />
      </div>

      <!-- 右侧：通话字幕 -->
      <div class="transcript-section" v-if="showTranscript">
        <CallTranscript
          :transcripts="transcripts"
        />
      </div>
    </div>

    <!-- 会话配置面板 -->
    <SessionConfig
      v-if="showConfig"
      :config="config"
      @close="showConfig = false"
      @save="handleConfigSave"
    />
  </div>
</template>

<script>
import PhoneInterface from '../components/PhoneInterface.vue'
import CallTranscript from '../components/CallTranscript.vue'
import SessionConfig from '../components/SessionConfig.vue'

export default {
  name: 'VoiceCallView',
  components: {
    PhoneInterface,
    CallTranscript,
    SessionConfig
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
      
      // 配置
      showConfig: false,
      config: {
        serverUrl: 'ws://118.31.127.156:8000/ws/sessions/start',
        userId: '17744270115',
        agentType: 'robam_workflow',
        configTemplate: 'ai_telephone',
        roomId: '',
        participantId: '',
        welcomeMessage: '你好，我是食神，欢迎致电老板电器。',
        systemPrompt: 'You are a helpful AI voice assistant.',
        allowInterruptions: true
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
      
      // 首先检查媒体权限
      const permissionCheck = await this.checkMediaPermissions()
      if (!permissionCheck.success) {
        alert(permissionCheck.error)
        console.error(permissionCheck.error)
        return
      }
      
      this.connecting = true
      
      // 重新连接时清空字幕
      this.transcripts = []
      
      try {
        // 生成房间ID和参与者ID
        this.config.roomId = `room_${Date.now()}`
        this.config.participantId = `sip_${this.config.userId}`
        
        // 连接 WebSocket
        this.websocket = new WebSocket(this.config.serverUrl)
        
        this.websocket.onopen = () => {
          this.sendInitMessage()
        }
        
        this.websocket.onmessage = (event) => {
          this.handleWebSocketMessage(JSON.parse(event.data))
        }
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error)
          alert('连接失败，请检查服务器地址')
          this.connecting = false
        }
        
        this.websocket.onclose = () => {
          this.isConnected = false
          this.isCallActive = false
          this.stopCallDuration()
          this.stopAudioCapture()
          
          // 只清空音频队列，保留字幕
          this.audioStreamQueue = []
          this.nextStartTime = 0
          this.isPlayingAudio = false
        }
        
      } catch (error) {
        console.error('Connection error:', error)
        alert('连接失败: ' + error.message)
        this.connecting = false
      }
    },
    
    sendInitMessage() {
      const initMessage = {
        type: 'init',
        config: {
          room_id: this.config.roomId,
          user_id: this.config.userId,
          participant_id: this.config.participantId,
          agent_type: this.config.agentType,
          config_template: this.config.configTemplate,
          welcome_message: this.config.welcomeMessage || '你好，我是食神，欢迎致电老板电器。',
          system_prompt: this.config.systemPrompt || 'You are a helpful AI voice assistant.',
          allow_interruptions: this.config.allowInterruptions ? 'true' : 'false'
        }
      }
      
      this.websocket.send(JSON.stringify(initMessage))
    },
    
    handleWebSocketMessage(message) {
      const { type, data, status } = message
      
      switch (type) {
        case 'init_ack':
          if (status === 'success') {
            // 初始化成功，静默处理
          } else {
            alert('初始化失败: ' + (message.message || '未知错误'))
            console.error('Init failed:', message)
            this.connecting = false
          }
          break
          
        case 'session_started':
          if (status === 'success') {
            this.sessionId = message.session_id
            this.isConnected = true
            this.connecting = false
            this.isCallActive = true
            this.startCallDuration()
            this.startAudioCapture()
          } else {
            alert('会话启动失败: ' + (message.message || '未知错误'))
            console.error('Session start failed:', message)
            this.connecting = false
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
      const { text, final: is_final, participant_id } = data
      
      if (is_final && text && text.trim()) {
        // 直接使用 participant_id: sip_phone 在左侧，phone 在右侧
        this.transcripts.push({
          participant_id: participant_id,
          text: text,
          is_final: true,
          timestamp: new Date().toISOString()
        })
      }
    },
    
    handleTextOutput(data) {
      const { text, participant_id } = data
      
      if (text && text.trim()) {
        // AI客服的回复，使用 participant_id
        this.transcripts.push({
          participant_id: participant_id || 'sip_phone',
          text: text,
          is_final: true,
          timestamp: new Date().toISOString()
        })
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
        const bufferSize = 4096
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
          
          // 只有当音量超过阈值时才发送
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
    
    toggleSidebar() {
      // 可以实现侧边栏功能
      console.log('Toggle sidebar')
    },
    
    openSettings() {
      this.showConfig = true
    },
    
    handleConfigSave(newConfig) {
      this.config = { ...newConfig }
      console.log('Config saved:', this.config)
    }
  },
  
  beforeDestroy() {
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

.transcript-section {
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
  
  .transcript-section {
    flex: 1;
    min-height: 400px;
  }
}
</style>
