<template>
  <div class="layout" :class="{ 'dark': isDark, 'menu-collapsed': isMenuCollapsed, 'is-mobile': isMobile }">
      <side-menu
        v-if="!isMobile"
        :active="activeMenu"
        v-model:collapsed="isMenuCollapsed"
        @update:active="handleMenuChange"
        class="side-menu"
      />

      <main class="main-content" :class="{ 'has-bottom-nav': isMobile }">
        <div class="content-wrapper">
          <component :is="currentComponent" />
        </div>
      </main>

      <bottom-nav
        v-if="isMobile"
        :active="activeMenu"
        @update:active="handleMenuChange"
      />
    </div>
</template>

<script setup>
import SideMenu from './SideMenu.vue'
import BottomNav from './BottomNav.vue'
import { componentMap } from '../config/menu.js'
import { isDark } from '../config/theme.js'
import { VCONSOLE_ENABLED_KEY } from '../config/storage-keys.js'
import { useI18n } from 'vue-i18n'
import toast from './toast.js'

const { t } = useI18n()

// 动态导入 Empty 组件，避免与 menu.js 中的动态导入冲突
const Empty = defineAsyncComponent(() => import('../views/Empty.vue'))

const isMobile = ref(window.innerWidth < 768)
const activeMenu = ref('nodes')
const isMenuCollapsed = ref(false)
const fastSettingMode = ref(false)

const handleMenuChange = (key) => {
  activeMenu.value = key
}

// 提供主题状态给子组件
provide('isDark', isDark)
// 提供当前菜单状态给子组件
provide('activeMenu', readonly(activeMenu))
provide('setActiveMenu', handleMenuChange)
provide('fastSettingMode', fastSettingMode)

const currentComponent = computed(() => {
  const component = componentMap[activeMenu.value]
  // 如果没有对应组件，返回空组件（显示提示或保持当前页面）
  if (!component) {
    return Empty
  }
  // 组件已同步加载，直接使用
  return component
})

// 从 localStorage 加载 VConsole（动态导入）
const loadVConsole = async () => {
  const vconsoleEnabled = localStorage.getItem(VCONSOLE_ENABLED_KEY)
  if (vconsoleEnabled !== 'true') return

  try {
    const VConsole = await import('vconsole')
    new VConsole.default()
  } catch (error) {
    console.error('加载 VConsole 失败:', error)
    localStorage.setItem(VCONSOLE_ENABLED_KEY, 'false')
    toast.error(t('settings.vconsoleFailed') + '\n' + error.message)
  }
}

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

// 防抖：停止调整 150ms 后才执行，避免频繁计算
let resizeTimer;
const handleResizeDebounced = () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    handleResize();
  }, 150);
}

onMounted(() => {
  window.addEventListener('resize', handleResizeDebounced)
  // 初始化时执行一次，确保状态正确
  handleResize()
  // 加载 VConsole（如果之前开启过）
  loadVConsole()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResizeDebounced)
  clearTimeout(resizeTimer)
})
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-body);
}

.side-menu {
  flex-shrink: 0;
  border-right: 1px solid var(--color-outline);
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: 200px;
  transition: margin-left 0.3s ease;
}

.menu-collapsed .main-content {
  margin-left: 72px;
}

.main-content.has-bottom-nav {
  padding-bottom: 64px;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* 移动端样式 - 使用类名控制 */
.layout.is-mobile {
  flex-direction: column;
  height: 100vh;
}

.layout.is-mobile .main-content {
  width: 100%;
  margin-left: 0;
}

.layout.is-mobile .content-wrapper {
  overflow-y: auto;
  padding: 0;
  flex: 1;
  min-height: 0;
}

/* 媒体查询作为后备 */
@media (max-width: 767px) {
  .layout {
    flex-direction: column;
    height: 100vh;
  }
  
  .side-menu {
    position: relative;
    width: 100%;
    height: auto;
  }
  
  .main-content {
    width: 100%;
    margin-left: 0;
  }
  
  .content-wrapper {
    overflow-y: auto;
    padding: 0;
    flex: 1;
    min-height: 0;
  }
}
</style>