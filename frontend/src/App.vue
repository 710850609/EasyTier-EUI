<template>
  <Layout />
</template>

<script setup>
import Layout from './components/Layout.vue'
</script>

<style>
:root {
  /* 避免其它App webview是非全面屏，导致多了空白区域 */
  /*--safe-area-inset-top: env(safe-area-inset-top, 0px);*/
  --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
  --safe-area-inset-right: env(safe-area-inset-right, 0px);
  --safe-area-inset-left: env(safe-area-inset-left, 0px);
}

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
  width: 4px;
  height: 4px;
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

:root {
  --app-primary: var(--color-primary);
  /* 按钮圆角 */
  --button-border-radius: 10px;
  /* 输入框圆角 */
  --field-decorator-line-border-radius: 10px;
  /* Toast 圆角 */
  --snackbar-border-radius: 10px;
  /* RGB 变量用于 rgba() */
  --color-surface-rgb: 253, 253, 254;
  --color-surface-container-rgb: 234, 240, 248;
}

/* 暗色主题 RGB 变量 - 使用 html.dark 提高优先级 */
html.dark {
  --color-surface-rgb: 22, 27, 36;
  --color-surface-container-rgb: 30, 36, 53;
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

.var-select__empty {
  color: var(--color-on-surface-variant) !important;
}

.var-option:hover {
  background: var(--color-surface-container-high) !important;
}

/* var-select 下拉框毛玻璃效果 — 内层只做毛玻璃，不带阴影 */
html body .var-select__scroller,
html body .var-select__scroller.var-elevation--3 {
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 234, 240, 248), 0.02) !important;
  background: rgba(var(--color-surface-container-rgb, 234, 240, 248), 0.02) !important;
  background-color: rgba(var(--color-surface-container-rgb, 234, 240, 248), 0.02) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border: none !important;
  border-left: 2px solid rgba(255, 255, 255, 0.25) !important;
  border-right: 2px solid rgba(255, 255, 255, 0.25) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
  --shadow-key-umbra-opacity: transparent !important;
  --shadow-key-penumbra-opacity: transparent !important;
  --shadow-key-ambient-opacity: transparent !important;
}

html.dark body .var-select__scroller,
html.dark body .var-select__scroller.var-elevation--3 {
  --select-scroller-background: rgba(var(--color-surface-container-rgb, 30, 36, 53), 0.18) !important;
  background: rgba(var(--color-surface-container-rgb, 30, 36, 53), 0.18) !important;
  background-color: rgba(var(--color-surface-container-rgb, 30, 36, 53), 0.18) !important;
  border-left: 1px solid rgba(255, 255, 255, 0.25) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.25) !important;
  box-shadow: none !important;
  --shadow-key-umbra-opacity: transparent !important;
  --shadow-key-penumbra-opacity: transparent !important;
  --shadow-key-ambient-opacity: transparent !important;
}

/* 关闭毛玻璃效果时，var-select 下拉框使用实色背景 */
html.no-glass body .var-select__scroller,
html.no-glass body .var-select__scroller.var-elevation--3 {
  background: var(--color-surface-container) !important;
  background-color: var(--color-surface-container) !important;
}

html.no-glass.dark body .var-select__scroller,
html.no-glass.dark body .var-select__scroller.var-elevation--3 {
  background: var(--color-surface-container) !important;
  background-color: var(--color-surface-container) !important;
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
/* 亮色模式：较高不透明度 + 强模糊 + 高饱和 + 清晰边界，避免脏玻璃感和边界模糊 */
.var-popup__content,
.var-popup__content[var-popup-cover] {
  overflow: hidden;
  background: rgba(var(--color-surface-container-rgb, 212, 223, 250), 0.16) !important;
  backdrop-filter: blur(20px) saturate(130%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(130%) !important;
  will-change: backdrop-filter !important;
  border: none !important;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    inset 0 -2px 0 rgba(255, 255, 255, 0.35) !important;
}

html.dark .var-popup__content,
html.dark .var-popup__content[var-popup-cover] {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.12) !important;
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    inset 0 -2px 0 rgba(255, 255, 255, 0.08) !important;
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
    rgba(255, 255, 255, 0.45),
    transparent
  );
  pointer-events: none;
  z-index: 1;
}

