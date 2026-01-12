<template>
  <div class="chat-area">
    <div class="messages" ref="messagesContainer">
      <div class="messages-buffer"></div> <!-- Spacing at top -->
      <message-item 
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
      <div class="input-card" @dragover.prevent @drop="handleDrop">
        <textarea 
          v-model="inputContent" 
          @keydown="handleKeydown"
          @paste="handlePaste"
          placeholder="Send a message..."
          rows="1"
          ref="textarea"
          @input="autoResize"
        ></textarea>
          <input type="file" accept="image/*" ref="fileInput" style="display:none" @change="handleFileChange" multiple />
        <button class="image-btn no-border" @click.prevent="triggerFileInput" :disabled="isStreaming" title="上传图片">
          <!-- Plus icon -->
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
          <button @click="sendMessage" :disabled="isStreaming || (!inputContent.trim() && imageBase64List.length === 0)" class="send-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
          <div v-if="imageBase64List.length" class="image-preview-list">
            <div v-for="(img, idx) in imageBase64List" :key="idx" class="image-thumb-wrapper">
              <img :src="img" class="image-thumb" @click="previewImage(img)" />
              <span class="remove-thumb" @click="removeImage(idx)">&times;</span>
            </div>
          </div>
      </div>

    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import MessageItem from './MessageItem.vue'

export default {
  data() {
    return {
      localInput: '',
      imageBase64List: [] // 支持多图上传
    }
  },
  components: {
    MessageItem
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
      if (this.isStreaming || (!this.localInput.trim() && this.imageBase64List.length === 0)) return

      let userMsg
      if (this.imageBase64List.length === 0) {
        // 仅文本，content为字符串
        userMsg = { role: 'user', content: this.localInput.trim() }
      } else {
        // 多模态，content为list
        const multimodalContent = []
        if (this.localInput.trim()) {
          multimodalContent.push({ type: 'text', text: this.localInput.trim() })
        }
        for (const img of this.imageBase64List) {
          multimodalContent.push({ type: 'image_url', image_url: { url: img } })
        }
        userMsg = { role: 'user', content: multimodalContent }
      }
      let messages = this.$store.state.messages.slice()
      // 过滤掉最后一条assistant空消息（流式占位）
      if (messages.length && messages[messages.length-1].role === 'assistant' && !messages[messages.length-1].content) {
        messages = messages.slice(0, -1)
      }
      messages = [...messages, userMsg]
      this.$store.dispatch('sendMessage', messages)
      this.localInput = ''
      this.imageBase64List = []
      this.$nextTick(() => {
        this.autoResize()
      })
    },
    handleKeydown(e) {
      if (e.key === 'Enter') {
        if (e.shiftKey) {
          // 允许换行
          return
        } else {
          e.preventDefault()
          this.sendMessage()
        }
      }
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
    },
    async handlePaste(e) {
      const items = e.clipboardData && e.clipboardData.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          const imageUrl = await this.uploadImage(file)
          if (imageUrl) {
            this.imageBase64List.push(imageUrl)
          }
        }
      }
    },
    async uploadImage(file) {
      // 生成缩略图（最大120x120），返回base64
      return new Promise(resolve => {
        const reader = new FileReader()
        reader.onload = e => {
          const img = new window.Image()
          img.onload = () => {
            const canvas = document.createElement('canvas')
            const maxSize = 120
            let w = img.width, h = img.height
            if (w > h) {
              if (w > maxSize) {
                h = Math.round(h * maxSize / w)
                w = maxSize
              }
            } else {
              if (h > maxSize) {
                w = Math.round(w * maxSize / h)
                h = maxSize
              }
            }
            canvas.width = w
            canvas.height = h
            const ctx = canvas.getContext('2d')
            ctx.drawImage(img, 0, 0, w, h)
            resolve(canvas.toDataURL('image/jpeg', 0.8))
          }
          img.src = e.target.result
        }
        reader.readAsDataURL(file)
      })
    },
    insertAtCursor(text) {
      // 只插入文本，不再插入图片base64
      const textarea = this.$refs.textarea
      if (!textarea) return
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const value = this.inputContent
      this.inputContent = value.slice(0, start) + text + value.slice(end)
      this.$nextTick(() => {
        textarea.selectionStart = textarea.selectionEnd = start + text.length
        this.autoResize()
      })
    },
    triggerFileInput() {
      this.$refs.fileInput && this.$refs.fileInput.click()
    },
    async handleFileChange(e) {
      const files = e.target.files
      if (files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          const file = files[i]
          if (file.type.startsWith('image/')) {
            const imageUrl = await this.uploadImage(file)
            if (imageUrl) {
              this.imageBase64List.push(imageUrl)
            }
          }
        }
      }
      e.target.value = '' // 清空选择
    },
    async handleDrop(e) {
      const files = e.dataTransfer.files
      if (files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          const file = files[i]
          if (file.type.startsWith('image/')) {
            const imageUrl = await this.uploadImage(file)
            if (imageUrl) {
              this.imageBase64List.push(imageUrl)
            }
          }
        }
      }
    },

    removeImage(idx) {
      this.imageBase64List.splice(idx, 1)
    },
    previewImage(url) {
      window.open(url, '_blank')
    },
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
  height: 100%;
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
    height: 20px; /* Reduced since we have header now */
}

.bottom-spacer {
    height: 280px; /* Increased to ensure last assistant message is never obscured by the input box */
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

.image-btn.no-border {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
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
