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
