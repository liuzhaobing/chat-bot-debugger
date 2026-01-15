<template>
  <nav class="main-sidebar">
    <div class="logo-container">
      <div class="logo-box">
        <!-- SVG 标志，保持简洁且色彩协调 -->
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="logo-icon"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
      </div>
    </div>
    
    <div class="nav-items">
      <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }" title="模型广场">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
        <span class="nav-text">模型广场</span>
      </router-link>

      <router-link to="/apps" class="nav-item" :class="{ active: $route.path.startsWith('/apps') }" title="应用广场">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
        <span class="nav-text">应用广场</span>
      </router-link>
      
      <router-link to="/chat" class="nav-item" :class="{ active: $route.path === '/chat' }" title="文本对话">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        <span class="nav-text">文本对话</span>
      </router-link>

      <router-link to="/voice-call" class="nav-item" :class="{ active: $route.path === '/voice-call' }" title="电话客服">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
        <span class="nav-text">电话客服</span>
      </router-link>
    </div>

    <div class="sidebar-footer">
      <div class="user-avatar" title="User Profile">
        <div class="avatar-placeholder">U</div>
      </div>
    </div>
  </nav>
</template>

<script>
/**
 * MainSidebar 组件
 * 提供核心导航功能：模型广场与文本对话
 */
export default {
  name: 'MainSidebar'
}
</script>

<style scoped>
.main-sidebar {
  width: 80px;
  background: linear-gradient(180deg, #4f46e5 0%, #1e1b4b 100%); /* 渐变深紫色背景 */
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
  flex-shrink: 0;
  z-index: 1000;
  box-shadow: 4px 0 10px rgba(0, 0, 0, 0.1);
}

.logo-container {
  margin-bottom: 40px;
}

.logo-box {
  width: 48px;
  height: 48px;
  background: #ffffff;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4f46e5;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
  transition: transform 0.3s ease;
}

.logo-box:hover {
  transform: rotate(5deg) scale(1.05);
}

.nav-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  align-items: center;
}

.nav-item {
  width: 56px;
  height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  gap: 4px;
}

.nav-item svg {
  transition: transform 0.3s ease;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.nav-item:hover svg {
  transform: translateY(-2px);
}

.nav-item.active {
  background-color: #ffffff; /* 激活状态背景反白 */
  color: #4f46e5; /* 激活状态图标深蓝 */
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.nav-text {
  font-size: 10px;
  font-weight: 500;
  opacity: 0.8;
}

.sidebar-footer {
  margin-top: auto;
  padding-bottom: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.user-avatar:hover {
  border-color: #ffffff;
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.avatar-placeholder {
  color: #ffffff;
  font-weight: 700;
  font-size: 1.1rem;
}
</style>
