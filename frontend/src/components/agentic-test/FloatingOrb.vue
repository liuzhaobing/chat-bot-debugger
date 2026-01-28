<template>
  <div class="floating-orb-container">
    <!-- 小球状态 -->
    <div 
      v-if="!isExpanded" 
      class="floating-orb"
      :class="{ 
        'is-active': isActive,
        'is-connecting': isConnecting,
        'has-audio': hasAudioActivity
      }"
      @click="handleOrbClick"
    >
      <div class="orb-inner">
        <div class="orb-glow"></div>
        <div class="orb-core">
          <svg v-if="!isConnecting" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
        </div>
        
        <!-- 音频波动效果 -->
        <div v-if="hasAudioActivity" class="audio-waves">
          <div class="wave" v-for="i in 4" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
        </div>
      </div>
    </div>

    <!-- 展开状态 - 灵动岛效果 -->
    <div 
      v-if="isExpanded" 
      class="dynamic-island"
      :class="{ 
        'is-active': isActive,
        'has-audio': hasAudioActivity
      }"
      @click="handleIslandClick"
    >
      <div class="island-content">
        <!-- 左侧：状态信息 -->
        <div class="island-left">
          <div class="status-indicator" :class="statusClass">
            <div class="status-dot"></div>
            <span class="status-text">{{ statusText }}</span>
          </div>
          <div v-if="isActive && sessionDuration > 0" class="session-duration">
            {{ formattedDuration }}
          </div>
        </div>

        <!-- 中间：音频可视化 -->
        <div v-if="hasAudioActivity" class="island-center">
          <div class="audio-visualization">
            <div class="viz-bar" v-for="i in 3" :key="i" :style="{ height: audioLevels[i-1] + 'px' }"></div>
          </div>
        </div>

        <!-- 右侧：控制按钮 -->
        <div class="island-right">
          <button 
            v-if="isActive"
            class="island-btn"
            :class="{ active: isMuted }"
            @click.stop="toggleMute"
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
            class="island-btn stop-btn"
            @click.stop="handleStop"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FloatingOrb',
  props: {
    isActive: {
      type: Boolean,
      default: false
    },
    isConnecting: {
      type: Boolean,
      default: false
    },
    hasAudioActivity: {
      type: Boolean,
      default: false
    },
    sessionDuration: {
      type: Number,
      default: 0
    },
    isMuted: {
      type: Boolean,
      default: false
    },
    connectionStatus: {
      type: String,
      default: 'disconnected' // 'disconnected' | 'connecting' | 'connected' | 'active'
    },
    audioLevel: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      isExpanded: false,
      audioLevels: [4, 4, 4], // 音频可视化高度
      audioAnimationInterval: null
    }
  },
  computed: {
    statusClass() {
      return this.connectionStatus
    },
    statusText() {
      const statusMap = {
        'disconnected': '未连接',
        'connecting': '连接中...',
        'connected': '已连接',
        'active': '会话中'
      }
      return statusMap[this.connectionStatus] || '未知状态'
    },
    formattedDuration() {
      const minutes = Math.floor(this.sessionDuration / 60)
      const seconds = this.sessionDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  watch: {
    hasAudioActivity(newVal) {
      if (newVal) {
        this.startAudioAnimation()
      } else {
        this.stopAudioAnimation()
      }
    },
    isActive(newVal) {
      if (newVal && !this.isExpanded) {
        this.expandOrb()
      } else if (!newVal && this.isExpanded) {
        this.collapseOrb()
      }
    }
  },
  methods: {
    handleOrbClick() {
      if (this.isConnecting) return
      
      if (!this.isActive) {
        this.$emit('start-session')
        this.expandOrb()
      } else {
        this.expandOrb()
      }
    },
    
    handleIslandClick() {
      // 点击灵动岛主体区域，可以用来显示详细信息或切换到主界面
      this.$emit('show-details')
    },
    
    expandOrb() {
      this.isExpanded = true
    },
    
    collapseOrb() {
      this.isExpanded = false
    },
    
    toggleMute() {
      this.$emit('toggle-mute', !this.isMuted)
    },
    
    handleStop() {
      this.$emit('stop-session')
      this.collapseOrb()
    },
    
    startAudioAnimation() {
      if (this.audioAnimationInterval) return
      
      this.audioAnimationInterval = setInterval(() => {
        if (this.hasAudioActivity) {
          this.updateAudioLevels()
        }
      }, 100)
    },
    
    stopAudioAnimation() {
      if (this.audioAnimationInterval) {
        clearInterval(this.audioAnimationInterval)
        this.audioAnimationInterval = null
      }
      this.audioLevels = [4, 4, 4]
    },
    
    updateAudioLevels() {
      const baseHeight = 4
      const maxHeight = 20
      const audioFactor = this.audioLevel || Math.random() * 0.5 + 0.3
      
      // 生成三个不同的波动高度
      this.audioLevels = [
        Math.max(baseHeight, baseHeight + maxHeight * audioFactor * (0.8 + Math.random() * 0.4)),
        Math.max(baseHeight, baseHeight + maxHeight * audioFactor * (0.9 + Math.random() * 0.2)),
        Math.max(baseHeight, baseHeight + maxHeight * audioFactor * (0.7 + Math.random() * 0.6))
      ]
    }
  },
  beforeDestroy() {
    this.stopAudioAnimation()
  }
}
</script>

<style scoped>
.floating-orb-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
}

