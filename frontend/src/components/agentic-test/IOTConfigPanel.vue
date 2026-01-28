<template>
  <div class="iot-device-panel">
    <!-- IOT配置区域 -->
    <div v-if="!hideConfig" class="config-section">
      <div class="section-header">
        <h3>IOT 配置</h3>
        <button 
          class="btn-icon"
          @click="showConfig = !showConfig"
          :title="showConfig ? '收起配置' : '展开配置'"
        >
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            stroke-width="2"
            :style="{ transform: showConfig ? 'rotate(180deg)' : 'rotate(0deg)' }"
          >
            <polyline points="6,9 12,15 18,9"></polyline>
          </svg>
        </button>
      </div>

      <div v-if="showConfig" class="config-content">
        <div class="config-form">
          <div class="form-row">
            <div class="form-group">
              <label>环境选择</label>
              <select 
                v-model="localEnv"
                @change="saveConfig"
              >
                <option value="test">测试环境 (api-test.myroki.com)</option>
                <option value="prod">生产环境 (api.myroki.com)</option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>IOT Token</label>
              <input 
                v-model="localIotToken"
                type="password"
                placeholder="请输入IOT认证Token..."
                @blur="saveConfig"
              />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Family ID</label>
              <input 
                v-model="localFamilyId"
                type="text"
                placeholder="请输入家庭ID..."
                @blur="saveConfig"
              />
            </div>
          </div>
        </div>
        
        <div class="config-status">
          <div class="status-item" :class="{ valid: isEnvValid }">
            <div class="status-indicator"></div>
            <span>环境: {{ envDisplayName }}</span>
          </div>
          <div class="status-item" :class="{ valid: isTokenValid }">
            <div class="status-indicator"></div>
            <span>Token: {{ isTokenValid ? '已配置' : '未配置' }}</span>
          </div>
          <div class="status-item" :class="{ valid: isFamilyIdValid }">
            <div class="status-indicator"></div>
            <span>Family ID: {{ isFamilyIdValid ? '已配置' : '未配置' }}</span>
          </div>
        </div>
        
        <div class="config-actions">
          <button 
            class="btn btn-outline btn-sm"
            @click="testConnection"
            :disabled="!isConfigValid || isTestingConnection"
          >
            <svg v-if="isTestingConnection" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
            {{ isTestingConnection ? '测试中...' : '测试连接' }}
          </button>
          
          <button 
            class="btn btn-outline btn-sm"
            @click="clearConfig"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"></polyline>
              <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
            </svg>
            清空配置
          </button>
          
          <button 
            class="btn btn-primary btn-sm"
            @click="loadDevices"
            :disabled="!isConfigValid || isLoadingDevices"
          >
            <svg v-if="isLoadingDevices" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
              <path d="M21 3v5h-5"></path>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
              <path d="M3 21v-5h5"></path>
            </svg>
            {{ isLoadingDevices ? '加载中...' : '加载设备' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 设备状态区域 -->
    <div class="devices-section">
      <div class="section-header">
        <h3>智能设备 ({{ devices.length }})</h3>
        <div class="header-actions">
          <span v-if="isDataFromCache" class="cache-indicator" :title="getCacheInfo()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4"></path>
              <path d="m16.2 7.8 2.9-2.9"></path>
              <path d="M18 12h4"></path>
              <path d="m16.2 16.2 2.9 2.9"></path>
              <path d="M12 18v4"></path>
              <path d="m4.9 19.1 2.9-2.9"></path>
              <path d="M2 12h4"></path>
              <path d="m4.9 4.9 2.9 2.9"></path>
            </svg>
            缓存
          </span>
          <button 
            v-if="hasRefreshingDevices"
            class="btn btn-outline btn-sm"
            @click="resetAllRefreshingStates"
            title="重置所有设备刷新状态"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c0-1 1-2 2-2v2"></path>
            </svg>
            重置
          </button>
          <button 
            class="btn btn-outline btn-sm"
            @click="refreshDevices"
            :disabled="!isConfigValid || isRefreshing"
          >
            <svg 
              v-if="isRefreshing" 
              width="14" 
              height="14" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
              class="spin"
            >
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
              <path d="M21 3v5h-5"></path>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
              <path d="M3 21v-5h5"></path>
            </svg>
            刷新
          </button>
        </div>
      </div>

      <div class="devices-content">
        <div v-if="devices.length === 0 && !isLoadingDevices" class="empty-devices">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
          <p>{{ isConfigValid ? '点击"加载设备"获取设备列表' : '请先完成IOT配置' }}</p>
        </div>

        <div v-else-if="isLoadingDevices" class="loading-devices">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          <p>正在加载设备...</p>
        </div>

        <div v-else class="device-grid">
          <div 
            v-for="device in devices" 
            :key="device.deviceId"
            class="device-card"
            :class="{ 
              online: device.netState === 1 || device.status === 1,
              offline: device.netState === 0 && device.status !== 1
            }"
          >
            <!-- 设备头部 -->
            <div class="device-header">
              <div class="device-main-info">
                <div class="device-icon">
                  <!-- 品类图标 -->
                  <svg v-if="device.categoryName === '油烟机'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="8" width="20" height="4" rx="1"></rect>
                    <path d="M6 8V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2"></path>
                    <path d="M12 12v8"></path>
                    <path d="M8 16h8"></path>
                  </svg>
                  <!-- 燃气灶图标 -->
                  <svg v-else-if="device.categoryName === '灶具'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="8" cy="12" r="3"></circle>
                    <circle cx="16" cy="12" r="3"></circle>
                    <rect x="2" y="8" width="20" height="8" rx="2"></rect>
                    <path d="M8 9v6"></path>
                    <path d="M16 9v6"></path>
                  </svg>
                  <!-- 一体机/烤箱图标 -->
                  <svg v-else-if="device.categoryName === '一体机'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="6" width="18" height="12" rx="2"></rect>
                    <circle cx="7" cy="10" r="1"></circle>
                    <circle cx="7" cy="14" r="1"></circle>
                    <rect x="10" y="9" width="8" height="6" rx="1"></rect>
                  </svg>
                  <!-- 智能音箱图标 -->
                  <svg v-else-if="device.categoryName === '智能烹饪音箱'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="22"></line>
                  </svg>
                  <!-- 自动翻炒锅图标 -->
                  <svg v-else-if="device.categoryName === '自动翻炒锅'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M8 2h8l2 2v4l-2 2H8L6 8V4l2-2z"></path>
                    <path d="M6 10v4a4 4 0 0 0 4 4h4a4 4 0 0 0 4-4v-4"></path>
                    <path d="M12 18v4"></path>
                    <path d="M8 22h8"></path>
                    <circle cx="12" cy="12" r="2"></circle>
                  </svg>
                  <!-- 默认设备图标 -->
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                  </svg>
                </div>
                
                <!-- 设备信息 -->
                <div class="device-info">
                  <h3 class="device-name" :title="getDeviceDisplayName(device)">
                    {{ getDeviceDisplayName(device) }}
                  </h3>
                  <div class="device-meta">
                    <span class="device-category">{{ device.categoryName }}</span>
                  </div>
                </div>
              </div>
              
              <div class="device-status-actions">
                <div class="device-status-dot" :class="{ online: device.netState === 1 || device.status === 1 }"></div>
                <button 
                  class="device-refresh-btn"
                  :class="{ refreshing: device.isRefreshing }"
                  @click="refreshSingleDevice(device)"
                  :disabled="!isConfigValid || device.isRefreshing"
                  :title="device.isRefreshing ? '刷新中...' : '刷新设备状态'"
                >
                  <svg 
                    v-if="device.isRefreshing" 
                    width="14" 
                    height="14" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    stroke-width="2"
                    class="spin"
                  >
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                    <path d="M21 3v5h-5"></path>
                    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                    <path d="M3 21v-5h5"></path>
                  </svg>
                </button>
              </div>
            </div>

            <!-- 设备属性 -->
            <div v-if="device.properties && Object.keys(device.properties).length > 0" class="device-properties">
              <div class="properties-header">
                <span>设备状态</span>
              </div>
              <div class="properties-grid">
                <div 
                  v-for="(value, key) in getDisplayProperties(device)" 
                  :key="key" 
                  class="property-item"
                  :class="{ active: isPropertyActive(key, value) }"
                >
                  <div class="property-label">{{ getPropertyLabel(key) }}</div>
                  <div class="property-value">{{ formatPropertyValue(key, value) }}</div>
                </div>
              </div>
            </div>

            <!-- 离线状态 -->
            <div v-else-if="device.netState === 0 && device.status !== 1" class="device-offline">
              <div class="offline-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                  <line x1="12" y1="9" x2="12" y2="13"></line>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </div>
              <span>设备离线，无法获取状态信息</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'IOTConfigPanel',
  props: {
    hideConfig: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showConfig: false,
      localIotToken: '',
      localFamilyId: '',
      localEnv: 'test',
      isTestingConnection: false,
      isLoadingDevices: false,
      isRefreshing: false,
      devices: [],
      isDataFromCache: false
    }
  },
  computed: {
    ...mapState('agenticTest', [
      'iotConfig'
    ]),
    
    isEnvValid() {
      return this.localEnv && ['test', 'prod'].includes(this.localEnv)
    },
    
    envDisplayName() {
      return this.localEnv === 'prod' ? '生产环境' : '测试环境'
    },
    
    isTokenValid() {
      return this.localIotToken && this.localIotToken.trim().length > 0
    },
    
    isFamilyIdValid() {
      return this.localFamilyId && this.localFamilyId.trim().length > 0
    },
    
    isConfigValid() {
      return this.isEnvValid && this.isTokenValid && this.isFamilyIdValid
    },
    
    hasRefreshingDevices() {
      return this.devices.some(device => device.isRefreshing)
    }
  },
  mounted() {
    this.loadConfig()
    this.loadDevicesFromCache()
    // 重置所有设备的刷新状态，防止缓存中的异常状态
    this.$nextTick(() => {
      this.resetAllRefreshingStates()
    })
  },
  methods: {
    // 安全地更新IOT配置到store
    updateIOTConfig(config) {
      // 如果store中有updateIOTConfig action，则调用它
      if (this.$store && this.$store.dispatch) {
        try {
          this.$store.dispatch('agenticTest/updateIOTConfig', config)
        } catch (error) {
          // 如果store不存在或action不存在，忽略错误
          console.debug('Store updateIOTConfig not available:', error)
        }
      }
    },
    
    // 从localStorage加载设备缓存
    loadDevicesFromCache() {
      try {
        const cachedDevices = localStorage.getItem('iot-devices')
        const cacheTimestamp = localStorage.getItem('iot-devices-timestamp')
        
        if (cachedDevices && cacheTimestamp) {
          const now = Date.now()
          const cacheAge = now - parseInt(cacheTimestamp)
          
          // 缓存有效期：5分钟
          if (cacheAge < 5 * 60 * 1000) {
            const devices = JSON.parse(cachedDevices)
            // 确保所有设备都没有刷新状态
            this.devices = devices.map(device => ({
              ...device,
              isRefreshing: false // 重置刷新状态
            }))
            this.isDataFromCache = true
            console.log('从缓存加载设备列表:', this.devices.length, '个设备')
          } else {
            // 缓存过期，清除
            this.clearDevicesCache()
          }
        }
      } catch (error) {
        console.warn('加载设备缓存失败:', error)
        this.clearDevicesCache()
      }
    },
    
    // 保存设备到localStorage
    saveDevicesToCache(devices) {
      try {
        // 清理临时状态后再保存
        const cleanDevices = devices.map(device => {
          // eslint-disable-next-line no-unused-vars
          const { isRefreshing, ...cleanDevice } = device
          return cleanDevice
        })
        localStorage.setItem('iot-devices', JSON.stringify(cleanDevices))
        localStorage.setItem('iot-devices-timestamp', Date.now().toString())
        console.log('设备列表已缓存:', cleanDevices.length, '个设备')
      } catch (error) {
        console.warn('保存设备缓存失败:', error)
      }
    },
    
    // 清除设备缓存
    clearDevicesCache() {
      localStorage.removeItem('iot-devices')
      localStorage.removeItem('iot-devices-timestamp')
    },
    
    // 重置所有设备的刷新状态
    resetAllRefreshingStates() {
      this.devices.forEach(device => {
        if (device.isRefreshing) {
          this.$set(device, 'isRefreshing', false)
        }
      })
    },
    
    loadConfig() {
      // 从localStorage加载配置
      const savedToken = localStorage.getItem('iot-token')
      const savedFamilyId = localStorage.getItem('family-id')
      const savedEnv = localStorage.getItem('iot-env')
      
      if (savedToken) {
        this.localIotToken = savedToken
      }
      
      if (savedFamilyId) {
        this.localFamilyId = savedFamilyId
      }
      
      if (savedEnv && ['test', 'prod'].includes(savedEnv)) {
        this.localEnv = savedEnv
      }
      
      // 同步到store（如果需要的话）
      this.updateIOTConfig({
        token: this.localIotToken,
        familyId: this.localFamilyId,
        env: this.localEnv
      })
    },
    
    saveConfig() {
      // 保存到localStorage
      if (this.localIotToken.trim()) {
        localStorage.setItem('iot-token', this.localIotToken.trim())
      } else {
        localStorage.removeItem('iot-token')
      }
      
      if (this.localFamilyId.trim()) {
        localStorage.setItem('family-id', this.localFamilyId.trim())
      } else {
        localStorage.removeItem('family-id')
      }
      
      if (this.localEnv && ['test', 'prod'].includes(this.localEnv)) {
        localStorage.setItem('iot-env', this.localEnv)
      } else {
        localStorage.removeItem('iot-env')
      }
      
      // 同步到store（如果需要的话）
      this.updateIOTConfig({
        token: this.localIotToken.trim(),
        familyId: this.localFamilyId.trim(),
        env: this.localEnv
      })
    },
    
    async testConnection() {
      if (!this.isConfigValid) return
      
      this.isTestingConnection = true
      
      try {
        const response = await fetch('/api/agentic-test/iot/test-connection/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            iot_token: this.localIotToken.trim(),
            family_id: this.localFamilyId.trim(),
            env: this.localEnv
          })
        })
        
        const result = await response.json()
        
        if (response.ok && result.success) {
          this.$message?.success(`IOT连接测试成功，发现 ${result.device_count || 0} 个设备`)
        } else {
          this.$message?.error(`IOT连接测试失败: ${result.error || '未知错误'}`)
        }
      } catch (error) {
        console.error('IOT connection test failed:', error)
        this.$message?.error('IOT连接测试失败，请检查配置')
      } finally {
        this.isTestingConnection = false
      }
    },
    
    clearConfig() {
      this.localIotToken = ''
      this.localFamilyId = ''
      this.localEnv = 'test'
      this.devices = []
      
      // 清除localStorage
      localStorage.removeItem('iot-token')
      localStorage.removeItem('family-id')
      localStorage.removeItem('iot-env')
      
      // 清除设备缓存
      this.clearDevicesCache()
      
      // 同步到store（如果需要的话）
      this.updateIOTConfig({
        token: '',
        familyId: '',
        env: 'test'
      })
      
      this.$message?.success('IOT配置已清空')
    },
    
    async loadDevices() {
      if (!this.isConfigValid) return
      
      this.isLoadingDevices = true
      
      try {
        // 1. 拉取设备列表
        const familyDevicesResponse = await fetch('/api/agentic-test/iot/family-devices/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            iot_token: this.localIotToken.trim(),
            family_id: this.localFamilyId.trim(),
            env: this.localEnv
          })
        })
        
        if (!familyDevicesResponse.ok) {
          throw new Error(`获取设备列表失败: ${familyDevicesResponse.status}`)
        }
        
        const familyDevicesData = await familyDevicesResponse.json()
        
        if (!familyDevicesData.success && familyDevicesData.rc !== 0) {
          throw new Error(familyDevicesData.msg || familyDevicesData.error || '获取设备列表失败')
        }
        
        const deviceList = familyDevicesData.data || []
        
        // 2. 并行拉取在线设备的详情
        const onlineDevices = deviceList.filter(device => device.status === 1)
        const offlineDevices = deviceList.filter(device => device.status !== 1)
        
        // 为在线设备并行获取详情
        const deviceStatusPromises = onlineDevices.map(async (device) => {
          try {
            const statusResponse = await fetch('/api/agentic-test/iot/device-status/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                iot_token: this.localIotToken.trim(),
                device_guid: device.deviceGuid,
                env: this.localEnv
              })
            })
            
            if (statusResponse.ok) {
              const statusData = await statusResponse.json()
              if ((statusData.success || statusData.rc === 0) && statusData.data && statusData.data.length > 0) {
                return {
                  ...device,
                  netState: statusData.data[0].status,
                  properties: statusData.data[0].properties || {}
                }
              }
            }
            
            // 如果获取详情失败，仍然返回基本设备信息
            return {
              ...device,
              netState: device.status,
              properties: {}
            }
          } catch (error) {
            console.warn(`获取设备 ${device.deviceGuid} 详情失败:`, error)
            return {
              ...device,
              netState: device.status,
              properties: {}
            }
          }
        })
        
        // 等待所有在线设备详情获取完成
        const onlineDevicesWithStatus = await Promise.all(deviceStatusPromises)
        
        // 合并在线和离线设备
        this.devices = [
          ...onlineDevicesWithStatus.map(device => ({
            ...device,
            isRefreshing: false // 确保初始状态正确
          })),
          ...offlineDevices.map(device => ({
            ...device,
            netState: 0,
            properties: {},
            isRefreshing: false // 确保初始状态正确
          }))
        ]
        
        // 保存到缓存
        this.saveDevicesToCache(this.devices)
        
        // 标记数据不是来自缓存
        this.isDataFromCache = false
        
        this.$message?.success(`成功加载 ${this.devices.length} 个设备，其中 ${onlineDevices.length} 个在线`)
      } catch (error) {
        console.error('Load devices failed:', error)
        this.$message?.error(`加载设备失败: ${error.message}`)
      } finally {
        this.isLoadingDevices = false
      }
    },
    
    async refreshDevices() {
      if (!this.isConfigValid || this.devices.length === 0) return
      
      this.isRefreshing = true
      
      try {
        // 重新加载设备列表和状态
        await this.loadDevices()
        this.$message?.success('设备状态已刷新')
      } catch (error) {
        console.error('Refresh devices failed:', error)
        this.$message?.error('刷新设备状态失败')
      } finally {
        this.isRefreshing = false
      }
    },
    
    async refreshSingleDevice(device) {
      if (!this.isConfigValid || !device || device.isRefreshing) return
      
      // 防抖：如果设备正在刷新，直接返回
      if (device.isRefreshing) {
        return
      }
      
      // 设置单个设备的刷新状态
      this.$set(device, 'isRefreshing', true)
      
      try {
        // 无论设备当前状态如何，都尝试获取最新状态
        const statusResponse = await fetch('/api/agentic-test/iot/device-status/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            iot_token: this.localIotToken.trim(),
            device_guid: device.deviceGuid,
            env: this.localEnv
          })
        })
        
        if (statusResponse.ok) {
          const statusData = await statusResponse.json()
          if ((statusData.success || statusData.rc === 0) && statusData.data && statusData.data.length > 0) {
            // 更新设备状态
            this.$set(device, 'netState', statusData.data[0].status)
            this.$set(device, 'properties', statusData.data[0].properties || {})
            
            // 更新缓存中的设备数据
            this.saveDevicesToCache(this.devices)
            
            const statusText = statusData.data[0].status === 1 ? '在线' : '离线'
            this.$message?.success(`${device.name || device.displayType} 状态已刷新 (${statusText})`)
          } else {
            // API返回成功但没有数据，可能设备真的离线
            this.$set(device, 'netState', 0)
            this.$set(device, 'properties', {})
            this.saveDevicesToCache(this.devices)
            this.$message?.info(`${device.name || device.displayType} 设备离线`)
          }
        } else {
          throw new Error(`API请求失败: ${statusResponse.status}`)
        }
      } catch (error) {
        console.error(`Refresh single device failed:`, error)
        this.$message?.error(`刷新 ${device.name || device.displayType} 状态失败: ${error.message}`)
      } finally {
        // 确保清除刷新状态
        this.$set(device, 'isRefreshing', false)
        // 强制更新视图
        this.$forceUpdate()
      }
    },
    
    getDisplayProperties(device) {
      const properties = device.properties
      if (!properties || typeof properties !== 'object') return {}
      
      // 根据设备品类选择要显示的属性
      if (device.categoryName === '一体机') {
        return this.getIntegratedMachineProperties(properties)
      } else if (device.categoryName === '油烟机') {
        return this.getRangeHoodProperties(properties)
      } else if (device.categoryName === '灶具') {
        return this.getStoveProperties(properties)
      } else if (device.categoryName === '自动翻炒锅') {
        return this.getAutomaticStirFryPotProperties(properties)
      } else {
        return this.getCommonProperties(properties)
      }
    },
    
    // 一体机属性筛选
    getIntegratedMachineProperties(properties) {
      const displayProps = {}
      
      // 基础状态
      if (properties.powerState !== undefined) {
        displayProps.powerState = properties.powerState
      }
      if (properties.workState !== undefined) {
        displayProps.workState = properties.workState
      }
      
      // 温度信息
      if (properties.curTopTemp !== undefined) {
        displayProps.curTopTemp = properties.curTopTemp
      }
      if (properties.curButtomTemp !== undefined) {
        displayProps.curButtomTemp = properties.curButtomTemp
      }
      
      // 门和水箱状态
      if (properties.doorState !== undefined) {
        displayProps.doorState = properties.doorState
      }
      if (properties.waterBoxState !== undefined) {
        displayProps.waterBoxState = properties.waterBoxState
      }
      if (properties.waterLevelState !== undefined) {
        displayProps.waterLevelState = properties.waterLevelState
      }
      
      // 蒸汽和照明
      if (properties.steamState !== undefined) {
        displayProps.steamState = properties.steamState
      }
      if (properties.lightSwitch !== undefined) {
        displayProps.lightSwitch = properties.lightSwitch
      }
      
      // 旋转烤功能
      if (properties.rotateSwitch !== undefined) {
        displayProps.rotateSwitch = properties.rotateSwitch
      }
      
      // 微波功能（仅当设备支持时显示）
      if (properties.stageOneMicroWaveLevel !== undefined) {
        displayProps.stageOneMicroWaveLevel = properties.stageOneMicroWaveLevel
      }
      
      // 故障码（仅当有故障时显示）
      if (properties.faultCode !== undefined && properties.faultCode !== 0) {
        displayProps.faultCode = properties.faultCode
      }
      
      // 剩余时间（仅当有工作时显示）
      if (properties.totalRemainSeonds !== undefined && properties.totalRemainSeonds > 0) {
        displayProps.totalRemainSeonds = properties.totalRemainSeonds
      }
      
      // 废水箱状态
      if (properties.wasteWaterTankWaterLevelState !== undefined) {
        displayProps.wasteWaterTankWaterLevelState = properties.wasteWaterTankWaterLevelState
      }
      
      return displayProps
    },
    
    // 油烟机属性筛选
    getRangeHoodProperties(properties) {
      const displayProps = {}
      
      // 基础状态
      if (properties.workStatus !== undefined) {
        displayProps.workStatus = properties.workStatus
      }
      if (properties.level !== undefined) {
        displayProps.level = properties.level
      }
      
      // 照明状态
      if (properties.lightStatus !== undefined) {
        displayProps.lightStatus = properties.lightStatus
      }
      
      // 清洗相关
      if (properties.cleanRequired !== undefined) {
        displayProps.cleanRequired = properties.cleanRequired
      }
      
      // 温度检测（如果有的话）
      if (properties.tempChannelOne !== undefined) {
        displayProps.tempChannelOne = properties.tempChannelOne
      }
      if (properties.tempChannelTwo !== undefined) {
        displayProps.tempChannelTwo = properties.tempChannelTwo
      }
      
      // 空气检测状态
      if (properties.airDetectionStatus !== undefined) {
        displayProps.airDetectionStatus = properties.airDetectionStatus
      }
      
      // 智能功能开关
      if (properties.intelligentSmokeSensingSwitch !== undefined) {
        displayProps.intelligentSmokeSensingSwitch = properties.intelligentSmokeSensingSwitch
      }
      if (properties.cruiseControlSwitch !== undefined) {
        displayProps.cruiseControlSwitch = properties.cruiseControlSwitch
      }
      
      // 定时相关（仅当有剩余时间时显示）
      if (properties.remainSecForVentilation !== undefined && properties.remainSecForVentilation > 0) {
        displayProps.remainSecForVentilation = properties.remainSecForVentilation
      }
      if (properties.timing !== undefined && properties.timing > 0) {
        displayProps.timing = properties.timing
      }
      
      // 联动开关
      if (properties.autoMatchVolumeSwitch !== undefined) {
        displayProps.autoMatchVolumeSwitch = properties.autoMatchVolumeSwitch
      }
      
      // 过温保护
      if (properties.overTempProtectionStatus !== undefined) {
        displayProps.overTempProtectionStatus = properties.overTempProtectionStatus
      }
      
      // 油杯状态
      if (properties.oilStatus !== undefined) {
        displayProps.oilStatus = properties.oilStatus
      }
      
      return displayProps
    },
    
    // 灶具属性筛选
    getStoveProperties(properties) {
      const displayProps = {}
      
      // 温度信息
      if (properties.leftCurrTemperature !== undefined) {
        displayProps.leftCurrTemperature = properties.leftCurrTemperature
      }
      if (properties.rightCurrTemperature !== undefined) {
        displayProps.rightCurrTemperature = properties.rightCurrTemperature
      }
      
      // 工作状态
      if (properties.leftWorkState !== undefined) {
        displayProps.leftWorkState = properties.leftWorkState
      }
      if (properties.rightWorkState !== undefined) {
        displayProps.rightWorkState = properties.rightWorkState
      }
      
      // 火力档位
      if (properties.leftLevel !== undefined) {
        displayProps.leftLevel = properties.leftLevel
      }
      if (properties.rightLevel !== undefined) {
        displayProps.rightLevel = properties.rightLevel
      }
      
      // 童锁状态
      if (properties.childLockState !== undefined) {
        displayProps.childLockState = properties.childLockState
      }
      
      // 定时剩余时间（仅当有剩余时间时显示）
      if (properties.leftTimedRemainingTime !== undefined && properties.leftTimedRemainingTime > 0) {
        displayProps.leftTimedRemainingTime = properties.leftTimedRemainingTime
      }
      if (properties.rightTimedRemainingTime !== undefined && properties.rightTimedRemainingTime > 0) {
        displayProps.rightTimedRemainingTime = properties.rightTimedRemainingTime
      }
      
      // 定温烹饪模式（仅当有设置时显示）
      if (properties.leftTimedCookMode !== undefined && properties.leftTimedCookMode > 0) {
        displayProps.leftTimedCookMode = properties.leftTimedCookMode
      }
      if (properties.rightTimedCookMode !== undefined && properties.rightTimedCookMode > 0) {
        displayProps.rightTimedCookMode = properties.rightTimedCookMode
      }
      
      // 防干烧开关
      if (properties.leftSwitch !== undefined) {
        displayProps.leftSwitch = properties.leftSwitch
      }
      if (properties.rightSwitch !== undefined) {
        displayProps.rightSwitch = properties.rightSwitch
      }
      
      // 故障报警（仅当有故障时显示）
      if (properties.leftAlarm !== undefined && properties.leftAlarm !== 255) {
        displayProps.leftAlarm = properties.leftAlarm
      }
      if (properties.rightAlarm !== undefined && properties.rightAlarm !== 255) {
        displayProps.rightAlarm = properties.rightAlarm
      }
      
      // APP曲线创作状态
      if (properties.leftCurveSwitch !== undefined) {
        displayProps.leftCurveSwitch = properties.leftCurveSwitch
      }
      if (properties.rightCurveSwitch !== undefined) {
        displayProps.rightCurveSwitch = properties.rightCurveSwitch
      }
      
      return displayProps
    },
    
    // 自动翻炒锅属性筛选
    getAutomaticStirFryPotProperties(properties) {
      const displayProps = {}
      
      // 基础状态
      if (properties.temperature !== undefined) {
        displayProps.temperature = properties.temperature
      }
      if (properties.systemState !== undefined) {
        displayProps.systemState = properties.systemState
      }
      
      // 搅拌相关
      if (properties.stirringMode !== undefined) {
        displayProps.stirringMode = properties.stirringMode
      }
      if (properties.potCoverState !== undefined) {
        displayProps.potCoverState = properties.potCoverState
      }
      
      // 电量信息
      if (properties.electricQuantity !== undefined) {
        displayProps.electricQuantity = properties.electricQuantity
      }
      
      // 模式状态
      if (properties.modeState !== undefined) {
        displayProps.modeState = properties.modeState
      }
      
      // 绑定炉头
      if (properties.bindPosition !== undefined) {
        displayProps.bindPosition = properties.bindPosition
      }
      
      // 菜谱相关（仅当有值时显示）
      if (properties.recipeValue !== undefined && properties.recipeValue > 0) {
        displayProps.recipeValue = properties.recipeValue
      }
      if (properties.recipeId !== undefined && properties.recipeId > 0) {
        displayProps.recipeId = properties.recipeId
      }
      
      // 运行时间（仅当有剩余时间时显示）
      if (properties.runningTime !== undefined && properties.runningTime > 0) {
        displayProps.runningTime = properties.runningTime
      }
      if (properties.recipeRunningTime !== undefined && properties.recipeRunningTime > 0) {
        displayProps.recipeRunningTime = properties.recipeRunningTime
      }
      
      // 电机参数（仅当搅拌模式激活时显示）
      if (properties.stirringMode > 0) {
        if (properties.frontRotationalSpeed !== undefined) {
          displayProps.frontRotationalSpeed = properties.frontRotationalSpeed
        }
        if (properties.reverseRotationalSpeed !== undefined) {
          displayProps.reverseRotationalSpeed = properties.reverseRotationalSpeed
        }
        if (properties.frontRunningTime !== undefined) {
          displayProps.frontRunningTime = properties.frontRunningTime
        }
        if (properties.reverseRunningTime !== undefined) {
          displayProps.reverseRunningTime = properties.reverseRunningTime
        }
        if (properties.totalRunningTime !== undefined) {
          displayProps.totalRunningTime = properties.totalRunningTime
        }
      }
      
      // 本地记录状态（仅当有记录时显示）
      if (properties.localRecordState !== undefined && properties.localRecordState > 0) {
        displayProps.localRecordState = properties.localRecordState
      }
      
      // 联动开关
      if (properties.linkageSwitch !== undefined) {
        displayProps.linkageSwitch = properties.linkageSwitch
      }
      
      // 本地模式烹饪相关（仅当有剩余时间时显示）
      if (properties.localModeCookRemainingTime !== undefined && properties.localModeCookRemainingTime > 0) {
        displayProps.localModeCookRemainingTime = properties.localModeCookRemainingTime
      }
      if (properties.localModeCookMode !== undefined && properties.localModeCookMode > 0) {
        displayProps.localModeCookMode = properties.localModeCookMode
      }
      if (properties.currentModeStage !== undefined && properties.currentModeStage > 0) {
        displayProps.currentModeStage = properties.currentModeStage
      }
      if (properties.totalStep !== undefined && properties.totalStep > 0) {
        displayProps.totalStep = properties.totalStep
      }
      if (properties.currentStepTotalTime !== undefined && properties.currentStepTotalTime > 0) {
        displayProps.currentStepTotalTime = properties.currentStepTotalTime
      }
      if (properties.currentStepRemainingTime !== undefined && properties.currentStepRemainingTime > 0) {
        displayProps.currentStepRemainingTime = properties.currentStepRemainingTime
      }
      
      return displayProps
    },
    
    // 通用属性筛选
    getCommonProperties(properties) {
      const displayProps = {}
      
      if (properties.powerState !== undefined) {
        displayProps.powerState = properties.powerState
      }
      if (properties.workState !== undefined) {
        displayProps.workState = properties.workState
      }
      if (properties.workStatus !== undefined) {
        displayProps.workStatus = properties.workStatus
      }
      
      return displayProps
    },
    
    getDeviceDisplayName(device) {
      // 格式：设备型号(设备昵称) 或者 设备型号
      const model = device.dt || device.displayType || ''
      const name = device.name || ''
      
      if (name && name !== model && !name.includes(model)) {
        return `${model}(${name})`
      }
      
      return name || model
    },
    
    getPropertyLabel(key) {
      const labels = {
        // 通用属性
        powerState: '电源状态',
        workState: '工作状态',
        workStatus: '工作状态',
        
        // 温度相关
        curTopTemp: '上层温度',
        curButtomTemp: '下层温度',
        leftCurrTemperature: '左灶温度',
        rightCurrTemperature: '右灶温度',
        tempChannelOne: '左侧温度',
        tempChannelTwo: '右侧温度',
        
        // 油烟机属性
        level: '风速档位',
        lightStatus: '照明开关',
        cleanRequired: '清洗提醒',
        airDetectionStatus: '空气检测',
        intelligentSmokeSensingSwitch: '智能烟感',
        cruiseControlSwitch: '定速巡航',
        remainSecForVentilation: '通风剩余',
        timing: '定时时间',
        autoMatchVolumeSwitch: '烟灶联动',
        overTempProtectionStatus: '过温保护',
        oilStatus: '油杯状态',
        
        // 灶具属性
        leftWorkState: '左灶状态',
        rightWorkState: '右灶状态',
        leftLevel: '左灶火力',
        rightLevel: '右灶火力',
        childLockState: '童锁状态',
        leftTimedRemainingTime: '左灶定时',
        rightTimedRemainingTime: '右灶定时',
        leftTimedCookMode: '左灶模式',
        rightTimedCookMode: '右灶模式',
        leftSwitch: '左灶防干烧',
        rightSwitch: '右灶防干烧',
        leftAlarm: '左灶故障',
        rightAlarm: '右灶故障',
        leftCurveSwitch: '左灶曲线',
        rightCurveSwitch: '右灶曲线',
        
        // 一体机属性
        doorState: '门状态',
        waterBoxState: '水箱状态',
        waterLevelState: '水位状态',
        steamState: '蒸汽状态',
        lightSwitch: '照明开关',
        rotateSwitch: '旋转烤',
        stageOneMicroWaveLevel: '微波功率',
        faultCode: '故障状态',
        totalRemainSeonds: '剩余时间',
        wasteWaterTankWaterLevelState: '废水箱',
        
        // 自动翻炒锅属性
        temperature: '锅温度',
        systemState: '系统状态',
        stirringMode: '搅拌模式',
        potCoverState: '锅盖状态',
        recipeValue: 'P档菜谱',
        recipeId: '菜谱ID',
        electricQuantity: '电量',
        modeState: '模式状态',
        localRecordState: '记录状态',
        runningTime: '运行时间',
        bindPosition: '绑定炉头',
        recipeRunningTime: '菜谱时长',
        frontRotationalSpeed: '正转速',
        reverseRotationalSpeed: '反转速',
        frontRunningTime: '正转时间',
        reverseRunningTime: '反转时间',
        totalRunningTime: '总时长',
        recipePosition: '菜谱炉头',
        localModeCookRemainingTime: '本地剩余',
        localModeCookMode: '本地模式',
        currentModeStage: '当前阶段',
        totalStep: '总步骤',
        currentStepTotalTime: '步骤总时',
        currentStepRemainingTime: '步骤剩余',
        linkageSwitch: '联动开关'
      }
      
      // 处理照明相关的统一标签
      if (key.includes('light') || key.includes('Light')) {
        return '照明开关'
      }
      
      return labels[key] || key
    },
    
    formatPropertyValue(key, value) {
      // 温度相关
      if (key.includes('Temp') || key.includes('Temperature') || key === 'tempChannelOne' || key === 'tempChannelTwo') {
        return `${value}°C`
      }
      
      // 时间相关
      if (key === 'totalRemainSeonds' || key === 'remainSecForVentilation' || key === 'leftTimedRemainingTime' || key === 'rightTimedRemainingTime') {
        if (value <= 0) return '0秒'
        const hours = Math.floor(value / 3600)
        const minutes = Math.floor((value % 3600) / 60)
        const seconds = value % 60
        
        if (hours > 0) {
          return `${hours}时${minutes}分`
        } else if (minutes > 0) {
          return `${minutes}分${seconds}秒`
        } else {
          return `${seconds}秒`
        }
      }
      
      if (key === 'timing') {
        return value > 0 ? `${value}分钟` : '关闭'
      }
      
      // 燃气灶专用属性
      if (key === 'leftWorkState' || key === 'rightWorkState') {
        const workStateMap = {
          0: '关机', 1: '待机', 2: '工作中', 3: '产测模式', 
          4: '菜谱模式', 5: '无人锅模式', 6: '定温烹饪', 
          11: '开机不工作', 12: '开机点火'
        }
        return workStateMap[value] || `状态${value}`
      }
      
      if (key === 'leftLevel' || key === 'rightLevel') {
        return value === 0 ? '关闭' : `${value}档`
      }
      
      if (key === 'childLockState') {
        return value === 0 ? '解锁' : '上锁'
      }
      
      if (key === 'leftTimedCookMode' || key === 'rightTimedCookMode') {
        const cookModeMap = {
          0: '无', 1: '炖', 2: '清蒸', 3: '高温煎炸', 4: '中温煎炸', 5: '低温煎炸'
        }
        return cookModeMap[value] || `模式${value}`
      }
      
      if (key === 'leftSwitch' || key === 'rightSwitch') {
        const switchMap = {
          0: '不支持', 1: '临时关闭', 2: '开启'
        }
        return switchMap[value] || `状态${value}`
      }
      
      if (key === 'leftAlarm' || key === 'rightAlarm') {
        const alarmMap = {
          1: '点火失败', 2: '意外熄火', 3: '保留占位', 4: '热电偶故障',
          5: '传感故障', 6: '通讯故障', 7: '温度过高', 8: '保留占位',
          9: '阀门故障', 255: '无故障'
        }
        return alarmMap[value] || `故障${value}`
      }
      
      if (key === 'leftCurveSwitch' || key === 'rightCurveSwitch') {
        return value === 0 ? '关闭' : '开启'
      }
      
      // 油烟机专用属性
      if (key === 'workStatus') {
        const workStatusMap = {
          0: '关机', 1: '开机', 2: '延时关机', 3: '待机', 4: '清洗锁定', 5: '挡风板拆除'
        }
        return workStatusMap[value] || `状态${value}`
      }
      
      if (key === 'level') {
        const levelMap = {
          0: '无风量', 1: '弱档', 2: '中档', 3: '强档', 6: '爆炒'
        }
        return levelMap[value] || `${value}档`
      }
      
      if (key === 'cleanRequired') {
        return value === 0 ? '不需要' : '需要清洗'
      }
      
      if (key === 'airDetectionStatus') {
        const airDetectionMap = {
          0: '关闭', 1: '检测中', 2: '优', 3: '不良', 10: '短路故障', 11: '开路故障'
        }
        return airDetectionMap[value] || `状态${value}`
      }
      
      if (key === 'intelligentSmokeSensingSwitch' || key === 'cruiseControlSwitch' || key === 'autoMatchVolumeSwitch') {
        return value === 0 ? '关闭' : '开启'
      }
      
      if (key === 'overTempProtectionStatus') {
        return value === 0 ? '正常' : '过温报警'
      }
      
      if (key === 'oilStatus') {
        return value === 0 ? '正常' : '需要倒油杯'
      }
      
      // 一体机专用属性
      if (key === 'powerState') {
        const powerStateMap = { 0: '关机', 1: '待机', 2: '开机', 10: '产测模式' }
        return powerStateMap[value] || `状态${value}`
      }
      
      if (key === 'workState') {
        const workStateMap = {
          0: '空闲', 1: '预约中', 2: '预热中', 3: '预热暂停',
          4: '工作中', 5: '工作暂停', 6: '待加时', 7: '自检中'
        }
        return workStateMap[value] || `状态${value}`
      }
      
      if (key === 'doorState') {
        const doorStateMap = {
          0: '已闭合', 1: '已打开', 2: '已半开', 3: '闭合中', 4: '开启中'
        }
        return doorStateMap[value] || `状态${value}`
      }
      
      if (key === 'waterBoxState') {
        const waterBoxStateMap = {
          0: '闭合', 1: '弹出', 2: '闭合中', 3: '弹出中'
        }
        return waterBoxStateMap[value] || `状态${value}`
      }
      
      if (key === 'waterLevelState') {
        return value === 0 ? '正常' : '缺水'
      }
      
      if (key === 'steamState') {
        const steamStateMap = {
          0: '禁止使用', 1: '工作中', 2: '空闲可用'
        }
        return steamStateMap[value] || `状态${value}`
      }
      
      if (key === 'rotateSwitch') {
        return value === 0 ? '关闭' : '开启'
      }
      
      if (key === 'stageOneMicroWaveLevel') {
        return value === 0 ? '关闭' : `${value}W`
      }
      
      if (key === 'faultCode') {
        const faultCodeMap = {
          0: '无故障', 1: '先蒸后烤', 2: '上温度传感器故障', 3: '下温度传感器故障',
          4: '散热风机故障', 5: '通讯故障', 6: '水位传感器故障', 7: '按键板传感器故障',
          8: '高温报警故障', 9: '温度加热异常', 10: '冷气阀故障', 11: '缺水故障',
          12: '上风机故障', 13: '微波变频板故障', 14: '按键板温度过高', 15: '磁控管高温故障',
          16: '变频板通讯故障', 17: '磁控管温度传感器故障', 18: '一体机与烟机通讯故障',
          19: '蒸发盘干烧', 20: '电源板通信故障', 21: '加热风机故障', 22: '煮水盘故障'
        }
        return faultCodeMap[value] || `故障${value}`
      }
      
      if (key === 'wasteWaterTankWaterLevelState') {
        return value === 0 ? '正常' : '水满'
      }
      
      // 自动翻炒锅专用属性
      if (key === 'temperature') {
        return `${value}°C`
      }
      
      if (key === 'systemState') {
        const systemStateMap = {
          0: '待机', 1: '开机', 2: '干烧预警', 3: '低电量提醒',
          4: '温度传感器故障', 5: '电机故障', 6: '充电状态'
        }
        return systemStateMap[value] || `状态${value}`
      }
      
      if (key === 'stirringMode') {
        const stirringModeMap = {
          0: '未运行', 1: '持续搅拌', 2: '间停搅拌', 3: '自定义模式', 255: '故障状态'
        }
        return stirringModeMap[value] || `模式${value}`
      }
      
      if (key === 'potCoverState') {
        return value === 1 ? '取下' : '盖上'
      }
      
      if (key === 'electricQuantity') {
        return `${value}%`
      }
      
      if (key === 'modeState') {
        const modeStateMap = {
          0: '普通模式', 1: '实时曲线记录', 2: 'P档菜谱模式', 3: '平台菜谱模式',
          4: '等待炉头开启', 5: 'P档等待开启', 6: '平台等待开启'
        }
        return modeStateMap[value] || `模式${value}`
      }
      
      if (key === 'localRecordState') {
        const recordStateMap = {
          0: '无记录', 1: '待上传', 2: '上传中'
        }
        return recordStateMap[value] || `状态${value}`
      }
      
      if (key === 'bindPosition' || key === 'recipePosition') {
        return value === 0 ? '左炉头' : '右炉头'
      }
      
      if (key === 'runningTime' || key === 'recipeRunningTime' || key === 'frontRunningTime' || 
          key === 'reverseRunningTime' || key === 'totalRunningTime' || 
          key === 'localModeCookRemainingTime' || key === 'currentStepTotalTime' || 
          key === 'currentStepRemainingTime') {
        if (value <= 0) return '0秒'
        const hours = Math.floor(value / 3600)
        const minutes = Math.floor((value % 3600) / 60)
        const seconds = value % 60
        
        if (hours > 0) {
          return `${hours}时${minutes}分`
        } else if (minutes > 0) {
          return `${minutes}分${seconds}秒`
        } else {
          return `${seconds}秒`
        }
      }
      
      if (key === 'frontRotationalSpeed' || key === 'reverseRotationalSpeed') {
        return `${value}转/分`
      }
      
      if (key === 'linkageSwitch') {
        const linkageMap = {
          0: '全关闭', 1: '干烧预警开', 2: '烟锅联动开', 3: '干烧+烟锅开',
          4: '开盖联动开', 5: '干烧+开盖开', 6: '烟锅+开盖开', 7: '全开启'
        }
        return linkageMap[value] || `状态${value}`
      }
      
      if (key === 'recipeValue' || key === 'recipeId' || key === 'localModeCookMode' || 
          key === 'currentModeStage' || key === 'totalStep') {
        return `${value}`
      }
      
      // 照明相关 - 统一为开启/关闭
      if (key === 'lightStatus' || key === 'lightSwitch' || key.includes('light') || key.includes('Light')) {
        return value === 0 ? '关闭' : '开启'
      }
      
      // 通用状态
      if (key.includes('State') || key.includes('Status')) {
        return value === 0 ? '关闭' : '开启'
      }
      
      // 档位相关
      if (key.includes('Level')) {
        return value === 0 ? '关闭' : `${value}档`
      }
      
      return value
    },
    
    // 判断属性值是否为"开启"状态
    isPropertyActive(key, value) {
      // 温度值不算开启状态
      if (key.includes('Temp') || key.includes('Temperature') || key === 'tempChannelOne' || key === 'tempChannelTwo') {
        return false
      }
      
      // 时间相关不算开启状态（除非有剩余时间）
      if (key === 'totalRemainSeonds' || key === 'remainSecForVentilation') {
        return value > 0
      }
      
      if (key === 'timing') {
        return value > 0
      }
      
      // 油烟机专用属性激活判断
      if (key === 'workStatus') {
        return [1, 2].includes(value) // 开机、延时关机
      }
      
      if (key === 'level') {
        return value > 0 // 有风量
      }
      
      if (key === 'cleanRequired') {
        return value === 1 // 需要清洗
      }
      
      if (key === 'airDetectionStatus') {
        return [1, 3, 10, 11].includes(value) // 检测中、不良、故障状态
      }
      
      if (key === 'intelligentSmokeSensingSwitch' || key === 'cruiseControlSwitch' || key === 'autoMatchVolumeSwitch') {
        return value === 1 // 开启状态
      }
      
      if (key === 'overTempProtectionStatus') {
        return value === 1 // 过温报警
      }
      
      if (key === 'oilStatus') {
        return value === 1 // 需要倒油杯
      }
      
      // 一体机专用属性激活判断
      if (key === 'powerState') {
        return value === 2 // 开机状态
      }
      
      if (key === 'workState') {
        return [2, 4].includes(value) // 预热中、工作中
      }
      
      if (key === 'doorState') {
        return [1, 2].includes(value) // 已打开、已半开
      }
      
      if (key === 'waterBoxState') {
        return value === 1 // 弹出状态
      }
      
      if (key === 'waterLevelState') {
        return value === 1 // 缺水状态（需要注意）
      }
      
      if (key === 'steamState') {
        return value === 1 // 工作中状态
      }
      
      if (key === 'rotateSwitch') {
        return value === 1 // 开启状态
      }
      
      if (key === 'stageOneMicroWaveLevel') {
        return value > 0 // 有功率输出
      }
      
      if (key === 'faultCode') {
        return value !== 0 // 有故障
      }
      
      if (key === 'wasteWaterTankWaterLevelState') {
        return value === 1 // 水满状态（需要注意）
      }
      
      // 自动翻炒锅专用属性激活判断
      if (key === 'systemState') {
        return [1, 2, 3, 4, 5, 6].includes(value) // 除待机外的所有状态
      }
      
      if (key === 'stirringMode') {
        return [1, 2, 3].includes(value) // 搅拌模式激活
      }
      
      if (key === 'potCoverState') {
        return value === 1 // 锅盖取下状态
      }
      
      if (key === 'electricQuantity') {
        return value < 20 // 低电量状态
      }
      
      if (key === 'modeState') {
        return [1, 2, 3, 4, 5, 6].includes(value) // 除普通模式外的状态
      }
      
      if (key === 'localRecordState') {
        return [1, 2].includes(value) // 有记录待上传或上传中
      }
      
      if (key === 'runningTime' || key === 'recipeRunningTime' || key === 'localModeCookRemainingTime' || 
          key === 'currentStepRemainingTime') {
        return value > 0 // 有剩余时间
      }
      
      if (key === 'frontRotationalSpeed' || key === 'reverseRotationalSpeed') {
        return value > 0 // 有转速
      }
      
      if (key === 'linkageSwitch') {
        return value > 0 // 有联动功能开启
      }
      
      if (key === 'recipeValue' || key === 'recipeId' || key === 'localModeCookMode' || 
          key === 'currentModeStage' || key === 'totalStep') {
        return value > 0 // 有设置值
      }
      
      // 照明相关
      if (key === 'lightStatus' || key === 'lightSwitch' || key.includes('light') || key.includes('Light')) {
        return value !== 0
      }
      
      // 灶具的状态相关
      if (key.includes('State') || key.includes('Status')) {
        return value !== 0
      }
      
      // 档位相关
      if (key.includes('Level')) {
        return value > 0
      }
      
      return false
    },
    
    getCacheInfo() {
      const cacheTimestamp = localStorage.getItem('iot-devices-timestamp')
      if (cacheTimestamp) {
        const cacheTime = new Date(parseInt(cacheTimestamp))
        const now = new Date()
        const diffMinutes = Math.floor((now - cacheTime) / (1000 * 60))
        
        if (diffMinutes < 1) {
          return '数据来自缓存（刚刚更新），点击刷新获取最新状态'
        } else {
          return `数据来自缓存（${diffMinutes}分钟前更新），点击刷新获取最新状态`
        }
      }
      return '数据来自缓存，点击刷新获取最新状态'
    }
  }
}
</script>

