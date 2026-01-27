<template>
  <div class="apps-container">
    <header class="apps-header">
      <div class="header-top">
        <div class="header-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="title-icon"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
          <h1>应用广场</h1>
        </div>
        <div class="search-section">
          <div class="search-bar">
            <input v-model="searchQuery" type="text" placeholder="请输入应用名称" />
            <button class="search-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="apps-body">
      <aside class="category-sidebar">
        <div class="sidebar-section-title">应用分类</div>
        <div class="category-nav">
          <div 
            v-for="cat in categories" 
            :key="cat.id"
            class="category-nav-item-wrapper"
            :class="{ active: currentCategoryId === cat.id }"
          >
            <button 
                class="category-nav-item"
                @click="currentCategoryId = cat.id"
            >
                <span class="category-dot"></span>
                {{ cat.name }}
            </button>
            <button class="category-edit-btn" @click.stop="openCategoryModal(cat)" title="编辑分类">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
          </div>
        </div>
        
        <div class="sidebar-footer">
          <button class="add-category-btn" @click="openCategoryModal(null)">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            <span>新增分组</span>
          </button>
        </div>
      </aside>

      <main class="apps-content">
        <!-- 类型筛选器 (新增) -->
        <div class="type-filter-bar">
          <button 
            class="type-filter-btn"
            :class="{ active: !currentAppTypeId }"
            @click="currentAppTypeId = null"
          >
            全部
          </button>
          <button 
            v-for="type in appTypes.filter(t => t.is_active)" 
            :key="type.id"
            class="type-filter-btn"
            :class="{ active: currentAppTypeId === type.id }"
            @click="currentAppTypeId = type.id"
          >
            {{ type.name }}
          </button>
        </div>

        <div class="apps-grid">
          <!-- 新建应用卡片 -->
          <div class="app-card add-app-card" @click="openAppModal(null)">
            <div class="add-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </div>
            <p>在当前分组下新建应用</p>
          </div>

          <div 
            v-for="app in filteredApps" 
            :key="app.id"
            class="app-card"
            @click="openAppModal(app)"
          >
            <div class="card-header">
              <div class="app-logo" :style="{ backgroundColor: getIconColor(app.name) }">
                <img v-if="app.icon_url" :src="app.icon_url" alt="logo">
                <span v-else>{{ app.name[0] }}</span>
              </div>
              <div class="header-text">
                <h3 class="app-name-text">{{ app.name }}</h3>
                <div class="header-subtext">
                  <span class="author-label">{{ app.app_type_name || 'Agent 1.0' }}</span>
                  <span class="v-divider">|</span>
                  <span class="price-val">免费</span>
                </div>
              </div>
            </div>
            
            <p class="app-summary">{{ app.description || '该应用旨在提供智能对话支持，帮助用户解决各类问题。' }}</p>

            <div class="card-footer-tags">
              <button class="chat-action-btn" @click.stop="startChat(app)">进入应用</button>
              <span class="tag-pill-fancy">{{ app.category_name || '未分类' }}</span>
              <div class="tag-group-right">
                <button class="delete-app-btn" @click.stop="deleteApp(app.id)" title="删除应用">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
                <button 
                  class="featured-star-btn" 
                  :class="{ active: app.is_featured }"
                  @click.stop="toggleFeatured(app)" 
                  :title="app.is_featured ? '取消精选' : '设为精选'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" :fill="app.is_featured ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="filteredApps.length === 0 && !loading" class="empty-state">
          <div class="empty-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>
          </div>
          <p>没有找到相关应用，请尝试其他关键词</p>
        </div>

        <div v-if="loading" class="loading-overlay">
          <div class="spinner"></div>
        </div>
      </main>
    </div>

    <!-- Group (Category) Edit Modal -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showCategoryModal" @click.self="showCategoryModal = false">
        <div class="add-modal-content">
          <div class="modal-header">
            <h3>{{ isEditingCategory ? '修改分组' : '新增分组' }}</h3>
            <button class="close-btn" @click="showCategoryModal = false">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="input-group">
              <label>分组名称</label>
              <input v-model="categoryForm.name" placeholder="请输入分组名称" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="delete-btn-modal" v-if="isEditingCategory" @click="deleteCategory">删除</button>
            <div class="footer-right-buttons">
              <button class="cancel-btn" @click="showCategoryModal = false">取消</button>
              <button class="save-btn" @click="saveCategory">{{ isEditingCategory ? '保存修改' : '立即创建' }}</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- App Edit/Add Modal -->
    <transition name="fade">
      <div class="modal-overlay" v-if="showAppModalFlag" @click.self="showAppModalFlag = false">
        <div class="modal-content large-modal">
          <div class="modal-sidebar">
            <div class="modal-sidebar-header">
              <h3>创建应用</h3>
            </div>
            <div class="sidebar-nav">
              <div class="sidebar-nav-item active">
                <div class="nav-icon purple">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                </div>
                <div class="nav-text">
                  <span class="nav-title">智能体应用</span>
                  <span class="nav-desc">构建智能体应用</span>
                </div>
              </div>
              <div class="sidebar-nav-item disabled">
                <div class="nav-icon blue">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                </div>
                <div class="nav-text">
                  <span class="nav-title">工作流应用</span>
                  <span class="nav-desc">自定义编排工作流</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-main">
            <div class="modal-main-header">
              <div class="header-info">
                <h2>创建智能体应用</h2>
                <p>构建智能体应用，连接知识、数据与服务。Agent 1.0 模式结合 Prompt 与业务逻辑控制。</p>
              </div>
              <button class="close-btn-top" @click="showAppModalFlag = false">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            
            <div class="modal-main-body">
              <div class="type-selector">
                <label class="section-label">类型</label>
                <div class="type-cards">
                  <div 
                    v-for="type in appTypes.filter(t => t.is_active)" 
                    :key="type.id"
                    class="type-card"
                    :class="{ active: appForm.app_type === type.id, disabled: !type.is_active }"
                    @click="type.is_active && (appForm.app_type = type.id)"
                  >
                    <div class="type-card-header">
                      <span class="type-card-title">{{ type.name }}</span>
                      <div class="check-icon" v-if="appForm.app_type === type.id">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      </div>
                    </div>
                    <p class="type-card-desc">{{ type.description }}</p>
                  </div>
                </div>
              </div>
              
              <div class="form-section">
                <div class="input-group">
                  <label>应用名称 <span class="required">*</span></label>
                  <input v-model="appForm.name" placeholder="请输入应用名称" maxlength="50" />
                  <span class="char-count">{{ appForm.name ? appForm.name.length : 0 }}/50</span>
                </div>
                
                <div class="input-group">
                  <label>描述信息</label>
                  <textarea v-model="appForm.description" placeholder="请输入描述信息"></textarea>
                </div>

                <div class="input-row">
                  <div class="input-group">
                    <label>应用头像</label>
                    <div class="avatar-uploader" :style="{ backgroundColor: getIconColor(appForm.name || 'App') }">
                       <img v-if="appForm.icon_url" :src="appForm.icon_url" @error="appForm.icon_url = ''" />
                       <span v-else>{{ (appForm.name || 'A')[0].toUpperCase() }}</span>
                    </div>
                  </div>
                  <div class="input-group flex-1">
                    <label>头像 URL</label>
                    <input v-model="appForm.icon_url" placeholder="https://..." />
                  </div>
                </div>
              </div>
            </div>
            
            <div class="modal-main-footer">
              <button class="cancel-btn-alt" @click="showAppModalFlag = false">取消</button>
              <button class="create-btn" @click="saveApp" :disabled="!appForm.name">
                {{ isEditingApp ? '保存修改' : '立即创建' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AppsView',
  data() {
    return {
      searchQuery: '',
      currentCategoryId: null,
      currentAppTypeId: null,  // 新增：当前选择的应用类型
      categories: [],
      appTypes: [],  // 新增：应用类型列表
      apps: [],
      loading: false,
      
      // Category Modal
      showCategoryModal: false,
      isEditingCategory: false,
      categoryForm: { id: null, name: '' },
      
      // App Modal
      showAppModalFlag: false,
      isEditingApp: false,
      appForm: { 
        id: null, 
        name: '', 
        description: '', 
        icon_url: '', 
        category: null,
        app_type: null  // 新增：应用类型
      }
    }
  },
  computed: {
    filteredApps() {
      let filtered = this.apps
      
      // 按分类筛选
      if (this.currentCategoryId) {
        const currentCategory = this.categories.find(cat => cat.id === this.currentCategoryId)
        if (currentCategory && currentCategory.name === '精选') {
          // 如果选择的是"精选"分类，显示所有精选应用
          filtered = filtered.filter(app => app.is_featured)
        } else {
          // 其他分类按正常逻辑筛选
          filtered = filtered.filter(app => app.category === this.currentCategoryId)
        }
      }

      // 按应用类型筛选（新增）
      if (this.currentAppTypeId) {
        filtered = filtered.filter(app => app.app_type === this.currentAppTypeId)
      }

      // 按搜索关键词筛选
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(app => 
          app.name.toLowerCase().includes(query) || 
          (app.description && app.description.toLowerCase().includes(query))
        )
      }
      
      return filtered
    }
  },
  methods: {
    async fetchData() {
      this.loading = true
      try {
        const [catsRes, appsRes, typesRes] = await Promise.all([
          axios.get('/api/app-categories/'),
          axios.get('/api/apps/'),
          axios.get('/api/app-types/')  // 新增：获取应用类型
        ])
        this.categories = catsRes.data
        this.apps = appsRes.data
        this.appTypes = typesRes.data  // 新增
        
        if (this.categories.length > 0 && !this.currentCategoryId) {
            this.currentCategoryId = this.categories[0].id
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        this.loading = false
      }
    },
    getIconColor(name) {
        const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899', '#6366f1']
        let hash = 0
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash)
        }
        return colors[Math.abs(hash) % colors.length]
    },

    // Category Methods
    openCategoryModal(cat) {
      if (cat) {
        this.isEditingCategory = true
        this.categoryForm = { id: cat.id, name: cat.name }
      } else {
        this.isEditingCategory = false
        this.categoryForm = { id: null, name: '' }
      }
      this.showCategoryModal = true
    },
    async saveCategory() {
      if (!this.categoryForm.name.trim()) return
      try {
        if (this.isEditingCategory) {
          await axios.patch(`/api/app-categories/${this.categoryForm.id}/`, { name: this.categoryForm.name })
          window.$message.success("修改成功")
        } else {
          await axios.post('/api/app-categories/', { name: this.categoryForm.name })
          window.$message.success("创建成功")
        }
        this.showCategoryModal = false
        await this.fetchData()
      } catch (e) {
        window.$message.error(e.response?.data?.error || "操作失败")
      }
    },
    async deleteCategory() {
      const confirmed = await window.$confirm({
        title: '删除分组',
        message: '确定要删除该分组吗？',
        type: 'danger'
      })
      if (!confirmed) return
      
      try {
        await axios.delete(`/api/app-categories/${this.categoryForm.id}/`)
        window.$message.success("删除成功")
        this.showCategoryModal = false
        this.currentCategoryId = null
        await this.fetchData()
      } catch (e) {
        window.$message.error(e.response?.data?.error || "删除失败")
      }
    },

    // App Methods
    openAppModal(app) {
      if (app) {
        this.isEditingApp = true
        this.appForm = { ...app }
      } else {
        this.isEditingApp = false
        // 获取第一个启用的应用类型作为默认值
        const defaultAppType = this.appTypes.find(t => t.is_active)
        this.appForm = { 
          id: null, 
          name: '', 
          description: '', 
          icon_url: '', 
          category: this.currentCategoryId,
          app_type: defaultAppType ? defaultAppType.id : null  // 新增
        }
      }
      this.showAppModalFlag = true
    },
    async saveApp() {
      // 验证必填字段
      if (!this.appForm.name || !this.appForm.name.trim()) {
        window.$message.error("应用名称不能为空")
        return
      }
      
      if (!this.appForm.description || !this.appForm.description.trim()) {
        window.$message.error("应用描述不能为空")
        return
      }
      
      // 验证驼峰命名
      const camelCasePattern = /^[A-Z][a-zA-Z]*$/
      if (!camelCasePattern.test(this.appForm.name)) {
        window.$message.error("应用名称必须符合驼峰命名规范（如 GetWeather），只允许英文字母，必须以大写字母开头，不允许空格和标点符号")
        return
      }
      
      if (!this.appForm.app_type) {
        window.$message.error("请选择应用类型")
        return
      }
      try {
        if (this.isEditingApp) {
          await axios.patch(`/api/apps/${this.appForm.id}/`, this.appForm)
          window.$message.success("应用已更新")
        } else {
          await axios.post('/api/apps/', this.appForm)
          window.$message.success("应用已创建")
        }
        this.showAppModalFlag = false
        await this.fetchData()
      } catch (e) {
        const errorMsg = e.response?.data?.name?.[0] || 
                        e.response?.data?.description?.[0] || 
                        e.response?.data?.error || 
                        "保存失败"
        window.$message.error(errorMsg)
      }
    },
    async deleteApp(id) {
       if(!id) return
        const confirmed = await window.$confirm({
            title: '删除应用',
            message: '确定要删除该应用吗？',
            type: 'danger'
        })
        if (!confirmed) return
        try {
            await axios.delete(`/api/apps/${id}/`)
            await this.fetchData()
            window.$message.success("应用已删除")
        } catch (e) {
            window.$message.error('删除失败')
        }
    },
    async toggleFeatured(app) {
      try {
        const response = await axios.post(`/api/apps/${app.id}/toggle-featured/`)
        if (response.data.status === 'success') {
          // 更新本地数据
          app.is_featured = response.data.is_featured
          window.$message.success(response.data.message)
        }
      } catch (e) {
        window.$message.error('操作失败')
      }
    },
    startChat(app) {
        this.$router.push(`/apps/${app.id}`)
    }
  },
  mounted() {
    this.fetchData()
  }
}
</script>

