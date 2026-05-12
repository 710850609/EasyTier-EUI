<template>
  <div class="nodes-page">
    <!-- 统计标题栏 -->
    <var-paper class="stats-bar" :elevation="1">
      <div class="stats-content">
        <div class="config-section">
          <var-select
            variant="outlined"
            class="config-select"
            size="small"
            v-model="selectedConfig"
            @change="handleConfigChange"
            placeholder="选择配置"
          >
            <var-option
              v-for="cfg in configList"
              :key="cfg.profile"
              :label="cfg.name"
              :value="cfg.profile"
            >
              <div class="config-option">
                <svg-icon size="16" type="mdi" :path="mdiCircle" :color="cfg.running ? 'var(--color-success)' : 'var(--color-text-disabled)'"></svg-icon>
                <span>{{ cfg.name }}</span>
              </div>
            </var-option>
          </var-select>
          <div class="service-status" v-if="selectedConfig">
             <var-chip size="small" :type="serviceRunning ? 'success' : 'danger'">
              {{ serviceOperating ? (serviceRunning ? '停止中...' : '启动中...') : serviceRunning ? '运行中' : '未启动' }}
             </var-chip>
          </div>
          <div class="service-actions">
            <var-loading type="circle" v-if="serviceOperating" />
            <var-button
              type="primary"
              size="small"
              auto-loading
              @click="startService"
              v-if="selectedConfig && !serviceRunning && !serviceOperating"
            >
              启动
            </var-button>
            <var-button
              type="danger"
              auto-loading
              size="small"
               
              @click="stopService"
              v-if="serviceRunning && !serviceOperating"
            >
              停止
            </var-button>
            <!-- <var-icon name="play-circle" size="24" @click="startService" color="var(--color-success)" v-if="!serviceRunning && !serviceOperating" :style="{ cursor: 'pointer' }"/> -->
            <!-- <var-icon name="radio-marked" size="24" @click="stopService" color="var(--color-danger)" v-if="serviceRunning && !serviceOperating"  :style="{ cursor: 'pointer' }"/> -->
          </div>
        </div>
        <!-- <div class="divider"></div> -->
        <div class="stat-item">
          <var-icon name="server" size="20" color="var(--color-primary)" />
          <span class="stat-label">普通节点</span>
          <span class="stat-value">{{ normalNodes.length }}</span>
        </div>
        <div class="divider"></div>
        <div class="stat-item">
          <var-icon name="cloud" size="20" color="var(--color-success)" />
          <span class="stat-label">服务节点</span>
          <span class="stat-value">{{ serverNodes.length }}</span>
        </div>
        
        <var-button
          text
          round
          class="column-btn"
          @click="showFilterMenu = true"
        >
          <var-icon name="menu" size="24" color="var(--color-on-surface)" />
        </var-button>
      </div>
    </var-paper>

    <!-- 筛选菜单 popup -->
    <var-popup v-model:show="showFilterMenu" position="top">
      <var-paper class="filter-menu">
        <var-tabs v-model:active="activeTab" @change="handleTabChange">
          <var-tab name="columnsFilter">
            <div class="tab-label">
              <span>列选择</span>
            </div>
          </var-tab>
          <var-tab name="rowFilter">
            <div class="tab-label">
              <span>行选择</span>
            </div>
          </var-tab>
          <var-tab name="refreshSpeed">
            <div class="tab-label">
              <span>刷新速度</span>
            </div>
          </var-tab>
        </var-tabs>
        
        <!-- 列选择内容 -->
        <div v-if="activeTab === 'columnsFilter'" class="tab-content">
          <var-checkbox-group v-model="selectedColumns" direction="vertical">
            <var-checkbox 
              v-for="col in allColumns" 
              :key="col.key"
              :checked-value="col.key"
              :disabled="col.key === 'ipv4'"
            >
              {{ col.label }}
            </var-checkbox>
          </var-checkbox-group>
        </div>
        
        <!-- 节点筛选内容 -->
        <div v-if="activeTab === 'rowFilter'" class="tab-content">
          <div class="filter-subtitle">节点类型</div>
          <var-checkbox-group v-model="selectedNodeTypes" direction="vertical">
            <var-checkbox checked-value="normal">
              <div class="type-option">
                <var-icon name="server" size="18" color="var(--color-primary)" />
                <span>普通节点</span>
              </div>
            </var-checkbox>
            <var-checkbox checked-value="server">
              <div class="type-option">
                <var-icon name="cloud" size="18" color="var(--color-success)" />
                <span>服务节点</span>
              </div>
            </var-checkbox>
          </var-checkbox-group>
        </div>

        <!-- 刷新速度内容 -->
        <div v-if="activeTab === 'refreshSpeed'" class="tab-content">
          <var-select variant="outlined" placeholder="请选择更新频率" v-model="refreshStep">
            <var-option v-for="item in refreshStepList" :label="item.label" :value="item.key" />
          </var-select>
        </div>
      </var-paper>
    </var-popup>  

    <!-- 数据表格 -->
    <var-paper class="table-container" :elevation="1">
      <div class="table-wrapper" ref="tableWrapper">
        <!-- 骨架屏 - 加载时显示 -->
        <div v-if="loadingSkeleton" class="skeleton-container">
          <div class="skeleton-header">
            <div v-for="n in visibleColumns.length" :key="n" class="skeleton-cell skeleton-title"></div>
          </div>
          <div class="skeleton-body">
            <div v-for="row in 8" :key="row" class="skeleton-row">
              <div v-for="n in visibleColumns.length" :key="n" class="skeleton-cell">
                <div class="skeleton-item" :style="{ width: getSkeletonWidth(n) }"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 实际表格 -->
        <table v-else class="data-table">
          <thead class="fixed-header">
            <tr>
              <th 
                v-for="(col, index) in visibleColumns" 
                :key="col.key"
                :class="{ 'fixed-col': index === 0 }"
              >
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="node in filteredNodes" :key="node.id">
              <td 
                v-for="(col, index) in visibleColumns" 
                :key="col.key"
                :class="{ 'fixed-col': index === 0 }"
              >
                <template v-if="col.key === 'cost'">
                  <var-badge 
                    :type="node.cost === 'Local' ? 'info' : (node.cost === 'p2p' ? 'success' : 'primary')" 
                    :value="parseNode(node, col.key)"
                  />
                </template>
                <template v-else>
                  <var-tooltip v-if="['hostname', 'tunnel_proto'].includes(col.key)" :content="parseNode(node, col.key)">
                    <span class="cell-text" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}</span>
                  </var-tooltip>
                  <span v-else class="cell-text" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}</span>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </var-paper>

    <var-dialog v-model:show="showFastSettingTip" :close-on-click-overlay="false" 
      @confirm="openConfigView(true)" @cancel="openConfigView(false)"
      confirmButtonText="需要" cancelButtonText="不需要">
      <template #title>
        <var-icon name="information" color="#2979ff" />
        <span style="color: #2979ff" >不存在组网配置</span>
      </template>
      <var-cell title="是否需要快速配置（新手推荐）？" description="" />
    </var-dialog>
    
  </div>
