/**
 * 验证工具函数
 */
import i18n from '../locales/index.js'

const { t } = i18n.global

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
export function validateIP(ip, label = t('validate.ip')) {
  if (!ip || !ip.trim()) {
    return t('validate.required', { label })
  }
  if (!isValidIP(ip.trim())) {
    return t('validate.invalid_format', { label })
  }
  return null
}

/**
 * 验证 IP:端口 格式，返回错误信息或 null
 * @param {string} addr - 地址，格式如 0.0.0.0:1111
 * @param {string} label - 字段名称，用于错误提示
 * @returns {string|null}
 */
export function validateIPPort(addr, label = t('validate.address')) {
  if (!addr || !addr.trim()) {
    return t('validate.required', { label })
  }
  if (!isValidIPPort(addr.trim())) {
    return t('validate.invalid_ip_port_format', { label })
  }
  return null
}