/* var-popup left/right 安全区域适配 */
.var-popup__content.var-popup--left,
.var-popup__content.var-popup--right {
  padding-top: var(--safe-area-inset-top, 0px);
  padding-bottom: var(--safe-area-inset-bottom, 0px);
}
.var-popup__content.var-popup--bottom {
  padding-bottom: var(--safe-area-inset-bottom, 0px);
}
/* 顶部弹出层：高光条移到底部，发光边框渐变反转，视觉聚焦在屏幕中间 */
.var-popup__content.var-popup--top {
  padding-top: var(--safe-area-inset-top, 0px);
}

.var-popup__content.var-popup--top::after {
  top: auto;
  bottom: 0;
}

/* 右侧弹出层：高光条移到左边，改为纵向暗-亮-暗渐变 */
.var-popup__content.var-popup--right::after {
  top: 20%;
  bottom: 20%;
  left: 0;
  right: auto;
  width: 1px;
  height: auto;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(255, 255, 255, 0.45),
    transparent
  );
}

/* 左侧弹出层：高光条移到右边 */
.var-popup__content.var-popup--left::after {
  top: 20%;
  bottom: 20%;
  left: auto;
  right: 0;
  width: 1px;
  height: auto;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(255, 255, 255, 0.45),
    transparent
  );
}

.var-popup__content.var-popup--top::before {
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.08) 0%,
    transparent 45%,
    rgba(255, 255, 255, 0.40) 100%
  );
}

/* 右侧弹出层：内发光边框左侧更亮，模拟玻璃边缘 */
.var-popup__content.var-popup--right::before {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.40) 0%,
    transparent 45%,
    rgba(0, 0, 0, 0.08) 100%
  );
}

/* 左侧弹出层：内发光边框右侧更亮 */
.var-popup__content.var-popup--left::before {
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.08) 0%,
    transparent 45%,
    rgba(255, 255, 255, 0.40) 100%
  );
}

.var-button {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

/* variant 模式未选中时去掉灰色外边框 */
.var-switch--variant .var-switch__track {
  border-color: transparent !important;
}

html.dark .var-switch--variant .var-switch__track {
  border-color: transparent !important;
}


html.dark .var-popup__content::after {
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
}

html.dark .var-popup__content.var-popup--right::after {
  background: linear-gradient(
    180deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
}

html.dark .var-popup__content.var-popup--left::after {
  background: linear-gradient(
    180deg,
    transparent,
    rgba(255, 255, 255, 0.2),
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
    rgba(255, 255, 255, 0.40) 0%,
    transparent 45%,
    rgba(0, 0, 0, 0.08) 100%
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
    rgba(255, 255, 255, 0.18) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.02) 100%
  );
}

html.dark .var-popup__content.var-popup--top::before {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.02) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.18) 100%
  );
}

html.dark .var-popup__content.var-popup--right::before {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.18) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.02) 100%
  );
}

html.dark .var-popup__content.var-popup--left::before {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.02) 0%,
    transparent 50%,
    rgba(255, 255, 255, 0.18) 100%
  );
}

/* var-select 框圆角 */
.var-select__menu {
  border-radius: 12px;
}
/* 底部弹出层圆角 */
.var-popup--bottom {
  border-radius: 20px 20px 0 0 !important;
}

/* 顶部弹出层圆角 */
.var-popup--top {
  border-radius: 0 0 20px 20px !important;
}

/* 左侧弹出层圆角 */
.var-popup--left {
  border-radius: 0 20px 20px 0 !important;
}

/* 右侧弹出层圆角 */
.var-popup--right {
  border-radius: 20px 0 0 20px !important;
}

.var-popup--top .var-popup__content {
  padding-top: var(--safe-area-inset-top, 0px) !important;
}

