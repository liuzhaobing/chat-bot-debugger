<template>
  <div class="employee-group" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- 4个角色的合照布局 -->
    <div class="group-container">
      <!-- 紫色方块 - 最高 -->
      <div
        class="character-wrapper character-purple"
        :style="getPositionStyle(1)"
        @click="selectCharacter(1)"
      >
        <div class="character-animation" :class="{ 'is-idle': isIdle }" :style="getAnimationStyle(1)">
          <!-- 悬停气泡 -->
          <div class="hover-bubble">选我</div>
          <div class="character-body">
            <!-- 圆形眼睛 + 高光 -->
            <div class="round-eyes" :style="getEyesContainerStyle()">
              <div class="round-eye round-eye-left">
                <div class="pupil" :style="getPupilStyle()"></div>
                <div class="highlight"></div>
              </div>
              <div class="round-eye round-eye-right">
                <div class="pupil" :style="getPupilStyle()"></div>
                <div class="highlight"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 黑色方块 - 次高 -->
      <div
        class="character-wrapper character-black"
        :style="getPositionStyle(2)"
        @click="selectCharacter(2)"
      >
        <div class="character-animation" :class="{ 'is-idle': isIdle }" :style="getAnimationStyle(2)">
          <!-- 悬停气泡 -->
          <div class="hover-bubble">选我</div>
          <div class="character-body">
            <!-- 圆形眼睛 + 高光 -->
            <div class="round-eyes" :style="getEyesContainerStyle()">
              <div class="round-eye round-eye-left">
                <div class="pupil" :style="getPupilStyle()"></div>
                <div class="highlight"></div>
              </div>
              <div class="round-eye round-eye-right">
                <div class="pupil" :style="getPupilStyle()"></div>
                <div class="highlight"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 橙色半圆 - 最矮胖 -->
      <div
        class="character-wrapper character-orange"
        :style="getPositionStyle(0)"
        @click="selectCharacter(0)"
      >
        <div class="character-animation" :class="{ 'is-idle': isIdle }" :style="getAnimationStyle(0)">
          <!-- 悬停气泡 -->
          <div class="hover-bubble">选我</div>
          <div class="character-body">
            <!-- 小圆点眼睛 -->
            <div class="dot-eyes" :style="getEyesContainerStyle()">
              <div class="dot-eye dot-eye-left"></div>
              <div class="dot-eye dot-eye-right"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 黄色圆角 - 第三 -->
      <div
        class="character-wrapper character-yellow"
        :style="getPositionStyle(3)"
        @click="selectCharacter(3)"
      >
        <div class="character-animation" :class="{ 'is-idle': isIdle }" :style="getAnimationStyle(3)">
          <!-- 悬停气泡 -->
          <div class="hover-bubble">选我</div>
          <div class="character-body">
            <!-- 小圆点眼睛 -->
            <div class="dot-eyes" :style="getEyesContainerStyle()">
              <div class="dot-eye dot-eye-left"></div>
              <div class="dot-eye dot-eye-right"></div>
            </div>
            <!-- 嘴巴 -->
            <div class="mouth"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import '@/styles/character.css'

export default {
  name: 'EmployeeGroup',
  data() {
    return {
      // 布局位置配置 - 紧凑排列，底部对齐
      positions: [
        { x: -55, z: 10 },    // 橙色 - 最前左，最矮
        { x: -75, z: -5 },    // 紫色 - 最后左，最高
        { x: 15, z: 0 },      // 黑色 - 中间，次高
        { x: 75, z: 8 }       // 黄色 - 最前右，第三
      ],
      mouseX: 0.5,
      mouseY: 0.5,
      isIdle: false,
      idleTimer: null
    }
  },
  mounted() {
    this.startIdleTimer()
  },
  beforeDestroy() {
    clearTimeout(this.idleTimer)
  },
  methods: {
    handleMouseMove(e) {
      const rect = this.$el.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2

      this.mouseX = Math.max(0, Math.min(1, (e.clientX - centerX) / (rect.width / 2) + 0.5))
      this.mouseY = Math.max(0, Math.min(1, (e.clientY - centerY) / (rect.height / 2) + 0.5))

      this.isIdle = false
      this.startIdleTimer()
    },
    handleMouseLeave() {
      this.mouseX = 0.5
      this.mouseY = 0.5
    },
    startIdleTimer() {
      clearTimeout(this.idleTimer)
      this.idleTimer = setTimeout(() => {
        this.isIdle = true
      }, 3000)
    },
    selectCharacter(index) {
      this.$emit('select', index)
    },
    getPositionStyle(index) {
      const pos = this.positions[index]
      return {
        transform: `translateX(${pos.x}px)`,
        zIndex: Math.round((pos.z + 10) * 10)
      }
    },
    getAnimationStyle(index) {
      const animations = ['sway', 'bounce', 'breathe', 'hop']
      if (this.isIdle) {
        return {
          animation: `character-${animations[index]} 2s ease-in-out infinite`,
          animationDelay: `${index * 0.3}s`
        }
      }
      return {}
    },
    getEyesContainerStyle() {
      const maxOffset = 4
      const offsetX = (this.mouseX - 0.5) * maxOffset * 2
      const offsetY = (this.mouseY - 0.5) * maxOffset * 2

      return {
        transform: `translate(${offsetX}px, ${offsetY}px)`
      }
    },
    getPupilStyle() {
      const maxOffset = 3
      const offsetX = (this.mouseX - 0.5) * maxOffset * 2
      const offsetY = (this.mouseY - 0.5) * maxOffset * 2

      return {
        transform: `translate(${offsetX}px, ${offsetY}px)`
      }
    }
  }
}
</script>

<style scoped>
.employee-group {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.group-container {
  position: relative;
  width: 480px;
  height: 320px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  /* 放大20% */
  transform: scale(1.2);
  transform-origin: center center;
}

.character-wrapper {
  position: absolute;
  cursor: pointer;
  /* 底部对齐 */
  bottom: 0;
}

.character-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

/* 悬停气泡 - 简洁现代风格 */
.hover-bubble {
  position: absolute;
  left: 50%;
  transform: translateX(-50%) scale(0.8);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  color: #374151;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  z-index: 10;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* 小尾巴 */
.hover-bubble::before {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid #f8f9fa;
}

/* 不同角色的气泡位置 - 都放在角色头顶上方，避免遮挡 */
.character-purple .hover-bubble {
  top: -45px;
}

.character-black .hover-bubble {
  top: -45px;
}

.character-orange .hover-bubble {
  top: -125px;
}

.character-yellow .hover-bubble {
  top: -95px;
}

.character-wrapper:hover .hover-bubble {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

/* 响应式 */
@media (max-width: 600px) {
  .group-container {
    transform: scale(0.9);
  }
}
</style>