<template>
  <div class="app-detail-wrapper">
    <!-- 根据应用类型动态加载配置组件 -->
    <component 
      :is="currentConfigComponent" 
      :app-id="appId"
      v-if="currentConfigComponent"
    />
    <div v-else-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else class="error-state">
      <p>暂不支持该应用类型的配置</p>
      <button @click="$router.push('/apps')">返回应用广场</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Agent1ConfigComponent from '../../../components/app-configs/Agent1ConfigComponent.vue'

export default {
  name: 'AppDetailView',
  components: {
    Agent1ConfigComponent
  },
  data() {
    return {
      appId: null,
      appTypeCode: null,
      loading: true
    }
  },
  computed: {
    currentConfigComponent() {
      // 根据应用类型代码返回对应的配置组件
      const componentMap = {
        'agent_1_0': 'Agent1ConfigComponent',
        'agent_2_0': null,  // 待实现
        'workflow': null    // 待实现
      }
      return componentMap[this.appTypeCode] || null
    }
  },
  methods: {
    async fetchAppType() {
      this.loading = true
      try {
        const id = this.$route.params.id
        this.appId = id
        const res = await axios.get(`/api/apps/${id}/`)
        this.appTypeCode = res.data.app_type_code
      } catch (e) {
        window.$message.error('加载应用失败')
        this.$router.push('/apps')
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.fetchAppType()
  },
  watch: {
    '$route.params.id'() {
      this.fetchAppType()
    }
  }
}
</script>

<style scoped>
.app-detail-wrapper {
  height: 100%;
  width: 100%;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state button {
  margin-top: 16px;
  padding: 8px 24px;
  background-color: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
</style>
