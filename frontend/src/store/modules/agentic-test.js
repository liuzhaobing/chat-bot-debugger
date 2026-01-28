import agenticTestService from '@/services/agenticTestService'

const state = {
  // 会话管理
  sessions: [],
  currentSession: null,
  isConnected: false,
  
  // 测试状态
  isTestRunning: false,
  currentStatus: '',
  
  // 音频可视化
  audioData: {
    isPlaying: false,
    audioType: '', // 'tts' | 'mic'
    features: {
      pitch: 0,
      volume: 0,
      energy: 0
    }
  },
  
  // 日志和设备状态
  logs: [],
  deviceStatus: [],
  
  // IOT配置
  iotConfig: {
    token: '',
    familyId: '',
    env: 'test'
  },
  
  // WebSocket连接
  websocket: null
}

const mutations = {
  SET_SESSIONS(state, sessions) {
    state.sessions = sessions
  },
  
  SET_CURRENT_SESSION(state, session) {
    state.currentSession = session
  },
  
  SET_CONNECTION_STATUS(state, status) {
    state.isConnected = status
  },
  
  SET_TEST_RUNNING(state, running) {
    state.isTestRunning = running
  },
  
  SET_CURRENT_STATUS(state, status) {
    state.currentStatus = status
  },
  
  SET_AUDIO_DATA(state, audioData) {
    state.audioData = { ...state.audioData, ...audioData }
  },
  
  ADD_LOG(state, log) {
    state.logs.unshift(log)
    if (state.logs.length > 100) {
      state.logs = state.logs.slice(0, 100)
    }
  },
  
  SET_DEVICE_STATUS(state, devices) {
    state.deviceStatus = devices
  },
  
  SET_IOT_CONFIG(state, config) {
    state.iotConfig = { ...state.iotConfig, ...config }
  },
  
  SET_WEBSOCKET(state, ws) {
    state.websocket = ws
  },
  
  CLEAR_LOGS(state) {
    state.logs = []
  }
}

const actions = {
  // 获取会话列表
  async fetchSessions({ commit }) {
    try {
      const sessions = await agenticTestService.getSessions()
      commit('SET_SESSIONS', sessions.results || sessions)
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  },
  
  // 创建新会话
  async createSession({ commit, dispatch }, name) {
    try {
      const session = await agenticTestService.createSession(name)
      commit('SET_CURRENT_SESSION', session)
      await dispatch('fetchSessions')
      return session
    } catch (error) {
      console.error('Failed to create session:', error)
      throw error
    }
  },
  
  // 激活会话
  async activateSession({ commit }, sessionId) {
    try {
      await agenticTestService.activateSession(sessionId)
      const sessions = await agenticTestService.getSessions()
      const session = sessions.results ? 
        sessions.results.find(s => s.id === sessionId) :
        sessions.find(s => s.id === sessionId)
      if (session) {
        commit('SET_CURRENT_SESSION', session)
      }
    } catch (error) {
      console.error('Failed to activate session:', error)
    }
  },
  
  // WebSocket连接
  connectWebSocket({ commit, state }, sessionId) {
    if (state.websocket) {
      state.websocket.close()
    }
    
    const ws = agenticTestService.createWebSocketConnection(sessionId)
    
    ws.onopen = () => {
      commit('SET_CONNECTION_STATUS', true)
      commit('ADD_LOG', {
        type: 'system',
        content: 'WebSocket连接已建立',
        timestamp: Date.now()
      })
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'status':
          commit('SET_CURRENT_STATUS', data.content)
          break
        case 'log':
          commit('ADD_LOG', {
            type: 'log',
            content: data.content,
            timestamp: data.timestamp
          })
          break
        case 'audio_play':
          commit('SET_AUDIO_DATA', {
            isPlaying: true,
            audioType: data.metadata?.type || 'tts'
          })
          break
        case 'error':
          commit('ADD_LOG', {
            type: 'error',
            content: data.content,
            timestamp: data.timestamp
          })
          break
      }
    }
    
    ws.onclose = () => {
      commit('SET_CONNECTION_STATUS', false)
      commit('SET_TEST_RUNNING', false)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      commit('ADD_LOG', {
        type: 'error',
        content: 'WebSocket连接错误',
        timestamp: Date.now()
      })
    }
    
    commit('SET_WEBSOCKET', ws)
  },
  
  // 断开WebSocket
  disconnectWebSocket({ commit, state }) {
    if (state.websocket) {
      state.websocket.close()
      commit('SET_WEBSOCKET', null)
      commit('SET_CONNECTION_STATUS', false)
    }
  },
  
  // 开始测试
  startTest({ state }, query) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
      state.websocket.send(JSON.stringify({
        type: 'start_test',
        query
      }))
    }
  },
  
  // 停止测试
  stopTest({ state, commit }) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
      state.websocket.send(JSON.stringify({
        type: 'stop_test'
      }))
    }
    commit('SET_TEST_RUNNING', false)
  },
  
  // 发送音频数据
  sendAudioData({ state }, { audioData, format = 'webm' }) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
      state.websocket.send(JSON.stringify({
        type: 'audio_data',
        audio: audioData,
        format: format
      }))
    }
  },
  
  // 人工干预
  sendIntervention({ state }, message) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
      state.websocket.send(JSON.stringify({
        type: 'intervention',
        message
      }))
    }
  },
  
  // 更新音频特征
  updateAudioFeatures({ commit }, features) {
    commit('SET_AUDIO_DATA', { features })
  },
  
  // 更新IOT配置
  updateIOTConfig({ commit }, config) {
    commit('SET_IOT_CONFIG', config)
  },
  
  // 测试IOT连接
  async testIOTConnection(_, { token, familyId, env }) {
    try {
      const result = await agenticTestService.testIOTConnection(token, familyId, env)
      return result
    } catch (error) {
      console.error('IOT connection test failed:', error)
      return { success: false, error: error.message }
    }
  },
  
  // 获取家庭设备列表
  async getFamilyDevices({ state }) {
    try {
      if (!state.iotConfig.token || !state.iotConfig.familyId) {
        throw new Error('IOT配置不完整')
      }
      
      const devices = await agenticTestService.getFamilyDevices(
        state.iotConfig.familyId,
        state.iotConfig.token,
        state.iotConfig.env
      )
      return devices
    } catch (error) {
      console.error('Failed to get family devices:', error)
      throw error
    }
  },
  
  // 获取设备状态
  async getDeviceStatus({ state }, deviceGuid) {
    try {
      if (!state.iotConfig.token) {
        throw new Error('IOT Token未配置')
      }
      
      const status = await agenticTestService.getDeviceStatus(
        deviceGuid,
        state.iotConfig.token,
        state.iotConfig.env
      )
      return status
    } catch (error) {
      console.error('Failed to get device status:', error)
      throw error
    }
  }
}

const getters = {
  activeSessions: state => state.sessions.filter(s => s.is_active),
  recentLogs: state => state.logs.slice(0, 20),
  isConnectedAndReady: state => state.isConnected && state.currentSession
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}