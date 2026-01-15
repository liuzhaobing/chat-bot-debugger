<template>
  <div class="chat-area">
    <!-- 消息区域 -->
    <div class="messages" ref="messagesContainer">
      <div class="messages-buffer"></div>
      <message-item 
        v-for="(msg, index) in messages" 
        :key="index"
        :role="msg.role"
        :content="msg.content"
        :reasoning-content="msg.reasoning_content"
        :token-usage="msg.usage"
        @preview-image="previewImage"
      />
      <div v-if="isStreaming && (!messages.length || messages[messages.length-1].role !== 'assistant')" class="status-message">
        <span class="typing-dot"></span>
        Thinking...
      </div>
    </div>
    
    <!-- 输入区域 -->
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
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <button @click="sendMessage" :disabled="isStreaming || (!inputContent.trim() && imageBase64List.length === 0)" class="send-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
        <div v-if="imageBase64List.length" class="image-preview-list">
          <div v-for="(img, idx) in imageBase64List" :key="idx" class="image-thumb-wrapper">
            <img :src="img.thumbnail" class="image-thumb" @click="previewImage(img.full)" />
            <span class="remove-thumb" @click="removeImage(idx)">&times;</span>
          </div>
        </div>
      </div>
    </div>
    
    <image-preview-modal 
      :visible="previewVisible" 
      :imageUrl="previewImageUrl"
      @close="closePreview"
    />
  </div>
</template>

<script>
import { mapState } from 'vuex'
import MessageItem from './MessageItem.vue'
import ImagePreviewModal from './ImagePreviewModal.vue'

export default {
  data() {
    return {
      localInput: '',
      imageBase64List: [], // 支持多图上传，每个元素为 { thumbnail, full }
      previewVisible: false,
      previewImageUrl: ''
    }
  },
  components: {
    MessageItem,
    ImagePreviewModal
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
          // 发送完整图片给模型，但在前端显示时使用缩略图
          multimodalContent.push({ type: 'image_url', image_url: { url: img.full } })
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
      // 生成两个版本：缩略图用于预览，原图用于发送给模型
      return new Promise(resolve => {
        const reader = new FileReader()
        reader.onload = e => {
          const img = new window.Image()
          img.onload = () => {
            // 生成缩略图（最大120x120）用于预览
            const thumbCanvas = document.createElement('canvas')
            const thumbMaxSize = 120
            let thumbW = img.width, thumbH = img.height
            if (thumbW > thumbH) {
              if (thumbW > thumbMaxSize) {
                thumbH = Math.round(thumbH * thumbMaxSize / thumbW)
                thumbW = thumbMaxSize
              }
            } else {
              if (thumbH > thumbMaxSize) {
                thumbW = Math.round(thumbW * thumbMaxSize / thumbH)
                thumbH = thumbMaxSize
              }
            }
            thumbCanvas.width = thumbW
            thumbCanvas.height = thumbH
            const thumbCtx = thumbCanvas.getContext('2d')
            thumbCtx.drawImage(img, 0, 0, thumbW, thumbH)
            const thumbnailBase64 = thumbCanvas.toDataURL('image/jpeg', 0.8)
            
            // 生成高质量图片用于发送给模型（最大1024px，保持高质量）
            const fullCanvas = document.createElement('canvas')
            const maxSize = 1024
            let w = img.width, h = img.height
            if (w > maxSize || h > maxSize) {
              if (w > h) {
                h = Math.round(h * maxSize / w)
                w = maxSize
              } else {
                w = Math.round(w * maxSize / h)
                h = maxSize
              }
            }
            fullCanvas.width = w
            fullCanvas.height = h
            const ctx = fullCanvas.getContext('2d')
            ctx.drawImage(img, 0, 0, w, h)
            const fullBase64 = fullCanvas.toDataURL('image/jpeg', 0.95)
            
            // 返回包含缩略图和完整图的对象
            resolve({
              thumbnail: thumbnailBase64,
              full: fullBase64
            })
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
      this.previewImageUrl = url
      this.previewVisible = true
    },
    closePreview() {
      this.previewVisible = false
      this.previewImageUrl = ''
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
  background-color: #f8fafc;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.messages-buffer {
  height: 20px;
  flex-shrink: 0;
}

.status-message {
  max-width: 48rem;
  margin: 0 auto;
  padding: 20px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: #94a3b8;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}

.input-area-wrapper {
  flex-shrink: 0;
  padding: 20px 24px 24px;
  background: linear-gradient(180deg, transparent 0%, #f8fafc 30%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-card {
  width: 100%;
  max-width: 48rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: flex-end;
  padding: 12px;
  gap: 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
}

.input-card:focus-within {
  border-color: #6366f1;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #1e293b;
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
  color: #94a3b8;
}

.image-btn {
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

.image-btn.no-border {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

.image-btn:hover:not(:disabled) {
  background: #f1f5f9;
  color: #4f46e5;
}

.image-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-btn {
  background-color: #4f46e5;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background-color: #4338ca;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.image-preview-list {
  position: absolute;
  bottom: 100%;
  left: 12px;
  right: 12px;
  margin-bottom: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.image-thumb-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.remove-thumb {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: background 0.2s;
}

.remove-thumb:hover {
  background: rgba(239, 68, 68, 0.9);
}

.footer-text {
  margin-top: 12px;
  font-size: 0.75rem;
  color: #94a3b8;
  text-align: center;
}

.empty-history {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}
</style>
