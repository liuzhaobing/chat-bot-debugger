<template>
  <div
    class="avatar-3d"
    :class="[
      `size-${size}`,
      `character-index-${characterIndex}`,
      `character-${animationState}`
    ]"
  >
    <!-- 卡通角色容器 -->
    <div class="character-container" :style="characterContainerStyle">
      <!-- 角色主体 -->
      <div class="character-body">
        <!-- 紫色和黑色：圆形眼睛 + 高光 -->
        <template v-if="hasRoundEyes">
          <div class="round-eyes" :style="eyesContainerStyle">
            <div class="round-eye round-eye-left">
              <div class="pupil" :style="pupilStyle"></div>
              <div class="highlight"></div>
            </div>
            <div class="round-eye round-eye-right">
              <div class="pupil" :style="pupilStyle"></div>
              <div class="highlight"></div>
            </div>
          </div>
        </template>

        <!-- 橙色和黄色：圆点眼睛 -->
        <template v-else>
          <div class="dot-eyes" :style="eyesContainerStyle">
            <div class="dot-eye dot-eye-left"></div>
            <div class="dot-eye dot-eye-right"></div>
          </div>
        </template>

        <!-- 嘴巴 - 仅黄色角色有 -->
        <div class="mouth" v-if="showMouth"></div>
      </div>
    </div>
  </div>
</template>

<script>
import '@/styles/character.css'

export default {
  name: 'Avatar3D',
  props: {
    animationState: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'working', 'error'].includes(value)
    },
    characterIndex: {
      type: Number,
      default: 0,
      validator: (value) => value >= 0 && value <= 3
    },
    size: {
      type: String,
      default: 'normal',
      validator: (value) => ['small', 'normal', 'large', 'hero'].includes(value)
    }
  },
  data() {
    return {
      mouseX: 0.5,
      mouseY: 0.5,
      isIdle: true,
      mouseMoveTimer: null,
      mouseMoveHandler: null
    }
  },
  computed: {
    hasRoundEyes() {
      // 紫色(1)和黑色(2)使用圆形眼睛
      return this.characterIndex === 1 || this.characterIndex === 2
    },
    showMouth() {
      // 黄色(3)有嘴巴
      return this.characterIndex === 3
    },
    characterContainerStyle() {
      // 闲置动画
      if (this.animationState === 'idle' && this.isIdle) {
        const animations = [
          'character-sway',      // 橙色 - 左右摇摆
          'character-bounce',    // 紫色 - 上下浮动
          'character-breathe',   // 黑色 - 轻微缩放
          'character-hop'        // 黄色 - 弹动
        ]
        return {
          animation: `${animations[this.characterIndex]} 2s ease-in-out infinite`
        }
      }
      return {}
    },
    eyesContainerStyle() {
      if (this.animationState === 'error') {
        return { transform: 'translate(0, 0)' }
      }

      const maxOffset = this.size === 'hero' ? 6 : this.size === 'large' ? 5 : 3
      const offsetX = (this.mouseX - 0.5) * maxOffset * 2
      const offsetY = (this.mouseY - 0.5) * maxOffset * 2

      return {
        transform: `translate(${offsetX}px, ${offsetY}px)`
      }
    },
    pupilStyle() {
      const maxOffset = this.size === 'hero' ? 4 : this.size === 'large' ? 3 : 2
      const offsetX = (this.mouseX - 0.5) * maxOffset * 2
      const offsetY = (this.mouseY - 0.5) * maxOffset * 2

      return {
        transform: `translate(${offsetX}px, ${offsetY}px)`
      }
    }
  },
  mounted() {
    this.setupMouseTracking()
  },
  beforeDestroy() {
    this.cleanupMouseTracking()
  },
  methods: {
    setupMouseTracking() {
      this.mouseMoveHandler = (e) => {
        const rect = this.$el.getBoundingClientRect()
        const centerX = rect.left + rect.width / 2
        const centerY = rect.top + rect.height / 2

        this.mouseX = Math.max(0, Math.min(1, (e.clientX - centerX) / (rect.width / 2) + 0.5))
        this.mouseY = Math.max(0, Math.min(1, (e.clientY - centerY) / (rect.height / 2) + 0.5))

        this.isIdle = false
        clearTimeout(this.mouseMoveTimer)
        this.mouseMoveTimer = setTimeout(() => {
          this.isIdle = true
        }, 3000)
      }

      document.addEventListener('mousemove', this.mouseMoveHandler)
    },
    cleanupMouseTracking() {
      if (this.mouseMoveHandler) {
        document.removeEventListener('mousemove', this.mouseMoveHandler)
      }
      clearTimeout(this.mouseMoveTimer)
    }
  }
}
</script>

<style scoped>
.avatar-3d {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* 尺寸容器 */
.avatar-3d.size-small {
  width: 70px;
  height: auto;
}

.avatar-3d.size-normal {
  width: 200px;
  height: 350px;
}

.avatar-3d.size-large {
  width: 280px;
  height: 450px;
}

.avatar-3d.size-hero {
  width: 320px;
  height: 480px;
}

/* 角色容器 */
.character-container {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* Small 尺寸变体 */
.size-small.character-index-1 .character-body {
  width: 54px;
  height: 140px;
}

.size-small.character-index-2 .character-body {
  width: 51px;
  height: 120px;
}

.size-small.character-index-3 .character-body {
  width: 57px;
  height: 60px;
}

.size-small.character-index-3 .character-body::before {
  top: -26px;
  width: 57px;
  height: 30px;
  border-radius: 28px 28px 0 0;
}

.size-small.character-index-0 .character-body {
  width: 85px;
  height: 6px;
}

.size-small.character-index-0 .character-body::before {
  top: -40px;
  width: 85px;
  height: 44px;
  border-radius: 42px 42px 0 0;
}

.size-small .round-eye {
  width: 16px;
  height: 16px;
}

.size-small .pupil {
  width: 8px;
  height: 8px;
}

.size-small .highlight {
  width: 5px;
  height: 5px;
}

.size-small .dot-eye {
  width: 10px;
  height: 10px;
}

.size-small .mouth {
  height: 4px;
}

/* Small 尺寸眼睛位置覆盖 */
.size-small.character-index-0 .dot-eyes {
  top: -25px;
  gap: 20px;
}

.size-small.character-index-3 .dot-eyes {
  top: -16px;
  gap: 14px;
}

/* Normal 尺寸变体 */
.size-normal.character-index-1 .character-body {
  width: 108px;
  height: 280px;
}

.size-normal.character-index-2 .character-body {
  width: 102px;
  height: 240px;
}

.size-normal.character-index-3 .character-body {
  width: 114px;
  height: 120px;
}

.size-normal.character-index-3 .character-body::before {
  top: -55px;
  width: 114px;
  height: 59px;
  border-radius: 57px 57px 0 0;
}

.size-normal.character-index-0 .character-body {
  width: 170px;
  height: 12px;
}

.size-normal.character-index-0 .character-body::before {
  top: -83px;
  width: 170px;
  height: 87px;
  border-radius: 85px 85px 0 0;
}
</style>