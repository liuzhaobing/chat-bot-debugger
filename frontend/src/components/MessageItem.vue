<template>
  <div class="message-item" :class="role">
    <div v-if="role === 'user'" class="user-message-content">
      <!-- 多模态：遍历content，text类型展示为气泡，image_url类型展示为缩略图，顺序与content一致 -->
      <template v-if="isMultimodal">
        <div v-for="(seg, idx) in content" :key="idx" style="width:100%">
          <span v-if="seg.type === 'text' && seg.text" class="user-text-bubble">{{ seg.text }}</span>
          <div v-else-if="seg.type === 'image_url' && seg.image_url && seg.image_url.url" class="image-thumb-wrapper" style="margin-top:8px;">
            <img :src="seg.image_url.url" class="user-image-thumb" @click="previewImage(seg.image_url.url)" />
          </div>
        </div>
      </template>
      <!-- 纯文本直接显示 -->
      <template v-else>
        <span class="user-text-bubble">{{ content }}</span>
      </template>
    </div>
    <div v-else class="assistant-message-content">
      <span>{{ content }}</span>
    </div>
    <div v-if="showPreview" class="image-modal" @click="showPreview = false">
      <img :src="previewUrl" class="modal-img" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'MessageItem',
  props: {
    role: {
      type: String,
      required: true
    },
    content: {
      type: [String, Array],
      required: true
    }
  },
  data() {
    return {
      showPreview: false,
      previewUrl: ''
    }
  },
  computed: {
    isMultimodal() {
      return Array.isArray(this.content)
    },
    firstText() {
      if (Array.isArray(this.content)) {
        const seg = this.content.find(s => s.type === 'text' && s.text)
        return seg ? seg.text : ''
      }
      return ''
    },
    imageThumbs() {
      if (Array.isArray(this.content)) {
        // 保持顺序，依次显示所有图片
        return this.content
          .filter(s => s.type === 'image_url' && s.image_url && s.image_url.url)
          .map(s => s.image_url.url)
      }
      return []
    },
    multimodalContent() {
      if (typeof this.content === 'string') {
        try {
          const obj = JSON.parse(this.content)
          if (obj && obj.content && Array.isArray(obj.content)) {
            return obj.content
          }
        } catch {
          // 不是JSON结构，直接返回纯文本
          return [{ type: 'text', text: this.content }]
        }
      } else if (Array.isArray(this.content)) {
        return this.content
      } else if (typeof this.content === 'object' && this.content && this.content.content && Array.isArray(this.content.content)) {
        return this.content.content
      }
      return []
    }
  },
  methods: {
    previewImage(url) {
      this.previewUrl = url
      this.showPreview = true
    }
  }
}
</script>

<style scoped>
.message-item {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.user-message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.user-text-bubble {
  background: #f2f2f2;
  border-radius: 12px;
  padding: 8px 14px;
  color: #222;
  display: inline-block;
  margin-bottom: 6px;
  max-width: 420px;
  word-break: break-word;
  font-size: 1rem;
}
.user-image-wrapper {
  margin-bottom: 6px;
}
.user-image-thumb {
  max-width: 120px;
  max-height: 120px;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  object-fit: cover;
}
.user-image-thumb:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.image-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.modal-img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 12px;
  background: #fff;
}
.assistant-message-content {
  background: #fff;
  border-radius: 12px;
  padding: 8px 14px;
  color: #222;
  display: inline-block;
  max-width: 420px;
  word-break: break-word;
  font-size: 1rem;
  margin-bottom: 6px;
}
</style>
<template>
  <div class="message-wrapper">
    <div class="message-container" :class="role">
      <div class="avatar-column">
        <div class="avatar" :class="role">
          <svg v-if="role === 'user'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>
        </div>
      </div>
      <div class="content-column">
        <div class="sender-name">{{ role === 'user' ? 'You' : 'Assistant' }}</div>
        <div class="markdown-body" v-html="renderedContent"></div>
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
      type: String,
      required: true
    }
  },
  computed: {
    renderedContent() {
      return md.render(this.content || '')
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
  min-width: 0; /* Prevent overflow */
}

.sender-name {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.markdown-body {
  color: var(--text-primary);
  line-height: 1.6;
  font-size: 1rem;
}

/* Deep Styles for Markdown Content */
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

.markdown-body :deep(ul), .markdown-body :deep(ol) {
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
</style>
