# Varlet UI `var-input` / `var-select` 在 collapse 中不显示 placeholder 问题排查

## 场景

Vue 3 + Varlet UI 3.3.2 项目中，配置页面使用 `var-collapse` 折叠面板来组织高级设置和代理转发设置。面板内的 `var-input`（`variant="outlined"`）和 `var-select` 组件在首次展开时不显示 placeholder 文字，必须手动点击控件后才能看到 placeholder。

## 问题表现

| 行为 | placeholder 是否显示 |
|------|---------------------|
| 首次加载页面后展开 collapse | ❌ 不显示 |
| 首次展开后，切换其他配置 | ✅ 正常显示 |
| 从未展开过，无论切换多少次配置 | ❌ 永远不显示 |
| 手动点击一下控件（获得焦点） | ✅ 显示 |

## 根本原因

### 直接原因

`var-input` 组件在初始化时（`mounted` 生命周期），通过 `getBoundingClientRect()` 计算 placeholder 的定位。当组件所在的 DOM 容器处于 `display: none` 状态时，`getBoundingClientRect()` 返回全 0，导致 placeholder 定位计算错误，placeholder 被渲染在不可见的位置。

### 触发条件链

1. **Varlet UI `var-collapse` 的实现机制**：折叠面板通过 CSS `display: none` 隐藏内部内容，内容 DOM 始终存在但不可见。

2. **骨架屏加载机制**：原版本使用 `v-if` / `v-else` 切换骨架屏和表单内容。加载时表单被销毁，加载完成后表单被重建。此时 collapse 处于关闭状态，表单内的 `var-input` 组件在 `display: none` 的容器中创建，placeholder 定位失败。

3. **首次展开 vs 后续切换**：
   - 首次展开：collapse 从 `display: none` 变为 `display: block`，但组件早已在隐藏状态下创建好，不会重新计算 placeholder。
   - 切换配置：`selectedConfig` 变化导致 `v-if` 或 `key` 变化，组件被销毁重建。此时 collapse 已展开，容器可见，组件在可见状态下创建，placeholder 正常。

### 排查过程中走过的弯路

1. **误以为是 `v-model` 值为 `undefined` 导致**：将 `|| undefined` 改为 `?? ''`，把 undefined 字段规范化为空字符串。修复了数据正确性，但未解决根本问题。

2. **误以为 collapse 内容的 `v-if` 能解决**：给 collapse 内容加了 `v-if="flagsOpen.includes('flags')"`，认为展开时组件才创建、就能在可见状态下初始化。但 `var-collapse` 内部展开有 CSS transition 动画，组件创建时容器仍在过渡中（height: 0 → height: auto），定位计算依然不准。

3. **误以为骨架屏 `v-else` 销毁重建是主因**：把骨架屏从 `v-if`/`v-else` 改为绝对定位遮罩层，确保表单 DOM 始终存在。有效但不完整，因为 collapse 仍然在隐藏内容。

## 最终解决方案

### 核心思路

**在 collapse 展开动画完全结束后，通过修改 `key` 强制 Vue 重建内容组件，使 `var-input` 在完全可见的容器中初始化。**

### 实现步骤

#### 1. 骨架屏改为遮罩覆盖（避免销毁表单 DOM）

```html
<!-- 原代码：v-if/v-else 切换，表单被销毁重建 -->
<template v-if="isLoadingConfig">
  <div class="sk-config-section">...</div>
</template>
<template v-else>
  <var-paper>...</var-paper>
</template>

<!-- 修改后：遮罩覆盖，表单始终在 DOM 中 -->
<div v-if="isLoadingConfig" class="sk-overlay"></div>
<var-paper>...</var-paper>
```

```css
.sk-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  background: var(--color-surface);
  opacity: 0.6;
  cursor: wait;
}

.content-area {
  position: relative;
}
```

#### 2. 移除 collapse 内容区的 `v-if`（保留组件在 DOM 中）

```html
<!-- 原代码 -->
<div class="flags-content" v-if="flagsOpen.includes('flags')">

<!-- 修改后 -->
<div class="flags-content" :key="'flags-' + selectedConfig + '-' + flagsRenderKey">
```

#### 3. 添加延迟重建机制（核心修复）

```javascript
import { ref, watch, nextTick } from 'vue'

// 渲染键，用于在 collapse 展开后强制重建内容
const flagsRenderKey = ref(0)
const forwardRenderKey = ref(0)

// 监听 collapse 展开，等待动画完成后重建内容
watch(flagsOpen, (newVal) => {
  if (newVal.includes('flags')) {
    nextTick(() => {
      setTimeout(() => {
        flagsRenderKey.value++
      }, 350)
    })
  }
})

watch(forwardOpen, (newVal) => {
  if (newVal.includes('forward')) {
    nextTick(() => {
      setTimeout(() => {
        forwardRenderKey.value++
      }, 350)
    })
  }
})
```

#### 4. 数据归一化（修复 `v-model` 绑定 `undefined` 问题）

