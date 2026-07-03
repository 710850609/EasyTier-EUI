---
name: "easytier-project"
description: "Quickly locate and read files in the EasyTier-EUI project using Glob + Read + SearchCodebase. Invoke when user asks to find, read, or modify any file in this project. Uses glob for file name patterns, Read for file contents, SearchCodebase for semantic code search."
---

# EasyTier-EUI 项目操作指南

## 项目结构

```
F:/git-space/EasyTier-EUI/
├── frontend/                  # 前端项目（Vue 3 + Vite）
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── Nodes.vue      # 节点管理页面
│   │   │   ├── Settings.vue   # 设置页面
│   │   │   └── ...
│   │   ├── components/        # 通用组件
│   │   ├── config/            # 配置文件
│   │   │   └── storage-keys.js # localStorage key 定义
│   │   ├── utils/             # 工具函数
│   │   │   ├── api.js         # API 请求
│   │   │   └── poller.js      # 轮询器
│   │   └── styles/            # 样式文件
│   │       └── glass-effect.css # 毛玻璃效果
│   └── package.json
├── README.md
└── ...
```

## 文件操作流程

当需要查找或修改文件时，按以下顺序操作：

1. **Glob** — 按文件名模式查找文件（如 `*.vue`, `*.js`, `*.css`）
2. **Read** — 读取文件内容，确认代码结构
3. **SearchCodebase** — 按语义搜索代码片段（如 "节点列表渲染", "localStorage 存储"）
4. **Edit** — 精确修改文件内容

## 技术栈

- **前端框架**: Vue 3 + script setup
- **构建工具**: Vite
- **UI 组件库**: Varlet UI
- **图标**: @mdi/js, @mdi/light-js, @jamescoyle/vue-icon
- **样式方案**: CSS 自定义属性（CSS Variables），支持暗色模式（html.dark）

## 暗色模式

暗色模式通过 `<html>` 标签上的 `dark` class 控制：
```css
html.dark .selector {
  /* 暗色模式样式 */
}
```

## 移动端适配

使用 `@media (max-width: 768px)` 进行移动端适配，移动端专用元素用 `.mobile-only-switch` class，PC 端隐藏用 `.mobile-hidden`。