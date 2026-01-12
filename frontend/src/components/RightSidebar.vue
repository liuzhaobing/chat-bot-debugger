<template>
  <div class="right-sidebar" :class="{ open: isRightSidebarOpen }">
    <div class="sidebar-header">
      <div class="header-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20v-6M9 20v-10M15 20V4M18 20V12M6 20v-4" /></svg>
        <span>模型设置</span>
      </div>
      <button class="close-btn" @click="closeSidebar" title="收起">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>

    <div class="content">
      <div class="param-section">
        <div class="section-label">系统提示词</div>
        <textarea 
          v-model="systemPrompt" 
          rows="6" 
          placeholder="输入系统提示词来设定 AI 的角色和行为..." 
          class="modern-textarea"
        />
      </div>

      <div class="param-section">
        <div class="section-label">推理参数</div>
        
        <div class="param-item">
          <div class="param-header">
            <span class="param-name">Temperature</span>
            <span class="param-value">{{ temperature }}</span>
          </div>
          <input type="range" v-model.number="temperature" min="0" max="2" step="0.01" class="modern-range" />
          <div class="range-labels">
            <span>精确</span>
            <span>创造性</span>
          </div>
        </div>

        <div class="param-item">
          <div class="param-header">
            <span class="param-name">Max Tokens</span>
            <span class="param-value">{{ maxTokens }}</span>
          </div>
          <input type="range" v-model.number="maxTokens" min="1" max="8192" step="1" class="modern-range" />
          <div class="range-labels">
            <span>短</span>
            <span>长</span>
          </div>
        </div>
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
    closeSidebar() {
      this.$store.commit('SET_RIGHT_SIDEBAR_OPEN', false)
    }
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
  box-shadow: -4px 0 15px rgba(0,0,0,0.08);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.right-sidebar:not(.open) {
  transform: translateX(100%);
}

.sidebar-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.content {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.param-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modern-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
}

.modern-textarea:focus {
  outline: none;
  border-color: var(--text-tertiary);
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-name {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.param-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-tertiary);
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: 4px;
}

.modern-range {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  background: var(--border-color);
  border-radius: 3px;
  outline: none;
}

.modern-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: var(--text-tertiary);
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.1s;
}

.modern-range::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
</style>
