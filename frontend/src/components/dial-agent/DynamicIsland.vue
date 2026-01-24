<template>
  <div v-if="isVisible" class="dynamic-island-container">
    <div class="dynamic-island expanded" @click="handleBackgroundClick">
      <!-- 展开状态 - 始终显示 -->
      <div class="island-expanded">
        <div class="call-info">
          <div class="call-status">
            <div class="status-dot active"></div>
            <span class="status-text">通话中</span>
          </div>
          <div class="call-duration-large">{{ formattedDuration }}</div>
        </div>
        
        <div class="call-controls">
          <button 
            class="control-btn" 
            :class="{ active: isMuted }"
            @click="toggleMute"
            @click.stop
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
            @click.stop
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.68-1.36-2.66-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
            </svg>
          </button>
        </div>

        <!-- 音频波动效果 -->
        <div class="audio-wave" v-if="isSpeaking">
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DynamicIsland',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    },
    callDuration: {
      type: Number,
      default: 0
    },
    isMuted: {
      type: Boolean,
      default: false
    },
    isSpeaking: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    formattedDuration() {
      const minutes = Math.floor(this.callDuration / 60)
      const seconds = this.callDuration % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
  },
  methods: {
    handleBackgroundClick() {
      // 点击空白区域时，发出事件通知父组件切回iPhone页面
      this.$emit('click')
    },
    toggleMute() {
      this.$emit('mute-toggle', !this.isMuted)
    },
    handleHangup() {
      this.$emit('hangup')
    }
  }
}
</script>

<style scoped>
.dynamic-island-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  animation: slideInFromTop 0.3s ease-out;
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

.dynamic-island {
  background: #000;
  border-radius: 20px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  min-width: 280px;
  position: relative;
}

.dynamic-island:hover {
  transform: scale(1.02);
}

/* 展开状态样式 */
.island-expanded {
  color: white;
  position: relative;
}

.call-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.call-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #10b981;
}

.call-duration-large {
  font-size: 16px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.call-controls {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.control-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.control-btn svg {
  width: 20px;
  height: 20px;
}

.control-btn.active {
  background: rgba(239, 68, 68, 0.8);
}

.control-btn.active:hover {
  background: rgba(239, 68, 68, 0.9);
}

.hangup-btn {
  background: rgba(239, 68, 68, 0.8);
}

.hangup-btn:hover {
  background: rgba(239, 68, 68, 0.9);
}

/* 音频波动效果 */
.audio-wave {
  position: absolute;
  top: 50%;
  right: 20px;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  height: 16px;
}

.wave-bar {
  width: 2px;
  background: #10b981;
  border-radius: 1px;
  animation: wave-animation 1s ease-in-out infinite;
}

.wave-bar:nth-child(1) {
  height: 8px;
  animation-delay: 0s;
}

.wave-bar:nth-child(2) {
  height: 12px;
  animation-delay: 0.1s;
}

.wave-bar:nth-child(3) {
  height: 6px;
  animation-delay: 0.2s;
}

@keyframes wave-animation {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.5);
  }
}
</style>