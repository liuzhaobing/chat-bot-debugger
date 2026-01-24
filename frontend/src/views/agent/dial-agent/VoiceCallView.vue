<template>
  <div class="voice-call-view">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">AI客服中心</h1>
        <span class="page-subtitle">老板电器客服测试平台</span>
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
            :class="{ active: activePanel === 'scenario' }"
            @click="switchPanel('scenario')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7" rx="1"></rect>
              <rect x="14" y="3" width="7" height="7" rx="1"></rect>
              <rect x="14" y="14" width="7" height="7" rx="1"></rect>
              <rect x="3" y="14" width="7" height="7" rx="1"></rect>
            </svg>
            <span>场景测试</span>
          </button>
        </div>
      </div>
      
      <div class="toolbar-right">
        <!-- 紧凑版灵动岛样式的语音调试按钮 -->
        <button 
          class="voice-debug-btn" 
          @click="togglePhoneModal"
          :class="{ connected: isConnected }"
        >
          <div class="status-dot"></div>
          <strong v-if="!isConnected && !connecting">VoiceAgent</strong>
          <strong v-if="connecting">连线中...</strong>
          <strong v-if="isConnected && !isCallActive">已连接</strong>
          <strong v-if="isCallActive" class="call-duration">{{ formattedDuration }}</strong>
        </button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <ScenarioPanel 
        v-if="activePanel === 'scenario'" 
        :testing="scenarioTesting"
        @test-scenario="handleScenarioTest"
        @error="handleError"
      />
      <TranscriptPanel 
        v-if="activePanel === 'transcript'"
        :log-collapsed="logCollapsed"
        :transcripts="transcripts"
        :consoleLogs="consoleLogs"
        :showAILogs="showAILogs"
        @update:logCollapsed="handleLogCollapsedUpdate"
      />
    </div>

    <!-- 悬浮iPhone模态框 - 只在未通话时显示 -->
    <IPhoneModal 
      :visible="showPhoneModal && !isCallActive" 
      title="VoiceAgent"
      :allowBackgroundClose="!isCallActive"
      @close="closePhoneModal"
    >
      <PhoneInterface
        :isConnected="isConnected"
        :isCallActive="isCallActive"
        :callDuration="callDuration"
        :agentState="agentState"
        :userState="userState"
        :audioLevel="currentAudioLevel"
        :connecting="connecting"
        :config="config"
        @mute-toggle="handleMuteToggle"
        @transcript-toggle="handleTranscriptToggle"
        @hangup="handleHangup"
        @connect="connectToServer"
        @config-update="handleConfigUpdate"
        @config-save="handleConfigSave"
        @close-modal="closePhoneModal"
      />
    </IPhoneModal>

    <!-- 灵动岛 - 只在通话中显示，始终展开状态 -->
    <DynamicIsland
      :isVisible="isCallActive"
      :callDuration="callDuration"
      :isMuted="isMuted"
      :isSpeaking="agentState === 'speaking'"
      @mute-toggle="handleMuteToggle"
      @hangup="handleHangup"
      @click="handleDynamicIslandClick"
    />
  </div>
</template>

<script>
import PhoneInterface from '../../../components/dial-agent/PhoneInterface.vue'
import ScenarioPanel from '../../../components/dial-agent/ScenarioPanel.vue'
import TranscriptPanel from '../../../components/dial-agent/TranscriptPanel.vue'
import DynamicIsland from '../../../components/dial-agent/DynamicIsland.vue'
import IPhoneModal from '../../../components/common/IPhoneModal.vue'
import dialAgentService from '../../../services/dialAgentService.js'

