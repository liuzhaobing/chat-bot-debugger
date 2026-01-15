<template>
  <div class="message-wrapper">
    <div class="message-container" :class="role">
      <!-- 头像列 -->
      <div class="avatar-column">
        <div class="avatar" :class="role">
          <svg v-if="role === 'user'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2"></rect>
            <circle cx="12" cy="5" r="2"></circle>
            <path d="M12 7v4"></path>
            <line x1="8" y1="16" x2="8" y2="16"></line>
            <line x1="16" y1="16" x2="16" y2="16"></line>
          </svg>
        </div>
      </div>

      <!-- 内容列 -->
      <div class="content-column">
        <div class="sender-name">{{ role === 'user' ? 'You' : 'Assistant' }}</div>
        
        <!-- 深度思考区域 (仅 assistant 且有 reasoningContent 时显示) -->
        <div v-if="role === 'assistant' && reasoningContent" class="thinking-section">
          <div class="thinking-header" @click="toggleThinking">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <span>已思考 (用时 {{ thinkingTime }}秒)</span>
            <svg 
              class="collapse-icon" 
              :class="{ expanded: isThinkingExpanded }"
              xmlns="http://www.w3.org/2000/svg" 
              width="14" 
              height="14" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
          <div v-show="isThinkingExpanded" class="thinking-content">
            {{ reasoningContent }}
          </div>
        </div>

        <!-- 最终回答内容 -->
        <div class="markdown-body" v-html="renderedContent" @click="handleImageClick"></div>

        <!-- Token 统计 (仅 assistant 且有 tokenUsage) -->
        <div v-if="role === 'assistant' && tokenUsage" class="token-usage">
          <span class="usage-item">
            <span class="usage-label">Prompt tokens:</span>
            <span class="usage-value">{{ tokenUsage.prompt_tokens }}</span>
          </span>
          <span class="usage-item">
            <span class="usage-label">Completion tokens:</span>
            <span class="usage-value">{{ tokenUsage.completion_tokens }}</span>
          </span>
          <span class="usage-item">
            <span class="usage-label">Total tokens:</span>
            <span class="usage-value">{{ tokenUsage.total_tokens }}</span>
          </span>
        </div>

        <!-- 操作按钮 (复制 消息) -->
        <div class="message-actions">
          <button @click="copyContent" class="action-btn" title="复制">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`;
      } catch (__) {
        // eslint-disable-next-line
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  }
});

export default {
  name: 'MessageItem',
  props: {
    role: {
      type: String,
      required: true
    },
    content: {
      type: [String, Array],  // 支持字符串或数组（多模态）
      required: true
    },
    reasoningContent: {
      type: String,
      default: ''
    },
    tokenUsage: {
      type: Object,
      default: null
    },
    messageId: {
      type: Number,
      default: null
    }
  },
  data() {
    return {
      isThinkingExpanded: false  // 默认折叠
    }
  },
  computed: {
    renderedContent() {
      // 处理多模态内容
      if (Array.isArray(this.content)) {
        let htmlParts = []
        for (const item of this.content) {
          if (item.type === 'text') {
            htmlParts.push(md.render(item.text || ''))
          } else if (item.type === 'image_url') {
            const imageUrl = item.image_url?.url || ''
            if (imageUrl) {
              // 用户消息中的图片显示为缩略图样式
              htmlParts.push(`<div class="message-image-wrapper"><img src="${imageUrl}" class="message-image-thumbnail" alt="User uploaded image" /></div>`)
            }
          }
        }
        return htmlParts.join('')
      }
      // 处理纯文本内容
      return md.render(this.content || '')
    },
    thinkingTime() {
      // 简单估算：每 100 字符约 1 秒
      if (this.reasoningContent) {
        return Math.max(1, Math.round(this.reasoningContent.length / 100))
      }
      return 0
    }
  },
  methods: {
    toggleThinking() {
      this.isThinkingExpanded = !this.isThinkingExpanded
    },
    handleImageClick(e) {
      // 点击图片时放大显示
      if (e.target.classList.contains('message-image-thumbnail')) {
        const imageUrl = e.target.src
        this.$emit('preview-image', imageUrl)
      }
    },
    copyContent() {
      // 提取纯文本内容用于复制
      let textContent = ''
      if (Array.isArray(this.content)) {
        for (const item of this.content) {
          if (item.type === 'text') {
            textContent += item.text || ''
          }
        }
      } else {
        textContent = this.content
      }
      
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textContent).then(() => {
          if (window.$message) {
            window.$message.success('已复制到剪贴板')
          } else {
            alert('已复制到剪贴板')
          }
        }).catch(() => {
          this.fallbackCopy(textContent)
        })
      } else {
        this.fallbackCopy(textContent)
      }
    },
    fallbackCopy(text) {
      // 降级方案
      const textarea = document.createElement('textarea')
      textarea.value = text || this.content
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        if (window.$message) {
          window.$message.success('已复制到剪贴板')
        } else {
          alert('已复制到剪贴板')
        }
      } catch (err) {
        console.error('复制失败:', err)
      }
      document.body.removeChild(textarea)
    }
  }
}
</script>

<style scoped>
.message-wrapper {
  padding: 24px 20px;
  width: 100%;
}

.message-container {
  max-width: 48rem;
  margin: 0 auto;
  display: flex;
  gap: 16px;
}

.avatar-column {
  flex-shrink: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar.user {
  background-color: var(--bg-surface);
  color: var(--text-secondary);
}

.avatar.assistant {
  background-color: var(--accent-green);
  color: #fff;
}

.content-column {
  flex: 1;
  min-width: 0;
}

.sender-name {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

/* 深度思考区域样式 - 参考 DeepSeek 官网 */
.thinking-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #0369a1;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.thinking-header:hover {
  background-color: rgba(186, 230, 253, 0.3);
}

.collapse-icon {
  margin-left: auto;
  transition: transform 0.2s;
}

.collapse-icon.expanded {
  transform: rotate(180deg);
}

.thinking-content {
  padding: 8px 12px 12px 12px;
  font-size: 0.85rem;
  line-height: 1.6;
  color: #0c4a6e;
  white-space: pre-wrap;
  word-break: break-word;
  border-top: 1px solid #bae6fd;
  background: rgba(255, 255, 255, 0.5);
}

/* Token 统计样式 */
.token-usage {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0;
  margin-top: 8px;
  font-size: 0.75rem;
  color: #64748b;
  border-top: 1px solid #f1f5f9;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.usage-label {
  color: #94a3b8;
}

.usage-value {
  font-weight: 600;
  color: #475569;
}

/* 操作按钮样式 */
.message-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-container:hover .message-actions {
  opacity: 1;
}

.action-btn {
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #475569;
}

.action-btn:active {
  transform: scale(0.95);
}

/* Markdown 内容样式 */
.markdown-body {
  color: var(--text-primary);
  line-height: 1.6;
  font-size: 1rem;
}

.markdown-body :deep(h1), 
.markdown-body :deep(h2), 
.markdown-body :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-body :deep(p) {
  margin-bottom: 1em;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul), 
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 1em;
}

.markdown-body :deep(pre) {
  background: #0d0d0d;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 10px 0;
  border: 1px solid var(--border-color);
}

.markdown-body :deep(code) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(:not(pre) > code) {
  background: rgba(255,255,255,0.1);
  padding: 2px 4px;
  border-radius: 4px;
}

/* 多模态消息中的图片样式 */
.message-image-wrapper {
  margin: 12px 0;
  display: inline-block;
}

/* 缩略图样式 - 正方形，类似上传预览 */
.markdown-body :deep(.message-image-thumbnail) {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: block;
}

.markdown-body :deep(.message-image-thumbnail:hover) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 保留原有的大图样式，以防需要 */
.message-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: transform 0.2s;
}

.message-image:hover {
  transform: scale(1.02);
}
</style>
