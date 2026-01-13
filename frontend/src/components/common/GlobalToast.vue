<template>
  <transition-group name="toast-fade" tag="div" class="toast-container">
    <div 
      v-for="msg in messages" 
      :key="msg.id" 
      class="toast-item" 
      :class="msg.type"
    >
      <div class="toast-icon">
        <svg v-if="msg.type === 'success'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <svg v-else-if="msg.type === 'error'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      </div>
      <div class="toast-content">{{ msg.text }}</div>
    </div>
  </transition-group>
</template>

<script>
export default {
  name: 'GlobalToast',
  data() {
    return {
      messages: []
    }
  },
  methods: {
    add(text, type = 'info', duration = 3000) {
      const id = Date.now() + Math.random()
      this.messages.push({ id, text, type })
      
      setTimeout(() => {
        this.messages = this.messages.filter(m => m.id !== id)
      }, duration)
    }
  },
  mounted() {
    // 注册全局总线
    window.$message = {
      success: (text) => this.add(text, 'success'),
      error: (text) => this.add(text, 'error'),
      info: (text) => this.add(text, 'info')
    }
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast-item {
  pointer-events: auto;
  min-width: 300px;
  padding: 12px 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 12px;
  border-left: 4px solid #6366f1;
  animation: slide-down 0.3s ease-out;
}

.toast-item.success {
  border-left-color: #10b981;
}

.toast-item.error {
  border-left-color: #ef4444;
}

.toast-icon {
  flex-shrink: 0;
}

.success .toast-icon { color: #10b981; }
.error .toast-icon { color: #ef4444; }
.info .toast-icon { color: #6366f1; }

.toast-content {
  font-size: 0.9rem;
  font-weight: 500;
  color: #1e293b;
}

/* Animations */
.toast-fade-enter, .toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.toast-fade-leave-active {
  position: absolute;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
