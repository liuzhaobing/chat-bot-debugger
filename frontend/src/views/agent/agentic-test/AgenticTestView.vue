<template>
  <div class="agentic-test-view">
    <div class="view-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <IOTConfigPanel />
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import IOTConfigPanel from '@/components/agentic-test/IOTConfigPanel.vue'

export default {
  name: 'AgenticTestView',
  components: {
    IOTConfigPanel
  },
  computed: {
    ...mapState('agenticTest', []),
    ...mapGetters('agenticTest', [])
  },
  mounted() {
    // 组件挂载后的初始化
  },
  beforeDestroy() {
    // 组件销毁前的清理
  },
  data() {
    return {}
  },
  methods: {
    ...mapActions('agenticTest', [])
  }
}
</script>

<style scoped>
.agentic-test-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

.view-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  min-height: 0;
}

.left-panel {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: calc(100vh - 48px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .view-content {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .view-content {
    padding: 12px;
  }
  
  .left-panel {
    max-width: 100%;
  }
}
</style>