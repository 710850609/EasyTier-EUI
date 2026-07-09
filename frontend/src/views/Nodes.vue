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
            :placeholder="$t('nodes.selectConfig')"
            blur-color="var(--color-primary)"
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
             <var-chip size="small" :type="serviceRunning ? 'success' : 'danger'" elevation="0">
              {{ serviceOperating ? (serviceRunning ? $t('nodes.stopping') : $t('nodes.starting')) : serviceRunning ? $t('nodes.running') : $t('nodes.stopped') }}
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
              {{ $t('nodes.start') }}
            </var-button>
            <var-button
              type="danger"
              auto-loading
              size="small"               
              @click="stopService"
              v-if="serviceRunning && !serviceOperating"
            >
              {{ $t('nodes.stop') }}
            </var-button>
            <!-- <var-icon name="play-circle" size="24" @click="startService" color="var(--color-success)" v-if="!serviceRunning && !serviceOperating" :style="{ cursor: 'pointer' }"/> -->
            <!-- <var-icon name="radio-marked" size="24" @click="stopService" color="var(--color-danger)" v-if="serviceRunning && !serviceOperating"  :style="{ cursor: 'pointer' }"/> -->
          </div>
        </div>
        <!-- <div class="divider"></div> -->
        <div class="stat-item">
          <var-icon name="server" size="20" color="var(--color-primary)" />
          <span class="stat-label">{{ $t('nodes.normalNodes') }}</span>
          <span class="stat-value">{{ normalNodes.length }}</span>
        </div>
        <div class="divider"></div>
        <div class="stat-item">
          <var-icon name="cloud" size="20" color="var(--color-success)" />
          <span class="stat-label">{{ $t('nodes.serverNodes') }}</span>
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
              <span>{{ $t('nodes.dataSelect') }}</span>
            </div>
          </var-tab>
          <var-tab name="rowFilter">
            <div class="tab-label">
              <span>{{ $t('nodes.rowSelect') }}</span>
            </div>
          </var-tab>
          <var-tab name="refreshSpeed">
            <div class="tab-label">
              <span>{{ $t('nodes.refreshSpeed') }}</span>
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
          <div class="filter-subtitle">{{ $t('nodes.nodeType') }}</div>
          <var-checkbox-group v-model="selectedNodeTypes" direction="vertical">
            <var-checkbox checked-value="normal">
              <div class="type-option">
                <var-icon name="server" size="18" color="var(--color-primary)" />
                <span>{{ $t('nodes.normalNodes') }}</span>
              </div>
            </var-checkbox>
            <var-checkbox checked-value="server">
              <div class="type-option">
                <var-icon name="cloud" size="18" color="var(--color-success)" />
                <span>{{ $t('nodes.serverNodes') }}</span>
              </div>
            </var-checkbox>
          </var-checkbox-group>
          <div class="mobile-only-switch">
            <div class="filter-divider"></div>
            <div class="filter-subtitle">{{ $t('nodes.displayMode') }}</div>
            <div class="switch-row">
              <span>{{ $t('nodes.mobileCardList') }}</span>
              <var-checkbox :model-value="useMobileList" @change="toggleMobileList" />
            </div>
          </div>
        </div>

        <!-- 刷新速度内容 -->
        <div v-if="activeTab === 'refreshSpeed'" class="tab-content">
          <var-select variant="outlined" :placeholder="$t('nodes.refreshSpeedPlaceholder')" v-model="refreshStep" size="small" blur-color="var(--field-decorator-focus-color)">
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
        
        <!-- 实际表格 - PC模式 -->
        <table v-else class="data-table" :class="{ 'mobile-hidden': useMobileList }">
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
                <template v-else-if="col.key === 'lat_ms'">
                  <span class="cell-text" :class="{ 'lat-medium': node.lat_ms >= 60 && node.lat_ms <= 150, 'lat-high': node.lat_ms > 150 }" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}ms</span>
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

        <!-- 移动端卡片列表 -->
        <div v-if="!loadingSkeleton && useMobileList" class="mobile-node-list">
          <div 
            v-for="node in filteredNodes" 
            :key="node.id" 
            class="node-card"
            :class="{ 'node-server': node.type === 'server' }"
          >
            <div class="node-card-header">
              <div class="node-ip-row">
                <var-icon 
                  :name="node.type === 'server' ? 'cloud' : 'server'" 
                  size="18" 
                  :color="node.type === 'server' ? 'var(--color-success)' : 'var(--color-primary)'" 
                />
                <span class="node-ip card-left" @click="handleClickCell(node, 'ipv4')">{{ node.ipv4 || '' }}</span>
                <span v-if="visibleColumnsMap.hostname && node.hostname" class="info-chip host-chip card-right">
                  <var-icon name="label" size="14" />
                  {{ node.hostname }}
                </span>
              </div>
            </div>
            <div class="node-card-info">
              <var-badge 
                v-if="visibleColumnsMap.cost"
                :type="node.cost === 'Local' ? 'info' : (node.cost === 'p2p' ? 'success' : 'primary')" 
                :value="parseNode(node, 'cost')"
              />
              <span v-if="visibleColumnsMap.lat_ms && node.lat_ms !== undefined && node.lat_ms !== '-'" class="info-chip" :class="{ 'lat-medium': node.lat_ms >= 60 && node.lat_ms <= 150, 'lat-high': node.lat_ms > 150 }">
                {{ parseNode(node, 'lat_ms') }}ms
              </span>
              <span v-if="visibleColumnsMap.loss_rate && node.loss_rate !== undefined && node.loss_rate !== '-'" class="info-chip" :class="{ 'loss-warn': node.loss_rate > 0 }">
                {{ $t('nodes.packetLoss') }} {{ parseNode(node, 'loss_rate') }}
              </span>
              <span v-if="visibleColumnsMap.tunnel_proto && node.tunnel_proto && node.tunnel_proto !== '-'" class="info-chip">
                {{ node.tunnel_proto }}
              </span>
            </div>
            <div v-if="visibleColumnsMap.hostname || visibleColumnsMap.nat_type || visibleColumnsMap.tunnel_proto || visibleColumnsMap.cidr" class="node-card-meta">
              <span v-if="visibleColumnsMap.nat_type && node.nat_type" class="info-chip nat-chip card-left">
                {{ parseNode(node, 'nat_type') }}
              </span>
              <span v-if="visibleColumnsMap.rx_bytes && node.rx_bytes !== undefined && node.rx_bytes !== '-'" class="traffic-item download card-right">
                <svg-icon size="14" type="mdi" :path="mdilArrowDown" color="var(--color-primary)"></svg-icon>
                {{ parseNode(node, 'rx_bytes') }}
              </span>
              <span v-if="visibleColumnsMap.tx_bytes && node.tx_bytes !== undefined && node.tx_bytes !== '-'" class="traffic-item upload card-right">
                <svg-icon size="14" type="mdi" :path="mdilArrowUp" color="var(--color-success)"></svg-icon>
                {{ parseNode(node, 'tx_bytes') }}
              </span>
            </div>
            <div class="node-card-footer">
              <span v-if="visibleColumnsMap.version && node.version" class="version-text card-left">v{{ node.version }}</span>
              <span v-if="visibleColumnsMap.cidr && node.cidr" class="info-chip cidr-chip card-right">
                {{ node.cidr }}
              </span>
            </div>
          </div>
          <div v-if="filteredNodes.length === 0" class="empty-state">
            <var-icon name="inbox" size="48" color="var(--color-text-disabled)" />
            <p>{{ $t('nodes.no_nodes') }}</p>
          </div>
        </div>
      </div>
    </var-paper>

    <var-dialog v-model:show="showFastSettingTip" :close-on-click-overlay="false" 
      @confirm="openConfigView(true)" @cancel="openConfigView(false)"
      :confirmButtonText="$t('nodes.need')" :cancelButtonText="$t('nodes.noNeed')">
      <template #title>
        <var-icon name="information" color="#2979ff" />
        <span style="color: #2979ff" >{{ $t('nodes.noConfig') }}</span>
      </template>
      <var-cell :title="$t('nodes.needQuickSetup')" description="" />
    </var-dialog>
    
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { copyToClipboard } from '../utils/clipboard.js'
import { api, cancelAllRequests } from '../utils/api.js'
import toast from '../components/toast.js'
import { Poller } from '../utils/poller.js'
import { NODES_SELECTED_COLUMNS_KEY, NODES_SELECTED_NODE_TYPES_KEY, NODES_REFRESH_STEP_KEY, NODES_MOBILE_LIST_KEY } from '../config/storage-keys.js'
import { mdiCircle } from '@mdi/js'
import { mdilArrowDown, mdilArrowUp } from '@mdi/light-js'
import SvgIcon from '@jamescoyle/vue-icon'

