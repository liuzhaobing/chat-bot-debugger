// API基础路径配置
export const API_BASE_PATH = '/abp/manager'

// 获取完整API路径
export const getApiUrl = (path) => `${API_BASE_PATH}${path}`