import { Snackbar, Icon } from '@varlet/ui'
import { h } from 'vue'
import i18n from '../locales/index.js'

const { t } = i18n.global

// 类型映射
const typeMap = {
  'default': '',
  'success': 'success',
  'warning': 'warning',
  'error': 'error',
  'info': 'primary',
  'loading': 'loading'
}

Snackbar.allowMultiple(true)

// 创建 Toast（clear 方法幂等）
function createToast(message, type = 'default', duration = 3000) {
  const snackbar = Snackbar({
    content: message,
    type: typeMap[type] || '',
    position: 'top',
    duration: duration,
    contentClass: 'toast-content',
    icon: () => type === 'loading' ? 'loading' : '',
    action: () =>
      h(Icon, {
        name: 'window-close',
        size: '20',
        style: { cursor: 'pointer', marginLeft: '8px' },
        onClick: () => {
            snackbar.clear()
          }
      })
  })
  return snackbar
}

// 导出直接可用的函数
export const toast = {
  success(message, duration = 3000) {
    return createToast(message, 'success', duration)
  },

  error(message, duration = 5000) {
    return createToast(message, 'error', duration)
  },

  warning(message, duration = 3000) {
    return createToast(message, 'warning', duration)
  },

  info(message, duration = 3000) {
    return createToast(message, 'info', duration)
  },

  loading(message = t('common.loading'), duration = 0) {
    return createToast(message, 'loading', duration)
  }
}

export default toast