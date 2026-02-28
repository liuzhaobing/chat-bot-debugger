<template>
  <div class="iot-device-panel">
    <!-- 设备状态区域 -->
    <div class="devices-section">
      <!-- 统计和筛选栏 -->
      <div class="stats-filter-bar">
        <!-- 左侧统计标签 -->
        <div class="stats-tags">
          <button 
            class="stat-tag" 
            :class="{ active: filterStatus === 'all' }"
            @click="filterStatus = 'all'"
          >
            <span class="stat-label">总设备</span>
            <span class="stat-value">{{ devices.length }}</span>
          </button>
          <button 
            class="stat-tag stat-online" 
            :class="{ active: filterStatus === 'online' }"
            @click="filterStatus = 'online'"
          >
            <span class="stat-label">在线</span>
            <span class="stat-value">{{ onlineDevicesCount }}</span>
          </button>
          <button 
            class="stat-tag stat-offline" 
            :class="{ active: filterStatus === 'offline' }"
            @click="filterStatus = 'offline'"
          >
            <span class="stat-label">离线</span>
            <span class="stat-value">{{ offlineDevicesCount }}</span>
          </button>
          <button 
            class="stat-tag stat-error" 
            :class="{ active: filterStatus === 'error' }"
            @click="filterStatus = 'error'"
          >
            <span class="stat-label">异常</span>
            <span class="stat-value">{{ errorDevicesCount }}</span>
          </button>
        </div>
        
        <!-- 右侧操作区 -->
        <div class="filter-actions">
          <!-- 设备类型筛选 -->
          <select v-model="filterCategory" class="filter-select">
            <option value="">全部类型</option>
            <option v-for="category in deviceCategories" :key="category" :value="category">
              {{ category }}
            </option>
          </select>
          
          <!-- IOT配置按钮 -->
          <button 
            class="btn btn-outline btn-sm"
            @click="showConfigModal = true"
            title="IOT配置"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"></path>
            </svg>
            IOT配置
          </button>
          
          <!-- 刷新按钮 -->
          <button 
            class="btn btn-primary btn-sm"
            @click="refreshDevices"
            :disabled="!isConfigValid || isRefreshing"
            title="刷新设备列表"
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
          <p>{{ isConfigValid ? '点击"刷新"获取设备列表' : '请先完成IOT配置' }}</p>
        </div>

        <div v-else-if="isLoadingDevices" class="loading-devices">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          <p>正在加载设备...</p>
        </div>
        
        <div v-else-if="filteredDevices.length === 0" class="empty-devices">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 8v4"></path>
            <path d="M12 16h.01"></path>
          </svg>
          <p>没有找到符合条件的设备</p>
        </div>

        <div v-else class="device-grid">
          <div 
            v-for="device in filteredDevices" 
            :key="device.deviceId"
            class="device-card"
            :class="{ 
              online: isDeviceOnline(device),
              offline: !isDeviceOnline(device) && !hasDeviceError(device),
              error: hasDeviceError(device),
              expanded: isDeviceExpanded(device)
            }"
            @click="handleDeviceClick(device)"
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
                    <div class="device-status-badge">
                      <div class="status-dot" :class="getDeviceStatusClass(device)"></div>
                      <span class="status-text">{{ getDeviceStatusText(device) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 刷新按钮 -->
                <button
                  class="device-refresh-btn"
                  @click.stop="refreshSingleDevice(device)"
                  :disabled="device.isRefreshing || !isConfigValid"
                  title="刷新设备状态"
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

            <!-- 在线设备详情（展开时显示） -->
            <div v-if="isDeviceOnline(device) && isDeviceExpanded(device) && device.properties && Object.keys(device.properties).length > 0" class="device-details">
              <!-- 核心状态区 -->
              <div class="core-status">
                <div 
                  v-for="(value, key) in getCoreProperties(device)" 
                  :key="key" 
                  class="core-property"
                  :class="{ 'highlight': isHighlightProperty(key), active: isPropertyActive(key, value) }"
                >
                  <div class="property-left">
                    <div class="property-icon">
                      <svg v-if="key.includes('power') || key.includes('Power')" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v10"></path>
                        <path d="M18.4 6.6a9 9 0 1 1-12.77.04"></path>
                      </svg>
                      <svg v-else-if="key.includes('work') || key.includes('Work')" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                      </svg>
                      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                      </svg>
                    </div>
                    <div class="property-label">{{ getPropertyLabel(key) }}</div>
                  </div>
                  <div class="property-value">{{ formatPropertyValue(key, value) }}</div>
                </div>
              </div>
              
              <!-- 其他参数 -->
              <div class="other-properties">
                <div 
                  v-for="(value, key) in getOtherProperties(device)" 
                  :key="key" 
                  class="property-item"
                  :class="{ 'highlight': isHighlightProperty(key), active: isPropertyActive(key, value) }"
                >
                  <div class="property-label">{{ getPropertyLabel(key) }}</div>
                  <div class="property-value">{{ formatPropertyValue(key, value) }}</div>
                </div>
              </div>
            </div>

            <!-- 离线/异常设备详情（展开时显示） -->
            <div v-else-if="!isDeviceOnline(device) && isDeviceExpanded(device)" class="device-details offline-details">
              <div class="offline-info">
                <div class="info-item">
                  <span class="info-label">告警原因：</span>
                  <span class="info-value">{{ getOfflineReason(device) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">最后在线：</span>
                  <span class="info-value">{{ getLastOnlineTime(device) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- IOT配置弹窗 -->
    <div v-if="showConfigModal" class="config-modal-overlay" @click="showConfigModal = false">
      <div class="config-modal" @click.stop>
        <div class="modal-header">
          <h3>IOT 配置</h3>
          <button class="close-btn" @click="showConfigModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div class="modal-content">
          <div class="config-form">
            <div class="form-group">
              <label>环境选择</label>
              <select v-model="localEnv" @change="saveConfig">
                <option value="test">测试环境 (api-test.myroki.com)</option>
                <option value="prod">生产环境 (api.myroki.com)</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>IOT Token</label>
              <input 
                v-model="localIotToken"
                type="password"
                placeholder="请输入IOT认证Token..."
                @blur="saveConfig"
              />
            </div>
            
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
        </div>
        
        <div class="modal-footer">
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
            @click="loadDevicesAndCloseModal"
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
      showConfigModal: false,
      localIotToken: '',
      localFamilyId: '',
      localEnv: 'test',
      isTestingConnection: false,
      isLoadingDevices: false,
      isRefreshing: false,
      devices: [],
      isDataFromCache: false,
      // 新增筛选和搜索状态
      filterStatus: 'all', // all, online, offline, error
      filterCategory: '',
      searchKeyword: '',
      // 新增卡片展开/收起状态
      expandedDevices: new Set() // 存储展开的设备ID
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
    },
    
    // 排序后的设备列表（在线设备优先）
    sortedDevices() {
      return [...this.devices].sort((a, b) => {
        const aOnline = this.isDeviceOnline(a) ? 1 : 0
        const bOnline = this.isDeviceOnline(b) ? 1 : 0
        return bOnline - aOnline
      })
    },
    
    // 筛选后的设备列表
    filteredDevices() {
      let filtered = this.sortedDevices
      
      // 按状态筛选
      if (this.filterStatus === 'online') {
        filtered = filtered.filter(device => this.isDeviceOnline(device))
      } else if (this.filterStatus === 'offline') {
        filtered = filtered.filter(device => !this.isDeviceOnline(device) && !this.hasDeviceError(device))
      } else if (this.filterStatus === 'error') {
        filtered = filtered.filter(device => this.hasDeviceError(device))
      }
      
      // 按类型筛选
      if (this.filterCategory) {
        filtered = filtered.filter(device => device.categoryName === this.filterCategory)
      }
      
      // 按关键词搜索
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.trim().toLowerCase()
        filtered = filtered.filter(device => {
          const name = (device.name || '').toLowerCase()
          const displayType = (device.displayType || '').toLowerCase()
          const dt = (device.dt || '').toLowerCase()
          const deviceId = (device.deviceId || '').toLowerCase()
          return name.includes(keyword) || displayType.includes(keyword) || 
                 dt.includes(keyword) || deviceId.includes(keyword)
        })
      }
      
      return filtered
    },
    
    // 设备类型列表
    deviceCategories() {
      const categories = new Set()
      this.devices.forEach(device => {
        if (device.categoryName) {
          categories.add(device.categoryName)
        }
      })
      return Array.from(categories).sort()
    },
    
    // 统计数据
    onlineDevicesCount() {
      return this.devices.filter(device => this.isDeviceOnline(device)).length
    },
    
    offlineDevicesCount() {
      return this.devices.filter(device => !this.isDeviceOnline(device) && !this.hasDeviceError(device)).length
    },
    
    errorDevicesCount() {
      return this.devices.filter(device => this.hasDeviceError(device)).length
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
    // 判断设备是否在线
    isDeviceOnline(device) {
      return device.netState === 1 || device.status === 1
    },
    
    // 判断设备是否有错误
    hasDeviceError(device) {
      if (!device.properties) return false
      // 检查故障码
      if (device.properties.faultCode && device.properties.faultCode !== 0) return true
      // 检查告警状态
      if (device.properties.leftAlarm && device.properties.leftAlarm !== 255) return true
      if (device.properties.rightAlarm && device.properties.rightAlarm !== 255) return true
      return false
    },
    
    // 获取设备状态类名
    getDeviceStatusClass(device) {
      if (this.hasDeviceError(device)) return 'error'
      if (this.isDeviceOnline(device)) return 'online'
      return 'offline'
    },
    
    // 获取设备状态文本
    getDeviceStatusText(device) {
      if (this.hasDeviceError(device)) return '异常'
      if (this.isDeviceOnline(device)) return '在线'
      return '离线'
    },
    
    // 获取核心属性（电源、工作状态）
    getCoreProperties(device) {
      const properties = device.properties || {}
      const coreProps = {}
      
      if (properties.powerState !== undefined) {
        coreProps.powerState = properties.powerState
      }
      if (properties.workState !== undefined) {
        coreProps.workState = properties.workState
      }
      if (properties.workStatus !== undefined) {
        coreProps.workStatus = properties.workStatus
      }
      
      return coreProps
    },
    
    // 获取其他属性（除核心属性外）
    getOtherProperties(device) {
      const allProps = this.getDisplayProperties(device)
      const coreKeys = ['powerState', 'workState', 'workStatus']
      const otherProps = {}
      
      Object.keys(allProps).forEach(key => {
        if (!coreKeys.includes(key)) {
          otherProps[key] = allProps[key]
        }
      })
      
      return otherProps
    },
    
    // 处理设备卡片点击
    handleDeviceClick(device) {
      if (this.expandedDevices.has(device.deviceId)) {
        this.expandedDevices.delete(device.deviceId)
      } else {
        this.expandedDevices.add(device.deviceId)
      }
      // 强制更新以确保UI刷新
      this.$forceUpdate()
    },
    
    // 判断设备卡片是否展开
    isDeviceExpanded(device) {
      return this.expandedDevices.has(device.deviceId)
    },
    
    // 判断是否是高优参数（电源状态、煮沸功率）
    isHighlightProperty(key) {
      return ['powerState', 'stageOneMicroWaveLevel'].includes(key)
    },
    
    // 获取离线原因
    getOfflineReason(device) {
      if (this.hasDeviceError(device)) {
        if (device.properties?.faultCode && device.properties.faultCode !== 0) {
          return this.formatPropertyValue('faultCode', device.properties.faultCode)
        }
        return '设备异常'
      }
      return '网络连接中断'
    },
    
    // 获取最后在线时间
    getLastOnlineTime() {
      // TODO: 从设备数据中获取最后在线时间
      return '2分钟前'
    },
    
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
    
    async loadDevicesAndCloseModal() {
      await this.loadDevices()
      this.showConfigModal = false
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

/* IOT配置弹窗 */
.config-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.config-modal {
  background: var(--bg-surface);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
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

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-content {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

/* 统计和筛选栏 */
.stats-filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 16px;
  flex-wrap: wrap;
}

.stats-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.stat-tag:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.stat-tag.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.stat-tag .stat-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.stat-tag.active .stat-label {
  color: rgba(255, 255, 255, 0.9);
}

.stat-tag .stat-value {
  font-weight: 700;
  font-size: 16px;
  color: var(--text-primary);
}

.stat-tag.active .stat-value {
  color: white;
}

.stat-tag.stat-online .stat-value {
  color: #10b981;
}

.stat-tag.stat-online.active .stat-value {
  color: white;
}

.stat-tag.stat-offline .stat-value {
  color: #6b7280;
}

.stat-tag.stat-offline.active .stat-value {
  color: white;
}

.stat-tag.stat-error .stat-value {
  color: #f59e0b;
}

.stat-tag.stat-error.active .stat-value {
  color: white;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.filter-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
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
  align-items: start;
}

/* 设备卡片 - 优化设计 */
.device-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  cursor: pointer;
}

.device-card:hover {
  border-color: var(--accent-blue);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.device-card.online {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.02);
}

.device-card.online:hover {
  border-color: #10b981;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
}

.device-card.offline {
  opacity: 0.7;
  background: rgba(107, 114, 128, 0.02);
  padding: 12px 16px;
}

.device-card.offline:hover {
  opacity: 0.85;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.device-card.error {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.02);
  padding: 12px 16px;
}

.device-card.error:hover {
  border-color: #f59e0b;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
}

/* 展开状态 */
.device-card.expanded {
  padding: 16px;
}

.device-card.expanded.offline,
.device-card.expanded.error {
  padding: 16px;
}

/* 设备头部 */
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.device-main-info {
  display: flex;
  align-items: flex-start;
  flex: 1;
  min-width: 0;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin-right: 12px;
  flex-shrink: 0;
}

.device-card.online .device-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.device-card.offline .device-icon {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.device-card.error .device-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

/* 设备信息 */
.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
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
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 3px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.device-card.online .device-category {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.device-status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
}

.status-dot.online {
  background: #10b981;
}

.status-dot.offline {
  background: #6b7280;
}

.status-dot.error {
  background: #f59e0b;
}

.status-text {
  color: var(--text-secondary);
}

.device-card.online .status-text {
  color: #059669;
}

.device-card.error .status-text {
  color: #d97706;
}

/* 设备详情 - 分组布局 */
.device-details {
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
  margin-top: 12px;
  position: relative;
}

/* 设备详情刷新按钮 */
.device-refresh-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
}

.device-card:hover .device-refresh-btn {
  opacity: 1;
}

.device-refresh-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.device-refresh-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.device-refresh-btn:disabled:hover {
  background: var(--bg-primary);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

/* 核心状态区 */
.core-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.core-property {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.core-property:hover {
  background: rgba(79, 70, 229, 0.05);
}

.core-property.highlight {
  background: rgba(79, 70, 229, 0.12);
  border-color: rgba(79, 70, 229, 0.3);
}

.core-property.active {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.property-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.core-property.active .property-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.core-property.highlight .property-icon {
  background: rgba(79, 70, 229, 0.1);
  color: var(--accent-blue);
}

.property-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.core-property .property-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.core-property.highlight .property-label {
  color: var(--text-primary);
  font-weight: 700;
}

.core-property.active .property-label {
  color: #059669;
}

.core-property .property-value {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 700;
  text-align: right;
}

.core-property.highlight .property-value {
  color: var(--accent-blue);
  font-size: 16px;
  font-weight: 800;
}

.core-property.active .property-value {
  color: #059669;
}

/* 其他属性 */
.other-properties {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 12px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: 6px;
  transition: all 0.2s ease;
  min-height: 36px;
}

.property-item:hover {
  background: rgba(79, 70, 229, 0.05);
}

.property-item.highlight {
  background: rgba(79, 70, 229, 0.12);
  border-color: rgba(79, 70, 229, 0.3);
}

.property-item.active {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.property-item .property-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.property-item.highlight .property-label {
  color: var(--text-primary);
  font-weight: 700;
}

.property-item.active .property-label {
  color: #059669;
}

.property-item .property-value {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 700;
  text-align: right;
}

.property-item.highlight .property-value {
  color: var(--accent-blue);
  font-size: 13px;
  font-weight: 800;
}

.property-item.active .property-value {
  color: #10b981;
}

/* 离线/异常详情 */
.offline-details {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.offline-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.info-label {
  color: var(--text-secondary);
  font-weight: 600;
  flex-shrink: 0;
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
  text-align: right;
}

/* 设备操作按钮 */
.device-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
  transform: translateY(-1px);
}

.action-btn svg {
  flex-shrink: 0;
}

/* 离线/异常状态 */
.device-offline,
.device-error {
  padding: 0;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
}

.offline-icon,
.error-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dc2626;
}

.device-error .error-icon {
  color: #f59e0b;
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
@media (max-width: 1200px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stats-tags {
    width: 100%;
    justify-content: space-between;
  }
  
  .stat-tag {
    flex: 1;
    justify-content: center;
    padding: 8px 12px;
  }
  
  .filter-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .search-box,
  .filter-select,
  .filter-actions .btn {
    width: 100%;
  }
  
  .search-box input {
    width: 100%;
  }
  
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
  
  .device-card {
    padding: 12px;
  }
  
  .device-card.offline,
  .device-card.error {
    padding: 10px 12px;
  }
  
  .device-card.expanded {
    padding: 12px;
  }
  
  .device-name {
    font-size: 14px;
  }
  
  .device-icon {
    width: 36px;
    height: 36px;
    margin-right: 10px;
  }
  
  .other-properties {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-tags {
    flex-direction: column;
  }
  
  .stat-tag {
    width: 100%;
  }
  
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
  
  .device-card.offline,
  .device-card.error {
    padding: 8px 10px;
  }
  
  .device-card.expanded {
    padding: 10px;
  }
  
  .device-name {
    font-size: 13px;
  }
  
  .device-icon {
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }
  
  .other-properties {
    grid-template-columns: 1fr;
  }
  
  .device-actions {
    flex-direction: column;
    gap: 6px;
  }
  
  .action-btn {
    width: 100%;
    padding: 8px 10px;
  }
}
</style>