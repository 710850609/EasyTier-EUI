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

  // 背景色 - 清透天空蓝，轻盈通透
  '--color-body': '#f8fafc',
  '--color-surface': '#fdfdfe',
  '--color-surface-rgb': '253, 253, 254',
  '--color-surface-container': '#eaf0f8',
  '--color-surface-container-rgb': '234, 240, 248',
  '--color-surface-container-low': '#f4f7fb',
  '--color-surface-container-high': '#d8e2f0',
  '--color-surface-container-highest': '#c0d0e4',

  // 文字色（更清晰的对比度）
  '--color-text': '#1e293b',
  '--color-on-surface': '#1e293b',
  '--color-on-surface-variant': '#475569',

  // 反色
  '--color-inverse-surface': '#11263d',

  // 边框和轮廓（与容器层级呼应，柔和过渡）
  '--color-outline': '#aebcc8',
  '--color-outline-variant': '#c0cfe5',

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

// 电光靛蓝 - 暗色主题（年轻活力风格）
export const freshDarkTheme = {
  // 主色调 - 亮电光蓝，更有活力
  '--color-primary': '#60a5fa',
  '--color-on-primary': '#0c1929',
  '--color-primary-container': '#1e3a5f',
  '--color-on-primary-container': '#bfdbfe',

  // 信息色 - 亮天青
  '--color-info': '#38bdf8',
  '--color-on-info': '#0c1929',
  '--color-info-container': '#164e63',
  '--color-on-info-container': '#cffafe',

  // 成功色 - 亮翡翠绿
  '--color-success': '#34d399',
  '--color-on-success': '#022c22',
  '--color-success-container': '#064e3b',
  '--color-on-success-container': '#a7f3d0',

  // 警告色 - 亮琥珀
  '--color-warning': '#fbbf24',
  '--color-on-warning': '#451a03',
  '--color-warning-container': '#78350f',
  '--color-on-warning-container': '#fde68a',

  // 错误色 - 亮珊瑚红
  '--color-danger': '#f87171',
  '--color-on-danger': '#450a0a',
  '--color-danger-container': '#7f1d1d',
  '--color-on-danger-container': '#fecaca',

  // 禁用状态
  '--color-disabled': '#1e293b',
  '--color-text-disabled': '#475569',

  // 背景色 - 通透蓝灰，轻盈不沉闷
  '--color-body': '#0d1117',
  '--color-surface': '#161b24',
  '--color-surface-rgb': '22, 27, 36',
  '--color-surface-container': '#1e2435',
  '--color-surface-container-rgb': '30, 36, 53',
  '--color-surface-container-low': '#111620',
  '--color-surface-container-high': '#272e42',
  '--color-surface-container-highest': '#313a55',

  // 文字色 - 更高对比度
  '--color-text': '#f1f5f9',
  '--color-on-surface': '#f1f5f9',
  '--color-on-surface-variant': '#94a3b8',

  // 反色
  '--color-inverse-surface': '#f1f5f9',

  // 边框和轮廓
  '--color-outline': '#2d3548',
  '--color-outline-variant': '#1e2433',

  // Checkbox 样式
  '--checkbox-unchecked-color': 'rgba(255, 255, 255, 0.3)',

  // Snackbar/Toast 样式
  '--snackbar-background': '#1e293b',
  '--snackbar-color': 'rgba(255, 255, 255, 0.9)',
  '--snackbar-info-background': '#1e3a5f',
  '--snackbar-success-background': '#059669',
  '--snackbar-success-color': '#ffffff',

  // Dialog 样式
  '--dialog-title-color': '#60a5fa',
  '--result-background': '#131620',
  '--result-description-color': 'var(--color-text)',
}