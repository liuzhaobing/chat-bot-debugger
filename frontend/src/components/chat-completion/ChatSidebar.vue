<template>
  <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
    <div class="sidebar-top-controls">
      <button v-if="!isSidebarCollapsed" @click="newChat" class="new-chat-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
        <span>新聊天</span>
      </button>
      <button class="icon-btn collapse-btn" @click="toggleCollapse" :title="isSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
      </button>
    </div>

    <!-- Collapsed icons only - 隐藏对话图标 -->
    <div class="collapsed-icons" v-if="isSidebarCollapsed">
      <button @click="newChat" class="collapsed-nav-item" title="新聊天">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
      </button>
      <!-- <router-link to="/chat" class="collapsed-nav-item" title="对话">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      </router-link> -->
    </div>

    <!-- Navigation Section - 隐藏，因为只有对话功能 -->
    <!-- <div class="nav-section" v-if="!isSidebarCollapsed">
      <router-link to="/chat" class="nav-item" exact-active-class="active">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        <span>对话</span>
      </router-link>
    </div> -->
    
    <div class="history-container" v-if="!isSidebarCollapsed">
      <div class="section-header" @click="isHistoryCollapsed = !isHistoryCollapsed">
        <span class="section-title">你的聊天</span>
        <svg class="chevron-icon" :class="{ collapsed: isHistoryCollapsed }" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
      
      <div 
        class="history-list" 
        ref="historyList" 
        @scroll="handleScroll" 
        v-show="!isHistoryCollapsed"
      >
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
            <span class="title">{{ conv.title || 'New Chat' }}</span>
        </div>
        <button class="delete-btn" @click.stop="deleteChat(conv.id)" title="Delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </div>
      
      <!-- Skeleton Loading State -->
      <div v-if="conversationsLoading" class="skeleton-container">
        <div v-for="i in 3" :key="'skeleton-'+i" class="skeleton-item">
          <div class="skeleton-text"></div>
        </div>
      </div>
      </div>
    </div>

  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'ChatSidebar',
  data() {
    return {
      searchQuery: '',
      isHistoryCollapsed: false
    }
  },
  computed: {
    ...mapState('chatCompletion', ['conversations', 'currentConversationId', 'conversationsNextPage', 'conversationsLoading']),
    ...mapState(['theme', 'isSidebarCollapsed'])
  },
  methods: {
    newChat() {
      this.$router.push({ name: 'NewChat' })
      this.$nextTick(() => {
        if (this.$refs.historyList) {
          this.$refs.historyList.scrollTop = 0
        }
      })
    },
    loadChat(id) {
      if (id !== this.$store.state.chatCompletion.currentConversationId) {
        this.$router.push({ name: 'Chat', params: { id } })
      }
    },
    async deleteChat(id) {
        const confirmed = await window.$confirm({
            title: '删除会话',
            message: '确定要删除这个会话吗？删除后无法恢复。',
            type: 'warning',
            confirmText: '删除',
            cancelText: '取消'
        })
        
        if (confirmed) {
            await this.$store.dispatch('chatCompletion/deleteConversation', id)
        }
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
        this.$store.dispatch('chatCompletion/fetchConversations', { append: true }).then(() => {
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
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
  border-right: 1px solid #f1f5f9;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 52px;
}

.sidebar-top-controls {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  min-height: 64px;
  box-sizing: border-box;
  border-bottom: 1px solid #f1f5f9;
}

.sidebar.collapsed .sidebar-top-controls {
  justify-content: center;
  padding: 12px;
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.new-chat-btn:hover {
  background-color: #f8fafc;
}

.icon-btn {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.icon-btn:hover {
  background-color: #f8fafc;
  color: #1e293b;
}

.collapse-btn {
  margin-left: 8px;
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
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  border: none;
  background: transparent;
}

.collapsed-nav-item:hover {
  background-color: #f8fafc;
  color: #1e293b;
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
    color: #1e293b;
    text-decoration: none;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.nav-item:hover {
    background-color: #f8fafc;
}

.nav-item.active {
    background-color: #eef2ff;
    color: #4f46e5;
}

.section-header {
  padding: 16px 16px 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
  margin: 0 8px;
}

.section-header:hover {
  background-color: #f8fafc;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.01em;
}

.chevron-icon {
  color: #94a3b8;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  transform: rotate(0deg);
  flex-shrink: 0;
}

.chevron-icon.collapsed {
  transform: rotate(-90deg);
}

.history-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 4px 8px 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  scrollbar-width: thin;
  scrollbar-color: #e2e8f0 transparent;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}
.history-list::-webkit-scrollbar-track {
  background: transparent;
}
.history-list::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}

.history-item {
  padding: 12px 14px;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.875rem;
  color: #475569;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  min-height: 44px;
}

.item-content {
    display: flex;
    align-items: center;
    overflow: hidden;
    flex: 1;
}

.title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-item:hover {
  background-color: #f1f5f9;
}

.history-item.active {
  background-color: #eef2ff;
  color: #4f46e5;
  font-weight: 500;
  border-left: 3px solid #4f46e5;
  padding-left: 11px;
}

.delete-btn {
    display: none;
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    align-items: center;
    justify-content: center;
}

.history-item:hover .delete-btn {
    display: flex;
}

.delete-btn:hover {
    background-color: #fee2e2;
    color: #ef4444;
}

.loading-more {
  display: none;
}

.empty-history {
  padding: 32px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}

/* Skeleton Loader Styles */
.skeleton-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 4px 0;
}

.skeleton-item {
    padding: 10px 12px;
    border-radius: 8px;
    height: 38px;
    display: flex;
    align-items: center;
}

.skeleton-text {
    height: 14px;
    background: #f8fafc;
    border-radius: 4px;
    width: 100%;
    position: relative;
    overflow: hidden;
}

.skeleton-text::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.03), transparent);
    animation: placeholder-glow 1.5s infinite;
}

@keyframes placeholder-glow {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}
</style>
