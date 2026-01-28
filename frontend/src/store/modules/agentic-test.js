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
  
  // 语音识别和转录
  transcriptMessages: [],
  isListening: false,
  currentTranscript: '',
  
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
  websocket: null,
  connectionStatus: 'disconnected', // 'disconnected' | 'connecting' | 'connected' | 'active'
  
  // 会话状态
  sessionActive: false,
  sessionDuration: 0,
  audioLevel: 0,
  isMuted: false
}

const mutations = {
  SET_SESSIONS(state, sessions) {
    state.sessions = sessions
  },
  
  SET_CURRENT_SESSION(state, session) {
    state.currentSession = session
  },
  
  SET_CONNECTION_STATUS(state, status) {
    state.isConnected = status === 'connected' || status === 'active'
    state.connectionStatus = status
  },
  
  SET_SESSION_ACTIVE(state, active) {
    state.sessionActive = active
  },
  
  SET_SESSION_DURATION(state, duration) {
    state.sessionDuration = duration
  },
  
  SET_AUDIO_LEVEL(state, level) {
    state.audioLevel = level
  },
  
  SET_MUTED(state, muted) {
    state.isMuted = muted
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
  
  SET_LISTENING(state, listening) {
    state.isListening = listening
  },
  
  SET_CURRENT_TRANSCRIPT(state, transcript) {
    state.currentTranscript = transcript
  },
  
  ADD_TRANSCRIPT_MESSAGE(state, message) {
    state.transcriptMessages.push(message)
    // 限制消息数量
    if (state.transcriptMessages.length > 100) {
      state.transcriptMessages = state.transcriptMessages.slice(-100)
    }
  },
  
  UPDATE_TRANSCRIPT_MESSAGE(state, { index, message }) {
    if (index >= 0 && index < state.transcriptMessages.length) {
      state.transcriptMessages.splice(index, 1, message)
    }
  },
  
  CLEAR_TRANSCRIPT_MESSAGES(state) {
    state.transcriptMessages = []
  },
  
  ADD_LOG(state, log) {
    state.logs.unshift(log)
    if (state.logs.length > 200) {
      state.logs = state.logs.slice(0, 200)
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
  
  // 启动会话
  startSession({ commit }) {
    commit('SET_SESSION_ACTIVE', true)
    commit('SET_CONNECTION_STATUS', 'active')
  },
  
  // 停止会话
  stopSession({ commit }) {
    commit('SET_SESSION_ACTIVE', false)
    commit('SET_CONNECTION_STATUS', 'disconnected')
    commit('SET_SESSION_DURATION', 0)
    commit('SET_AUDIO_LEVEL', 0)
    commit('SET_LISTENING', false)
  },
  
  // 更新会话时长
  updateSessionDuration({ commit }, duration) {
    commit('SET_SESSION_DURATION', duration)
  },
  
  // 更新音频级别
  updateAudioLevel({ commit }, level) {
    commit('SET_AUDIO_LEVEL', level)
  },
  
  // 切换静音状态
  toggleMute({ commit, state }) {
    const newMutedState = !state.isMuted
    commit('SET_MUTED', newMutedState)
    return newMutedState
  },
  
  // WebSocket连接
  connectWebSocket({ commit, state }, sessionId) {
    if (state.websocket) {
      state.websocket.close()
    }
    
    const ws = agenticTestService.createWebSocketConnection(sessionId)
    
    ws.onopen = () => {
      commit('SET_CONNECTION_STATUS', 'connected')
      commit('ADD_LOG', {
        id: Date.now(),
        category: 'websocket',
        level: 'success',
        message: 'WebSocket连接已建立',
        timestamp: Date.now()
      })
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'status':
          commit('SET_CURRENT_STATUS', data.content)
          break
        case 'transcript_partial':
          commit('SET_CURRENT_TRANSCRIPT', data.content)
          commit('SET_LISTENING', true)
          break
        case 'transcript_final':
          commit('ADD_TRANSCRIPT_MESSAGE', {
            id: Date.now(),
            type: 'user',
            content: data.content,
            confidence: data.confidence,
            timestamp: Date.now(),
            isPartial: false,
            isFinal: true
          })
          commit('SET_CURRENT_TRANSCRIPT', '')
          commit('SET_LISTENING', false)
          break
        case 'ai_response':
          commit('ADD_TRANSCRIPT_MESSAGE', {
            id: Date.now(),
            type: 'agent',
            content: data.content,
            timestamp: Date.now(),
            isPartial: false,
            isFinal: true
          })
          break
        case 'ai_response_partial': {
          // 更新最后一条AI消息或创建新的
          const lastMessage = state.transcriptMessages[state.transcriptMessages.length - 1]
          if (lastMessage && lastMessage.type === 'agent' && lastMessage.isPartial) {
            commit('UPDATE_TRANSCRIPT_MESSAGE', {
              index: state.transcriptMessages.length - 1,
              message: {
                ...lastMessage,
                content: data.content,
                timestamp: Date.now()
              }
            })
          } else {
            commit('ADD_TRANSCRIPT_MESSAGE', {
              id: Date.now(),
              type: 'agent',
              content: data.content,
              timestamp: Date.now(),
              isPartial: true,
              isFinal: false
            })
          }
          break
        }
        case 'log':
          commit('ADD_LOG', {
            id: Date.now(),
            category: data.category || 'system',
            level: data.level || 'info',
            message: data.content,
            details: data.details,
            timestamp: data.timestamp || Date.now()
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
            id: Date.now(),
            category: 'error',
            level: 'error',
            message: data.content,
            details: data.details,
            timestamp: data.timestamp || Date.now()
          })
          break
      }
    }
    
    ws.onclose = () => {
      commit('SET_CONNECTION_STATUS', 'disconnected')
      commit('SET_SESSION_ACTIVE', false)
      commit('ADD_LOG', {
        id: Date.now(),
        category: 'websocket',
        level: 'warning',
        message: 'WebSocket连接已断开',
        timestamp: Date.now()
      })
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      commit('ADD_LOG', {
        id: Date.now(),
        category: 'websocket',
        level: 'error',
        message: 'WebSocket连接错误',
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
      commit('SET_CONNECTION_STATUS', 'disconnected')
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
  sendAudioData({ state }, { audioData, format = 'webm', isComplete = false }) {
    if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
      state.websocket.send(JSON.stringify({
        type: 'audio_data',
        audio: audioData,
        format: format,
        is_complete: isComplete,
        timestamp: Date.now()
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
  
  // 添加转录消息
  addTranscriptMessage({ commit }, message) {
    commit('ADD_TRANSCRIPT_MESSAGE', {
      id: Date.now() + Math.random(),
      timestamp: Date.now(),
      ...message
    })
  },
  
  // 清空转录消息
  clearTranscriptMessages({ commit }) {
    commit('CLEAR_TRANSCRIPT_MESSAGES')
  },
  
  // 添加日志
  addLog({ commit }, { category, level, message, details = null }) {
    commit('ADD_LOG', {
      id: Date.now() + Math.random(),
      category,
      level,
      message,
      details,
      timestamp: Date.now()
    })
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
  isConnectedAndReady: state => state.isConnected && state.currentSession,
  isSessionActive: state => state.sessionActive,
  connectionStatus: state => state.connectionStatus,
  currentAudioLevel: state => state.audioLevel,
  isMuted: state => state.isMuted,
  transcriptMessages: state => state.transcriptMessages,
  isListening: state => state.isListening,
  currentTranscript: state => state.currentTranscript,
  sessionDuration: state => state.sessionDuration
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}