<style scoped>
.iot-device-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 48px);
  min-height: 0;
  overflow: hidden;
}

/* 配置区域 */
.config-section {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.cache-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-tertiary);
  padding: 2px 6px;
  background: var(--bg-secondary);
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

.cache-indicator svg {
  opacity: 0.7;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-icon svg {
  transition: transform 0.2s ease;
}

.config-content {
  padding: 20px;
}

.config-form {
  margin-bottom: 16px;
}

.form-row {
  margin-bottom: 16px;
}

.form-group {
  width: 100%;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.config-status {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-item.valid {
  color: #059669;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
  transition: background-color 0.2s ease;
}

.status-item.valid .status-indicator {
  background: #10b981;
}

.config-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 设备区域 */
.devices-section {
  background: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  overflow: hidden;
}

/* 当配置隐藏时，设备区域占满整个面板 */
.iot-device-panel:not(:has(.config-section)) {
  gap: 0;
}

.iot-device-panel:not(:has(.config-section)) .devices-section {
  height: 100%;
  min-height: calc(100vh - 120px);
}

.devices-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
  max-height: none;
}

/* 自定义滚动条样式 */
.devices-content::-webkit-scrollbar {
  width: 8px;
}

.devices-content::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 4px;
}

.devices-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.devices-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.empty-devices,
.loading-devices {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-devices svg,
.loading-devices svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-devices p,
.loading-devices p {
  margin: 0;
  font-size: 14px;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  min-height: 200px;
  padding-bottom: 16px;
}

/* 设备卡片 - 紧凑设计 */
.device-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.device-card:hover {
  border-color: var(--accent-blue);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.device-card.online {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.02);
}

.device-card.offline {
  opacity: 0.75;
}

/* 设备头部 - 水平布局 */
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.device-main-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0; /* 允许内容收缩 */
}

.device-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin-right: 12px;
  flex-shrink: 0; /* 防止图标被压缩 */
}