<style scoped>
.apps-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8fafc;
  overflow: hidden;
  color: #1e293b;
}

.apps-header {
  padding: 24px 40px;
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
  gap: 12px;
}

.title-icon {
  color: #6366f1;
}

.header-title h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.search-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  width: 360px;
  height: 42px;
  transition: all 0.2s;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.search-bar:focus-within {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-bar input {
  padding: 0 14px;
  border: none;
  outline: none;
  flex: 1;
  font-size: 0.9rem;
  background: transparent;
}

.search-btn {
  background: transparent;
  border: none;
  padding: 0 12px;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.2s;
}

.search-btn:hover {
  color: #6366f1;
}

.apps-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Sidebar Styling */
.category-sidebar {
  width: 260px;
  background-color: #ffffff;
  border-right: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  flex-shrink: 0;
}

.sidebar-section-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 16px;
  padding-left: 12px;
}

.category-nav {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-nav-item-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 10px;
  padding-right: 8px;
  transition: all 0.2s;
}

.category-nav-item-wrapper:hover {
  background-color: #f8fafc;
}

.category-nav-item-wrapper.active {
  background-color: #f5f3ff;
}

.category-nav-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  text-align: left;
  font-weight: 500;
  font-size: 0.95rem;
  transition: color 0.2s;
}

