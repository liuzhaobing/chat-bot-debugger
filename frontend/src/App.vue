<template>
  <div id="app">
    <div class="layout">
      <Sidebar @open-settings="showSettings = true" />
      <main class="main-content">
        <header class="main-header">
          <div class="header-left-tools">
            <ModelSelector />
          </div>
          <button class="settings-gear-btn" @click="toggleRightSidebar" title="System Settings">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          </button>
        </header>
        <div class="content-view">
          <router-view />
        </div>
      </main>
      <RightSidebar />
      <SettingsModal v-if="showSettings" @close="showSettings = false" />
    </div>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue'
import ModelSelector from './components/ModelSelector.vue'
import SettingsModal from './components/SettingsModal.vue'
import RightSidebar from './components/RightSidebar.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    ModelSelector,
    SettingsModal,
    RightSidebar
  },
  data() {
    return {
      showSettings: false
    }
  },
  methods: {
    toggleRightSidebar() {
      this.$store.commit('SET_RIGHT_SIDEBAR_OPEN', !this.$store.state.isRightSidebarOpen)
    },
    newChat() {
      this.$store.dispatch('createNewChat')
    }
  },
  created() {
    this.$store.dispatch('fetchProviders')
    this.$store.dispatch('fetchConversations')
    // Initialize theme
    const theme = this.$store.state.theme
    document.documentElement.setAttribute('data-theme', theme)
  }
}
</script>

<style>

.layout {
  display: flex;
  height: 100vh;
  position: relative;
}

.main-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 100;
}

.header-left-tools {
    display: flex;
    align-items: center;
    width: auto;
    min-width: 40px;
}

.header-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.header-btn:hover {
    background-color: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--text-tertiary);
}

.content-view {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.settings-gear-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.settings-gear-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-primary);
  min-width: 0;
}
</style>