const { t } = useI18n()

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
const selectedColumns = ref(['ipv4', 'hostname', 'cost', 'tunnel_proto','lat_ms', 'loss_rate', 'rx_bytes', 'tx_bytes', 'nat_type'])
// 默认选中的节点类型
const selectedNodeTypes = ref(['normal'])
// 刷新速度
const refreshStep = ref(3)
// 移动端列表模式（默认启用卡片列表）
const useMobileList = ref(true)
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

  const savedMobileList = localStorage.getItem(NODES_MOBILE_LIST_KEY)
  if (savedMobileList !== null) {
    try {
      useMobileList.value = JSON.parse(savedMobileList)
    } catch (e) {
      console.error('加载移动端列表模式失败:', e)
    }
  }
}

// 监听变化并保存到 localStorage
watch(selectedColumns, (newVal) => {
  localStorage.setItem(NODES_SELECTED_COLUMNS_KEY, JSON.stringify(newVal))
}, { deep: true })

watch(selectedNodeTypes, (newVal) => {
  localStorage.setItem(NODES_SELECTED_NODE_TYPES_KEY, JSON.stringify(newVal))
}, { deep: true })

watch(useMobileList, (newVal) => {
  localStorage.setItem(NODES_MOBILE_LIST_KEY, JSON.stringify(newVal))
})

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
  { key: 1, label: `1${t('nodes.second')}` },
  { key: 2, label: `2${t('nodes.second')}` },
  { key: 3, label: `3${t('nodes.second')}` },
  { key: 4, label: `4${t('nodes.second')}` },
  { key: 5, label: `5${t('nodes.second')}` },
  { key: 10, label: `10${t('nodes.second')}` },
]
// 所有可用列
const allColumns = computed(() => [
  { key: "ipv4", label: "IPv4" },
  { key: "cidr", label: t('nodes.columns.cidr') },
  { key: "hostname", label: t('nodes.columns.hostname') },
  { key: "cost", label: t('nodes.columns.cost') },
  { key: "tunnel_proto", label: t('nodes.columns.tunnel_proto') },
  { key: "lat_ms", label: t('nodes.columns.lat_ms') },
  { key: "loss_rate", label: t('nodes.columns.loss_rate') },
  { key: "rx_bytes", label: t('nodes.columns.rx_bytes') }, 
  { key: "tx_bytes", label: t('nodes.columns.tx_bytes') },
  { key: "nat_type", label: t('nodes.columns.nat_type') },
  { key: "version", label: t('nodes.columns.version') },
  { key: "id", label: "id" },
])

