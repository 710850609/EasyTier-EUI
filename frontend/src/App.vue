<template>
  <Layout />
</template>

<script setup>
import Layout from './components/Layout.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--color-body);
  color: var(--color-text);
  transition: background-color 0.3s, color 0.3s;
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-surface-container-low);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--color-outline);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-on-surface-variant);
}

/* MD3 主题变量适配 */
:root {
  --app-primary: var(--color-primary);
  /* RGB 变量用于 rgba() */
  --color-surface-rgb: 255, 255, 255;
  --color-surface-container-rgb: 224, 242, 254;
}

/* 暗色主题 RGB 变量 - 使用 html.dark 提高优先级 */
html.dark {
  --color-surface-rgb: 30, 41, 59;
  --color-surface-container-rgb: 51, 65, 85;
}

/* 隐藏 Snackbar 图标 */
.var-snackbar__icon {
  display: none !important;
}

/* Snackbar success 样式 - 使用 CSS 变量 */
.var-snackbar--success {
  background: var(--snackbar-success-background) !important;
  color: var(--snackbar-success-color) !important;
}

.var-snackbar--success .var-snackbar__content {
  color: var(--snackbar-success-color) !important;
}

/* ========== Varlet 组件全局样式适配 ========== */

/* var-select 下拉框样式适配 */
.var-select__control {
  background: var(--color-surface-container) !important;
  color: var(--color-on-surface) !important;
}

.var-select__label {
  color: var(--color-on-surface-variant) !important;
}

.var-select__placeholder {
  color: var(--color-on-surface-variant) !important;
}

.var-select__menu {
  background: var(--color-surface-container) !important;
  /* 覆盖 Varlet option 的文字颜色变量 */
  --option-text-color: var(--color-on-surface);
  --option-selected-background: var(--color-primary-container);
}

.var-option {
  color: var(--color-on-surface) !important;
}

.var-option--selected {
  background: var(--color-primary-container) !important;
  color: var(--color-on-primary-container) !important;
}

.var-option:hover {
  background: var(--color-surface-container-high) !important;
}

/* var-select 下拉框毛玻璃效果 */
html body .var-select__scroller,
html body .var-select__scroller.var-elevation--3 {
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.18) !important;
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.18) !important;
  background-color: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.18) !important;
  backdrop-filter: blur(28px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(140%) !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
}

html.dark body .var-select__scroller,
html.dark body .var-select__scroller.var-elevation--3 {
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.38) !important;
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.38) !important;
  background-color: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.38) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
}

/* var-tabs 样式适配 */
.var-tabs {
  background: transparent !important;
}

.var-tab {
  color: var(--color-on-surface-variant) !important;
}

.var-tab--active {
  color: var(--color-primary) !important;
}

.var-tabs-indicator {
  background: var(--color-primary) !important;
}

/* var-checkbox 文字颜色适配 */
.var-checkbox__text {
  color: var(--color-on-surface) !important;
}

.var-checkbox--disabled .var-checkbox__text {
  color: var(--color-on-surface-variant) !important;
}

/* var-popup 背景适配 - 磨砂玻璃效果（必须在 var-paper 之前定义） */
.var-popup__content,
.var-popup__content[var-popup-cover] {
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.18) !important;
  backdrop-filter: blur(28px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(140%) !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
}

html.dark .var-popup__content,
html.dark .var-popup__content[var-popup-cover] {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.38) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
}

/* 底部弹出层圆角 */
.var-popup--bottom {
  border-radius: 16px 16px 0 0 !important;
}

/* 顶部弹出层圆角 */
.var-popup--top {
  border-radius: 0 0 16px 16px !important;
}

/* 居中弹出层圆角 */
.var-popup--center {
  border-radius: 16px !important;
}

/* var-paper 背景适配 */
.var-paper {
  background: var(--color-surface-container) !important;
}

/* popup 内的 paper 保持透明 */
.var-popup__content .var-result,
.var-popup__content .var-paper {
  background: transparent !important;
  box-shadow: none !important;
}

/* popup 遮罩层 - 半透明 */
.var-popup__overlay {
  background: rgba(0, 0, 0, 0.25) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

/* var-cell 样式适配 */
.var-cell {
  color: var(--color-on-surface) !important;
}

.var-cell__description {
  color: var(--color-on-surface-variant) !important;
}

.markdown-content th {
  /* markdown 表头透明 */
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.1) !important;
}
.toast-content {
  white-space: pre-line;
}
</style>