/**
 * WebSocket 服务配置
 * Worker 服务独立部署，前端直接连接
 */

// Worker 服务配置
export const WORKER_CONFIG = {
  // WebSocket 基础 URL
  WS_BASE_URL: process.env.VUE_APP_WORKER_WS_URL || 'ws://localhost:8001',

  // HTTP 基础 URL (用于健康检查等)
  HTTP_BASE_URL: process.env.VUE_APP_WORKER_HTTP_URL || 'http://localhost:8001',

  // WebSocket 端点路径
  ENDPOINTS: {
    AGENTIC_TEST: '/ws/agentic-test',
    VAD_ASR_TEST: '/ws/agentic-test/vad-asr-test'
  }
}

/**
 * 获取 WebSocket 完整 URL
 * @param {string} sessionId - 会话 ID
 * @returns {string} WebSocket URL
 */
export const getAgenticTestWsUrl = (sessionId) => {
  return `${WORKER_CONFIG.WS_BASE_URL}${WORKER_CONFIG.ENDPOINTS.AGENTIC_TEST}/${sessionId}/`
}

/**
 * 获取 VAD+ASR 测试 WebSocket URL
 * @param {string} appId - App ID (可选)
 * @returns {string} WebSocket URL
 */
export const getVadAsrTestWsUrl = (appId = '4f95e97b0ec641fab9772b68a81bcf4a') => {
  return `${WORKER_CONFIG.WS_BASE_URL}${WORKER_CONFIG.ENDPOINTS.VAD_ASR_TEST}/?app_id=${appId}`
}

/**
 * 获取 Worker 健康检查 URL
 * @returns {string} 健康检查 URL
 */
export const getWorkerHealthUrl = () => {
  return `${WORKER_CONFIG.HTTP_BASE_URL}/health`
}

export default WORKER_CONFIG