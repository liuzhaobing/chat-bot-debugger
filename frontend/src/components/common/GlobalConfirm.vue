<template>
  <transition name="confirm-fade">
    <div v-if="visible" class="confirm-overlay" @click.self="cancel">
      <div class="confirm-card">
        <div class="confirm-header">
          <div class="confirm-icon" :class="type">
             <svg v-if="type === 'warning'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
             <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <h3 class="confirm-title">{{ title }}</h3>
        </div>
        <div class="confirm-body">
          <p>{{ message }}</p>
        </div>
        <div class="confirm-footer">
          <button class="btn-cancel" @click="cancel">{{ cancelText }}</button>
          <button class="btn-confirm" :class="type" @click="confirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'GlobalConfirm',
  data() {
    return {
      visible: false,
      title: '确认提交',
      message: '',
      type: 'warning',
      confirmText: '确定',
      cancelText: '取消',
      resolve: null,
      reject: null
    }
  },
  methods: {
    show(options) {
      this.title = options.title || '确认提示'
      this.message = options.message || ''
      this.type = options.type || 'warning'
      this.confirmText = options.confirmText || '确定'
      this.cancelText = options.cancelText || '取消'
      this.visible = true
      
      return new Promise((resolve, reject) => {
        this.resolve = resolve
        this.reject = reject
      })
    },
    confirm() {
      this.visible = false
      this.resolve(true)
    },
    cancel() {
      this.visible = false
      this.resolve(false)
    }
  },
  mounted() {
    window.$confirm = (options) => this.show(typeof options === 'string' ? { message: options } : options)
  }
}
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-card {
  background: #ffffff;
  width: 400px;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 24px;
  display: flex;
  flex-direction: column;
  animation: modal-pop 0.2s ease-out;
}

.confirm-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.confirm-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-icon.warning {
  background: #fffbeb;
  color: #f59e0b;
}

.confirm-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
}

.confirm-body {
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 24px;
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 8px 20px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-confirm {
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-confirm.warning {
  background: #6366f1;
}

.btn-confirm.danger {
  background: #ef4444;
}

.btn-confirm:hover {
  filter: brightness(0.9);
}

.confirm-fade-enter-active, .confirm-fade-leave-active {
  transition: opacity 0.2s;
}
.confirm-fade-enter, .confirm-fade-leave-to {
  opacity: 0;
}

@keyframes modal-pop {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
