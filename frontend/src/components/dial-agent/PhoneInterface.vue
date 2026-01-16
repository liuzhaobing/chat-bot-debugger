<template>
  <div class="phone-container">
    <div class="iphone-frame">
      <!-- 顶部状态栏 -->
      <div class="status-bar">
        <div class="status-left">
          <span class="time">{{ currentTime }}</span>
        </div>
        <div class="dynamic-island">
          <div class="island-content">
            <div class="island-icon camera"></div>
            <div class="island-icon speaker"></div>
          </div>
        </div>
        <div class="status-right">
          <!-- 信号强度 -->
          <svg class="status-icon signal" viewBox="0 0 20 12" fill="currentColor">
            <rect x="0" y="8" width="3" height="4" rx="0.5"/>
            <rect x="5" y="5" width="3" height="7" rx="0.5"/>
            <rect x="10" y="2" width="3" height="10" rx="0.5"/>
            <rect x="15" y="0" width="3" height="12" rx="0.5"/>
          </svg>
          <!-- 电池 -->
          <div class="battery-icon">
            <div class="battery-body">
              <div class="battery-level" :style="{ width: batteryLevel + '%' }"></div>
            </div>
            <div class="battery-tip"></div>
          </div>
        </div>
      </div>

      <!-- 通话内容区域 -->
      <div class="call-content">
        <!-- 未连接状态 -->
        <div v-if="!isConnected" class="pre-call-screen">
          <!-- 顶部按钮组 -->
          <div class="top-actions">
            <button 
              class="panel-btn" 
              :class="{ active: activePanel === 'scenario' }"
              @click="switchPanel('scenario')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7" rx="1"></rect>
                <rect x="14" y="3" width="7" height="7" rx="1"></rect>
                <rect x="14" y="14" width="7" height="7" rx="1"></rect>
                <rect x="3" y="14" width="7" height="7" rx="1"></rect>
              </svg>
            </button>
            <button 
              class="panel-btn" 
              :class="{ active: activePanel === 'transcript' }"
              @click="switchPanel('transcript')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button 
              class="panel-btn" 
              :class="{ active: activePanel === 'config' }"
              @click="switchPanel('config')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
              </svg>
            </button>
          </div>

          <div class="call-animation">
            <div class="avatar-circle large">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
          </div>
          
          <div class="call-info">
            <h2>AI客服中心</h2>
            <p class="service-name">老板电器客服中心</p>
            <p class="call-hint-text">点击下方按钮开始通话</p>
          </div>
        </div>

        <!-- 已连接/通话中状态 -->
        <div v-else class="in-call-screen">
          <!-- 连接状态指示 -->
          <div class="connection-status" :class="statusClass">
            <div class="status-dot"></div>
            <span>{{ connectionStatusText }}</span>
          </div>

          <!-- 通话动画 -->
          <div class="call-animation">
            <div class="avatar-circle" :class="{ active: isCallActive, speaking: isSpeaking, listening: isListening, thinking: isThinking }">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </div>
            <!-- 音频波动效果 - Agent说话 -->
            <div class="audio-waves" v-if="isSpeaking">
              <div class="wave"></div>
              <div class="wave"></div>
              <div class="wave"></div>
              <div class="wave"></div>
            </div>
            <div class="pulse-ring" v-if="isCallActive && !isSpeaking && !isUserSpeaking"></div>
            <div class="pulse-ring pulse-ring-2" v-if="isCallActive && !isSpeaking && !isUserSpeaking"></div>
          </div>

          <!-- 状态提示 -->
          <div class="call-hint">
            <p class="hint-text">{{ agentStateText }}</p>
          </div>

          <!-- 通话时长 -->
          <div class="call-duration">
            <span>{{ formattedDuration }}</span>
          </div>

          <!-- 用户说话状态指示器 -->
          <div class="user-speaking-indicator" v-if="isUserSpeaking">
            <div class="user-audio-dots">
              <div class="dot" :style="{ height: userAudioLevels[0] + 'px' }"></div>
              <div class="dot" :style="{ height: userAudioLevels[1] + 'px' }"></div>
              <div class="dot" :style="{ height: userAudioLevels[2] + 'px' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部控制按钮 -->
      <div class="call-controls">
        <button 
          v-if="!isConnected"
          class="control-btn call-btn"
          @click="handleConnect"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/>
          </svg>
        </button>

        <template v-else>
          <button 
            class="control-btn" 
            :class="{ active: isMuted }"
            @click="toggleMute"
          >
            <svg v-if="!isMuted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="1" y1="1" x2="23" y2="23"></line>
              <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path>
              <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
          </button>

          <button 
            class="control-btn hangup-btn"
            @click="handleHangup"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.68-1.36-2.66-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
            </svg>
          </button>

          <button 
            class="control-btn"
            :class="{ active: showTranscript }"
            @click="toggleTranscript"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </button>
        </template>
      </div>

      <!-- 底部指示器 -->
      <div class="home-indicator"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PhoneInterface',
  props: {
    isConnected: {
      type: Boolean,
      default: false
    },
    isCallActive: {
      type: Boolean,
      default: false
    },
    callDuration: {
      type: Number,
      default: 0
    },
    agentState: {
      type: String,
      default: ''
    },
    userState: {
      type: String,
      default: ''
    },
    audioLevel: {
      type: Number,
      default: 0
    },
    activePanel: {
      type: String,
      default: 'transcript'
    }
  },
  data() {
    return {
      currentTime: '',
      isMuted: false,
      showTranscript: true,
      timeInterval: null,
      batteryLevel: 85,
      userAudioLevels: [4, 4, 4], // 用户音频波动高度（像素）
      audioAnimationInterval: null
    }
  },
  computed: {
    connectionStatusText() {
      if (!this.isConnected) return '未连接'
      if (this.isCallActive) return '通话中'
      return '已连接'
    },
    statusClass() {
      if (!this.isConnected) return 'disconnected'
      if (this.isCallActive) return 'active'
      return 'connected'
    },
    agentStateText() {
      if (this.isThinking) return '客服正在思考...'
      if (this.isSpeaking) return '客服正在说话...'
      if (this.isListening) return '客服正在听...'
      return '你可以开始说话'
    },
    userStateText() {
      if (this.isUserSpeaking) return '你正在说话'
      return ''
    },
    isSpeaking() {
      return this.agentState === 'speaking'
    },
    isListening() {
      return this.agentState === 'listening'
    },
    isThinking() {
      return this.agentState === 'thinking'
    },
    isUserSpeaking() {
      return this.userState === 'speaking'
    },
    formattedDuration() {
      const minutes = Math.floor(this.callDuration / 60)
      const seconds = this.callDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  methods: {
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })
    },
    toggleMute() {
      this.isMuted = !this.isMuted
      this.$emit('mute-toggle', this.isMuted)
    },
    toggleTranscript() {
      this.showTranscript = !this.showTranscript
      this.$emit('transcript-toggle', this.showTranscript)
    },
    handleHangup() {
      this.$emit('hangup')
    },
    handleConnect() {
      this.$emit('connect')
    },
    toggleSidebar() {
      this.$emit('toggle-sidebar')
    },
    switchPanel(panel) {
      this.$emit('switch-panel', panel)
    },
    selectScenario() {
      this.$emit('switch-panel', 'scenario')
    },
    openSettings() {
      this.$emit('switch-panel', 'config')
    },
    animateUserAudio() {
      // 根据音频级别生成波动效果
      const baseHeight = 8
      const maxHeight = 40
      const audioFactor = this.audioLevel || Math.random()
      
      this.userAudioLevels = [
        baseHeight + Math.random() * maxHeight * audioFactor,
        baseHeight + Math.random() * maxHeight * audioFactor * 1.2,
        baseHeight + Math.random() * maxHeight * audioFactor * 0.9
      ]
    },
    startAudioAnimation() {
      if (this.audioAnimationInterval) return
      this.audioAnimationInterval = setInterval(() => {
        if (this.isUserSpeaking) {
          this.animateUserAudio()
        }
      }, 100) // 每100ms更新一次
    },
    stopAudioAnimation() {
      if (this.audioAnimationInterval) {
        clearInterval(this.audioAnimationInterval)
        this.audioAnimationInterval = null
      }
    }
  },
  watch: {
    isUserSpeaking(newVal) {
      if (newVal) {
        this.startAudioAnimation()
      } else {
        this.stopAudioAnimation()
      }
    }
  },
  mounted() {
    this.updateTime()
    this.timeInterval = setInterval(this.updateTime, 1000)
    this.startAudioAnimation()
  },
  beforeDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval)
    }
    this.stopAudioAnimation()
  }
}
</script>

