/**
 * API 请求封装
 * 统一管理 HTTP 请求和基础路径
 */
import toast from '../components/toast.js'

// 使用 Vite 注入的环境变量
const API_BASE = typeof __API_BASE__ !== 'undefined' ? __API_BASE__ : '/'
// console.log(API_BASE)

// 活跃的 AbortController 映射，用于取消请求
const pendingControllers = new Map()

// 清理超时的请求
function cleanupTimeout() {
  const now = Date.now()
  for (const [key, { timestamp, controller }] of pendingControllers) {
    if (now - timestamp > 60000) { // 超过60秒的自动清理
      pendingControllers.delete(key)
    }
  }
}

// 定期清理
setInterval(cleanupTimeout, 30000)

function getFullUrl(url, data) {
  url = url.startsWith('http') ? url : `${API_BASE}${url}`
  let search_parts = ''
  Object.keys(data || {}).forEach(key => {
    search_parts += `&${key}=${data[key]}`
  })
  if (url.indexOf('?') > 0) {
    url += search_parts
  } else {
    url += '?' + search_parts.substring(1)
  }
  return url
}

/**
 * 取消指定请求
 * @param {string} requestId - 请求唯一标识
 */
export function cancelRequest(requestId) {
  const controller = pendingControllers.get(requestId)
  if (controller) {
    controller.abort()
    pendingControllers.delete(requestId)
    console.log(`Request ${requestId} cancelled`)
  }
}

/**
 * 取消所有活跃请求
 */
export function cancelAllRequests() {
  for (const [, { controller }] of pendingControllers) {
    controller.abort()
  }
  pendingControllers.clear()
  console.log('All requests cancelled')
}

/**
 * 发送 HTTP 请求
 * @param {string} url - 请求路径（会自动拼接 API_BASE）
 * @param {Object} options - fetch 选项
 * @param {Object} otherOptions - 其他选项
 * @param {number} otherOptions.timeout - 请求超时时间(ms)，默认30000
 * @param {string} otherOptions.requestId - 请求唯一标识，用于取消
 * @returns {Promise} - 返回响应数据
 */
async function request(url, options = {}, otherOptions = {}) {
  const toastError = (otherOptions.toastError === undefined || otherOptions.toastError == null) ? true : otherOptions.toastError
  const fullUrl = getFullUrl(url)
  const requestId = otherOptions.requestId || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  const timeout = otherOptions.timeout || 30000 // 默认30秒超时
  
  // 创建新的 AbortController
  const controller = new AbortController()
  const signal = controller.signal
  
  // 保存控制器
  pendingControllers.set(requestId, { controller, timestamp: Date.now() })
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    signal
  }
  
  let timeoutId
  
  try {
    // 设置超时
    timeoutId = setTimeout(() => {
      controller.abort()
      console.warn(`Request to ${fullUrl} timed out after ${timeout}ms`)
    }, timeout)
    
    const response = await fetch(fullUrl, { ...defaultOptions, ...options })
    
    clearTimeout(timeoutId)
    
    const contentType = response.headers.get('content-type')
    if (!response.ok) {
      console.error(response)
      if (contentType && contentType.includes('application/json')) {
        return await response.json().then(data => {
          throw new Error(data.data || 'Status error 500')
        })
      } else {
        throw new Error(`HTTP status: ${response.status}\n${fullUrl}`)
      }
    }    
    // 根据响应类型解析数据
    if (contentType && contentType.includes('application/json')) {
      return await response.json().then(data => {
        if (data.code === 0) {
          return data
        }
        throw new Error(data.data || 'API error')
      })
    }
    return await response.text()
  } catch (error) {
    if (error.name === 'AbortError') {
      console.warn(`Request ${requestId} was cancelled`)
      // 取消操作不提示错误
      throw error
    }
    
    console.error('API request failed:', error)
    if (toastError) {
      toast.error(error.message)
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
    pendingControllers.delete(requestId)
  }
}

/**
 * GET 请求
 * @param {string} url - 请求路径
 * @param {Object} params - URL 参数
 * @param {Object} otherOptions - 其他选项
 * @param {number} otherOptions.timeout - 超时时间
 * @param {string} otherOptions.requestId - 请求标识
 * @returns {Promise}
 */
export function get(url, params = {}, otherOptions = {}) {
  const queryString = new URLSearchParams(params).toString()
  const fullUrl = queryString ? `${url}?${queryString}` : url
  return request(fullUrl, { method: 'GET' }, otherOptions)
}

