/**
 * 菜单配置
 * 统一维护应用的所有菜单项
 * 
 * 图标配置方式：
 * 1. Varlet 内置图标: icon: 'format-list-checkbox' (字符串)
 * 2. @mdi/js 图标: icon: { type: 'mdi', name: 'mdiHome' } - name 为库的导出名称
 * 3. @mdi/light-js 图标: icon: { type: 'mdil/light', name: 'mdilPencil' } - name 为库的导出名称
 * 4. 图片路径: icon: './images/windows.svg'
 */

// 核心页面（Nodes、Config）同步加载，确保首屏速度
const coreModules = import.meta.glob('../views/{Nodes,Config}.vue', { eager: true })

// 非核心页面延迟加载，减少首屏 bundle 体积
const lazyModules = import.meta.glob('../views/**/*.vue')

// 菜单树结构（每个节点单行）
export const menuTree = [
  { key: 'nodes', label: 'menu.nodes.label', icon: 'format-list-checkbox', title: 'menu.nodes.title', component: 'Nodes' },
  { key: 'config', label: 'menu.config.label', icon: 'bookmark-outline', title: 'menu.config.title', component: 'Config' },
  { key: 'software', label: 'menu.software.label', icon: 'shopping-outline', title: 'menu.software.title',
    children: [
      { key: 'softwares-windows', label: 'menu.software.windows', icon: { type: 'mdi', name: 'mdiMicrosoftWindows' }, component: 'softwares/Windows' },
      { key: 'softwares-macos', label: 'menu.software.macos', icon: { type: 'mdi', name: 'mdiLaptop' }, component: 'softwares/MacOS' },
      { key: 'softwares-linux', label: 'menu.software.linux', icon: { type: 'mdi', name: 'mdiPenguin' }, component: 'softwares/Linux' },
      { key: 'softwares-feiniu', label: 'menu.software.fnos', icon: { type: 'mdi', name: 'mdiAlphaFBox' }, component: 'softwares/FnOS' },
      { key: 'softwares-android', label: 'menu.software.android', icon: { type: 'mdi', name: 'mdiAndroid' }, component: 'softwares/Android' },
      { key: 'softwares-ios', label: 'menu.software.ios', icon: { type: 'mdi', name: 'mdiApple' }, component: 'softwares/IOS' },
      { key: 'softwares-harmonyos', label: 'menu.software.harmonyos', icon: { type: 'mdi', name: 'mdiCellphone' }, component: 'softwares/HarmonyOS' },
      { key: 'softwares-docker', label: 'menu.software.docker', icon: { type: 'mdi', name: 'mdiDocker' }, component: 'softwares/Docker' },
    ]
  },
  { key: 'settings', label: 'menu.settings.label', icon: 'cog-outline', title: 'menu.settings.title', component: 'Settings' }
]

// 扁平化菜单树
const flattenMenuTree = (items) => {
  const result = []
  items.forEach(item => {
    result.push(item)
    if (item.children) {
      result.push(...flattenMenuTree(item.children))
    }
  })
  return result
}

// 组件映射表（从菜单树构建）
// 只处理叶子节点（没有 children 的菜单项）
// 核心页面（Nodes, Config）同步加载，其他页面延迟加载
const buildComponentMap = () => {
  const map = {}
  const flatMenus = flattenMenuTree(menuTree)
  flatMenus.forEach(item => {
    if (!item.children && item.component) {
      const modulePath = `../views/${item.component}.vue`
      if (coreModules[modulePath]) {
        // 核心页面同步加载
        map[item.key] = coreModules[modulePath].default
      } else if (lazyModules[modulePath]) {
        // 非核心页面延迟加载，存储异步导入函数
        map[item.key] = lazyModules[modulePath]
      }
    }
  })
  return map
}

export const componentMap = buildComponentMap()

export default menuTree