// 可见列
const visibleColumns = computed(() => {
  return allColumns.value.filter(col => selectedColumns.value.includes(col.key))
})

// 列可见性映射表，用于移动端卡片快速判断
const visibleColumnsMap = computed(() => {
  const map = {}
  allColumns.value.forEach(col => {
    map[col.key] = selectedColumns.value.includes(col.key)
  })
  return map
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

// 切换移动端列表模式
const toggleMobileList = (val) => {
  useMobileList.value = val
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
        toast.success(`${t('nodes.copySuccess')}: ${node[key]}`)
      } else {
        toast.error(t('nodes.copyFailed'))
      }
    } catch (error) {
      console.error(t('nodes.copyFailed'), error)
      toast.error(t('nodes.copyFailed'))
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
    return t('nodes.costDirect')
  } else if (node.cost === 'Local') {
    return t('nodes.costLocal')
  } else if (node.cost.startsWith('relay')) {
    return node.cost.replace('relay', t('nodes.costRelay'))
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
    return t('nodes.natSymInc')
  } else if (node.nat_type === 'SymmetricEasyDec') {
    return t('nodes.natSymDec')
  } else if (node.nat_type === 'SymUdpFirewall') {
    return t('nodes.natSymUdp')
  } else if (['NoPAT', 'NoPat'].includes(node.nat_type)) {
    return t('nodes.natNoPat')
  } else if (node.nat_type === 'OpenInternet') {
    return t('nodes.natOpen')
  } else if (node.nat_type === 'Unknown') {
    return t('nodes.natUnknown')
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
    console.error(t('nodes.loadConfigFailed'), error)
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
        toast.success(t('nodes.serviceRestartSuccess'))
        resolve()
      }).catch(e => reject(e))
    } catch (error) {
      toast.error(t('nodes.serviceRestartFailed') + ': ' + error.message)
      reject(error)
    }
  })
}