</template>

<script setup>
import { copyToClipboard } from '../utils/clipboard.js'
import { api, cancelAllRequests } from '../utils/api.js'
import toast from '../components/toast.js'
import { Poller } from '../utils/poller.js'
import { NODES_SELECTED_COLUMNS_KEY, NODES_SELECTED_NODE_TYPES_KEY, NODES_REFRESH_STEP_KEY } from '../config/storage-keys.js'
import { mdiCircle } from '@mdi/js'
import SvgIcon from '@jamescoyle/vue-icon'

// 注入菜单切换方法和快速设置模式
const setActiveMenu = inject('setActiveMenu')
const fastSettingMode = inject('fastSettingMode')
const showFastSettingTip = ref(false)
const isFirstLoadConfigs = ref(true)

const showFilterMenu = ref(false)
const dataLoading = ref(false)
const isUnmounted = ref(false)
const activeTab = ref('columnsFilter')
// 加载骨架屏
const loadingSkeleton = ref(true)

// 默认选中的列
const selectedColumns = ref(['ipv4', 'hostname', 'cost', 'lat_ms', 'loss_rate', 'rx_bytes', 'tx_bytes'])
// 默认选中的节点类型
const selectedNodeTypes = ref(['normal'])
// 刷新速度
const refreshStep = ref(3)
// 节点数据
const allNodes = ref([])

const configList = ref([])
const selectedConfig = ref('')
const serviceRunning = ref(false)
const serviceOperating = ref(false)
const pendingAction = ref('')


