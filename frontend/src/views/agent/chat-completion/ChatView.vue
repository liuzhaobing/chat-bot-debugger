<template>
  <div class="chat-view">
    <ChatSidebar />
    <div class="chat-main">
      <header class="chat-header">
        <div class="header-left-tools">
          <ModelSelector />
        </div>
        <div class="header-right-tools">
          <button class="settings-btn" @click="toggleSettings" title="聊天设置">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"></path></svg>
          </button>
        </div>
      </header>
      <div class="chat-content">
        <ChatArea @toggle-settings="toggleSettings" />
      </div>
    </div>
    <RightSidebar v-if="showSettings" @close="showSettings = false" />
    <SettingsModal v-if="showSettingsModal" @close="showSettingsModal = false" />
  </div>
</template>

<script>
import ChatSidebar from '../../../components/chat-completion/ChatSidebar.vue'
import ModelSelector from '../../../components/model-square/ModelSelector.vue'
import ChatArea from '../../../components/chat-completion/ChatArea.vue'
import RightSidebar from '../../../components/chat-completion/RightSidebar.vue'
import SettingsModal from '../../../components/chat-completion/SettingsModal.vue'

export default {
  name: 'ChatView',
  components: {
    ChatSidebar,
    ModelSelector,
    ChatArea,
    RightSidebar,
    SettingsModal
  },
  data() {
    return {
      showSettings: false,
      showSettingsModal: false
    }
  },
  methods: {
    toggleSettings() {
      this.showSettings = !this.showSettings
    }
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-secondary);
  min-width: 0;
}

.chat-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 100;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.header-left-tools {
  display: flex;
  align-items: center;
  width: auto;
}

.header-right-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.settings-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--text-tertiary);
}

.chat-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>