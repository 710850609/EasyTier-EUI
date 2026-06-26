/**
 * 验证工具函数
 */

/**
 * 验证是否为合法的 IPv4 地址
 * @param {string} ip - IP 地址
 * @returns {boolean}
 */
export function isValidIP(ip) {
  if (!ip || typeof ip !== 'string') return false
  const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d{2}|0|[1-9]\d?)\.(25[0-5]|2[0-4]\d|1\d{2}|0|[1-9]\d?)\.(25[0-5]|2[0-4]\d|1\d{2}|0|[1-9]\d?)\.(25[0-5]|2[0-4]\d|1\d{2}|0|[1-9]\d?)$/
  return ipv4Regex.test(ip)
}

/**
 * 验证是否为合法的 IP:端口 格式
 * @param {string} addr - 地址，格式如 0.0.0.0:1111
 * @returns {boolean}
 */
export function isValidIPPort(addr) {
  if (!addr || typeof addr !== 'string') return false
  const parts = addr.split(':')
  if (parts.length !== 2) return false
  const [ip, port] = parts
  if (!isValidIP(ip)) return false
  const portNum = parseInt(port, 10)
  if (isNaN(portNum) || portNum < 1 || portNum > 65535) return false
  if (port !== String(portNum)) return false
  return true
}

/**
 * 验证 IP 地址，返回错误信息或 null
 * @param {string} ip - IP 地址
 * @param {string} label - 字段名称，用于错误提示
 * @returns {string|null}
 */
export function validateIP(ip, label = 'IP地址') {
  if (!ip || !ip.trim()) {
    return `${label}不能为空`
  }
  if (!isValidIP(ip.trim())) {
    return `${label}格式不正确`
  }
  return null
}

/**
 * 验证 IP:端口 格式，返回错误信息或 null
 * @param {string} addr - 地址，格式如 0.0.0.0:1111
 * @param {string} label - 字段名称，用于错误提示
 * @returns {string|null}
 */
export function validateIPPort(addr, label = '地址') {
  if (!addr || !addr.trim()) {
    return `${label}不能为空`
  }
  if (!isValidIPPort(addr.trim())) {
    return `${label}格式不正确，正确格式: IP:端口 (如 0.0.0.0:1111)`
  }
  return null
}