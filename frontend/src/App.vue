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
  --color-surface-container-rgb: 226, 236, 250;
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
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  background-color: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border: none !important;
  border-radius: 16px !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

html.dark body .var-select__scroller,
html.dark body .var-select__scroller.var-elevation--3 {
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18) !important;
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18) !important;
  background-color: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18) !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

/* 下拉选项渐变分割线 */
html body .var-select__scroller .var-option:not(:last-child)::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 0, 0, 0.08) 20%,
    rgba(0, 0, 0, 0.08) 80%,
    transparent
  );
  pointer-events: none;
}

html.dark body .var-select__scroller .var-option:not(:last-child)::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1) 20%,
    rgba(255, 255, 255, 0.1) 80%,
    transparent
  );
}

/* 竖排 var-checkbox 渐变分割线 */
html body .var-checkbox-group--vertical .var-checkbox__wrap {
  position: relative;
}

html body .var-checkbox-group--vertical .var-checkbox__wrap:not(:last-child)::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 36px;
  right: 12px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 0, 0, 0.08) 20%,
    rgba(0, 0, 0, 0.08) 80%,
    transparent
  );
  pointer-events: none;
}

html.dark body .var-checkbox-group--vertical .var-checkbox__wrap:not(:last-child)::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1) 20%,
    rgba(255, 255, 255, 0.1) 80%,
    transparent
  );
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
  overflow: hidden;
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.22) !important;
  backdrop-filter: blur(30px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(30px) saturate(160%) !important;
  will-change: backdrop-filter !important;
  border: none !important;
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
}

html.dark .var-popup__content,
html.dark .var-popup__content[var-popup-cover] {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.35) !important;
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

/* 弹窗顶部高光条 —— 模拟玻璃边缘反光 */
.var-popup__content::after {
  content: '';
  position: absolute;
  top: 0;
  left: 20%;
  right: 20%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.25),
    transparent
  );
  pointer-events: none;
  z-index: 1;
}

/* 顶部弹出层：高光条移到底部，发光边框渐变反转，视觉聚焦在屏幕中间 */
.var-popup__content.var-popup--top::after {
  top: auto;
  bottom: 0;
}

.var-popup__content.var-popup--top::before {
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.06) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.3) 100%
  );
}

html.dark .var-popup__content::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.12),
    transparent
  );
}

/* 弹窗内发光边框 —— 替代生硬 border，让边缘"呼吸" */
.var-popup__content::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1.5px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.3) 0%,
    transparent 50%,
    rgba(0, 0, 0, 0.06) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 0;
}

html.dark .var-popup__content::before {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.15) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.06) 100%
  );
}

html.dark .var-popup__content.var-popup--top::before {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.06) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.15) 100%
  );
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

/* var-paper 背景适配 + 玻璃质感增强 */
.var-paper {
  background: var(--color-surface-container) !important;
  position: relative;
  overflow: hidden;
}

/* 内发光边框 - 替代生硬边界，模拟玻璃边缘厚度 */
.var-paper::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.3) 0%,
    transparent 40%,
    rgba(0, 0, 0, 0.06) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 1;
}

/* 暗色模式 - 内发光边框 */
html.dark .var-paper::before {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.15) 0%,
    transparent 40%,
    rgba(255, 255, 255, 0.05) 100%
  );
}

/* 顶部高光条 - 模拟玻璃边缘反光 */
.var-paper::after {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1.5px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.45),
    transparent
  );
  pointer-events: none;
  z-index: 2;
}

/* 暗色模式 - 高光条 */
html.dark .var-paper::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
}

/* popup 内的 paper 保持透明，去掉玻璃效果 */
.var-popup__content .var-result,
.var-popup__content .var-paper {
  background: transparent !important;
  box-shadow: none !important;
}

/* popup 内的表格滚动时防止背景穿透 */
.var-popup__content .var-table thead {
  background: var(--color-surface-container);
}

.var-popup__content .var-paper::before,
.var-popup__content .var-paper::after {
  display: none;
}

/* popup 遮罩层 - 渐变暗角聚焦（替代纯色半透明） */
.var-popup__overlay {
  background: radial-gradient(
    ellipse 70% 55% at 50% 50%,
    rgba(0, 0, 0, 0.35) 0%,
    transparent 70%
  ) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

/* 亮色模式遮罩 - 压暗值极低，避免脏玻璃感 */
html:not(.dark) .var-popup__overlay {
  background: radial-gradient(
    ellipse 70% 55% at 50% 50%,
    rgba(0, 0, 0, 0.1) 0%,
    transparent 70%
  ) !important;
}

/* var-cell 样式适配 */
.var-cell {
  color: var(--color-on-surface) !important;
}

.var-cell__description {
  color: var(--color-on-surface-variant) !important;
}

/* var-dialog 遮罩层 - 渐变暗角聚焦 */
.var-dialog__overlay {
  background: radial-gradient(
    ellipse 60% 60% at 50% 50%,
    rgba(0, 0, 0, 0.4) 0%,
    rgba(0, 0, 0, 0.15) 60%,
    transparent 100%
  ) !important;
  backdrop-filter: blur(4px) saturate(120%) !important;
  -webkit-backdrop-filter: blur(4px) saturate(120%) !important;
  transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

html:not(.dark) .var-dialog__overlay {
  background: radial-gradient(
    ellipse 60% 60% at 50% 50%,
    rgba(0, 0, 0, 0.12) 0%,
    rgba(0, 0, 0, 0.04) 60%,
    transparent 100%
  ) !important;
}

/* var-dialog 弹窗盒子 - 毛玻璃背景 + 玻璃质感 */
/* 关键：dialog box 背景必须透明，让 popup content 的毛玻璃透出来 */
.var-dialog--box,
.var-dialog {
  position: relative !important;
  overflow: hidden !important;
  background: transparent !important;
  border: none !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.08) !important;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
  animation: dialog-enter 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

html.dark .var-dialog--box,
html.dark .var-dialog {
  background: transparent !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.45),
    0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

/* 内发光边框 */
.var-dialog--box::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.25) 0%,
    transparent 40%,
    rgba(0, 0, 0, 0.05) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 1;
}

html.dark .var-dialog--box::before {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.12) 0%,
    transparent 40%,
    rgba(255, 255, 255, 0.04) 100%
  );
}

/* 顶部高光条 */
.var-dialog--box::after {
  content: '';
  position: absolute;
  top: 0;
  left: 12%;
  right: 12%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.35),
    transparent
  );
  pointer-events: none;
  z-index: 2;
}

html:not(.dark) .var-dialog--box::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.55),
    transparent
  );
}

@keyframes dialog-enter {
  from {
    transform: translateY(8px) scale(0.98);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

.toast-content {
  white-space: pre-line;
}

/* ========== 全局毛玻璃面板样式 ========== */

/* 下拉框菜单毛玻璃 */
.var-menu.var--box.var-select__menu {
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
}

html.dark .var-menu.var--box.var-select__menu {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

/* 折叠面板样式 - 移除高光，更柔和 */
.var-collapse {
  background: transparent !important;
}

.var-collapse-item {
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  border: none !important;
  box-shadow: none !important;
}

.var-collapse-item__header {
  background: transparent !important;
  box-shadow: none !important;
}

.var-collapse-item__header::before,
.var-collapse-item__header::after {
  display: none !important;
}

.var-collapse-item__content {
  padding: 8px 16px 16px;
  background: transparent !important;
  border-top: none !important;
}

html.dark .var-collapse-item {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.1) !important;
}
</style>