export default {
  name: 'VoiceCallView',
  components: {
    PhoneInterface,
    ScenarioPanel,
    TranscriptPanel,
    DynamicIsland,
    IPhoneModal
  },
  data() {
    return {
      // 从服务获取的状态
      isConnected: false,
      connecting: false,
      isCallActive: false,
      callDuration: 0,
      agentState: '',
      userState: '',
      isMuted: false,
      currentAudioLevel: 0,
      
      // 字幕数据
      transcripts: [],
      
      // 控制台日志
      consoleLogs: [],
      
      // 面板控制
      activePanel: 'transcript', // 'scenario' | 'transcript'
      
      // iPhone模态框控制
      showPhoneModal: false,
      
      // 场景测试相关
      scenarioTesting: false,
      currentScenario: null,
      scenarioEventSource: null,
      
      // AI日志显示控制（独立于场景测试状态）
      showAILogs: false,
      
      // AI日志折叠状态控制
      logCollapsed: false
    }
  },
  computed: {
    connectionStatusText() {
      if (this.connecting) return '连线中...'
      if (!this.isConnected) return '未连接'
      if (this.isCallActive) return '通话中'
      return '已连接'
    },
    statusClass() {
      if (this.connecting) return 'connecting'
      if (!this.isConnected) return 'disconnected'
      if (this.isCallActive) return 'active'
      return 'connected'
    },
    config() {
      return dialAgentService.config
    },
    formattedDuration() {
      const minutes = Math.floor(this.callDuration / 60)
      const seconds = this.callDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  methods: {
    // 初始化服务监听器
    initServiceListeners() {
      dialAgentService.on('connecting', (connecting) => {
        this.connecting = connecting
      })
      
      dialAgentService.on('connected', () => {
        this.isConnected = true
        this.activePanel = 'transcript'
      })
      
      dialAgentService.on('disconnected', () => {
        this.isConnected = false
        this.isCallActive = false
      })
      
      dialAgentService.on('callStateChanged', (isActive) => {
        this.isCallActive = isActive
        // 打电话时自动折叠AI日志
        if (isActive) {
          this.logCollapsed = true
        }
      })
      
      dialAgentService.on('callDurationChanged', (duration) => {
        this.callDuration = duration
      })
      
      dialAgentService.on('agentStateChanged', (state) => {
        this.agentState = state
      })
      
      dialAgentService.on('userStateChanged', (state) => {
        this.userState = state
      })
      
      dialAgentService.on('muteChanged', (isMuted) => {
        this.isMuted = isMuted
      })
      
      dialAgentService.on('audioLevelChanged', (level) => {
        this.currentAudioLevel = level
      })
      
      dialAgentService.on('transcription', (data) => {
        this.handleTranscription(data)
      })
      
      dialAgentService.on('textOutput', (data) => {
        this.handleTextOutput(data)
      })
      
      dialAgentService.on('error', (error) => {
        alert(error)
        console.error(error)
      })
    },

    async connectToServer() {
      // 打电话前清空字幕和AI日志
      this.transcripts = []
      this.consoleLogs = []
      
      await dialAgentService.connect()
    },
    
    disconnectFromServer() {
      dialAgentService.disconnect()
    },
    
    handleMuteToggle(muted) {
      if (muted !== undefined) {
        // 从外部组件传入的值
        if (muted !== this.isMuted) {
          dialAgentService.toggleMute()
        }
      } else {
        // 内部切换
        dialAgentService.toggleMute()
      }
    },
    
    handleTranscriptToggle() {
      // 保留兼容性
    },
    
    handleHangup() {
      // 如果正在进行场景测试，先停止测试
      if (this.scenarioTesting) {
        this.stopScenarioTest()
      }
      this.disconnectFromServer()
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
    
    
    // 面板控制
    switchPanel(panel) {
      this.activePanel = panel
    },

    // iPhone模态框控制
    togglePhoneModal() {
      if (this.isCallActive) {
        // 通话中时，切换显示状态
        this.showPhoneModal = !this.showPhoneModal
      } else {
        // 未通话时，正常切换
        this.showPhoneModal = !this.showPhoneModal
      }
    },

    closePhoneModal() {
      if (this.isCallActive) {
        // 通话中关闭iPhone页面，不断开连接
        this.showPhoneModal = false
      } else {
        // 未通话时正常关闭
        this.showPhoneModal = false
      }
    },

    // 灵动岛点击处理
    handleDynamicIslandClick() {
      // 点击灵动岛空白区域时，切回iPhone手机页面
      this.showPhoneModal = true
    },

    // 右侧面板控制（保留兼容性）
    toggleSidebar() {
      // 不再需要，保留以防组件调用
    },
    
    handleConfigUpdate(newConfig) {
      // 实时更新配置（不保存）
      dialAgentService.updateConfig(newConfig)
    },
    
    handleConfigSave(newConfig) {
      dialAgentService.updateConfig(newConfig)
      console.log('Config saved:', newConfig)
    },

    // 场景测试相关方法
    async handleScenarioTest(scenario) {
      if (this.scenarioTesting) {
        console.log('场景测试已在进行中')
        return
      }

      this.currentScenario = scenario
      this.scenarioTesting = true
      this.showAILogs = true // 开始显示AI日志
      this.logCollapsed = false // 场景测试时自动展开AI日志
      this.switchPanel('transcript')
      
      // 清空之前的字幕和日志
      this.transcripts = []
      this.consoleLogs = []
      
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

      // 添加到控制台日志
      this.addConsoleLog(type, data)

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
          // if (data.audio_data) {
          //   this.playTTSAudio(data.audio_data, data.sample_rate || 24000)
          // }
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
      // 注意：不设置 showAILogs = false，保持AI日志显示

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
    },

    addConsoleLog(type, data) {
      // 添加控制台日志
      this.consoleLogs.push({
        type: type,
        data: data,
        timestamp: Date.now(),
        message: data.message || ''
      })
    },

    // 处理AI日志折叠状态更新
    handleLogCollapsedUpdate(collapsed) {
      this.logCollapsed = collapsed
    }
  },
  
  mounted() {
    // 初始化服务监听器
    this.initServiceListeners()
    
    // 同步当前状态
    const state = dialAgentService.getState()
    this.isConnected = state.isConnected
    this.connecting = state.connecting
    this.isCallActive = state.isCallActive
    this.callDuration = state.callDuration
    this.agentState = state.agentState
    this.userState = state.userState
    this.isMuted = state.isMuted
    this.currentAudioLevel = state.currentAudioLevel
  },
  
  beforeDestroy() {
    // 清理服务监听器
    dialAgentService.off('connecting')
    dialAgentService.off('connected')
    dialAgentService.off('disconnected')
    dialAgentService.off('callStateChanged')
    dialAgentService.off('callDurationChanged')
    dialAgentService.off('agentStateChanged')
    dialAgentService.off('userStateChanged')
    dialAgentService.off('muteChanged')
    dialAgentService.off('audioLevelChanged')
    dialAgentService.off('transcription')
    dialAgentService.off('textOutput')
    dialAgentService.off('error')
    
    this.stopScenarioTest()
  }
}
</script>

<style scoped>
.voice-call-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  position: relative;
}

/* 顶部工具栏 - 进一步紧凑化 */
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

.connection-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

/* 紧凑版灵动岛样式的打电话按钮 */
.voice-debug-btn {
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

.voice-debug-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.voice-debug-btn.connected {
  background: #000;
  border-color: rgba(16, 185, 129, 0.3);
  animation: connected-glow 2s infinite;
}

.voice-debug-btn.connected .status-dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

.voice-debug-btn.connected .call-duration {
  color: #10b981;
}

@keyframes connected-glow {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), 0 0 0 4px rgba(16, 185, 129, 0.2);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.voice-debug-btn .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  transition: all 0.3s ease;
}

.voice-debug-btn .call-duration {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: white;
  font-weight: 600;
}

.voice-debug-btn svg {
  width: 16px;
  height: 16px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg-secondary);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.connection-status.connected .status-dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

.connection-status.connecting .status-dot {
  background: #f59e0b;
  animation: pulse 0.8s infinite;
}

.connection-status.active .status-dot {
  background: #3b82f6;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 主内容区域 - 进一步紧凑化 */
.main-content {
  flex: 1;
  padding: 12px 20px;
  overflow: hidden;
}

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
  
  .modal-content {
    flex-direction: column;
    padding: 16px;
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
}
</style>
