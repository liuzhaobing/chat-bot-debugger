<template>
  <div class="apps-container">
    <div class="apps-header">
      <div class="header-left">
        <h1>应用</h1>
        <span class="beta-tag">测试版</span>
        <p class="subtitle">在 ChatGPT 中与你喜爱的应用对话</p>
      </div>
      <div class="search-box">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" v-model="searchQuery" placeholder="搜索应用" @input="handleSearch" />
      </div>
    </div>

    <!-- Featured Banner (Mockup based on screenshot) -->
    <div class="featured-banner" v-if="!searchQuery && featuredApps.length > 0">
      <div class="banner-content">
        <div class="banner-text">
            <div class="banner-app-icon">C</div>
            <h2>使用 Canva 进行创作</h2>
            <p>制作设计与宣传单</p>
            <button class="view-btn">查看</button>
        </div>
        <div class="banner-image">
            <img src="https://via.placeholder.com/300x150" alt="Canva Banner" />
            <div class="banner-badge">@Canva create social posts</div>
        </div>
      </div>
    </div>

    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: currentTab === tab.id }"
        @click="currentTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="apps-grid">
      <div v-for="app in filteredApps" :key="app.id" class="app-card" @click="$router.push(`/apps/${app.id}`)">
        <div class="app-card-left">
            <div class="app-icon" :style="{ backgroundColor: getIconColor(app.name) }">
                {{ app.name[0] }}
            </div>
            <div class="app-info">
                <div class="app-name">{{ app.name }}</div>
                <div class="app-desc">{{ app.description }}</div>
            </div>
        </div>
        <div class="app-card-right">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="arrow-icon"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
        <div class="spinner"></div>
    </div>
    <div v-if="!loading && filteredApps.length === 0" class="no-results">
        暂无应用
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AppsView',
  data() {
    return {
      searchQuery: '',
      currentTab: 'featured',
      tabs: [
        { id: 'featured', label: '精选' },
        { id: 'lifestyle', label: '生活方式' },
        { id: 'productivity', label: '工作效率' }
      ],
      apps: [],
      loading: false,
      searchTimeout: null
    }
  },
  computed: {
    filteredApps() {
      if (this.searchQuery) {
        return this.apps
      }
      if (this.currentTab === 'featured') {
          return this.apps.filter(app => app.is_featured)
      }
      return this.apps.filter(app => app.category === this.currentTab)
    },
    featuredApps() {
        return this.apps.filter(app => app.is_featured)
    }
  },
  methods: {
    async fetchApps() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery) {
            params.search = this.searchQuery
        }
        const response = await axios.get('/api/apps/', { params })
        this.apps = response.data
      } catch (error) {
        console.error('Failed to fetch apps:', error)
      } finally {
        this.loading = false
      }
    },
    handleSearch() {
        clearTimeout(this.searchTimeout)
        this.searchTimeout = setTimeout(() => {
            this.fetchApps()
        }, 500)
    },
    getIconColor(name) {
        const colors = ['#000', '#f1c40f', '#e67e22', '#e74c3c', '#9b59b6', '#3498db', '#2ecc71', '#1abc9c']
        let hash = 0
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash)
        }
        return colors[Math.abs(hash) % colors.length]
    }
  },
  mounted() {
    this.fetchApps()
  }
}
</script>

<style scoped>
.apps-container {
  padding: 40px 10%;
  flex: 1;
  overflow-y: auto;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.apps-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.header-left h1 {
  font-size: 2rem;
  margin-bottom: 4px;
}

.beta-tag {
  font-size: 0.7rem;
  background: var(--bg-hover);
  padding: 2px 6px;
  border-radius: 10px;
  vertical-align: middle;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-top: 8px;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
}

.search-box input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-primary);
  outline: none;
  font-size: 0.9rem;
}

.featured-banner {
  background: linear-gradient(135deg, #e0f2fe 0%, #ccfbf1 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 40px;
  color: #1e293b;
  position: relative;
  overflow: hidden;
}

[data-theme="dark"] .featured-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #064e3b 100%);
    color: #f8fafc;
}

.banner-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.banner-app-icon {
    width: 48px;
    height: 48px;
    background: #00c4cc;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 1.5rem;
    margin-bottom: 16px;
}

.banner-text h2 {
    font-size: 1.8rem;
    margin-bottom: 8px;
}

.banner-text p {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-bottom: 24px;
}

.view-btn {
    padding: 8px 24px;
    background: #000;
    color: #fff;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-weight: 500;
}

[data-theme="dark"] .view-btn {
    background: #fff;
    color: #000;
}

.banner-image {
    position: relative;
}

.banner-badge {
    position: absolute;
    top: -20px;
    right: 0;
    background: rgba(255, 255, 255, 0.8);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8rem;
    color: #1e293b;
}

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 30px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 10px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.app-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;
}

.app-card:hover {
  background: var(--bg-hover);
}

.app-card-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.app-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 1.2rem;
    flex-shrink: 0;
}

.app-info {
    overflow: hidden;
}

.app-name {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 2px;
}

.app-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.arrow-icon {
    color: var(--text-tertiary);
    opacity: 0;
    transition: opacity 0.2s;
}

.app-card:hover .arrow-icon {
    opacity: 1;
}

.loading, .no-results {
    padding: 40px;
    text-align: center;
    color: var(--text-secondary);
}

.spinner {
    width: 30px;
    height: 30px;
    border: 3px solid var(--border-color);
    border-top-color: var(--text-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