.category-nav-item-wrapper.active .category-nav-item {
  color: #6366f1;
  font-weight: 600;
}

.category-edit-btn {
    opacity: 0;
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 6px;
    border-radius: 6px;
    display: flex;
    transition: all 0.2s;
}

.category-nav-item-wrapper:hover .category-edit-btn {
    opacity: 1;
}

.category-edit-btn:hover {
    background: #ffffff;
    color: #6366f1;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.category-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: transparent;
  transition: background-color 0.2s;
}

.category-nav-item-wrapper.active .category-dot {
  background-color: #6366f1;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid #f1f5f9;
}

.add-category-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background-color: #ffffff;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-category-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: #f5f3ff;
  transform: translateY(-1px);
}

/* Content Area Styling */
.apps-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  position: relative;
  background-color: #f8fafc;
}

/* 类型筛选器样式 (新增) */
.type-filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
  padding: 8px;
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
}

.type-filter-btn {
  padding: 10px 24px;
  border: none;
  background-color: transparent;
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.type-filter-btn:hover {
  background-color: #f8fafc;
  color: #1e293b;
}

.type-filter-btn.active {
  background-color: #6366f1;
  color: #ffffff;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.app-card {
  background-color: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
}

.app-card:not(.add-app-card):hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
  transform: translateY(-4px);
  border-color: #e2e8f0;
}

