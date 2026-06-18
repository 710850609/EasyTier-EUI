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

// 使用 import.meta.glob 预加载所有视图组件（包括子目录）
// eager: true 表示同步加载，所有组件合并到主 bundle
const viewModules = import.meta.glob('../views/**/*.vue', { eager: true })

// 菜单树结构（每个节点单行）
export const menuTree = [
  { key: 'nodes', label: '节点', icon: 'format-list-checkbox', title: '节点管理', component: 'Nodes' },
  { key: 'config', label: '配置', icon: 'bookmark-outline', title: '配置管理', component: 'Config' },
  { key: 'software', label: '应用', icon: 'shopping-outline', title: '软件下载',
    children: [
      { key: 'softwares-windows', label: 'Windows', icon: { type: 'mdi', name: 'mdiMicrosoftWindows' }, component: 'softwares/Windows' },
      { key: 'softwares-android', label: 'Android', icon: { type: 'mdi', name: 'mdiAndroid' }, component: 'softwares/Android' },
      { key: 'softwares-macos', label: 'MacOS', icon: { type: 'mdi', name: 'mdiLaptop' }, component: 'softwares/MacOS' },
      { key: 'softwares-linux', label: 'Linux', icon: { type: 'mdi', name: 'mdiPenguin' }, component: 'softwares/Linux' },
      { key: 'softwares-feiniu', label: 'FnOS', icon: { type: 'mdi', name: 'mdiAlphaFBox' }, component: 'softwares/FnOS' },
      { key: 'softwares-ios', label: 'IOS', icon: { type: 'mdi', name: 'mdiApple' }, component: 'softwares/IOS' },
      { key: 'softwares-harmonyos', label: 'HarmonyOS', icon: { type: 'mdi', name: 'mdiCellphone' }, component: 'softwares/HarmonyOS' },
      // { key: 'softwares-feiniu', label: 'FnOS', icon: 'data:image/png;base64,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', component: 'softwares/FnOS' },
    ]
  },
  { key: 'settings', label: '设置', icon: 'cog-outline', title: '系统设置', component: 'Settings' }
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
const buildComponentMap = () => {
  const map = {}
  const flatMenus = flattenMenuTree(menuTree)
  flatMenus.forEach(item => {
    // 只有叶子节点（没有子菜单）且配置了 component 才加入映射
    if (!item.children && item.component) {
      const modulePath = `../views/${item.component}.vue`
      if (viewModules[modulePath]) {
        // eager: true 时，直接取 default 导出
        map[item.key] = viewModules[modulePath].default
      }
    }
  })
  return map
}

export const componentMap = buildComponentMap()

export default menuTree