```javascript
config.value = {
  ...json,
  hostname: json.hostname ?? '',  // 确保是空字符串而非 undefined
  ipv4: json.ipv4 ?? '',
  // ...
}

// 将 flags 中 undefined 的字符串字段统一设为空字符串
;['dev_name', 'encryption_algorithm', 'default_protocol', 'compression', 'relay_network_whitelist'].forEach(key => {
  if (config.value.flags[key] == null) config.value.flags[key] = ''
})
```

### 为什么 350ms？

Varlet UI 3.x 的 `var-collapse` 组件使用 CSS transition，展开动画时长约 300ms。`nextTick` 确保 Vue 响应式更新完成，`setTimeout(350ms)` 确保 CSS 动画已经完全结束，此时容器高度稳定，`getBoundingClientRect()` 能返回正确值。

## 排查方法论总结

当遇到 UI 组件在某种条件下表现异常时，按以下步骤排查：

1. **对比工作版本**：找到能正常工作的版本（如 `Config-back.vue`），逐一对比 DOM 结构差异。
2. **隔离变量**：逐一排除可能的因素（数据值、CSS、DOM 结构、渲染时机），识别真正的原因。
3. **关注渲染时机**：组件在 `display: none` 的容器中初始化是 UI 库常见问题，`getBoundingClientRect()` 在隐藏元素上返回 0。
4. **理解组件生命周期**：Vue 组件的 `mounted` / `onMounted` 在 DOM 插入后执行，但此时父容器可能仍处于隐藏状态。
5. **延迟重建策略**：当需要在动画完成后重建组件时，使用 `nextTick` + `setTimeout` 组合，等待 CSS 动画完成。

## 相关文件

- [Config.vue](file:///F:/git-space/EasyTier-EUI/frontend/src/views/Config.vue) — 配置文件页面
- [Config-back.vue](file:///F:/git-space/EasyTier-EUI/frontend/src/views/Config-back.vue) — 工作版本（用于对比分析）

---

## 延伸问题：`var-select` 下拉菜单内的 `var-input` 同样不显示 placeholder

### 场景

`var-select` 多选模式下，下拉菜单中通过 `#description` 或 `#default` 插槽放了一个 `var-input` 用于输入自定义选项（如添加自定义节点、自定义监听地址等）。首次打开下拉菜单时，该 `var-input` 的 placeholder 同样不显示。

### 原因

同一根因：`var-select` 的下拉菜单（popup）在关闭时通过 `display: none` 隐藏，`var-input` 组件在隐藏状态下创建，`getBoundingClientRect()` 返回全 0，placeholder 定位失败。

### 与 collapse 问题的区别

| 对比维度 | collapse | var-select 下拉 |
|---------|----------|----------------|
| 隐藏容器 | `var-collapse-item` 内容区 | `var-select` popup 弹窗 |
| 可监听事件 | `v-model`（`flagsOpen` 数组） | `@focus`（点击打开下拉时触发） |
| 动画时长 | ~300ms | ~150ms（popup 动画更短） |
| 触发方式 | watch `flagsOpen` 变化 | `@focus` 事件回调 |

### 解决方案（简洁版）

与 collapse 方案思路一致但更轻量，用一个对象存储所有 key，一个函数复用逻辑：

```javascript
// 下拉菜单内 var-input 渲染键，用于下拉打开后强制重建以正确显示 placeholder
const selectInputRenderKey = ref({
  peer: 0,
  listener: 0,
  exitNode: 0,
  proxyNetwork: 0
})

const onSelectFocus = (name) => {
  nextTick(() => {
    setTimeout(() => {
      selectInputRenderKey.value[name]++
    }, 150)
  })
}
```

模板中给 `var-select` 加 `@focus`，给 `var-input` 的容器加 `:key`：

```html
<!-- 示例：peer 选择器 -->
<var-select @focus="onSelectFocus('peer')" ...>
  <template #default>
    <div class="peer-custom-input" :key="selectInputRenderKey.peer">
      <var-input :placeholder="$t('config.customNodePlaceholder')" ... />
    </div>
  </template>
</var-select>

<!-- 示例：listeners 选择器 -->
<var-select @focus="onSelectFocus('listener')" ...>
  <var-cell :key="selectInputRenderKey.listener">
    <template #description>
      <var-input :placeholder="$t('config.customListenerPlaceholder')" ... />
    </template>
  </var-cell>
</var-select>
```

### 为什么 150ms？

`var-select` 的 popup 弹窗动画比 collapse 更短，约 150ms 即可完成。`nextTick` 确保 Vue DOM 更新完成，`setTimeout(150ms)` 确保 CSS popup 动画结束。

### 设计考量：为什么用对象而非多个独立 watch

- 一个对象 `selectInputRenderKey` 存储所有 key，内存占用 1 个 ref
- 一个函数 `onSelectFocus` 处理所有事件，无额外 watch 开销
- 对比独立 watch 方案：如果创建 4 个 watch，每个 watch 都会在组件生命周期内持续运行，资源占用更大
- 当前方案仅在用户点击时才触发一次 `setTimeout`，完成后自动释放，资源占用极小