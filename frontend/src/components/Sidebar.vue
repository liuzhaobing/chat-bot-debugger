<template>
  <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
    <div class="sidebar-top-controls">
      <button class="icon-btn" @click="toggleCollapse" :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
      </button>
      <button v-if="!isSidebarCollapsed" @click="newChat" class="icon-btn" title="新聊天">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
      </button>
    </div>

    <div class="sidebar-header" v-if="!isSidebarCollapsed">
      <button @click="newChat" class="new-chat-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
        <span>新聊天</span>
      </button>
    </div>

    <!-- Collapsed icons only -->
    <div class="collapsed-icons" v-if="isSidebarCollapsed">
      <button @click="newChat" class="collapsed-nav-item" title="新聊天">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
      </button>
      <router-link to="/" class="collapsed-nav-item" title="对话">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      </router-link>
      <router-link to="/apps" class="collapsed-nav-item" title="应用">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
      </router-link>
    </div>

    <!-- Navigation Section -->
    <div class="nav-section" v-if="!isSidebarCollapsed">
      <router-link to="/" class="nav-item" exact-active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        <span>对话</span>
      </router-link>
      <div class="nav-item placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span>搜索聊天</span>
      </div>
      <div class="nav-item placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
        <span>图片</span>
      </div>
      <router-link to="/apps" class="nav-item" exact-active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
        <span>应用</span>
      </router-link>
      <div class="nav-item placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
        <span>项目</span>
      </div>
    </div>
    
    <div class="history-list" ref="historyList" @scroll="handleScroll" v-if="!isSidebarCollapsed">
      <div v-if="!searchQuery && conversations.length > 0" class="section-title">你的聊天</div>
      <div v-if="conversations.length === 0 && !conversationsLoading" class="empty-history">
        No chats yet.
      </div>
      <div 
        v-for="conv in conversations" 
        :key="conv.id" 
        class="history-item"
        :class="{ active: conv.id === currentConversationId }"
        @click="loadChat(conv.id)"
      >
        <div class="item-content">
            <svg class="chat-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span class="title">{{ conv.title || 'New Chat' }}</span>
        </div>
        <button class="delete-btn" @click.stop="deleteChat(conv.id)" title="Delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </div>
      
      <div v-if="conversationsLoading" class="loading-more">
        <div class="spinner-small"></div>
        <span>Loading...</span>
      </div>
    </div>

    <div class="sidebar-footer" v-if="!isSidebarCollapsed">
      <button @click="toggleTheme" class="footer-btn" :title="theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
        <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        <span>{{ theme === 'dark' ? 'Light Mode' : 'Dark Mode' }}</span>
      </button>

      <button @click="$emit('open-settings')" class="footer-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        <span>Settings</span>
      </button>
    </div>


    <!-- Redesigned Toggle Button -->
    <div class="toggle-wrapper" :class="{ collapsed: isSidebarCollapsed }">
      <button class="edge-toggle-btn" @click="toggleCollapse" :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <div class="toggle-icon-container">
            <svg v-if="!isSidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </div>
      </button>
    </div>
    <!-- Redesigned Toggle Button -->
    <div class="toggle-wrapper" :class="{ collapsed: isSidebarCollapsed }">
      <button class="edge-toggle-btn" @click="toggleCollapse" :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <div class="toggle-icon-container">
            <svg v-if="!isSidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </div>
      </button>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'ChatSidebar',
  data() {
    return {
    }
  },
  computed: {
    ...mapState(['conversations', 'currentConversationId', 'theme', 'conversationsNextPage', 'conversationsLoading', 'isSidebarCollapsed'])
  },
  methods: {
    newChat() {
      this.$store.dispatch('createNewChat')
      this.$nextTick(() => {
        if (this.$refs.historyList) {
          this.$refs.historyList.scrollTop = 0
        }
      })
    },
    loadChat(id) {
      if (id !== this.$store.state.currentConversationId) {
        this.$store.dispatch('loadConversation', id)
      }
    },
    async deleteChat(id) {
        if(confirm("Delete this chat?")) {
            await this.$store.dispatch('deleteConversation', id)
        }
    },
    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark'
        this.$store.commit('SET_THEME', newTheme)
    },
    handleScroll(e) {
      const { scrollTop, clientHeight, scrollHeight } = e.target
      // If we are within 50px of the bottom, load more
      if (scrollTop + clientHeight >= scrollHeight - 50) {
        this.loadMore()
      }
    },
    loadMore() {
      if (this.conversationsNextPage && !this.conversationsLoading) {
        this.$store.dispatch('fetchConversations', { append: true }).then(() => {
          // After loading, check if we're still at the bottom (e.g. if the new items didn't add enough height)
          this.$nextTick(() => {
            this.checkIfNeedsMore()
          })
        })
      }
    },
    checkIfNeedsMore() {
      const el = this.$refs.historyList
      if (!el) return
      // If there's no vertical scrollbar and we have more pages, load them
      if (el.scrollHeight <= el.clientHeight && this.conversationsNextPage && !this.conversationsLoading) {
        this.loadMore()
      }
    },
    toggleCollapse() {
        this.$store.commit('SET_SIDEBAR_COLLAPSED', !this.isSidebarCollapsed)
    }
  },
  mounted() {
    // Initial check after mounting and potential data load
    this.$nextTick(() => {
      this.checkIfNeedsMore()
    })
  },
  watch: {
    // Also check when conversations change (e.g. first load)
    conversations() {
      this.$nextTick(() => {
        this.checkIfNeedsMore()
      })
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
  border-right: 1px solid var(--border-color);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 52px;
}

.sidebar-top-controls {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  height: 56px;
  box-sizing: border-box;
}

.sidebar.collapsed .sidebar-top-controls {
  justify-content: center;
}

.icon-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.sidebar-header {
  padding: 0 12px 12px 12px;
  flex-shrink: 0;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.new-chat-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--border-color);
}

