<template>
  <div class="side-menu" :class="{ collapsed: isCollapsed }" @click="submenuPopup.show = false">
    <div class="logo">
      <var-icon name="network-wired" :size="32" />
      <span v-if="!isCollapsed" class="logo-text">EasyTier</span>
      <span v-if="isCollapsed" class="logo-text">ET&nbsp;&nbsp;&nbsp;&nbsp;</span>
      <var-button
        class="collapse-btn"
        text
        round
        :size="isCollapsed ? 'small' : 'mini'"
        @click="toggleCollapse"
      >
        <var-icon :name="isCollapsed ? 'menu-right' : 'menu-left'" />
      </var-button>
    </div>

    <div class="menu-list">
      <template v-for="menu in menuTree" :key="menu.key">
        <!-- 有子菜单的项 -->
        <div v-if="menu.children" class="menu-group">
          <div
            class="menu-item"
            :class="{ active: active?.startsWith(menu.key) }"
            @click.stop="isCollapsed ? showSubmenuPopup(menu, $event) : toggleExpand(menu.key)"
          >
            <!-- Varlet 内置图标 -->
            <var-icon v-if="isVarletIcon(menu.icon)" :name="menu.icon" class="menu-icon" />
            <!-- SVG 图标 (@mdi/js 或 @mdi/light-js) -->
            <svg-icon
              v-else-if="isSvgIcon(menu.icon)"
              type="mdi"
              :path="getIconPath(menu.icon)"
              class="menu-icon"
              width="24"
              height="24"
            />
            <!-- 图片图标 -->
            <img v-else-if="isImageIcon(menu.icon)" :src="menu.icon" class="menu-icon" />
            <span v-if="!isCollapsed" class="menu-title">{{ menu.label }}</span>
            <var-icon
              v-if="!isCollapsed"
              name="chevron-down"
              class="expand-icon"
              :class="{ expanded: expandedKeys.includes(menu.key) }"
            />
          </div>

          <div v-if="!isCollapsed && expandedKeys.includes(menu.key)" class="sub-menu-list">
            <div
              v-for="child in menu.children"
              :key="child.key"
              class="sub-menu-item"
              :class="{ active: active === child.key }"
              @click="handleClick(child.key)"
            >
              <!-- Varlet 内置图标 -->
              <var-icon v-if="isVarletIcon(child.icon)" :name="child.icon" size="18" />
              <!-- SVG 图标 (@mdi/js 或 @mdi/light-js) -->
              <svg-icon
                v-else-if="isSvgIcon(child.icon)"
                type="mdi"
                :path="getIconPath(child.icon)"
                width="18"
                height="18"
              />
              <!-- 图片图标 -->
              <img v-else-if="isImageIcon(child.icon)" :src="child.icon" class="submenu-icon" />
              <span>{{ child.label }}</span>
            </div>
          </div>
        </div>

        <!-- 无子菜单的项 -->
        <div
          v-else
          class="menu-item"
          :class="{ active: active === menu.key }"
          @click="handleClick(menu.key)"
        >
          <!-- Varlet 内置图标 -->
          <var-icon v-if="isVarletIcon(menu.icon)" :name="menu.icon" class="menu-icon" />
          <!-- SVG 图标 (@mdi/js 或 @mdi/light-js) -->
          <svg-icon
            v-else-if="isSvgIcon(menu.icon)"
            type="mdi"
            :path="getIconPath(menu.icon)"
            class="menu-icon"
            width="24"
            height="24"
          />
          <!-- 图片图标 -->
          <img v-else-if="isImageIcon(menu.icon)" :src="menu.icon" class="menu-icon" />
          <span v-if="!isCollapsed" class="menu-title">{{ menu.label }}</span>
        </div>
      </template>
    </div>

    <!-- 收缩状态下的子菜单弹出框 -->
    <Transition name="submenu">
      <div v-if="submenuPopup.show">
        <!-- 透明遮罩层，点击关闭 -->
        <div class="submenu-overlay" @click="submenuPopup.show = false"></div>
        <!-- 弹出框内容 -->
        <div
          class="submenu-popup-wrapper"
          :style="submenuPopupStyle"
        >
          <div class="submenu-popup-content" @click.stop>
            <div class="submenu-popup-title">{{ submenuPopup.menu?.label }}</div>
            <div
              v-for="child in submenuPopup.menu?.children"
              :key="child.key"
              class="submenu-popup-item"
              :class="{ active: active === child.key }"
              @click="handleSubmenuClick(child.key)"
            >
              <!-- Varlet 内置图标 -->
              <var-icon v-if="isVarletIcon(child.icon)" :name="child.icon" size="18" />
              <!-- SVG 图标 (@mdi/js 或 @mdi/light-js) -->
              <svg-icon
                v-else-if="isSvgIcon(child.icon)"
                type="mdi"
                :path="getIconPath(child.icon)"
                width="18"
                height="18"
              />
              <!-- 图片图标 -->
              <img v-else-if="isImageIcon(child.icon)" :src="child.icon" class="submenu-icon" />
              <span>{{ child.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { menuTree } from '../config/menu.js'
import { SIDEBAR_COLLAPSED_KEY } from '../config/storage-keys.js'
import SvgIcon from '@jamescoyle/vue-icon'
import { isVarletIcon, isImageIcon, isSvgIcon, getIconPath } from '../utils/iconHelper.js'

const props = defineProps({
  active: String,
  collapsed: Boolean
})



const emit = defineEmits(['update:active', 'update:collapsed'])

const expandedKeys = ref([])
const isCollapsed = ref(props.collapsed || false)

// 子菜单弹出框状态
const submenuPopup = ref({
  show: false,
  menu: null,
  top: 0
})

// 弹出框位置样式
const submenuPopupStyle = computed(() => ({
  position: 'fixed',
  top: `${submenuPopup.value.top}px`,
  left: '72px',
  zIndex: 101
}))

// 显示子菜单弹出框
const showSubmenuPopup = (menu, event) => {
  const rect = event.currentTarget.getBoundingClientRect()
  submenuPopup.value.menu = menu
  submenuPopup.value.top = rect.top
  submenuPopup.value.show = true
}

// 处理子菜单点击
const handleSubmenuClick = (key) => {
  submenuPopup.value.show = false
  handleClick(key)
}

// 页面加载时从 localStorage 恢复折叠状态
onMounted(() => {
  const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
  if (saved !== null) {
    isCollapsed.value = saved === 'true'
    emit('update:collapsed', isCollapsed.value)
  }
})

// 监听 props.collapsed 变化
watch(() => props.collapsed, (val) => {
  isCollapsed.value = val
})

// 监听 isCollapsed 变化，保存到 localStorage
watch(isCollapsed, (val) => {
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(val))
})

const toggleCollapse = () => {
  submenuPopup.value.show = false
  isCollapsed.value = !isCollapsed.value
  emit('update:collapsed', isCollapsed.value)
}

// 监听 active 变化，自动展开父菜单
watch(() => props.active, (val) => {
  if (val?.startsWith('software-') && !expandedKeys.value.includes('software')) {
    expandedKeys.value.push('software')
  }
}, { immediate: true })

const toggleExpand = (key) => {
  const index = expandedKeys.value.indexOf(key)
  if (index > -1) {
    expandedKeys.value.splice(index, 1)
  } else {
    expandedKeys.value.push(key)
  }
}

const handleClick = (key) => {
  emit('update:active', key)
}
</script>

<style scoped>
.side-menu {
  height: 100vh;
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-outline);
  width: 200px;
  transition: width 0.3s ease;
}

