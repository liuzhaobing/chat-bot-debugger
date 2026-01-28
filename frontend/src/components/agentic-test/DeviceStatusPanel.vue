<template>
  <div class="device-status-panel">
    <div class="panel-header">
      <h3>设备状态</h3>
      <button class="btn btn-outline btn-sm" @click="refreshDevices">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
          <path d="M21 3v5h-5"></path>
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
          <path d="M3 21v-5h5"></path>
        </svg>
        刷新
      </button>
    </div>

    <div class="device-list">
      <div 
        v-for="device in mockDevices" 
        :key="device.device_id"
        class="device-item"
        :class="{ online: device.status.power }"
      >
        <div class="device-header">
          <div class="device-icon">
            <svg v-if="device.device_type === '油烟机'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H5a2 2 0 0 0-2-2z"></path>
              <line x1="9" y1="9" x2="9" y2="15"></line>
              <line x1="15" y1="9" x2="15" y2="15"></line>
            </svg>
            <svg v-else-if="device.device_type === '空调'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 2v4"></path>
              <path d="M16 2v4"></path>
              <rect width="18" height="18" x="3" y="4" rx="2"></rect>
              <path d="M3 10h18"></path>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
          </div>
          <div class="device-info">
            <div class="device-name">{{ device.device_name }}</div>
            <div class="device-type">{{ device.device_type }}</div>
          </div>
          <div class="device-status" :class="{ online: device.status.power }">
            <div class="status-dot"></div>
          </div>
        </div>

        <div class="device-details" v-if="device.status.power">
          <div class="detail-grid">
            <div v-for="(value, key) in getDisplayStatus(device.status)" :key="key" class="detail-item">
              <span class="detail-label">{{ getStatusLabel(key) }}</span>
              <span class="detail-value">{{ formatStatusValue(key, value) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="device-offline">
          <span>设备离线</span>
        </div>
      </div>

      <div v-if="mockDevices.length === 0" class="empty-devices">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
          <path d="M2 17l10 5 10-5"></path>
          <path d="M2 12l10 5 10-5"></path>
        </svg>
        <p>暂无设备数据</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DeviceStatusPanel',
  data() {
    return {
      // 模拟设备数据
      mockDevices: [
        {
          device_id: 'hood_001',
          device_name: '厨房油烟机',
          device_type: '油烟机',
          status: {
            power: true,
            fan_speed: 3,
            light: true,
            temperature: 25
          }
        },
        {
          device_id: 'ac_001',
          device_name: '客厅空调',
          device_type: '空调',
          status: {
            power: false,
            temperature: 26,
            mode: 'cool'
          }
        },
        {
          device_id: 'tv_001',
          device_name: '客厅电视',
          device_type: '电视',
          status: {
            power: true,
            volume: 15,
            channel: 'CCTV-1'
          }
        }
      ]
    }
  },
  methods: {
    refreshDevices() {
      // TODO: 实际从API获取设备状态
      console.log('Refreshing device status...')
      
      // 模拟状态变化
      this.mockDevices.forEach(device => {
        if (Math.random() > 0.7) {
          if (device.device_type === '油烟机' && device.status.power) {
            device.status.fan_speed = Math.floor(Math.random() * 5) + 1
          } else if (device.device_type === '空调' && device.status.power) {
            device.status.temperature = Math.floor(Math.random() * 10) + 20
          }
        }
      })
    },
    
    getDisplayStatus(status) {
      // 过滤掉power字段，只显示其他状态
      // eslint-disable-next-line no-unused-vars
      const { power, ...displayStatus } = status
      return displayStatus
    },
    
    getStatusLabel(key) {
      const labels = {
        fan_speed: '风速',
        light: '照明',
        temperature: '温度',
        mode: '模式',
        volume: '音量',
        channel: '频道'
      }
      return labels[key] || key
    },
    
    formatStatusValue(key, value) {
      switch (key) {
        case 'temperature':
          return `${value}°C`
        case 'fan_speed':
          return `${value}档`
        case 'light':
          return value ? '开启' : '关闭'
        case 'mode': {
          const modes = { cool: '制冷', heat: '制热', auto: '自动' }
          return modes[value] || value
        }
        case 'volume':
          return `${value}%`
        default:
          return value
      }
    }
  },
  mounted() {
    // 定期刷新设备状态
    this.refreshInterval = setInterval(() => {
      if (Math.random() > 0.8) {
        this.refreshDevices()
      }
    }, 5000)
  },
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  }
}
</script>

<style scoped>
.device-status-panel {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  height: 400px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.device-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.device-item {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.device-item:last-child {
  margin-bottom: 0;
}

.device-item.online {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.02);
}

.device-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin-right: 12px;
}

.device-item.online .device-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-type {
  font-size: 12px;
  color: var(--text-tertiary);
}

.device-status {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  transition: background-color 0.3s ease;
}

.device-status.online .status-dot {
  background: #10b981;
}

.device-details {
  padding: 0 16px 12px 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
  padding-top: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.detail-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
}

.detail-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.device-offline {
  padding: 12px 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  border-top: 1px solid var(--border-color);
}

.empty-devices {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-devices svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-devices p {
  margin: 0;
  font-size: 14px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-sm {
  padding: 4px 8px;
  font-size: 11px;
}
</style>