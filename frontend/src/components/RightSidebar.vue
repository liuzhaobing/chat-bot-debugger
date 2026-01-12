<template>
  <div class="right-sidebar" :class="{ open: isRightSidebarOpen }">
    <div v-if="isRightSidebarOpen" class="content">
      <h3>System Prompt</h3>
      <textarea v-model="systemPrompt" rows="3" placeholder="System prompt..." />
      <div class="param-group">
        <label>Temperature
          <input type="number" v-model.number="temperature" min="0" max="2" step="0.01" />
        </label>
        <label>Max Tokens
          <input type="number" v-model.number="maxTokens" min="1" max="4096" step="1" />
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'RightSidebar',
  data() {
    return {
      systemPrompt: '',
      temperature: 0.7,
      maxTokens: 1024
    }
  },
  computed: {
      ...mapState(['isRightSidebarOpen'])
  },
  watch: {
    systemPrompt(val) {
      this.$store.commit('SET_SYSTEM_PROMPT', val)
    },
    temperature(val) {
      this.$store.commit('SET_TEMPERATURE', val)
    },
    maxTokens(val) {
      this.$store.commit('SET_MAX_TOKENS', val)
    }
  },
  mounted() {
    this.systemPrompt = this.$store.state.systemPrompt || ''
    this.temperature = this.$store.state.temperature || 0.7
    this.maxTokens = this.$store.state.maxTokens || 1024
  },
  methods: {
  }
}
</script>

<style scoped>
.right-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 340px;
  height: 100vh;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  box-shadow: -2px 0 8px rgba(0,0,0,0.04);
  transition: transform 0.2s;
  transform: translateX(0);
  z-index: 100;
  display: flex;
  flex-direction: column;
}
.right-sidebar:not(.open) {
  transform: translateX(100%);
}
.toggle-btn {
  position: absolute;
  left: -36px;
  top: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px 0 0 6px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
}
.content {
  padding: 24px 20px 20px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.param-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.param-group label {
  display: flex;
  flex-direction: column;
  font-size: 0.95rem;
  color: var(--text-secondary);
}
.param-group input[type="number"] {
  margin-top: 4px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-input);
  color: var(--text-primary);
  width: 100%;
}
textarea {
  width: 100%;
  min-height: 60px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-input);
  color: var(--text-primary);
  padding: 8px;
  font-size: 1rem;
  resize: vertical;
}
</style>
