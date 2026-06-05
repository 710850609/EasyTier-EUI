/**
 * 配色配置文件
 * 清新蓝绿主题 - 适配 Varlet 官方 CSS 变量规范
 * @see https://www.varletjs.com/#/zh-CN/themes
 */

// 清新蓝绿 - 亮色主题
export const freshLightTheme = {
  // 主色调 - 活力亮蓝
  '--color-primary': '#0284c7',
  '--color-on-primary': '#ffffff',
  '--color-primary-container': '#e0f2fe',
  '--color-on-primary-container': '#075985',

  // 信息色 - 天蓝
  '--color-info': '#06b6d4',
  '--color-on-info': '#ffffff',
  '--color-info-container': '#cffafe',
  '--color-on-info-container': '#0e7490',

  // 成功色 - 鲜艳绿
  '--color-success': '#059669',
  '--color-on-success': '#ffffff',
  '--color-success-container': '#d1fae5',
  '--color-on-success-container': '#065f46',

  // 警告色 - 活力橙
  '--color-warning': '#ea580c',
  '--color-on-warning': '#ffffff',
  '--color-warning-container': '#ffedd5',
  '--color-on-warning-container': '#9a3412',

  // 错误色 - 活力红
  '--color-danger': '#ef4444',
  '--color-on-danger': '#ffffff',
  '--color-danger-container': '#fee2e2',
  '--color-on-danger-container': '#b91c1c',

  // 禁用状态
  '--color-disabled': '#e2e8f0',
  '--color-text-disabled': '#94a3b8',

  // 背景色 - 使用 Varlet 规范变量名（更有活力的浅色调）
  '--color-body': '#f0f9ff',
  '--color-surface': '#ffffff',
  '--color-surface-container': '#e0f2fe',
  '--color-surface-container-low': '#f0f9ff',
  '--color-surface-container-high': '#bae6fd',
  '--color-surface-container-highest': '#7dd3fc',

  // 文字色（调整为更柔和的深灰色）
  '--color-text': '#2d3748',
  '--color-on-surface': '#2d3748',
  '--color-on-surface-variant': '#5a6578',

  // 反色
  '--color-inverse-surface': '#1e293b',

  // 边框和轮廓（清新蓝调）
  '--color-outline': '#7dd3fc',
  '--color-outline-variant': '#bae6fd',

  // Snackbar/Toast 样式
  '--snackbar-background': '#e2e8f0',
  '--snackbar-color': '#1e293b',
  '--snackbar-info-background': '#cbd5e1',
  '--snackbar-success-background': '#07c160',
  '--snackbar-success-color': '#ffffff',

  // Dialog 样式
  '--dialog-title-color': '#0284c7',
  '--result-background': '#fff',
  '--result-description-color': 'var(--color-text)',
}

// 清新蓝绿 - 暗色主题
export const freshDarkTheme = {
  // 主色调 - 亮蓝
  '--color-primary': '#38bdf8',
  '--color-on-primary': '#0c4a6e',
  '--color-primary-container': '#075985',
  '--color-on-primary-container': '#e0f2fe',

  // 信息色 - 亮青
  '--color-info': '#22d3ee',
  '--color-on-info': '#164e63',
  '--color-info-container': '#155e75',
  '--color-on-info-container': '#cffafe',

  // 成功色 - 亮绿
  '--color-success': '#34d399',
  '--color-on-success': '#064e3b',
  '--color-success-container': '#065f46',
  '--color-on-success-container': '#d1fae5',

  // 警告色 - 亮橙
  '--color-warning': '#fbbf24',
  '--color-on-warning': '#78350f',
  '--color-warning-container': '#92400e',
  '--color-on-warning-container': '#fef3c7',

  // 错误色 - 亮红
  '--color-danger': '#f87171',
  '--color-on-danger': '#7f1d1d',
  '--color-danger-container': '#991b1b',
  '--color-on-danger-container': '#fee2e2',

  // 禁用状态
  '--color-disabled': '#334155',
  '--color-text-disabled': '#64748b',

  // 背景色 - 使用 Varlet 规范变量名
  '--color-body': '#0f172a',
  '--color-surface': '#1e293b',
  '--color-surface-container': '#334155',
  '--color-surface-container-low': '#1e293b',
  '--color-surface-container-high': '#475569',
  '--color-surface-container-highest': '#64748b',

  // 文字色
  '--color-text': '#f8fafc',
  '--color-on-surface': '#f8fafc',
  '--color-on-surface-variant': '#94a3b8',

  // 反色
  '--color-inverse-surface': '#f8fafc',

  // 边框和轮廓
  '--color-outline': '#475569',
  '--color-outline-variant': '#334155',

  // Snackbar/Toast 样式
  '--snackbar-background': '#1e293b',
  '--snackbar-color': 'rgba(255, 255, 255, 0.87)',
  '--snackbar-info-background': '#334155',
  '--snackbar-success-background': '#2ba245',
  '--snackbar-success-color': '#000000',

  // Dialog 样式
  '--dialog-title-color': '#0284c7',
  '--result-background': '#1e293b',
  '--result-description-color': 'var(--color-text)',
}