const loadConfigs = async () => {
  try {
    const res = await api.configs.listConfigStatus()
    configList.value = res.data || []
    if (isFirstLoadConfigs.value && configList.value.length > 0 && !selectedConfig.value) {
      isFirstLoadConfigs.value = false
      selectedConfig.value = configList.value.filter(e => e.running || false)?.[0]?.profile
      if (!selectedConfig.value) {
        selectedConfig.value = configList.value[0].profile
      }
    }
    updateServiceStatus()
    return true
  } catch (error) {
    console.error(t('nodes.loadConfigListFailed'), error)
    return false
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
    toast.success(t('nodes.serviceStartSuccess'))
    serviceRunning.value = true
    const cfg = configList.value.find(c => c.profile === selectedConfig.value)
    if (cfg) cfg.running = true
    fetchNodes()
  // } catch (error) {
  //   toast.error('服务启动失败: ' + error.message)
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
    toast.success(t('nodes.serviceStopped'))
    allNodes.value = []
    serviceRunning.value = false
    const cfg = configList.value.find(c => c.profile === selectedConfig.value)
    if (cfg) cfg.running = false
  } catch (error) {
    toast.error(t('nodes.serviceStopFailed') + ': ' + error.message)
  } finally {
    serviceOperating.value = false
    pendingAction.value = ''
  }
}