/* 小球状态 */
.floating-orb {
  width: 60px;
  height: 60px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: float 3s ease-in-out infinite;
}

.floating-orb:hover {
  transform: scale(1.1) translateY(-2px);
}

.orb-inner {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
}

.orb-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(147, 51, 234, 0.3) 0%, transparent 70%);
  transition: all 0.3s ease;
}

.floating-orb.is-active .orb-glow {
  background: radial-gradient(circle, rgba(16, 185, 129, 0.4) 0%, transparent 70%);
  animation: pulse-glow 2s ease-in-out infinite;
}

.floating-orb.is-connecting .orb-glow {
  background: radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, transparent 70%);
  animation: pulse-glow 1s ease-in-out infinite;
}

.floating-orb.has-audio .orb-glow {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.5) 0%, transparent 70%);
  animation: audio-pulse 0.5s ease-in-out infinite;
}

.orb-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.floating-orb.is-active .orb-core {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.floating-orb.is-connecting .orb-core {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.orb-core svg {
  width: 24px;
  height: 24px;
}

/* 音频波动效果 */
.audio-waves {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 3px;
  z-index: 1;
}

.wave {
  width: 3px;
  height: 8px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  animation: wave-animation 1s ease-in-out infinite;
}

/* 灵动岛状态 */
.dynamic-island {
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 25px;
  padding: 12px 20px;
  min-width: 280px;
  height: 50px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideInFromTop 0.3s ease-out;
}

.dynamic-island:hover {
  transform: scale(1.02);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}

.island-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  color: white;
}

.island-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  flex: 1;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  transition: all 0.2s ease;
}

.status-indicator.connecting .status-dot {
  background: #f59e0b;
  animation: pulse 1s infinite;
}

.status-indicator.connected .status-dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

.status-indicator.active .status-dot {
  background: #3b82f6;
  animation: pulse 1.5s infinite;
}

.status-text {
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.session-duration {
  font-size: 13px;
  font-weight: 600;
  color: white;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.island-center {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 12px;
}

.audio-visualization {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 16px;
}

.viz-bar {
  width: 2px;
  min-height: 4px;
  background: #3b82f6;
  border-radius: 1px;
  transition: height 0.1s ease-out;
}

.island-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.island-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.island-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.island-btn svg {
  width: 14px;
  height: 14px;
}

.island-btn.active {
  background: rgba(239, 68, 68, 0.8);
}

.island-btn.active:hover {
  background: rgba(239, 68, 68, 0.9);
}

.stop-btn {
  background: rgba(239, 68, 68, 0.8);
}

.stop-btn:hover {
  background: rgba(239, 68, 68, 0.9);
}

/* 动画 */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-6px);
  }
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

@keyframes audio-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.2);
  }
}

@keyframes wave-animation {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(2);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .floating-orb-container {
    top: 15px;
    right: 15px;
  }
  
  .floating-orb {
    width: 50px;
    height: 50px;
  }
  
  .orb-core {
    width: 42px;
    height: 42px;
  }
  
  .orb-core svg {
    width: 20px;
    height: 20px;
  }
  
  .dynamic-island {
    min-width: 240px;
    height: 45px;
    padding: 10px 16px;
  }
  
  .status-text {
    font-size: 10px;
  }
  
  .session-duration {
    font-size: 12px;
  }
  
  .island-btn {
    width: 24px;
    height: 24px;
  }
  
  .island-btn svg {
    width: 12px;
    height: 12px;
  }
}
</style>