/**
 * POST 请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求体数据
 * @param {Object} options - fetch 选项
 * @param {Object} otherOptions - 其他选项
 * @returns {Promise}
 */
export function post(url, data = {}, options = {}, otherOptions = {}) {
  return request(url, {
    method: 'POST',
    body: JSON.stringify(data),
    ...options
  }, otherOptions)
}

/**
 * PUT 请求
 * @param {string} url - 请求路径
 * @param {Object} data - 请求体数据
 * @param {Object} options - fetch 选项
 * @param {Object} otherOptions - 其他选项
 * @returns {Promise}
 */
export function put(url, data = {}, options = {}, otherOptions = {}) {
  return request(url, {
    method: 'PUT',
    body: JSON.stringify(data),
    ...options  
  }, otherOptions)
}

/**
 * DELETE 请求
 * @param {string} url - 请求路径
 * @param {Object} options - fetch 选项
 * @param {Object} otherOptions - 其他选项
 * @returns {Promise}
 */
export function del(url, options = {}, otherOptions = {}) {
  return request(url, { method: 'DELETE', ...options }, otherOptions) 
}

// API 接口定义
export const api = {
  // 节点相关
  monitor: {
    getList: (params = {}) => get('/monitor/list', params, {toastError: false}),
  },
  
  // 配置相关
  configs: {
    save: (data) => post('/configs/save', data, {}, {toastError: false}),
    saveToml: (data) => post('/configs/save_toml', data),
    get: (profile) => get('/configs/get', profile ? { profile: profile } : {}),
    getToml: (profile) => get('/configs/get_toml', profile ? { profile } : {}),
    getShareConfigDownloadUrl: (profile) => getFullUrl('/configs/download_share_config', profile ? { profile } : {}),
    getShareConfigStr: (profile) => get('/configs/get_share_config_str', profile ? { profile } : {}),
    listConfigStatus: () => get('/configs/list_config_status', {}, {toastError: false}),
    listConfigFiles: () => get('/configs/list_config_files', {}, {toastError: false}),
    delete: (profile) => post('/configs/delete', { profile }, {toastError: false}),
    rename: (oldProfile, newProfile) => post('/configs/rename', { oldProfile, newProfile }, {toastError: false}),
    getLanIps: () => get('/configs/list_lan_ips', {}),
  },
  peers: {
    checkPeers: (params = {}) => get('/peers/check_peers', params),
    publicPeers: (params = {}) => get('/peers/public_peers', params),
    setPeerSource: (params = {}) => post('/peers/set_peer_source', params),
    getPeerSource: (params = {}) => post('/peers/get_peer_source', params),
  },
  // 服务相关
  services: {
    status: (profile) => get('/services/status', { profile: profile }),
    restart: (profile) => post('/services/restart', { profile: profile }),
    start: (profile) => post('/services/start', { profile: profile }, {toastError: false}),
    stop: (profile) => post('/services/stop', { profile: profile }),
    systemService: (profile, enabled) => post('/services/system_service', { profile, enabled }),
    autoStart: (profile, enabled) => post('/services/auto_start', { profile, enabled }),
  },
  
  // 窗口相关
  windows: {
    getDownloadMgrProUrl: (data) => getFullUrl('/windows/download_mgr_pro', data)
  },

  // easytier-lite 相关
  etEui: {
    getDownloadEasyTierEuiUrl: (data) => getFullUrl('/et_eui/download_easytier_eui', data),
    update: (data) => post('/et_eui/update', data),
    getReleaseInfo: (data) => post('/et_eui/get_release_info', data),
  },
  // ET 核心相关
  etCore: {
    getVersion: () => get('/et_core/version'),
    // getReleaseInfo: (data) => get('/et_core/get_release_info', data),
    getVersionList: (params = {}) => get('/et_core/version_list', params),
    install: (data) => post('/et_core/install', data),
    getEtLogLevel: (params = {}) => get('/et_core/get_log_level', params),
    setEtLogLevel: (params = {}) => post('/et_core/set_log_level', params),
  },
  // 设置相关
  settings: {
    shutdown: () => post('/settings/shutdown'),
    getEuiInfo: () => get('/settings/eui_info'),
    getGithubMirrors: (params = {}) => get('/settings/github_mirrors', params),
    deleteCache: () => post('/settings/delete_cache'),
  }
}

// 导出基础配置
export { API_BASE }
export default api
