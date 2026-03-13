/**
 * 场景测试服务
 * 处理测试任务相关的API通信
 */

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'

class SceneTestService {
  /**
   * 获取测试任务列表
   */
  async getTestTasks() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch test tasks:', error)
      throw error
    }
  }

  /**
   * 创建测试任务
   */
  async createTestTask(data) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to create test task:', error)
      throw error
    }
  }

  /**
   * 获取测试任务详情
   */
  async getTestTaskDetail(taskId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/${taskId}/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch test task detail:', error)
      throw error
    }
  }

  /**
   * 更新测试任务
   */
  async updateTestTask(taskId, data) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/${taskId}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to update test task:', error)
      throw error
    }
  }

  /**
   * 删除测试任务
   */
  async deleteTestTask(taskId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/${taskId}/`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return true
    } catch (error) {
      console.error('Failed to delete test task:', error)
      throw error
    }
  }

  /**
   * 启动测试任务
   */
  async startTestTask(taskId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/test-tasks/${taskId}/start/`, {
        method: 'POST'
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to start test task:', error)
      throw error
    }
  }

  /**
   * 获取TTS音色列表
   */
  async getTTSVoices() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts-voices/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch TTS voices:', error)
      throw error
    }
  }

  /**
   * TTS试听
   * @param {string} voiceId - TTS音色ID
   * @param {string} text - 试听文本
   * @returns {string} base64音频数据 (wav格式)
   */
  async previewTTS(voiceId, text) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts-voices/${voiceId}/invoke/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, sample_rate: 24000 })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      // 后端返回的是 base64 音频数据，不是 URL
      if (data.status === 'success' && data.audio) {
        return data.audio  // 返回 base64 音频数据
      }
      throw new Error(data.error || 'TTS synthesis failed')
    } catch (error) {
      console.error('Failed to preview TTS:', error)
      throw error
    }
  }

  /**
   * 获取设备协议列表
   */
  async getDeviceProtocols() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agentic-test/device-protocols/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch device protocols:', error)
      throw error
    }
  }
}

export default new SceneTestService()
