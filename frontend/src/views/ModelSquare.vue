<template>
  <div class="model-square-container">
    <header class="square-header">
      <div class="header-top">
        <div class="header-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="title-icon"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
          <h1>模型广场</h1>
        </div>
        <div class="search-section">
          <div class="search-bar">
            <input v-model="searchQuery" type="text" placeholder="请输入模型名称" />
            <button class="search-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="square-body">
      <aside class="provider-sidebar">
        <div class="sidebar-section-title">Providers</div>
        <div class="provider-nav">
          <div 
            v-for="provider in providers" 
            :key="provider.id"
            class="provider-nav-item-wrapper"
            :class="{ active: activeProviderId === provider.id }"
          >
            <button 
                class="provider-nav-item"
                @click="activeProviderId = provider.id"
            >
                <span class="provider-dot"></span>
                {{ provider.name }}
            </button>
            <button class="sync-action-btn" @click.stop="syncProvider(provider.id)" title="同步模型">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/></svg>
            </button>
            <button class="edit-action-btn" @click.stop="openEditModal(provider)" title="编辑提供商">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
          </div>
        </div>
        
        <div class="sidebar-footer">
          <button class="add-provider-btn" @click="openAddModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            <span>Add New Provider</span>
          </button>
        </div>
      </aside>

      <main class="square-content">
        <div class="model-grid">
          <div 
            v-for="model in filteredModels" 
            :key="model.name"
            class="model-card"
          >
            <div class="card-header">
              <div class="model-logo">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" v-if="!getProviderLogo(activeProviderId)">
                   <path d="M12 2L4 7v10l8 5 8-5V7l-8-5z" stroke="#3730A3" stroke-width="2" stroke-linejoin="round"/>
                   <path d="M12 22V12m0 0l-8-5m8 5l8-5" stroke="#3730A3" stroke-width="2" stroke-linejoin="round"/>
                </svg>
                <img v-else :src="getProviderLogo(activeProviderId)" alt="logo">
              </div>
              <div class="header-text">
                <h3 class="model-name-text">{{ model.display_name || model.name }}</h3>
                <div class="header-subtext">
                  <span class="author-label">{{ getProviderName(activeProviderId) }}</span>
                  <span class="v-divider">|</span>
                  <span class="price-val">{{ model.pricing ? `¥${model.pricing.input}/M` : '付费' }}</span>
                </div>
              </div>
            </div>
            
            <p class="model-summary">{{ model.description || '该模型支持思考模式（适用于复杂逻辑推理、数学、代码撰写等场景）。' }}</p>

            <div class="card-footer-tags">
              <button class="chat-action-btn" @click="startChat(model)">对话</button>
              <span class="tag-pill-fancy">Tools</span>
              <span class="tag-pill-fancy">推理模型</span>
              <span class="tag-pill-fancy" v-if="model.parameters">{{ model.parameters }}</span>
              <div class="tag-group-right">
                <span class="tag-pill-fancy" v-if="model.context_window">{{ formatTokens(model.context_window) }}</span>
                <button class="delete-model-btn" @click.stop="deleteModel(model.id)" title="删除模型">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="filteredModels.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>
          </div>
          <p>没有找到相关模型，请尝试其他关键词</p>
        </div>
      </main>
    </div>

    <!-- Add Provider Modal -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showAddModal" @click.self="showAddModal = false">
        <div class="add-modal-content">
          <div class="modal-header">
            <h3>{{ isEditing ? 'Edit Provider' : 'Add New Provider' }}</h3>
            <button class="close-btn" @click="showAddModal = false">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="input-group">
              <label>Name</label>
              <input v-model="newProvider.name" placeholder="Name (e.g. OpenAI)" />
            </div>
            <div class="input-group">
              <label>Base URL</label>
              <input v-model="newProvider.base_url" placeholder="https://api.openai.com/v1" />
            </div>
            <div class="input-group">
              <label>API Key</label>
              <input v-model="newProvider.api_key" placeholder="sk-..." type="password" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="delete-btn-modal" v-if="isEditing" @click="deleteProvider">删除</button>
            <div class="footer-right-buttons">
                <button class="cancel-btn" @click="showAddModal = false">取消</button>
                <button class="save-btn" @click="saveProvider">{{ isEditing ? '保存修改' : '添加提供商' }}</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