<style scoped>
.phone-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  height: 100%;
}

.iphone-frame {
  width: 375px;
  height: 812px;
  background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
  border-radius: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 状态栏 */
.status-bar {
  height: 54px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-direction: row;
  padding: 0 20px;
  padding-top: 14px;
  color: #1e293b;
  font-size: 15px;
  font-weight: 600;
  position: relative;
  z-index: 10;
}

.status-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 60px;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 5px;
  flex: 1;
  justify-content: flex-end;
  min-width: 60px;
}

.status-icon.signal {
  width: 18px;
  height: 11px;
}

/* 动态岛 */
.dynamic-island {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 126px;
  height: 37px;
  background: #000;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.island-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.island-icon {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.island-icon.camera {
  background: radial-gradient(circle, #1e3a8a 30%, #1e293b 70%);
}

.island-icon.speaker {
  width: 60px;
  height: 6px;
  border-radius: 3px;
  background: #1e293b;
}

/* 电池图标 */
.battery-icon {
  display: flex;
  align-items: center;
  gap: 1px;
}

.battery-body {
  width: 24px;
  height: 11px;
  border: 1.5px solid #1e293b;
  border-radius: 3px;
  padding: 1.5px;
  position: relative;
  background: #1e293b;
}

.battery-level {
  height: 100%;
  background: #1e293b;
  border-radius: 1.5px;
  transition: width 0.3s ease;
}

.battery-tip {
  width: 2px;
  height: 5px;
  background: #1e293b;
  border-radius: 0 2px 2px 0;
}

/* 通话内容区域 */
.call-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
}

