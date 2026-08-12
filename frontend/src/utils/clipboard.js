/**
 * 剪贴板工具函数
 * 支持读写剪贴板，兼容 HTTP/HTTPS 环境
 */

/**
 * 降级复制方案（使用 document.execCommand）
 * @param {string} text - 要复制的文本
 * @returns {boolean} - 是否复制成功
 */
const fallbackCopy = (text) => {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  textarea.style.top = '0'
  textarea.setAttribute('readonly', '')
  document.body.appendChild(textarea)
  textarea.select()
  textarea.setSelectionRange(0, text.length)
  
  try {
    const result = document.execCommand('copy')
    document.body.removeChild(textarea)
    return result
  } catch (e) {
    document.body.removeChild(textarea)
    return false
  }
}

/**
 * 降级读取方案（通过粘贴事件读取剪贴板）
 * @returns {Promise<string>} - 剪贴板文本内容
 */
const fallbackRead = () => {
  return new Promise((resolve, reject) => {
    const textarea = document.createElement('textarea')
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.style.top = '0'
    textarea.setAttribute('readonly', '')
    document.body.appendChild(textarea)
    textarea.focus()

    const onPaste = (e) => {
      const text = e.clipboardData?.getData('text') || ''
      cleanup()
      resolve(text)
    }
    const onTimeout = () => {
      cleanup()
      reject(new Error('Clipboard read timeout'))
    }
    const cleanup = () => {
      textarea.removeEventListener('paste', onPaste)
      clearTimeout(timeout)
      document.body.removeChild(textarea)
    }

    textarea.addEventListener('paste', onPaste)
    const timeout = setTimeout(onTimeout, 10000)
  })
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} - 是否复制成功
 */
export const copyToClipboard = async (text) => {
  if (!text) return false
  
  // 尝试使用现代 API（仅在 HTTPS 下可用）
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      return fallbackCopy(text)
    }
  }
  
  // 使用降级方案
  return fallbackCopy(text)
}

/**
 * 从剪贴板读取文本
 * Android WebView 中 navigator.clipboard 不可用，需通过原生桥接
 * @returns {Promise<string>} - 剪贴板文本内容
 * @throws {Error} - 读取失败时抛出异常
 */
export const readFromClipboard = async () => {
  if (window.AndroidBridge && window.AndroidBridge.readClipboard) {
    return await window.AndroidBridge.readClipboard()
  }
  if (navigator.clipboard && window.isSecureContext) {
    return await navigator.clipboard.readText()
  }
  return await fallbackRead()
}


export default {
  copyToClipboard,
  readFromClipboard
}