.add-app-card {
  border: 2px dashed #e2e8f0;
  background-color: #ffffff;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  gap: 16px;
  text-align: center;
}

.add-app-card:hover {
  border-color: #6366f1;
  color: #6366f1;
  background-color: #f5f3ff;
}

.add-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background-color: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.add-app-card:hover .add-icon {
  background-color: #ffffff;
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
}

.app-logo {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 1.5rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.app-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.app-name-text {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.header-subtext {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #64748b;
}

.author-label {
  font-weight: 600;
  color: #475569;
}

.v-divider {
  color: #e2e8f0;
}

.price-val {
  font-weight: 700;
  color: #10b981;
}

.app-summary {
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.6;
  margin: 0 0 24px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: auto;
}

.chat-action-btn {
  background-color: #6366f1;
  color: #ffffff;
  border: none;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-action-btn:hover {
  background-color: #4f46e5;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
}

.tag-pill-fancy {
  background-color: #f1f5f9;
  color: #475569;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
}

.tag-group-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
}

.featured-star-btn {
    opacity: 0;
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    display: flex;
    transition: all 0.2s;
}

.featured-star-btn.active {
    opacity: 1;
    color: #f59e0b;
}

.app-card:hover .featured-star-btn {
    opacity: 1;
}

.featured-star-btn:hover {
    background: #fef3c7;
    color: #f59e0b;
    transform: scale(1.1);
}

.delete-app-btn {
    opacity: 0;
    background: transparent;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    display: flex;
    transition: all 0.2s;
}

.app-card:hover .delete-app-btn {
    opacity: 1;
}

.delete-app-btn:hover {
    background: #fef2f2;
    color: #ef4444;
}

.empty-state {
  text-align: center;
  color: #94a3b8;
  margin-top: 120px;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.2;
}

.loading-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(248, 250, 252, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e2e8f0;
    border-top-color: #6366f1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* New Modal Styling */
/* Premium Modal Styling */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(8px);
}

.add-modal-content {
  background: #ffffff;
  width: 520px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px 32px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 8px;
  border-radius: 10px;
  display: flex;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f1f5f9;
  color: #1e293b;
}

.modal-body {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group label {
  font-size: 0.9rem;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 4px;
}

.input-group input, .input-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  outline: none;
  font-size: 1rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background-color: #f8fafc;
  color: #0f172a;
}

.input-group input:focus, .input-group textarea:focus {
  border-color: #6366f1;
  background-color: #ffffff;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.modal-footer {
  padding: 20px 32px;
  background-color: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.footer-right-buttons {
    display: flex;
    gap: 12px;
}

.delete-btn-modal {
  padding: 10px 20px;
  background: #ffffff;
  border: 1px solid #fee2e2;
  border-radius: 10px;
  color: #ef4444;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s;
}

.delete-btn-modal:hover {
    background: #fef2f2;
    border-color: #fecaca;
}

.cancel-btn, .cancel-btn-alt {
  padding: 10px 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #64748b;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s;
}

.save-btn, .create-btn {
  padding: 10px 32px;
  background: #6366f1;
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s;
}

.save-btn:hover, .create-btn:hover:not(:disabled) {
  background: #4f46e5;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Large Modal (App Creation) Redesign */
.large-modal {
  width: 1000px;
  height: 740px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  border-radius: 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-sidebar {
  width: 280px;
  background-color: #f8fafc;
  border-right: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
}

.modal-sidebar-header {
  padding: 32px 24px;
}

.modal-sidebar-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.sidebar-nav {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-nav-item.active {
  background-color: #ffffff;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.sidebar-nav-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon.purple { background-color: #6366f1; color: #ffffff; }
.nav-icon.blue { background-color: #3b82f6; color: #ffffff; }

.nav-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
}

.nav-desc {
  font-size: 0.8rem;
  color: #64748b;
}

.modal-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

.modal-main-header {
  padding: 32px 40px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h2 {
  margin: 0 0 6px 0;
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}

.header-info p {
  margin: 0;
  font-size: 0.95rem;
  color: #64748b;
  line-height: 1.6;
}

.close-btn-top {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.2s;
}

.close-btn-top:hover {
  background-color: #f1f5f9;
  color: #1e293b;
}

.modal-main-body {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.type-cards {
  display: flex;
  gap: 20px;
}

.type-card {
  flex: 1;
  padding: 24px;
  border: 2px solid #f1f5f9;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background-color: #fafafa;
}

.type-card.active {
  border-color: #6366f1;
  background-color: #f5f3ff;
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
}

.type-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #fdfdfd;
}

.type-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.type-card-title {
  font-weight: 800;
  font-size: 1.1rem;
  color: #1e293b;
}

.check-icon {
  width: 24px;
  height: 24px;
  background-color: #6366f1;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
}

.tag-recommend {
  font-size: 0.75rem;
  background-color: #e0f2fe;
  color: #0ea5e9;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 700;
}

.type-card-desc {
  margin: 0;
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.6;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.char-count {
  position: absolute;
  right: 16px;
  top: 40px;
  font-size: 0.8rem;
  color: #94a3b8;
  font-weight: 500;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

.avatar-uploader {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 1.75rem;
  overflow: hidden;
  box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffffff;
}

.avatar-uploader img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-main-footer {
  padding: 24px 40px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  background-color: #ffffff;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