// 实际项目中这里调用 HTTP API
onMounted(async () => {
  loadSettings()
  const result = await loadConfigs()
  if (!result) {    
    toast.error(t('nodes.loadConfigListFailed'))
    return
  }
  try {
    if (!selectedConfig.value) {
      // showFastSettingTip.value = true
      // 没有选择配置，直接跳配置页面
      toast.success(t('nodes.noConfigGoCreate'))
      setTimeout(() => {
        setActiveMenu?.('config')
      }, 250)
      return;
    }
  } catch (error) {
    console.error(t('nodes.loadConfigStatusFailed'), error)
    return
  }
  try {
    await fetchNodes()
    loadingSkeleton.value = false
    // 启动配置状态轮询
    configStatusPoller.start(loadConfigs)
    nodesPoller.start(fetchNodes)
  } catch (error) {
    console.error(t('nodes.loadNodeListFailed'), error)
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stats-bar {
  padding: 16px 20px;
  margin-bottom: 16px;
  border-radius: 12px;
  background: var(--color-surface-container) !important;
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
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
  white-space: nowrap;
  flex-shrink: 0;
}

.stat-label {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  white-space: nowrap;
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
  color: var(--color-text);
  font-size: 15px;
  font-weight: 700;
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
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.table-wrapper {
  overflow: auto;
  flex: 1;
  min-height: 0;
  position: relative;
}

@media (max-width: 768px) {
  .stats-bar {
    padding: 10px 12px;
  }

  .stats-content {
    gap: 12px;
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

.cell-text.lat-medium {
  color: #f9a825;
}

.cell-text.lat-high {
  color: var(--color-danger);
}

html.dark .cell-text.lat-medium {
  color: #ffd54f;
}

html.dark .cell-text.lat-high {
  color: #ff6b6b;
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

/* ========== 移动端卡片列表样式 ========== */
/* 移动端列表开关 - 仅移动端可见 */
.mobile-only-switch {
  display: none;
  margin-top: 12px;
}

.filter-divider {
  height: 1px;
  background: var(--color-outline-variant);
  margin: 8px 0 12px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: var(--color-text);
}

@media (max-width: 768px) {
  .mobile-only-switch {
    display: block;
  }
  
  .mobile-hidden {
    display: none !important;
  }
  
  .mobile-node-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 2px 0;
  }
  
  .node-card {
    background: var(--color-surface-container-low);
    border-radius: 10px;
    padding: 10px 14px 12px;
    transition: background 0.2s ease;
    border-left: 2px solid var(--color-primary);
    overflow: hidden;
  }
  
  .node-card.node-server {
    border-left-color: var(--color-success);
  }
  
  .node-card:active {
    background: var(--color-surface-container);
  }
  
  .card-left {
    flex: 0 0 auto;
    margin-right: 0;
  }
  
  .card-right {
    margin-left: auto;
  }
  
  .node-card-header {
    margin-bottom: 6px;
  }
  
  .node-ip-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }
  
  .node-ip {
    font-size: 15px;
    font-weight: 600;
    color: var(--color-on-surface);
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .node-card-info {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 6px;
    overflow: hidden;
    margin-top: 6px;
  }
  
  .node-card-info .info-chip,
  .node-card-info .traffic-item {
    flex-shrink: 0;
    font-size: 11px;
    padding: 2px 8px;
  }
  
  .info-chip {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 8px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 500;
    background: var(--color-surface-container-high);
    color: var(--color-on-surface-variant);
    white-space: nowrap;
    flex-shrink: 0;
  }
  
  .info-chip.host-chip {
    background: rgba(255, 152, 0, 0.08);
    color: var(--color-warning);
  }
  
  .info-chip.nat-chip {
    background: rgba(41, 121, 255, 0.08);
    color: var(--color-primary);
  }
  
  .info-chip.cidr-chip {
    background: rgba(76, 175, 80, 0.08);
    color: var(--color-success);
  }
  
  .info-chip.loss-warn {
    background: rgba(255, 82, 82, 0.1);
    color: var(--color-danger);
  }

  .info-chip.lat-medium {
    background: rgba(255, 193, 7, 0.1);
    color: #f9a825;
  }

  .info-chip.lat-high {
    background: rgba(255, 82, 82, 0.1);
    color: var(--color-danger);
  }
  
  html.dark .info-chip {
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.8);
  }
  
  html.dark .info-chip.loss-warn {
    background: rgba(255, 82, 82, 0.18);
    color: #ff6b6b;
  }

  html.dark .info-chip.lat-medium {
    background: rgba(255, 193, 7, 0.18);
    color: #ffd54f;
  }

  html.dark .info-chip.lat-high {
    background: rgba(255, 82, 82, 0.18);
    color: #ff6b6b;
  }
  
  html.dark .info-chip.nat-chip {
    background: rgba(41, 121, 255, 0.18);
    color: #6ea8fe;
  }
  
  html.dark .info-chip.cidr-chip {
    background: rgba(76, 175, 80, 0.18);
    color: #81c784;
  }
  
  html.dark .info-chip.host-chip {
    background: rgba(255, 152, 0, 0.18);
    color: #ffb74d;
  }
  
  html.dark .traffic-item {
    color: rgba(255, 255, 255, 0.7);
  }
  
  .node-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid var(--color-outline-variant);
    overflow: hidden;
  }
  
  .traffic-item {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    font-weight: 500;
    color: var(--color-on-surface-variant);
    white-space: nowrap;
    flex-shrink: 0;
  }
  
  .node-card-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
  }
  
  .version-text {
    font-size: 11px;
    color: var(--color-text-disabled);
    font-weight: 400;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 20px;
    color: var(--color-text-disabled);
    gap: 12px;
  }
  
  .empty-state p {
    margin: 0;
    font-size: 14px;
  }
}

@media (min-width: 769px) {
  .mobile-node-list {
    display: none;
  }
}
</style>