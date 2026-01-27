<template>
  <div class="audio-sphere-container">
    <div class="sphere-wrapper" :class="{ 'is-playing': isPlaying }">
      <canvas ref="sphereCanvas" class="sphere-canvas"></canvas>
      <div class="sphere-glow" :style="glowStyle"></div>
    </div>
    <div class="audio-info">
      <div class="status-text">{{ statusText }}</div>
      <div class="audio-metrics" v-if="showMetrics">
        <div class="metric">
          <span class="label">音调:</span>
          <span class="value">{{ Math.round(audioFeatures.pitch) }}Hz</span>
        </div>
        <div class="metric">
          <span class="label">音量:</span>
          <span class="value">{{ Math.round(audioFeatures.volume * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AudioVisualizationSphere',
  props: {
    isPlaying: {
      type: Boolean,
      default: false
    },
    audioType: {
      type: String,
      default: 'tts' // 'tts' | 'mic'
    },
    audioFeatures: {
      type: Object,
      default: () => ({
        pitch: 150,
        volume: 0.5,
        energy: 0.3
      })
    },
    statusText: {
      type: String,
      default: '等待中...'
    }
  },
  data() {
    return {
      canvas: null,
      ctx: null,
      animationId: null,
      particles: [],
      time: 0,
      showMetrics: false
    }
  },
  computed: {
    glowStyle() {
      const intensity = this.isPlaying ? this.audioFeatures.energy : 0.1
      const color = this.audioType === 'tts' ? '79, 70, 229' : '236, 72, 153'
      
      return {
        boxShadow: `0 0 ${20 + intensity * 40}px rgba(${color}, ${intensity})`,
        background: `radial-gradient(circle, rgba(${color}, ${intensity * 0.3}) 0%, transparent 70%)`
      }
    }
  },
  mounted() {
    this.initCanvas()
    this.initParticles()
    this.startAnimation()
  },
  beforeDestroy() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
    }
  },
  watch: {
    isPlaying(newVal) {
      if (newVal) {
        this.showMetrics = true
      } else {
        setTimeout(() => {
          this.showMetrics = false
        }, 2000)
      }
    }
  },
  methods: {
    initCanvas() {
      this.canvas = this.$refs.sphereCanvas
      this.ctx = this.canvas.getContext('2d')
      
      // 设置高DPI支持
      const dpr = window.devicePixelRatio || 1
      const rect = this.canvas.getBoundingClientRect()
      
      this.canvas.width = rect.width * dpr
      this.canvas.height = rect.height * dpr
      this.ctx.scale(dpr, dpr)
      
      this.canvas.style.width = rect.width + 'px'
      this.canvas.style.height = rect.height + 'px'
    },
    
    initParticles() {
      this.particles = []
      const particleCount = 50
      
      for (let i = 0; i < particleCount; i++) {
        this.particles.push({
          x: Math.random() * 200,
          y: Math.random() * 200,
          z: Math.random() * 200,
          originalX: Math.random() * 200,
          originalY: Math.random() * 200,
          originalZ: Math.random() * 200,
          size: Math.random() * 2 + 1,
          speed: Math.random() * 0.02 + 0.01
        })
      }
    },
    
    startAnimation() {
      const animate = () => {
        this.time += 0.016
        this.updateParticles()
        this.drawSphere()
        this.animationId = requestAnimationFrame(animate)
      }
      animate()
    },
    
    updateParticles() {
      const centerX = 100
      const centerY = 100
      const baseRadius = 60
      
      this.particles.forEach(particle => {
        // 音频响应的半径变化
        const audioResponse = this.isPlaying ? 
          1 + this.audioFeatures.energy * 0.5 + Math.sin(this.time * 10) * 0.1 : 1
        
        const radius = baseRadius * audioResponse
        
        // 球面坐标
        const phi = (particle.originalX / 200) * Math.PI * 2
        const theta = (particle.originalY / 200) * Math.PI
        
        // 音频频率影响粒子分布
        const pitchInfluence = this.isPlaying ? 
          Math.sin(this.time * (this.audioFeatures.pitch / 100)) * 0.2 : 0
        
        particle.x = centerX + Math.sin(theta) * Math.cos(phi + this.time * particle.speed) * radius
        particle.y = centerY + Math.cos(theta) * radius + pitchInfluence * 20
        particle.z = Math.sin(theta) * Math.sin(phi + this.time * particle.speed) * radius
      })
    },
    
    drawSphere() {
      const canvas = this.canvas
      const ctx = this.ctx
      
      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // 根据音频类型设置颜色
      const baseColor = this.audioType === 'tts' ? 
        [79, 70, 229] : [236, 72, 153] // 蓝色 vs 粉色
      
      // 绘制粒子
      this.particles.forEach(particle => {
        const alpha = this.isPlaying ? 
          0.6 + this.audioFeatures.volume * 0.4 : 0.3
        
        const size = particle.size * (this.isPlaying ? 
          1 + this.audioFeatures.energy * 0.5 : 1)
        
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${alpha})`
        ctx.fill()
        
        // 添加发光效果
        if (this.isPlaying) {
          ctx.beginPath()
          ctx.arc(particle.x, particle.y, size * 2, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${alpha * 0.2})`
          ctx.fill()
        }
      })
      
      // 绘制连接线
      if (this.isPlaying) {
        this.drawConnections(baseColor)
      }
    },
    
    drawConnections(color) {
      const ctx = this.ctx
      const maxDistance = 80
      
      for (let i = 0; i < this.particles.length; i++) {
        for (let j = i + 1; j < this.particles.length; j++) {
          const p1 = this.particles[i]
          const p2 = this.particles[j]
          
          const distance = Math.sqrt(
            Math.pow(p1.x - p2.x, 2) + 
            Math.pow(p1.y - p2.y, 2)
          )
          
          if (distance < maxDistance) {
            const alpha = (1 - distance / maxDistance) * 0.3 * this.audioFeatures.energy
            
            ctx.beginPath()
            ctx.moveTo(p1.x, p1.y)
            ctx.lineTo(p2.x, p2.y)
            ctx.strokeStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${alpha})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
    }
  }
}
</script>

<style scoped>
.audio-sphere-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.sphere-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.sphere-wrapper.is-playing {
  transform: scale(1.05);
}

.sphere-canvas {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.sphere-glow {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  border-radius: 50%;
  pointer-events: none;
  transition: all 0.3s ease;
}

.audio-info {
  text-align: center;
  min-height: 60px;
}

.status-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.audio-metrics {
  display: flex;
  gap: 24px;
  justify-content: center;
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.metric .label {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric .value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-blue);
}
</style>