/* 居中弹出层圆角 */
.var-popup--center {
  border-radius: 20px !important;
  margin: 10px 5px 10px 5px;
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

/* popup 遮罩层 - 中心弹出：径向渐变暗角 */
.var-popup__overlay {
  background: radial-gradient(
    ellipse 70% 55% at 50% 50%,
    rgba(0, 0, 0, 0.25) 0%,
    transparent 70%
  ) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

html:not(.dark) .var-popup__overlay {
  background: radial-gradient(
    ellipse 70% 55% at 50% 50%,
    rgba(0, 0, 0, 0.18) 0%,
    transparent 70%
  ) !important;
  backdrop-filter: blur(3px) !important;
  -webkit-backdrop-filter: blur(3px) !important;
}

/* 左右弹窗：Y轴暗带 */
.var-popup:has(.var-popup--right) .var-popup__overlay {
  background: linear-gradient(to right, transparent 50%, rgba(0, 0, 0, 0.12) 70%, rgba(0, 0, 0, 0.12) 70%, transparent 100%) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

.var-popup:has(.var-popup--left) .var-popup__overlay {
  background: linear-gradient(to right, rgba(0, 0, 0, 0.30) 0%, transparent 70%) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

/* 上下弹窗：X轴暗带 */
.var-popup:has(.var-popup--bottom) .var-popup__overlay {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.30) 0%, transparent 70%) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

.var-popup:has(.var-popup--top) .var-popup__overlay {
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.30) 0%, transparent 70%) !important;
  backdrop-filter: blur(2px) !important;
  -webkit-backdrop-filter: blur(2px) !important;
}

/* 亮色模式方向适配 */
html:not(.dark) .var-popup:has(.var-popup--right) .var-popup__overlay {
  background: linear-gradient(to left, rgba(0, 0, 0, 0.20) 0%, transparent 70%) !important;
}

html:not(.dark) .var-popup:has(.var-popup--left) .var-popup__overlay {
  background: linear-gradient(to right, rgba(0, 0, 0, 0.20) 0%, transparent 70%) !important;
}

html:not(.dark) .var-popup:has(.var-popup--bottom) .var-popup__overlay {
  background: linear-gradient(to bottom, transparent 15%, rgba(0, 0, 0, 0.15) 40%, rgba(0, 0, 0, 0.1) 60%, rgba(0, 0, 0, 0.05) 100%) !important;
}

html:not(.dark) .var-popup:has(.var-popup--top) .var-popup__overlay {
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.20) 0%, transparent 70%) !important;
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
    0 8px 32px rgba(0, 0, 0, 0.20),
    0 2px 8px rgba(0, 0, 0, 0.10),
    inset 0 -2px 0 rgba(255, 255, 255, 0.28) !important;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
  animation: dialog-enter 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

html.dark .var-dialog--box,
html.dark .var-dialog {
  background: transparent !important;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.45),
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 -2px 0 rgba(255, 255, 255, 0.08) !important;
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
    rgba(255, 255, 255, 0.30) 0%,
    transparent 40%,
    rgba(0, 0, 0, 0.10) 100%
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

/* 顶部 + 底部高光条 */
.var-dialog--box::after {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    linear-gradient(90deg, transparent 12%, rgba(255, 255, 255, 0.35) 30%, rgba(255, 255, 255, 0.35) 70%, transparent 88%) 0 0 / 100% 1px no-repeat,
    linear-gradient(90deg, transparent 12%, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.12) 70%, transparent 88%) 0 100% / 100% 1px no-repeat;
  pointer-events: none;
  z-index: 2;
}

