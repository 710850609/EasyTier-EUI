/**
 * 配色配置文件
 * 电光蓝主题 - 现代清爽，适配年轻人审美
 * @see https://www.varletjs.com/#/zh-CN/themes
 */

// 电光蓝 - 亮色主题
export const freshLightTheme = {
  // 主色调 - 电光蓝，Apple/Stripe 风格
  '--color-primary': '#2563eb',
  '--color-on-primary': '#ffffff',
  '--color-primary-container': '#dbeafe',
  '--color-on-primary-container': '#1e40af',

  // 信息色 - 天空蓝
  '--color-info': '#0ea5e9',
  '--color-on-info': '#ffffff',
  '--color-info-container': '#e0f2fe',
  '--color-on-info-container': '#075985',

  // 成功色 - 薄荷绿
  '--color-success': '#10b981',
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

  // 背景色 - 清新天空蓝，明亮有活力
  '--color-body': '#f3f6fa',
  '--color-surface': '#ffffff',
  '--color-surface-rgb': '255, 255, 255',
  '--color-surface-container': '#e8f0f8',
  '--color-surface-container-rgb': '232, 240, 248',
  '--color-surface-container-low': '#f3f6fa',
  '--color-surface-container-high': '#d0ddee',
  '--color-surface-container-highest': '#b0c4dd',

  // 文字色（更清晰的对比度）
  '--color-text': '#1e293b',
  '--color-on-surface': '#1e293b',
  '--color-on-surface-variant': '#475569',

  // 反色
  '--color-inverse-surface': '#11263d',

  // 边框和轮廓（与容器层级呼应，柔和过渡）
  '--color-outline': '#b0bcc8',
  '--color-outline-variant': '#c4d1e5',

  // Checkbox 样式
  '--checkbox-unchecked-color': '#94a3b8',

  // Snackbar/Toast 样式
  '--snackbar-background': '#dde7f5',
  '--snackbar-color': '#1e293b',
  '--snackbar-info-background': '#b3d5ed',
  '--snackbar-success-background': '#07c160',
  '--snackbar-success-color': '#ffffff',

  // Dialog 样式
  '--dialog-title-color': '#2563eb',
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
  '--color-disabled': '#1a2838',
  '--color-text-disabled': '#4d5e75',

  // 背景色 - 冷灰微蓝，温和不夺目
  '--color-body': '#0c1520',
  '--color-surface': '#152130',
  '--color-surface-rgb': '21, 33, 48',
  '--color-surface-container': '#1e2d40',
  '--color-surface-container-rgb': '30, 45, 64',
  '--color-surface-container-low': '#111c2a',
  '--color-surface-container-high': '#2a3b52',
  '--color-surface-container-highest': '#374b68',

  // 文字色
  '--color-text': '#f8fafc',
  '--color-on-surface': '#f8fafc',
  '--color-on-surface-variant': '#94a3b8',

  // 反色
  '--color-inverse-surface': '#f8fafc',

  // 边框和轮廓
  '--color-outline': '#2a3b52',
  '--color-outline-variant': '#1e2d40',

  // Checkbox 样式
  '--checkbox-unchecked-color': 'rgba(255, 255, 255, 0.4)',

  // Snackbar/Toast 样式
  '--snackbar-background': '#152130',
  '--snackbar-color': 'rgba(255, 255, 255, 0.87)',
  '--snackbar-info-background': '#1e2d40',
  '--snackbar-success-background': '#2ba245',
  '--snackbar-success-color': '#000000',

  // Dialog 样式
  '--dialog-title-color': '#2563eb',
  '--result-background': '#152130',
  '--result-description-color': 'var(--color-text)',
}