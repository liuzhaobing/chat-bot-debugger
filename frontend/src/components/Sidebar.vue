<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <button @click="newChat" class="new-chat-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        <span v-if="!isCollapsed">New Chat</span>
      </button>
      <button class="collapse-btn" @click="toggleCollapse" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
        <svg v-if="!isCollapsed" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
      </button>
    </div>
    
    <div class="history-list" ref="historyList" @scroll="handleScroll" v-show="!isCollapsed">
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

    <div class="sidebar-footer" v-show="!isCollapsed">
      <button @click="toggleTheme" class="footer-btn" :title="theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
        <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        <span>{{ theme === 'dark' ? 'Light Mode' : 'Dark Mode' }}</span>
      </button>

      <button @click="$emit('open-settings')" class="footer-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        <span>Settings</span>
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
      isCollapsed: false
    }
  },
  computed: {
    ...mapState(['conversations', 'currentConversationId', 'theme', 'conversationsNextPage', 'conversationsLoading'])
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
      this.isCollapsed = !this.isCollapsed
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
  transition: background-color 0.3s ease, border-color 0.3s ease, width 0.2s;
  box-sizing: border-box;
}
.sidebar.collapsed {
  width: 56px;
}

.sidebar-header {
  padding: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: 500;
  flex: 1;
  min-width: 0;
}
.sidebar.collapsed .new-chat-btn span {
  display: none;
}
.collapse-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.collapse-btn:hover {
  background: var(--bg-hover);
}

.new-chat-btn:hover {
  background-color: var(--bg-surface);
  border-color: var(--text-tertiary);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  /* 强制显示滚动条，兼容主流浏览器 */
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}

/* 滚动条样式优化，兼容 Webkit 浏览器 */
.history-list::-webkit-scrollbar {
  width: 6px;
}
.history-list::-webkit-scrollbar-track {
  background: transparent;
}
.history-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 10px;
}
.history-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}


.empty-history {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.history-item {
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 6px;
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
  color: var(--text-primary);
}

.history-item:hover {
  background-color: var(--bg-hover);
}

.history-item.active {
  background-color: var(--bg-surface);
  font-weight: 500;
}

.delete-btn {
    display: none; /* Hidden by default */
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

.delete-btn:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
}

/* Footer Section */
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
    border-radius: 6px;
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
  gap: 8px;
  padding: 12px;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-color);
  border-top-color: var(--text-secondary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