/**
 * ModelSquare 组件
 * 实现模型展示、搜索与快速对话跳转
 * 布局严格参照用户提供的 Qwen 卡片样式，并整合原 Settings 的同步与删除功能
 */
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  name: 'ModelSquare',
  data() {
    return {
      searchQuery: '',
      activeProviderId: null,
      showAddModal: false,
      isEditing: false,
      editingProviderId: null,
      newProvider: { name: '', base_url: '', api_key: '' }
    }
  },
  computed: {
    ...mapState(['providers']),
    filteredModels() {
      if (!this.activeProviderId) return []
      const provider = this.providers.find(p => p.id === this.activeProviderId)
      if (!provider) return []
      
      let models = provider.models || []
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase()
        models = models.filter(m => 
          (m.display_name || m.name).toLowerCase().includes(query) || 
          m.name.toLowerCase().includes(query)
        )
      }
      return models
    }
  },
  watch: {
    providers: {
      handler(val) {
        if (val && val.length > 0 && !this.activeProviderId) {
          this.activeProviderId = val[0].id
        }
      },
      immediate: true
    }
  },
  methods: {
    getProviderLogo() {
      return null 
    },
    getProviderName(id) {
      const p = this.providers.find(p => p.id === id)
      return p ? p.name : ''
    },
    formatTokens(val) {
      if (val >= 1000) return (val / 1000) + 'K'
      return val
    },
    startChat(model) {
      // 跳转到模型调试页面
      this.$router.push({
        path: '/model-debug',
        query: {
          model: model.name,
          provider: this.activeProviderId
        }
      })
    },
    openEditModal(provider) {
      this.isEditing = true
      this.editingProviderId = provider.id
      this.newProvider = { 
        name: provider.name, 
        base_url: provider.base_url, 
        api_key: '' // Clear for security, only update if entered
      }
      this.showAddModal = true
    },
    openAddModal() {
      this.isEditing = false
      this.editingProviderId = null
      this.newProvider = { name: '', base_url: '', api_key: '' }
      this.showAddModal = true
    },
    async saveProvider() {
      if (this.isEditing) {
        await this.updateProvider()
      } else {
        await this.addProvider()
      }
    },
    async addProvider() {
      try {
        if (!this.newProvider.name || !this.newProvider.base_url) {
          window.$message.error("提供商名称和基础 URL 不能为空")
          return
        }
        await axios.post('/api/providers/', this.newProvider)
        this.showAddModal = false
        await this.$store.dispatch('fetchProviders')
        window.$message.success("提供商添加成功")
      } catch (e) {
        console.error(e)
        window.$message.error('添加失败: ' + (e.response?.data?.error || e.message))
      }
    },
    async updateProvider() {
      try {
        const payload = { ...this.newProvider }
        if (!payload.api_key) delete payload.api_key
        
        await axios.patch(`/api/providers/${this.editingProviderId}/`, payload)
        this.showAddModal = false
        await this.$store.dispatch('fetchProviders')
        window.$message.success("提供商已更新")
      } catch (e) {
        console.error(e)
        window.$message.error('更新失败')
      }
    },
    async deleteProvider() {
      const confirmed = await window.$confirm({
        title: '删除提供商',
        message: '确定要删除此提供商吗？关联的所有模型也将被移除。',
        type: 'danger'
      })
      if (!confirmed) return
      
      try {
        await axios.delete(`/api/providers/${this.editingProviderId}/`)
        this.showAddModal = false
        await this.$store.dispatch('fetchProviders')
        window.$message.success("提供商已删除")
      } catch (e) {
        console.error(e)
        window.$message.error('删除失败')
      }
    },
    async syncProvider(id) {
        try {
            const res = await axios.post(`/api/providers/${id}/refresh_models/`)
            window.$message.success(`已成功同步 ${res.data.count} 个模型！`)
            await this.$store.dispatch('fetchProviders')
        } catch (e) {
            console.error(e)
            window.$message.error('同步失败: ' + (e.response?.data?.error || e.message))
        }
    },
    async deleteModel(id) {
        if(!id) return
        const confirmed = await window.$confirm({
            title: '删除模型',
            message: '确定要从列表中删除该模型吗？',
            type: 'danger',
            confirmText: '删除',
            cancelText: '取消'
        })
        
        if (!confirmed) return
        
        try {
            await axios.delete(`/api/models/${id}/`)
            await this.$store.dispatch('fetchProviders')
            window.$message.success("模型已成功删除")
        } catch (e) {
            console.error(e)
            window.$message.error('删除失败')
        }
    }
  }
}
</script>