// 从 localStorage 加载设置
const loadSettings = () => {
  const savedColumns = localStorage.getItem(NODES_SELECTED_COLUMNS_KEY)
  if (savedColumns) {
    try {
      selectedColumns.value = JSON.parse(savedColumns)
    } catch (e) {
      console.error('加载列设置失败:', e)
    }
  }

  const savedNodeTypes = localStorage.getItem(NODES_SELECTED_NODE_TYPES_KEY)
  if (savedNodeTypes) {
    try {
      selectedNodeTypes.value = JSON.parse(savedNodeTypes)
    } catch (e) {
      console.error('加载节点类型设置失败:', e)
    }
  }

  const savedRefreshStep = localStorage.getItem(NODES_REFRESH_STEP_KEY)
  if (savedRefreshStep) {
    refreshStep.value = parseInt(savedRefreshStep, 10) || 3000
  }
}

// 监听变化并保存到 localStorage
watch(selectedColumns, (newVal) => {
  localStorage.setItem(NODES_SELECTED_COLUMNS_KEY, JSON.stringify(newVal))
}, { deep: true })

watch(selectedNodeTypes, (newVal) => {
  localStorage.setItem(NODES_SELECTED_NODE_TYPES_KEY, JSON.stringify(newVal))
}, { deep: true })

// 创建节点列表轮询器实例
const nodesPoller = new Poller({
  interval: refreshStep.value * 1000,
  immediate: false,
  onError: (error) => console.error('获取节点列表失败:', error)
})

// 创建配置状态轮询器实例（每10秒刷新一次）
const configStatusPoller = new Poller({
  interval: refreshStep.value * 1000,
  immediate: false,
  onError: (error) => console.error('获取配置状态失败:', error)
})

// 监听刷新间隔变化，更新轮询器
watch(refreshStep, (newVal) => {
  localStorage.setItem(NODES_REFRESH_STEP_KEY, newVal.toString())
  nodesPoller.setInterval(newVal * 1000)
  configStatusPoller.setInterval(newVal * 1000)
})

const refreshStepList = [
  { key: 1, label: '1秒' },
  { key: 2, label: '2秒' },
  { key: 3, label: '3秒' },
  { key: 4, label: '4秒' },
  { key: 5, label: '5秒' },
  { key: 10, label: '10秒' },
]
// 所有可用列
const allColumns = [
  { key: "ipv4", label: "IPv4" },
  { key: "cidr", label: "网段" },
  { key: "hostname", label: "主机名" },
  { key: "cost", label: "穿透方式" },
  { key: "tunnel_proto", label: "协议" },
  { key: "lat_ms", label: "延迟" },
  { key: "loss_rate", label: "丢包率" },
  { key: "rx_bytes", label: "下载" }, 
  { key: "tx_bytes", label: "上传" },
  { key: "nat_type", label: "Nat类型" },
  { key: "version", label: "内核版本" },
  { key: "id", label: "id" },
]

// 可见列
const visibleColumns = computed(() => {
  return allColumns.filter(col => selectedColumns.value.includes(col.key))
})

const normalNodes = computed(() => allNodes.value.filter(n => n.type === 'normal'))
const serverNodes = computed(() => allNodes.value.filter(n => n.type === 'server'))

// 根据选择的节点类型筛选数据
const filteredNodes = computed(() => {
  return allNodes.value.filter(node => selectedNodeTypes.value.includes(node.type))
})

// 处理 tab 切换
const handleTabChange = (tab) => {
  activeTab.value = tab
}

// 防止重复点击
let isCopying = false

const handleClickCell = async (node, key) => {
  if (key === 'ipv4' && node[key]) {
    if (isCopying) return
    
    isCopying = true
    try {
      const success = await copyToClipboard(node[key])
      if (success) {
        toast.success(`已复制: ${node[key]}`)
      } else {
        toast.error('复制失败')
      }
    } catch (error) {
      console.error('复制出错:', error)
      toast.error('复制出错')
    } finally {
      // 延迟重置，防止快速连续点击
      setTimeout(() => {
        isCopying = false
      }, 500)
    }
  }
}

const parseNode = (node, key) => {
  switch (key) {
  case 'cost':
    return parseCost(node)
  case 'nat_type':
    return parseNatType(node)
  default:
    return node[key]
  }
}

const parseCost = (node) => {
  if (node.cost === 'p2p') {
    return '直连'
  } else if (node.cost === 'Local') {
    return '本地'
  } else if (node.cost.startsWith('relay')) {
    return node.cost.replace('relay', '中继')
  } else {
    return node.cost
  }
}