.device-card.online .device-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.device-card.offline .device-icon {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.device-status-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0; /* 防止右侧按钮被压缩 */
}

.device-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  transition: all 0.2s ease;
}

.device-status-dot.online {
  background: #10b981;
}

.device-refresh-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-tertiary);
  transition: all 0.2s ease;
  opacity: 0;
}

.device-card:hover .device-refresh-btn,
.device-refresh-btn.refreshing {
  opacity: 1;
}

.device-refresh-btn.refreshing {
  color: var(--accent-blue);
}

.device-refresh-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.device-refresh-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* 设备信息 - 紧凑内联布局 */
.device-info {
  flex: 1;
  min-width: 0; /* 允许内容收缩 */
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.device-category {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 2px 6px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.device-card.online .device-category {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

/* 设备属性 - 优化协调的布局 */
.device-properties {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}

.properties-header {
  margin-bottom: 10px;
}

.properties-header span {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.properties-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: 6px;
  transition: all 0.2s ease;
  min-height: 36px;
}

.property-item:hover {
  background: rgba(79, 70, 229, 0.08);
  transform: translateY(-1px);
}

/* 激活状态的属性项 */
.property-item.active {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.1);
}

.property-item.active:hover {
  background: rgba(16, 185, 129, 0.12);
  border-color: #059669;
}

.property-label {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: 600;
  flex-shrink: 0;
  width: 45%;
  line-height: 1.3;
  letter-spacing: 0.2px;
}

.property-item.active .property-label {
  color: #059669;
  font-weight: 700;
}

.property-value {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 700;
  text-align: right;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
  word-break: break-all;
  letter-spacing: 0.3px;
}

.property-item.active .property-value {
  color: #059669;
  font-weight: 800;
}

/* 离线状态 - 紧凑显示 */
.device-offline {
  padding: 16px;
  text-align: center;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
}

.offline-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dc2626;
}

.device-offline span {
  font-size: 13px;
  font-weight: 500;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn-primary {
  background: var(--accent-blue);
  color: white;
  border: 1px solid var(--accent-blue);
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
  border-color: #4338ca;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn svg {
  flex-shrink: 0;
}

/* 动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
  }
  
  .config-actions {
    flex-direction: column;
  }
  
  .config-actions .btn {
    width: 100%;
    justify-content: center;
  }
  
  .iot-device-panel {
    height: 100vh;
    max-height: none;
  }
  
  .devices-section {
    min-height: 200px;
  }
  
  .devices-content {
    padding: 12px;
  }
  
  /* 移动端始终显示刷新按钮 */
  .device-refresh-btn {
    opacity: 1;
  }
  
  /* 移动端设备卡片调整 */
  .device-card {
    padding: 12px;
  }
  
  .device-name {
    font-size: 15px;
  }
  
  .device-icon {
    width: 32px;
    height: 32px;
    margin-right: 10px;
  }
}

@media (max-width: 480px) {
  .device-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .devices-content {
    padding: 8px;
  }
  
  .device-card {
    padding: 10px;
  }
  
  .device-name {
    font-size: 14px;
  }
  
  .device-icon {
    width: 28px;
    height: 28px;
    margin-right: 8px;
  }
  
  .properties-grid {
    grid-template-columns: 1fr;
  }
}
</style>