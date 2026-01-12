<template>
  <div class="app-detail-container" v-if="app">
    <div class="breadcrumb">
      <router-link to="/apps">应用</router-link>
      <span class="separator">›</span>
      <span class="current">{{ app.name }}</span>
    </div>

    <div class="app-hero">
      <div class="app-icon-large" :style="{ backgroundColor: getIconColor(app.name) }">
        {{ app.name[0] }}
      </div>
      <div class="app-header-info">
        <h1>{{ app.name }}</h1>
        <p class="app-tagline">{{ app.description }}</p>
      </div>
      <button class="connect-btn">连接</button>
    </div>

    <div class="feature-grid">
      <div class="feature-card" v-for="i in 3" :key="i">
        <div class="feature-image">
          <img :src="`https://via.placeholder.com/300x200?text=${app.name}+Example+${i}`" alt="Feature Image" />
        </div>
        <div class="feature-desc">
          <span>@{{ app.name }} apply an artistic effect</span>
        </div>
      </div>
    </div>

    <div class="app-description-long">
      <p>{{ app.name }} for ChatGPT simplifies complex tasks for creators of any skill level, for free. Upload an image and easily remove the background, refine lighting and color, or apply creative effects like motion blur, dust, and more. Intuitive controls let you adjust visuals to match your unique style while delivering high-quality results. With one click, continue your edits in {{ app.name }} on the web or mobile for full creative control. Ideal for creative profile photos, social posts, and more.</p>
    </div>
  </div>
  <div v-else-if="loading" class="loading-state">
    <div class="spinner"></div>
  </div>
  <div v-else class="error-state">
    App not found
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AppDetailView',
  data() {
    return {
      app: null,
      loading: true
    }
  },
  methods: {
    async fetchApp() {
      this.loading = true
      try {
        const id = this.$route.params.id
        const response = await axios.get(`/api/apps/${id}/`)
        this.app = response.data
      } catch (error) {
        console.error('Failed to fetch app:', error)
      } finally {
        this.loading = false
      }
    },
    getIconColor(name) {
        const colors = ['#000', '#f1c40f', '#e67e22', '#e74c3c', '#9b59b6', '#3498db', '#2ecc71', '#1abc9c']
        let hash = 0
        if (name) {
            for (let i = 0; i < name.length; i++) {
                hash = name.charCodeAt(i) + ((hash << 5) - hash)
            }
        }
        return colors[Math.abs(hash) % colors.length]
    }
  },
  mounted() {
    this.fetchApp()
  },
  watch: {
    '$route.params.id': 'fetchApp'
  }
}
</script>

<style scoped>
.app-detail-container {
  padding: 40px 10%;
  flex: 1;
  overflow-y: auto;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 40px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.breadcrumb a {
  color: var(--text-secondary);
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.separator {
  color: var(--text-tertiary);
}

.app-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 40px;
  position: relative;
}

.app-icon-large {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2.5rem;
  font-weight: bold;
}

.app-header-info h1 {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.app-tagline {
  font-size: 1.2rem;
  color: var(--text-secondary);
}

.connect-btn {
  margin-left: auto;
  padding: 10px 24px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}

[data-theme="dark"] .connect-btn {
  background: #fff;
  color: #000;
}

.connect-btn:hover {
  opacity: 0.8;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.feature-card {
  background: var(--bg-surface);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.feature-image img {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.feature-desc {
  padding: 16px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.app-description-long {
  line-height: 1.6;
  color: var(--text-secondary);
}

.loading-state, .error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: var(--text-secondary);
}

.spinner {
    width: 30px;
    height: 30px;
    border: 3px solid var(--border-color);
    border-top-color: var(--text-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