html:not(.dark) .var-dialog--box::after {
  background: 
    linear-gradient(90deg, transparent 12%, rgba(255, 255, 255, 0.55) 30%, rgba(255, 255, 255, 0.55) 70%, transparent 88%) 0 0 / 100% 1px no-repeat,
    linear-gradient(90deg, transparent 12%, rgba(255, 255, 255, 0.30) 30%, rgba(255, 255, 255, 0.30) 70%, transparent 88%) 0 100% / 100% 1px no-repeat;
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
.var-menu__menu.var--box.var-select__menu {
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  border-radius: 12px !important;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.10),
    0 8px 24px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

html.dark .var-menu__menu.var--box.var-select__menu {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  border-left-color: rgba(255, 255, 255, 0.12) !important;
  border-right-color: rgba(255, 255, 255, 0.12) !important;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.18),
    0 8px 24px rgba(0, 0, 0, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

/* 通用 var-menu 毛玻璃（非 select，如更多菜单等） */
html body .var-menu__menu.var--box:not(.var-select__menu),
html body .var-menu__menu.var--box.var-menu--menu-background-color:not(.var-select__menu) {
  --menu-background-color: transparent !important;
  background-image: none !important;
  background: rgba(var(--color-surface-container-rgb, 234, 240, 248), 0.08) !important;
  background-color: rgba(var(--color-surface-container-rgb, 234, 240, 248), 0.08) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border: none !important;
  border-left: 2px solid rgba(255, 255, 255, 0.25) !important;
  border-right: 2px solid rgba(255, 255, 255, 0.25) !important;
  border-radius: 12px !important;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.32),
    0 8px 24px rgba(0, 0, 0, 0.22),
    0 16px 48px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

html.dark body .var-menu__menu.var--box:not(.var-select__menu),
html.dark body .var-menu__menu.var--box.var-menu--menu-background-color:not(.var-select__menu) {
  background: rgba(var(--color-surface-container-rgb, 30, 36, 53), 0.25) !important;
  background-color: rgba(var(--color-surface-container-rgb, 30, 36, 53), 0.25) !important;
  backdrop-filter: blur(20px) saturate(140%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
  will-change: backdrop-filter !important;
  border-left: 1px solid rgba(255, 255, 255, 0.25) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.25) !important;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.12),
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 16px 48px rgba(0, 0, 0, 0.20),
    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
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

/* ========== 性能优化：关闭毛玻璃效果 ========== */
html.no-glass *,
html.no-glass *::before,
html.no-glass *::after {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  will-change: auto !important;
}

/* 关闭毛玻璃后，弹窗/下拉框等透明元素改为实色背景 */
html.no-glass .var-popup__content,
html.no-glass .var-popup__content[var-popup-cover] {
  background: var(--color-surface-container) !important;
}

html.no-glass .var-menu__menu.var--box.var-select__menu {
  background: var(--color-surface-container) !important;
  box-shadow: none !important;
}

html.no-glass .var-popup__overlay {
  background: rgba(0, 0, 0, 0.35) !important;
}

html:not(.dark).no-glass .var-popup__overlay {
  background: rgba(0, 0, 0, 0.12) !important;
}

html.no-glass .var-dialog__overlay {
  background: rgba(0, 0, 0, 0.35) !important;
}

html:not(.dark).no-glass .var-dialog__overlay {
  background: rgba(0, 0, 0, 0.12) !important;
}

/* 关闭毛玻璃后，SideMenu 子菜单弹出框使用实色背景 */
html.no-glass .submenu-popup-content {
  background: var(--color-surface-container) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
}

html.no-glass.dark .submenu-popup-content {
  background: var(--color-surface-container) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

/* 关闭毛玻璃后，底部导航栏保留渐变透明效果，只去掉 blur */
html.no-glass .bottom-nav {
  background: transparent !important;
}

html.no-glass .bottom-nav::before {
  background: var(--color-surface) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  -webkit-mask-image: linear-gradient(
    to top,
    rgba(0, 0, 0, 1) 0%,
    rgba(0, 0, 0, 1) 66%,
    rgba(0, 0, 0, 0) 100%
  );
  mask-image: linear-gradient(
    to top,
    rgba(0, 0, 0, 1) 0%,
    rgba(0, 0, 0, 1) 66%,
    rgba(0, 0, 0, 0) 100%
  );
}

html.no-glass.dark .bottom-nav {
  background: transparent !important;
}

html.no-glass.dark .bottom-nav::before {
  background: var(--color-surface) !important;
}

/* 关闭毛玻璃后，popover 使用实色背景 */
html.no-glass .var-popover,
html.no-glass .var-popover__content {
  background: var(--color-surface-container) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

html.no-glass .var-menu__menu.var--box:not(.var-select__menu),
html.no-glass .var-menu__menu.var--box.var-menu--menu-background-color:not(.var-select__menu) {
  background: var(--color-surface-container) !important;
  background-color: var(--color-surface-container) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: 1px solid var(--color-outline-variant) !important;
  border-radius: 12px !important;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.08),
    0 16px 48px rgba(0, 0, 0, 0.05) !important;
}

/* 关闭毛玻璃后，底部导航子菜单使用实色背景 */
html.no-glass .submenu-popup {
  background: var(--color-surface-container) !important;
}

html.no-glass.dark .submenu-popup {
  background: var(--color-surface-container) !important;
}
</style>