<style scoped>
.model-square-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f9fafb;
  overflow: hidden;
  color: #1e293b;
}

.square-header {
  padding: 20px 40px;
  background-color: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #6366f1;
}

.header-title h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.search-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.85rem;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  width: 320px;
  height: 36px;
}

.search-bar input {
  padding: 0 12px;
  border: none;
  outline: none;
  flex: 1;
  font-size: 0.85rem;
}

.search-btn {
  background: transparent;
  border: none;
  padding: 0 10px;
  color: #94a3b8;
  cursor: pointer;
}

.square-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.provider-sidebar {
  width: 240px;
  background-color: #ffffff;
  border-right: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  flex-shrink: 0;
}

.sidebar-section-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  padding-left: 12px;
}

.provider-nav {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.provider-nav-item-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 8px;
  padding-right: 8px;
  transition: all 0.2s;
}

.provider-nav-item-wrapper:hover {
  background-color: #f8fafc;
}

.provider-nav-item-wrapper.active {
  background-color: #eef2ff;
}

.provider-nav-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  text-align: left;
  font-weight: 500;
  font-size: 0.95rem;
}

.sync-action-btn,
.edit-action-btn {
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 6px;
    border-radius: 6px;
    display: flex;
    transition: all 0.2s;
    opacity: 0;
}

.provider-nav-item-wrapper:hover .sync-action-btn,
.provider-nav-item-wrapper:hover .edit-action-btn {
    opacity: 1;
}

.sync-action-btn:hover,
.edit-action-btn:hover {
    background: #eef2ff;
    color: #4f46e5;
}

.provider-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: transparent;
}

.provider-nav-item-wrapper.active .provider-dot {
  background-color: #4f46e5;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.add-provider-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background-color: #ffffff;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.add-provider-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: #f5f3ff;
}

.square-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.model-card {
  background-color: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s ease;
}

.model-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.model-logo {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-name-text {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
}

.header-subtext {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #6b7280;
}

.author-label {
  font-weight: 500;
}

.v-divider {
  color: #d1d5db;
}

.price-val {
  font-weight: 600;
  color: #111827;
}

.model-summary {
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 20px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: auto;
}

.chat-action-btn {
  background-color: #f0f9ff;
  color: #0ea5e9;
  border: 1px solid #e0f2fe;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-action-btn:hover {
  background-color: #e0f2fe;
}

.tag-pill-fancy {
  background-color: #f5f3ff;
  color: #8b5cf6;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.tag-group-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
}

.delete-model-btn {
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 6px;
    border-radius: 6px;
    display: flex;
    transition: all 0.2s;
}

.model-card:hover .delete-model-btn {
    color: #ef4444;
}

.delete-model-btn:hover {
    background: #fef2f2;
}

.empty-state {
  text-align: center;
  color: #94a3b8;
  margin-top: 80px;
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.3;
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.add-modal-content {
  background: #ffffff;
  width: 480px;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.add-modal-content .modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.add-modal-content .modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}

.input-group input {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  outline: none;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.input-group input:focus {
  border-color: #6366f1;
}

.modal-footer {
  padding: 16px 24px;
  background-color: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.footer-right-buttons {
    display: flex;
    gap: 12px;
}

.delete-btn-modal {
  padding: 8px 16px;
  background: #ffffff;
  border: 1px solid #fee2e2;
  border-radius: 8px;
  color: #ef4444;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.delete-btn-modal:hover {
    background: #fef2f2;
}

.cancel-btn {
  padding: 8px 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  font-weight: 500;
}

.save-btn {
  padding: 8px 16px;
  background: #6366f1;
  border: none;
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  font-weight: 500;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
