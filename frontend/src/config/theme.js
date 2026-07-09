/**
 * 主题管理模块
 * 统一管理主题相关的逻辑和状态
 * 使用 Varlet StyleProvider 进行主题定制
 * @see https://www.varletjs.com/#/zh-CN/themes
 */

import { ref } from 'vue'
import { StyleProvider } from '@varlet/ui'
import { freshLightTheme, freshDarkTheme } from './colors.js'
import { THEME_MODE_KEY } from './storage-keys.js'

// localStorage key
const STORAGE_KEY = THEME_MODE_KEY

// 主题状态
const isDark = ref(false)
const themeMode = ref('system') // 'system' | 'light' | 'dark'

// 获取系统主题偏好
const getSystemTheme = () => {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

// 应用主题 - 使用 Varlet StyleProvider
const applyTheme = (mode) => {
  themeMode.value = mode
  const shouldBeDark = mode === 'dark' || (mode === 'system' && getSystemTheme())
  isDark.value = shouldBeDark

  // 获取主题配置
  const theme = shouldBeDark ? freshDarkTheme : freshLightTheme
  // const theme = shouldBeDark ? Themes.md3Dark : Themes.md3Light

  // 使用 Varlet StyleProvider 应用主题
  StyleProvider(theme)

  // 同步设置 CSS 变量到 html 元素，确保非 Varlet 组件也能使用
  const root = document.documentElement
  Object.entries(theme).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })

  // 设置 dark class 用于自定义样式
  document.documentElement.classList.toggle('dark', shouldBeDark)
}

// 保存主题设置到 localStorage
const saveTheme = (mode) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    mode,
    isDark: isDark.value
  }))
}

// 从 localStorage 加载主题设置
const loadTheme = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const { mode } = JSON.parse(saved)
      if (mode && ['system', 'light', 'dark'].includes(mode)) {
        applyTheme(mode)
        return mode
      }
    } catch (error) {
      console.error('解析主题设置失败:', error)
    }
  }
  // 默认使用系统主题
  applyTheme('system')
  return 'system'
}

// 切换主题模式
export const setThemeMode = (mode) => {
  applyTheme(mode)
  saveTheme(mode)
}

// 监听系统主题变化
const listenSystemThemeChange = () => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const handler = () => {
    if (themeMode.value === 'system') {
      applyTheme('system')
    }
  }
  mediaQuery.addEventListener('change', handler)
}

// 模块加载时自动初始化主题
const init = () => {
  loadTheme()
  listenSystemThemeChange()
}

// 执行初始化（在 DOM 就绪后）
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
}

// 主题选项配置
export const themeOptions = [
  { label: 'settings.theme.auto', value: 'system', icon: 'palette-outline' },
  { label: 'settings.theme.light', value: 'light', icon: 'white-balance-sunny' },
  { label: 'settings.theme.dark', value: 'dark', icon: 'weather-night' }
]

// 对外导出响应式状态
export { isDark, themeMode }