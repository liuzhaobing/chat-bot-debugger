<template>
  <div class="chat-area">
    <div class="messages" ref="messagesContainer">
      <div class="messages-buffer"></div> <!-- Spacing at top -->
      <MessageItem 
        v-for="(msg, index) in messages" 
        :key="index"
        :role="msg.role"
        :content="msg.content"
      />
      <div v-if="isStreaming && (!messages.length || messages[messages.length-1].role !== 'assistant')" class="status-message">
        <span class="typing-dot"></span>
        Thinking...
      </div>
      <div class="bottom-spacer"></div>
    </div>
    
    <div class="input-area-wrapper">
      <div class="input-card">
        <textarea 
          v-model="inputContent" 
          @keydown.enter.prevent="sendMessage"
          placeholder="Send a message..."
          rows="1"
          ref="textarea"
          @input="autoResize"
        ></textarea>
        <button @click="sendMessage" :disabled="isStreaming || !inputContent.trim()" class="send-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>

    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import MessageItem from './MessageItem.vue'

export default {
  name: 'ChatArea',
  components: {
    MessageItem
  },
  data() {
    return {
      localInput: ''
    }
  },
  computed: {
    ...mapState(['messages', 'isStreaming', 'inputMessage']),
    inputContent: {
      get() {
        return this.localInput
      },
      set(val) {
        this.localInput = val
      }
    }
  },
  watch: {
    messages() {
      this.scrollToBottom()
    }
  },
  methods: {
    sendMessage() {
      if (this.isStreaming || !this.localInput.trim()) return
      this.$store.dispatch('sendMessage', this.localInput)
      this.localInput = ''
      this.$nextTick(() => {
          this.autoResize()
      })
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
        }
      })
    },
    autoResize() {
        const el = this.$refs.textarea
        if(el) {
            el.style.height = 'auto'
            el.style.height = Math.min(el.scrollHeight, 200) + 'px'
        }
    }
  },
  mounted() {
      this.autoResize()
      this.scrollToBottom()
  }
}
</script>

<style scoped>
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
  position: relative;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.messages-buffer {
    height: 160px; /* Space for model selector with gradient (prevents first message blocking) */
}

.bottom-spacer {
    height: 220px; /* Space for input area with extra clearance */
}

.status-message {
    max-width: 48rem;
    margin: 0 auto;
    padding: 20px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
}

.typing-dot {
    width: 8px;
    height: 8px;
    background: var(--text-secondary);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { opacity: 0.4; }
    50% { opacity: 1; }
    100% { opacity: 0.4; }
}

.input-area-wrapper {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px;
  background: linear-gradient(180deg, transparent 0%, var(--bg-primary) 20%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 5;
}

.input-card {
  width: 100%;
  max-width: 48rem;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: flex-end;
  padding: 12px;
  gap: 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-card:focus-within {
    border-color: var(--text-tertiary);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  resize: none;
  max-height: 200px;
  padding: 4px;
  outline: none;
  min-height: 24px;
}

textarea::placeholder {
    color: var(--text-tertiary);
}

.send-btn {
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

.send-btn:hover:not(:disabled) {
  background: var(--bg-surface);
  color: var(--accent);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.footer-text {
    margin-top: 12px;
    font-size: 0.75rem;
    color: var(--text-tertiary);
    text-align: center;
}
</style>