const parseNatType = (node) => {
  if (node.nat_type === 'FullCone') {
    return 'Nat1'
  } else if (node.nat_type === 'Restricted') {
    return 'Nat2'
  } else if (node.nat_type === 'PortRestricted') {
    return 'Nat3'
  } else if (node.nat_type === 'Symmetric') {
    return 'Nat4'
  } else if (node.nat_type === 'SymmetricEasyInc') {
    return 'Nat4(对称递增型)'
  } else if (node.nat_type === 'SymmetricEasyDec') {
    return 'Nat4(对称递减型)'
  } else if (node.nat_type === 'SymUdpFirewall') {
    return '对称UDP防火墙'
  } else if (['NoPAT', 'NoPat'].includes(node.nat_type)) {
    return `无PAT`
  } else if (node.nat_type === 'OpenInternet') {
    return '开放网络'
  } else if (node.nat_type === 'Unknown') {
    return '未知'
  } else {
    return node.nat_type
  }
}

// 骨架屏宽度随机化，更真实
const getSkeletonWidth = (index) => {
  const widths = ['60%', '80%', '40%', '70%', '50%', '90%', '65%', '45%']
  return widths[(index + Math.floor(Math.random() * 3)) % widths.length]
}

const fetchNodes = async () => {
  if (dataLoading.value) return
  dataLoading.value = true
  try {
    const params = {}
    if (selectedConfig.value) {
      params.profile = selectedConfig.value
    }
    const data = await api.monitor.getList(params);
    if (isUnmounted.value) return
    let peersData = []
    if (Array.isArray(data)) {
      peersData = data
    } else if (data && Array.isArray(data.data)) {
      peersData = data.data
    } else {
      console.error('Unexpected response format:', data)
    }
    peersData.sort((a, b) => {
      const hasIpA = a.ipv4 && a.ipv4.trim() !== ''
      const hasIpB = b.ipv4 && b.ipv4.trim() !== ''
      if (!hasIpA && !hasIpB) return 0
      if (!hasIpA) return 1
      if (!hasIpB) return -1
      return a.ipv4 > b.ipv4
    })
    allNodes.value = peersData
    peersData.forEach(peer => {
      if (peer.hostname.startsWith('PublicServer_')) {
        peer.type = 'server'
        peer.hostname = peer.hostname.replace('PublicServer_', '')
      } else {
        peer.type = 'normal'
      }
    })
  } catch (error) {
    if (isUnmounted.value) return
    console.error('获取组网信息失败:', error)
  } finally {
    dataLoading.value = false
  }
}

const openConfigView = (isFastConfig) => {
  fastSettingMode.value = isFastConfig ? true : false
  setActiveMenu?.('config')
}

const restartService = () => {
  return new Promise((resolve, reject) => {
    try {
      api.services.restart(selectedConfig.value).then(() => {
        toast.success('服务重启成功')
        resolve()
      }).catch(e => reject(e))
    } catch (error) {
      toast.error('服务重启失败: ' + error.message)
      reject(error)
    }
  })
}

const loadConfigs = async () => {
  try {
    const res = await api.configs.listConfigStatus()
    configList.value = res.data || []
    updateServiceStatus()
    if (isFirstLoadConfigs.value && configList.value.length > 0 && !selectedConfig.value) {
      isFirstLoadConfigs.value = false
      selectedConfig.value = configList.value.filter(e => e.running || false)?.[0]?.profile
      if (!selectedConfig.value) {
        selectedConfig.value = configList.value[0].profile
      }
    }
  } catch (error) {
    console.error('加载配置列表失败:', error)
  }
}

const updateServiceStatus = () => {
  const cfg = configList.value.find(c => c.profile === selectedConfig.value)
  serviceRunning.value = cfg ? cfg.running : false
}

const handleConfigChange = async () => {
  updateServiceStatus()
  allNodes.value = []
  nodesPoller.stop()
  cancelAllRequests()
  console.log('serviceRunning.value', serviceRunning.value)
  if (serviceRunning.value) {
    loadingSkeleton.value = true
    dataLoading.value = false
    isUnmounted.value = false
    await fetchNodes()
    loadingSkeleton.value = false
  }
  nodesPoller.start(fetchNodes)
}

const startService = async () => {
  if (serviceOperating.value) return
  serviceOperating.value = true
  pendingAction.value = 'start'
  try {
    allNodes.value = []
    await api.services.start(selectedConfig.value)
    toast.success('服务启动成功')
    serviceRunning.value = true
    const cfg = configList.value.find(c => c.profile === selectedConfig.value)
    if (cfg) cfg.running = true
    fetchNodes()
  } catch (error) {
    toast.error('服务启动失败: ' + error.message)
  } finally {
    serviceOperating.value = false
    pendingAction.value = ''
  }
}