/* 未连接状态屏幕 */
.pre-call-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 40px;
  position: relative;
}

.top-actions {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.icon-btn-minimal {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #1e293b;
}

.icon-btn-minimal:hover {
  background: rgba(30, 41, 59, 0.1);
}

.icon-btn-minimal svg {
  width: 20px;
  height: 20px;
}

.panel-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #1e293b;
}

.panel-btn:hover {
  background: rgba(255, 255, 255, 0.6);
  transform: translateY(-2px);
}

.panel-btn.active {
  background: rgba(255, 255, 255, 0.9);
  color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.panel-btn svg {
  width: 20px;
  height: 20px;
}

.call-info {
  text-align: center;
}

.call-info h2 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 600;
  color: #1e293b;
}

.service-name {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #64748b;
  font-weight: 400;
}

.call-hint-text {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

.avatar-circle.large {
  width: 200px;
  height: 200px;
}

.avatar-circle.large svg {
  width: 90px;
  height: 90px;
}

/* 通话中状态屏幕 */
.in-call-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  position: relative;
}

.connection-status {
  position: absolute;
  top: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
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

.connection-status.active .status-dot {
  background: #3b82f6;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 通话动画 */
.call-animation {
  position: relative;
  margin: 40px 0;
}

.avatar-circle {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
  transition: all 0.3s ease;
}

.avatar-circle svg {
  width: 80px;
  height: 80px;
  color: #1e293b;
}

.avatar-circle.active {
  background: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.avatar-circle.speaking {
  background: rgba(16, 185, 129, 0.3);
  animation: speaking-pulse 1s infinite;
}

.avatar-circle.listening {
  background: rgba(59, 130, 246, 0.3);
}

.avatar-circle.thinking {
  background: rgba(251, 191, 36, 0.3);
  animation: thinking-pulse 1.5s infinite;
}

@keyframes speaking-pulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
  }
}

@keyframes thinking-pulse {
  0%, 100% { 
    opacity: 1;
  }
  50% { 
    opacity: 0.6;
  }
}

/* 音频波动效果 */
.audio-waves {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 6px;
  align-items: center;
  z-index: 3;
}

.wave {
  width: 4px;
  background: #10b981;
  border-radius: 2px;
  animation: wave-animation 1s ease-in-out infinite;
}

.wave:nth-child(1) {
  height: 20px;
  animation-delay: 0s;
}

.wave:nth-child(2) {
  height: 30px;
  animation-delay: 0.1s;
}

.wave:nth-child(3) {
  height: 25px;
  animation-delay: 0.2s;
}

.wave:nth-child(4) {
  height: 35px;
  animation-delay: 0.3s;
}

@keyframes wave-animation {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.5);
  }
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 2px solid rgba(59, 130, 246, 0.5);
  animation: pulse-ring 2s infinite;
}

.pulse-ring-2 {
  animation-delay: 1s;
}

@keyframes pulse-ring {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

/* 通话提示 */
.call-hint {
  text-align: center;
  margin-top: 20px;
}

.hint-text {
  font-size: 15px;
  color: #1e293b;
  font-weight: 500;
  margin: 0;
}

/* 用户说话指示器 */
.user-speaking-indicator {
  position: absolute;
  bottom: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-audio-dots {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 50px;
}

.user-audio-dots .dot {
  width: 8px;
  min-height: 8px;
  background: #1e293b;
  border-radius: 4px;
  transition: height 0.08s ease-out;
}

/* 通话时长 */
.call-duration {
  position: absolute;
  bottom: 140px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  padding: 8px 20px;
  border-radius: 20px;
}

/* 底部控制按钮 */
.call-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  padding: 30px 20px;
  margin-bottom: 20px;
}

.control-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #1e293b;
}

.control-btn svg {
  width: 28px;
  height: 28px;
}

.control-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.control-btn.active {
  background: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.call-btn {
  background: #10b981;
  color: white;
  width: 72px;
  height: 72px;
}

.call-btn:hover {
  background: #059669;
  transform: scale(1.05);
}

.hangup-btn {
  background: #ef4444;
  color: white;
  width: 72px;
  height: 72px;
}

.hangup-btn:hover:not(:disabled) {
  background: #dc2626;
  transform: scale(1.05);
}

/* 底部指示器 */
.home-indicator {
  width: 134px;
  height: 5px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 100px;
  margin: 0 auto 8px;
}
</style>
