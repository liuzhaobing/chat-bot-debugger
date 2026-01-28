/**
 * Agentic Test 服务
 * 处理与后端API的通信
 */

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'

class AgenticTestService {
  /**
   * 获取会话列表
   */
  async getSessions() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/sessions/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      throw error
    }
  }

  /**
   * 创建新会话
   */
  async createSession(name) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/sessions/create_session/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to create session:', error)
      throw error
    }
  }

  /**
   * 激活会话
   */
  async activateSession(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/sessions/${sessionId}/activate/`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to activate session:', error)
      throw error
    }
  }

  /**
   * 获取会话日志
   */
  async getSessionLogs(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/sessions/${sessionId}/logs/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch session logs:', error)
      throw error
    }
  }

  /**
   * 获取设备状态列表
   */
  async getDeviceStatusList() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/devices/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch device status:', error)
      throw error
    }
  }

  /**
   * 获取设备状态摘要
   */
  async getDeviceStatusSummary() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/devices/summary/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch device status summary:', error)
      throw error
    }
  }

  /**
   * 创建WebSocket连接
   */
  createWebSocketConnection(sessionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/agentic-test/${sessionId}/`
    return new WebSocket(wsUrl)
  }

  /**
   * 测试IOT连接
   */
  async testIOTConnection(token, familyId, env = 'test') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/iot/test-connection/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          iot_token: token,
          family_id: familyId,
          env: env
        })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to test IOT connection:', error)
      throw error
    }
  }

  /**
   * 获取家庭设备列表
   */
  async getFamilyDevices(familyId, token, env = 'test') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/iot/family-devices/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          family_id: familyId,
          iot_token: token,
          env: env
        })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to get family devices:', error)
      throw error
    }
  }

  /**
   * 获取设备状态详情
   */
  async getDeviceStatus(deviceGuid, token, env = 'test') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/iot/device-status/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          device_guid: deviceGuid,
          iot_token: token,
          env: env
        })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to get device status:', error)
      throw error
    }
  }
}

export default new AgenticTestService()