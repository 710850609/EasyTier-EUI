/**
 * 图标工具函数
 * 支持多种图标来源：Varlet内置、@mdi/js、@mdi/light-js、图片路径
 * 
 * 图标配置格式：
 * 1. Varlet 内置图标: icon: 'format-list-checkbox' (字符串)
 * 2. @mdi/js 图标: icon: { type: 'mdi', name: 'mdiHome' } - name 为库的导出名称
 * 3. @mdi/light-js 图标: icon: { type: 'mdil/light', name: 'mdilPencil' } - name 为库的导出名称
 * 4. 图片路径: icon: './images/windows.svg'
 */

// 导入 @mdi/js 图标（按需导入，支持 Tree Shaking）
// import * as mdiIcons from '@mdi/js'

// 导入 @mdi/light-js 图标（轻量版）
// import * as mdilIcons from '@mdi/light-js'

// 改成 Tree Shaking 按需导入
import { mdiMicrosoftWindows, mdiAndroid, mdiPenguin, mdiLaptop, mdiApple, mdiCellphone, mdiAlphaFBox }  from '@mdi/js'
const mdiIcons = {
  mdiMicrosoftWindows,
  mdiAndroid,
  mdiPenguin,
  mdiLaptop,
  mdiApple,
  mdiCellphone,
  mdiAlphaFBox
}

/**
 * 获取图标路径
 * @param {string|Object} icon - 图标配置
 * @returns {Object|null} 图标信息对象
 */
export const getIconInfo = (icon) => {
  // 字符串类型：Varlet 内置图标或图片路径
  if (typeof icon === 'string') {
    // 图片路径
    if (icon.startsWith('./') || icon.startsWith('/') || icon.startsWith('http')) {
      return {
        type: 'image',
        src: icon
      }
    }
    // Varlet 内置图标
    return {
      type: 'varlet',
      name: icon
    }
  }

  // 对象类型：@mdi/js 或 @mdi/light-js
  if (typeof icon === 'object' && icon !== null) {
    const { type, name } = icon

    // @mdi/js 图标 - name 直接使用库的导出名称，如 'mdiHome'
    if (type === 'mdi') {
      const path = mdiIcons[name]
      if (path) {
        return {
          type: 'svg',
          path: path
        }
      }
      console.warn(`@mdi/js 图标 "${name}" 未找到，请检查导出名称是否正确`)
      return null
    }

    // @mdi/light-js 图标 - name 直接使用库的导出名称，如 'mdilPencil'
    if (type === 'mdil/light') {
      const path = mdilIcons[name]
      if (path) {
        return {
          type: 'svg',
          path: path
        }
      }
      console.warn(`@mdi/light-js 图标 "${name}" 未找到，请检查导出名称是否正确`)
      return null
    }
  }

  return null
}

/**
 * 获取 SVG 图标路径（便捷函数）
 * @param {Object} icon - 图标配置对象
 * @returns {string} SVG path
 */
export const getIconPath = (icon) => {
  const iconInfo = getIconInfo(icon)
  return iconInfo?.path || ''
}

/**
 * 判断是否为 Varlet 内置图标
 * @param {string|Object} icon
 */
export const isVarletIcon = (icon) => {
  return typeof icon === 'string' && !icon.startsWith('./') && !icon.startsWith('/') && !icon.startsWith('http')
}

/**
 * 判断是否为图片图标
 * @param {string|Object} icon
 */
export const isImageIcon = (icon) => {
  return typeof icon === 'string' && (icon.startsWith('./') || icon.startsWith('/') || icon.startsWith('http'))
}

/**
 * 判断是否为 SVG 图标（@mdi/js 或 @mdi/light-js）
 * @param {string|Object} icon
 */
export const isSvgIcon = (icon) => {
  return typeof icon === 'object' && icon !== null && (icon.type === 'mdi' || icon.type === 'mdil/light')
}

export default {
  getIconInfo,
  getIconPath,
  isVarletIcon,
  isImageIcon,
  isSvgIcon
}
