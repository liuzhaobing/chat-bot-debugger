<template>
  <div v-if="visible" class="iphone-modal-overlay" @click="handleOverlayClick">
    <div class="iphone-modal" @click.stop>
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="closeModal">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="modal-content">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IPhoneModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '语音调试'
    },
    allowBackgroundClose: {
      type: Boolean,
      default: true
    }
  },
  methods: {
    closeModal() {
      this.$emit('close')
    },
    handleOverlayClick() {
      if (this.allowBackgroundClose) {
        this.closeModal()
      }
    }
  }
}
</script>

<style scoped>
/* iPhone模态框 - 完全透明背景，纯阴影效果 */
.iphone-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 100px;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
  pointer-events: none;
}

.iphone-modal {
  background: transparent;
  border-radius: 0;
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.25),
    0 12px 24px rgba(0, 0, 0, 0.15),
    0 6px 12px rgba(0, 0, 0, 0.1);
  overflow: visible;
  animation: slideInRight 0.3s ease;
  display: flex;
  flex-direction: column;
  pointer-events: auto;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.modal-header {
  display: none;
}

.modal-content {
  display: flex;
  gap: 0;
  padding: 0;
  overflow: visible;
  background: transparent;
}

@media (max-width: 1200px) {
  .iphone-modal-overlay {
    justify-content: center;
    padding-right: 0;
  }
  
  .modal-content {
    flex-direction: column;
    padding: 16px;
  }
}
</style>