.collapsed-icons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
}

.collapsed-nav-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  border: none;
  background: transparent;
}

.collapsed-nav-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.nav-section {
    padding: 0 12px 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.nav-item:hover {
    background-color: var(--bg-hover);
}

.nav-item.active {
    background-color: var(--bg-surface);
}

.nav-item.placeholder {
    cursor: default;
    opacity: 0.8;
}

.section-title {
    padding: 12px 12px 4px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}

.history-list::-webkit-scrollbar {
  width: 4px;
}
.history-list::-webkit-scrollbar-track {
  background: transparent;
}
.history-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 10px;
}

.history-item {
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.9rem;
  color: var(--text-primary);
  transition: background-color 0.2s;
  position: relative;
  overflow: hidden;
}

.item-content {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow: hidden;
    flex: 1;
}

.chat-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-item:hover {
  background-color: var(--bg-hover);
}

.history-item.active {
  background-color: var(--bg-surface);
  font-weight: 500;
}

.delete-btn {
    display: none;
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    align-items: center;
    justify-content: center;
}

.history-item:hover .delete-btn {
    display: flex;
}

.sidebar-footer {
    padding: 12px;
    border-top: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex-shrink: 0;
}

.footer-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--text-primary);
    cursor: pointer;
    transition: background-color 0.2s;
    font-size: 0.9rem;
    text-align: left;
}

.footer-btn:hover {
    background-color: var(--bg-hover);
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: var(--text-secondary);
}

/* Edge Toggle Button */
.toggle-wrapper {
    position: absolute;
    right: -12px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1000;
}

.toggle-wrapper.collapsed {
    right: -24px;
}

.edge-toggle-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 100px;
    position: relative;
    outline: none;
}

.toggle-icon-container {
    width: 4px;
    height: 30px;
    background: var(--text-tertiary);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    opacity: 0.3;
}

.edge-toggle-btn:hover .toggle-icon-container {
    opacity: 1;
    width: 20px;
    height: 20px;
    background: var(--bg-surface);
    border-radius: 50%;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    border: 1px solid var(--border-color);
}

.edge-toggle-btn svg {
    display: none;
    color: var(--text-primary);
}

.edge-toggle-btn:hover svg {
    display: block;
}
</style>
