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

/**
 * IPv6 地址正则（RFC 4291，支持 :: 压缩形式）
 */
const IPV6_REGEX = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$/

/**
 * 验证是否为合法的 IPv6 地址
 * @param {string} addr - IPv6 地址
 * @returns {boolean}
 */
export function isValidIPv6(addr) {
  if (!addr || typeof addr !== 'string') return false
  return IPV6_REGEX.test(addr.trim())
}

/**
 * 验证是否为合法的 IPv6 CIDR 格式（如 2001:db8::/64）
 * @param {string} cidr - IPv6 CIDR 地址
 * @returns {boolean}
 */
export function isValidIpv6Cidr(cidr) {
  if (!cidr || typeof cidr !== 'string') return false
  const parts = cidr.trim().split('/')
  if (parts.length !== 2) return false
  const [addr, prefixStr] = parts
  if (!isValidIPv6(addr)) return false
  if (!/^\d{1,3}$/.test(prefixStr)) return false
  const prefix = parseInt(prefixStr, 10)
  return prefix >= 0 && prefix <= 128
}