<template>
  <div id="app">
    <div class="app-container">
      <MainSidebar />
      <div class="layout">
        <main class="main-content">
          <div class="content-view">
            <router-view />
          </div>
        </main>
        <GlobalToast />
        <GlobalConfirm />
      </div>
    </div>
  </div>
</template>

<script>
import MainSidebar from './views/layouts/MainSidebar.vue'
import GlobalToast from './components/common/GlobalToast.vue'
import GlobalConfirm from './components/common/GlobalConfirm.vue'

export default {
  name: 'App',
  components: {
    MainSidebar,
    GlobalToast,
    GlobalConfirm
  },
  methods: {
    newChat() {
      this.$store.dispatch('chatCompletion/createNewChat')
    }
  },
  created() {
    this.$store.dispatch('modelSquare/fetchProviders')
    this.$store.dispatch('chatCompletion/fetchConversations')
    // Initialize theme
    const theme = this.$store.state.theme
    document.documentElement.setAttribute('data-theme', theme)
  }
}
</script>

<style>
/* 全局设计变量 */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-surface: #ffffff;
  --bg-hover: #f1f5f9;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-tertiary: #94a3b8;
  --border-color: #e2e8f0;
  --accent-blue: #4f46e5;
  --accent-blue-hover: #4338ca;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

[data-theme='dark'] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-surface: #1e293b;
  --bg-hover: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --border-color: #334155;
  --accent-blue: #6366f1;
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout {
  display: flex;
  flex: 1;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-secondary);
  min-width: 0;
}

.content-view {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}


/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