.side-menu.collapsed {
  width: 72px;
}

.logo {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--color-outline);
  position: relative;
}

.side-menu.collapsed .logo {
  padding: 20px 12px;
  justify-content: center;
}

.collapse-btn {
  margin-left: auto;
  color: var(--color-primary);
}

.side-menu.collapsed .collapse-btn {
  margin-left: 0;
  position: absolute;
  right: -12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-primary);
}

.menu-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-on-surface);
}

.side-menu.collapsed .menu-item {
  padding: 12px;
  justify-content: center;
}

.side-menu.collapsed .menu-icon {
  margin-right: 0;
}

.menu-item:hover {
  background: var(--color-surface-container-highest);
}

.menu-item.active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.menu-icon {
  margin-right: 12px;
  color: var(--color-on-surface-variant);
}

.menu-item.active .menu-icon {
  color: var(--color-on-primary-container);
}

.menu-title {
  flex: 1;
  font-size: 14px;
}

.expand-icon {
  transition: transform 0.2s;
  color: var(--color-on-surface-variant);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.menu-group {
  margin-bottom: 4px;
}

.sub-menu-list {
  padding-left: 8px;
}

.sub-menu-item {
  display: flex;
  align-items: center;
  padding: 10px 16px 10px 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  gap: 8px;
}

.sub-menu-item:hover {
  background: var(--color-surface-container-highest);
}

.sub-menu-item.active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

/* 子菜单弹出框样式 */
.submenu-overlay {
  position: fixed;
  top: 0;
  left: 72px;
  right: 0;
  bottom: 0;
  z-index: 99;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.submenu-popup-wrapper {
  position: fixed;
  z-index: 100;
}

.submenu-popup-content {
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.08);
  backdrop-filter: blur(20px) saturate(140%);
  -webkit-backdrop-filter: blur(20px) saturate(140%);
  will-change: backdrop-filter;
  border-radius: 12px;
  padding: 12px;
  margin-left: 8px;
  min-width: 180px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

html.dark .submenu-popup-content {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.18);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

/* 子菜单弹出过渡动画 */
.submenu-enter-active,
.submenu-leave-active {
  transition: opacity 0.2s ease;
}
.submenu-enter-active .submenu-overlay,
.submenu-leave-active .submenu-overlay {
  transition: opacity 0.2s ease, backdrop-filter 0.2s ease, -webkit-backdrop-filter 0.2s ease;
}
.submenu-enter-active .submenu-popup-content,
.submenu-leave-active .submenu-popup-content {
  transition: opacity 0.2s ease 0.2s, transform 0.2s ease 0.2s;
}
.submenu-enter-from,
.submenu-leave-to {
  opacity: 0;
}
.submenu-enter-from .submenu-overlay,
.submenu-leave-to .submenu-overlay {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}
.submenu-enter-from .submenu-popup-content,
.submenu-leave-to .submenu-popup-content {
  opacity: 0;
  transform: translateX(-12px);
}

.submenu-popup-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-outline);
  margin-bottom: 8px;
}

.submenu-popup-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-on-surface);
  font-size: 13px;
  gap: 10px;
}

.submenu-popup-item:hover {
  background: var(--color-surface-container-highest);
}

.submenu-popup-item.active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.submenu-icon {
  width: 18px;
  height: 18px;
}
</style>