const stopService = async () => {
  if (serviceOperating.value) return
  serviceOperating.value = true
  pendingAction.value = 'stop'
  try {
    await api.services.stop(selectedConfig.value)
    toast.success('服务已停止')
    serviceRunning.value = false
    const cfg = configList.value.find(c => c.profile === selectedConfig.value)
    if (cfg) cfg.running = false
  } catch (error) {
    toast.error('服务停止失败: ' + error.message)
  } finally {
    serviceOperating.value = false
    pendingAction.value = ''
  }
}

// 实际项目中这里调用 HTTP API
onMounted(async () => {
  loadSettings()
  await loadConfigs()
  try {
    if (!selectedConfig.value) {
      showFastSettingTip.value = true
      return;
    }
  } catch (error) {
    console.error('获取配置状态失败:', error)
    return
  }
  try {
    await fetchNodes()
    loadingSkeleton.value = false
    // 启动配置状态轮询
    configStatusPoller.start(loadConfigs)
    nodesPoller.start(fetchNodes)
  } catch (error) {
    console.error('获取节点列表失败:', error)
  }
})

// 页面销毁时清除定时器和取消请求
onUnmounted(() => {
  isUnmounted.value = true
  nodesPoller.stop()
  configStatusPoller.stop()
  cancelAllRequests()
})

</script>

<style scoped>
.nodes-page {
  padding: 16px;
}

.stats-bar {
  padding: 16px 20px;
  margin-bottom: 16px;
  border-radius: 12px;
  background: var(--color-surface-container) !important;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.config-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-select {
  min-width: 160px;
  max-width: 200px;
}

.config-option {
  display: flex;
  align-items: center;
  justify-content: left;
  width: 100%;
  gap: 8px;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.status-text {
  font-size: 13px;
  font-weight: 500;
}

.service-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: var(--color-on-surface-variant);
  font-size: 14px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.divider {
  width: 1px;
  height: 24px;
  background: var(--color-outline);
}

.column-btn {
  margin-left: auto;
}

.filter-menu {
  padding: 16px;
  max-height: 500px;
  display: flex;
  flex-direction: column;
}

.filter-menu :deep(.var-tabs) {
  flex-shrink: 0;
}

.filter-menu .tab-content {
  overflow-y: auto;
  max-height: 400px;
}



.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-content {
  padding: 16px 0;
}

.filter-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text);
}

.table-container {
  border-radius: 12px;
  overflow: hidden;
}

.table-wrapper {
  overflow: auto;
  max-height: calc(100vh - 160px);
  position: relative;
}

@media (max-width: 768px) {
  .table-wrapper {
    max-height: calc(100vh - 180px);
  }
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 800px;
}

/* 首行固定 - 所有表头统一样式，使用 surface-container 背景 */
.fixed-header th {
  position: sticky;
  top: 0;
  background: var(--color-surface-container);
  z-index: 20;
}

/* 首行首列交叉点 - 与首行其他单元格样式一致 */
.fixed-header th.fixed-col {
  position: sticky;
  top: 0;
  left: 0;
  z-index: 25;
  background: var(--color-surface-container);
}

/* 首列固定 */
.fixed-col {
  position: sticky;
  left: 0;
  background: var(--color-surface-container);
  z-index: 10;
}

th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--color-on-surface);
  border-bottom: 2px solid var(--color-outline);
  white-space: nowrap;
}

td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  color: var(--color-on-surface-variant);
  background: var(--color-surface) !important;
}

.cell-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

tr:hover td {
  background: var(--color-surface-container-high);
}

/* 骨架屏样式 */
.skeleton-container {
  min-width: 800px;
}

.skeleton-header {
  display: flex;
  padding: 16px;
  border-bottom: 2px solid var(--color-outline);
  background: var(--color-surface-container-highest);
}

.skeleton-body {
  padding: 8px 0;
}

.skeleton-row {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.skeleton-cell {
  flex: 1;
  padding: 0 8px;
}

.skeleton-title {
  height: 16px;
  background: linear-gradient(90deg, var(--color-outline) 25%, var(--color-surface-container) 50%, var(--color-outline) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-item {
  height: 14px;
  background: linear-gradient(90deg, var(--color-outline-variant) 25%, var(--color-surface-container) 50%, var(--color-outline-variant) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
