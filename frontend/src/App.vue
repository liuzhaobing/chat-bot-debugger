<template>
  <div id="app">
    <div class="layout">
      <Sidebar @open-settings="showSettings = true" />
      <main class="main-content">
        <ModelSelector />
        <router-view />
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

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-primary);
  min-width: 0;
}
</style>
