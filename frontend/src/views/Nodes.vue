<template>
  <div class="nodes-page">
    <!-- 统计标题栏 -->
    <var-paper class="stats-bar" :elevation="1">
      <div class="stats-content">
        <!-- 选择配置 -->
        <div class="config-section">
          <var-select
            variant="outlined"
            class="config-select"
            size="small"
            v-model="selectedConfig"
            @change="handleConfigChange"
            :placeholder="$t('nodes.selectConfig')"
          >
            <template #selected>
              <div class="config-option">
                <svg-icon size="16" type="mdi" :path="mdiCircle" :color="serviceRunning ? 'var(--color-success)' : 'var(--color-text-disabled)'"></svg-icon>
                <span>{{ selectedConfig?.replace('.toml', '') }}</span>
              </div>
            </template>
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
              size="small"
              auto-loading            
              @click="stopService"
              v-if="serviceRunning && !serviceOperating"
            >
              {{ $t('nodes.stop') }}
            </var-button>
          </div>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ $t('nodes.normalNodes') }}</span>
          <span class="stat-value">{{ normalNodes.length }}</span>
        </div>
        <div class="divider"></div>
        <div class="stat-item">
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
        <!-- 骨架屏 - PC 表格骨架 -->
        <div v-if="loadingSkeleton && !useMobileList" class="skeleton-container skeleton-pc">
          <div class="sk-pc-header">
            <div class="sk-pill sk-pill-hdr" v-for="n in visibleColumns.length" :key="'h'+n">
              <div class="sk-breathe"></div>
            </div>
          </div>
          <div class="sk-pc-body">
            <div v-for="row in 6" :key="row" class="sk-pc-row" :style="{ animationDelay: `${row * 0.05}s` }">
              <div class="sk-pc-cell" v-for="n in visibleColumns.length" :key="n">
                <div class="sk-pill" :style="{ width: skeletonWidths[(n - 1) % skeletonWidths.length] }">
                  <div class="sk-breathe"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 骨架屏 - 移动端卡片骨架 -->
        <div v-else-if="loadingSkeleton && useMobileList" class="skeleton-container skeleton-mobile">
          <div v-for="card in 4" :key="card" class="sk-card" :style="{ animationDelay: `${card * 0.08}s` }">
            <div class="sk-card-top">
              <div class="sk-icon"><div class="sk-breathe"></div></div>
              <div class="sk-card-title"><div class="sk-breathe"></div></div>
            </div>
            <div class="sk-card-chips">
              <div class="sk-chip sk-chip-sm"><div class="sk-breathe"></div></div>
              <div class="sk-chip sk-chip-md"><div class="sk-breathe"></div></div>
              <div class="sk-chip sk-chip-lg"><div class="sk-breathe"></div></div>
            </div>
            <div class="sk-card-meta">
              <div class="sk-chip sk-chip-sm"><div class="sk-breathe"></div></div>
              <div class="sk-chip sk-chip-md"><div class="sk-breathe"></div></div>
            </div>
          </div>
        </div>
        
        <!-- 实际表格 - PC模式 -->
        <table v-else-if="!useMobileList" class="data-table" :class="{ 'mobile-hidden': useMobileList }">
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
            <tr v-if="topSpacerHeight > 0" aria-hidden="true">
              <td :colspan="visibleColumns.length" :style="{ height: topSpacerHeight + 'px', padding: 0, border: 'none' }"></td>
            </tr>
            <tr v-for="node in virtualFilteredNodes" :key="node.id">
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
                  <span class="cell-text" :class="{ 'lat-medium': node.lat_ms >= 60 && node.lat_ms <= 150, 'lat-high': node.lat_ms > 150 }" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}</span>
                </template>
                <template v-else-if="col.key === 'loss_rate'">                  
                  <span class="cell-text" :class="{ 'loss-medium': parseFloat(node.loss_rate) > 0 && parseFloat(node.loss_rate) <= 1, 'loss-high': parseFloat(node.loss_rate) > 1 }">
                    {{ parseNode(node, 'loss_rate') }}
                  </span>
                </template>
                <template v-else>
                  <var-tooltip v-if="['hostname', 'tunnel_proto'].includes(col.key)" :content="parseNode(node, col.key)">
                    <span class="cell-text" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}</span>
                  </var-tooltip>
                  <span v-else class="cell-text" @click="handleClickCell(node, col.key)">{{ parseNode(node, col.key) }}</span>
                </template>
              </td>
            </tr>
            <tr v-if="bottomSpacerHeight > 0" aria-hidden="true">
              <td :colspan="visibleColumns.length" :style="{ height: bottomSpacerHeight + 'px', padding: 0, border: 'none' }"></td>
            </tr>
          </tbody>
        </table>

        <!-- 移动端卡片列表 -->
        <div v-else class="mobile-node-list">
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
                <span class="node-ip" @click="handleClickCell(node, 'ipv4')">{{ node.ipv4 || '' }}</span>
                <span v-if="visibleColumnsMap.hostname && node.hostname" class="info-chip host-chip">
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
              <span v-if="visibleColumnsMap.lat_ms && node.lat_ms !== undefined && node.lat_ms !== '-'" class="info-chip metric-chip" :class="{ 'lat-medium': node.lat_ms >= 60 && node.lat_ms <= 150, 'lat-high': node.lat_ms > 150 }">
                {{ parseNode(node, 'lat_ms') }}
              </span>
              <span v-if="visibleColumnsMap.loss_rate && node.loss_rate !== undefined && node.loss_rate !== '-'" class="info-chip metric-chip" :class="{ 'loss-medium': parseFloat(node.loss_rate) > 0 && parseFloat(node.loss_rate) <= 1, 'loss-high': parseFloat(node.loss_rate) > 1 }">
                {{ $t('nodes.packetLoss') }} {{ parseNode(node, 'loss_rate') }}
              </span>
              <span v-if="visibleColumnsMap.tunnel_proto && node.tunnel_proto && node.tunnel_proto !== '-'" class="info-chip">
                {{ node.tunnel_proto }}
              </span>
            </div>
            <div v-if="visibleColumnsMap.nat_type || visibleColumnsMap.rx_bytes || visibleColumnsMap.tx_bytes" class="node-card-meta">
              <span v-if="visibleColumnsMap.nat_type && node.nat_type" class="info-chip nat-chip">
                {{ parseNode(node, 'nat_type') }}
              </span>
              <span v-if="visibleColumnsMap.rx_bytes && node.rx_bytes !== undefined && node.rx_bytes !== '-'" class="traffic-item download">
                <svg-icon size="14" type="mdi" :path="mdilArrowDown" color="var(--color-primary)"></svg-icon>
                {{ parseNode(node, 'rx_bytes') }}
              </span>
              <span v-if="visibleColumnsMap.tx_bytes && node.tx_bytes !== undefined && node.tx_bytes !== '-'" class="traffic-item upload">
                <svg-icon size="14" type="mdi" :path="mdilArrowUp" color="var(--color-success)"></svg-icon>
                {{ parseNode(node, 'tx_bytes') }}
              </span>
            </div>
            <div class="node-card-footer">
              <span v-if="visibleColumnsMap.version && node.version" class="version-text">v{{ node.version }}</span>
              <span v-if="visibleColumnsMap.cidr && node.cidr" class="info-chip cidr-chip">
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
// 移动端列表模式（默认根据屏幕宽度判断）
const useMobileList = ref(window.innerWidth <= 768)
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
  case 'lat_ms':
    return node.lat_ms === '-' ? '' : node.lat_ms + ' ms'
  default:
    return node[key] === '-' ? '' : node[key]
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

// 骨架屏宽度 - 固定值，避免 Math.random() 导致重复渲染
const skeletonWidths = ['60%', '80%', '45%', '72%', '55%', '90%', '68%', '48%', '75%', '52%', '85%', '40%']

// ========== 虚拟滚动（PC 表格模式） ==========
const VIRTUAL_ROW_HEIGHT = 42
const VIRTUAL_BUFFER = 6
const VIRTUAL_THRESHOLD = 50

const visibleStart = ref(0)
const visibleCount = ref(20)

const virtualFilteredNodes = computed(() => {
  const nodes = filteredNodes.value
  if (nodes.length <= VIRTUAL_THRESHOLD || useMobileList.value) return nodes
  const start = Math.max(0, visibleStart.value - VIRTUAL_BUFFER)
  const end = Math.min(nodes.length, visibleStart.value + visibleCount.value + VIRTUAL_BUFFER)
  return nodes.slice(start, end)
})

const virtualStartIndex = computed(() => {
  const nodes = filteredNodes.value
  if (nodes.length <= VIRTUAL_THRESHOLD || useMobileList.value) return 0
  return Math.max(0, visibleStart.value - VIRTUAL_BUFFER)
})

const topSpacerHeight = computed(() => {
  return virtualStartIndex.value * VIRTUAL_ROW_HEIGHT
})

const bottomSpacerHeight = computed(() => {
  const nodes = filteredNodes.value
  if (nodes.length <= VIRTUAL_THRESHOLD || useMobileList.value) return 0
  const renderedEnd = virtualStartIndex.value + virtualFilteredNodes.value.length
  return Math.max(0, (nodes.length - renderedEnd) * VIRTUAL_ROW_HEIGHT)
})

const handleTableScroll = () => {
  if (!tableWrapper.value || useMobileList.value) return
  const scrollTop = tableWrapper.value.scrollTop
  visibleStart.value = Math.floor(scrollTop / VIRTUAL_ROW_HEIGHT)
  visibleCount.value = Math.ceil(tableWrapper.value.clientHeight / VIRTUAL_ROW_HEIGHT) + 2
}

let tableScrollHandler = null
const tableWrapper = ref(null)

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
  // 重置虚拟滚动位置
  visibleStart.value = 0
  if (tableWrapper.value) {
    tableWrapper.value.scrollTop = 0
  }
  nodesPoller.stop()
  cancelAllRequests()
  if (serviceRunning.value) {
    loadingSkeleton.value = true
    dataLoading.value = false
    isUnmounted.value = false
    const skStart = Date.now()
    await fetchNodes()
    const minSkTime = 400
    const elapsed = Date.now() - skStart
    if (elapsed < minSkTime) {
      await new Promise(r => setTimeout(r, minSkTime - elapsed))
    }
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
  // 绑定滚动事件用于虚拟滚动
  if (tableWrapper.value) {
    tableScrollHandler = handleTableScroll
    tableWrapper.value.addEventListener('scroll', handleTableScroll, { passive: true })
    visibleCount.value = Math.ceil(tableWrapper.value.clientHeight / VIRTUAL_ROW_HEIGHT) + 2
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
    const skStart = Date.now()
    await fetchNodes()
    const minSkTime = 400
    const elapsed = Date.now() - skStart
    if (elapsed < minSkTime) {
      await new Promise(r => setTimeout(r, minSkTime - elapsed))
    }
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
  if (tableWrapper.value && tableScrollHandler) {
    tableWrapper.value.removeEventListener('scroll', tableScrollHandler)
  }
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
  flex: 0 1 auto;
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

  .stat-item {
    gap: 2px;
  }

  .config-section {
    width: 100%;
    justify-content: space-between;
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

.cell-text.loss-medium {
  color: var(--color-warning);
}

.cell-text.loss-high {
  color: var(--color-danger);
}

html.dark .cell-text.lat-medium {
  color: #ffd54f;
}

html.dark .cell-text.lat-high {
  color: #ff6b6b;
}

html.dark .cell-text.loss-medium {
  color: var(--color-warning);
}

html.dark .cell-text.loss-high {
  color: var(--color-danger);
}

tr:hover td {
  background: var(--color-surface-container-high);
}

/* 虚拟滚动占位行不显示 hover 效果 */
tr[aria-hidden="true"] td {
  background: transparent !important;
  border-bottom: none !important;
}

tr[aria-hidden="true"]:hover td {
  background: transparent !important;
}

/* ========== 骨架屏 ========== */
.skeleton-container {
  overflow: hidden;
  min-height: 200px;
}

.skeleton-pc {
  padding: 12px 0;
}

/* PC 头部 */
.sk-pc-header {
  display: flex;
  gap: 10px;
  padding: 10px 16px 12px;
  border-bottom: 1px solid var(--color-outline-variant);
  margin-bottom: 4px;
}

.sk-pill-hdr {
  height: 14px;
  width: 100%;
  max-width: 100px;
  border-radius: 7px;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.06);
  opacity: 0.7;
}

html.dark .sk-pill-hdr {
  background: rgba(255, 255, 255, 0.06);
  opacity: 0.5;
}

/* PC 行 */
.sk-pc-body {
  display: flex;
  flex-direction: column;
}

.sk-pc-row {
  display: flex;
  gap: 10px;
  padding: 9px 16px;
  animation: sk-slideUp 0.45s ease both;
}

.sk-pc-cell {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
}

/* 通用圆角条 */
.sk-pill {
  height: 12px;
  border-radius: 7px;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.05);
  overflow: hidden;
  position: relative;
  max-width: 100%;
}

html.dark .sk-pill {
  background: rgba(255, 255, 255, 0.05);
}

/* 呼吸微光 */
.sk-breathe {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 132, 255, 0.12) 20%,
    rgba(127, 90, 240, 0.18) 40%,
    rgba(99, 132, 255, 0.12) 60%,
    transparent 80%
  );
  animation: sk-breathe 2.4s ease-in-out infinite;
  will-change: opacity;
}

html.dark .sk-breathe {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 132, 255, 0.2) 20%,
    rgba(167, 139, 250, 0.28) 40%,
    rgba(99, 132, 255, 0.2) 60%,
    transparent 80%
  );
}

@keyframes sk-breathe {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

@keyframes sk-slideUp {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ========== 移动端卡片骨架 ========== */
.skeleton-mobile {
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sk-card {
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.02);
  border-radius: 14px;
  padding: 14px 16px;
  border-left: 4px solid rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.06);
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: sk-slideUp 0.45s ease both;
  overflow: hidden;
}

html.dark .sk-card {
  background: rgba(255, 255, 255, 0.02);
  border-left-color: rgba(255, 255, 255, 0.06);
}

.sk-card-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sk-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.06);
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
}

html.dark .sk-icon {
  background: rgba(255, 255, 255, 0.06);
}

.sk-card-title {
  flex: 1;
  height: 15px;
  border-radius: 8px;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.05);
  overflow: hidden;
  position: relative;
  max-width: 55%;
}

html.dark .sk-card-title {
  background: rgba(255, 255, 255, 0.05);
}

.sk-card-chips,
.sk-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sk-chip {
  height: 22px;
  border-radius: 6px;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.05);
  overflow: hidden;
  position: relative;
}

html.dark .sk-chip {
  background: rgba(255, 255, 255, 0.05);
}

.sk-chip-sm { width: 52px; }
.sk-chip-md { width: 76px; }
.sk-chip-lg { width: 100px; }

@media (max-width: 768px) {
  .skeleton-pc {
    display: none !important;
  }
}

@media (min-width: 769px) {
  .skeleton-mobile {
    display: none !important;
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
}

/* ========== 移动端卡片列表样式（全尺寸可用） ========== */
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
  transition: background 0.2s ease, border-color 0.2s ease;
  border-left: 3px solid var(--color-primary);
  overflow: hidden;
}

.node-card.node-server {
  border-left-color: var(--color-success);
}

.node-card:active {
  background: var(--color-surface-container);
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
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
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
  background: rgba(92, 107, 192, 0.08);
  color: #5c6bc0;
  white-space: nowrap;
  flex-shrink: 0;
}

.info-chip.host-chip {
  background: rgba(0, 150, 136, 0.08);
  color: #00897b;
}

.info-chip.nat-chip {
  background: rgba(41, 121, 255, 0.08);
  color: var(--color-primary);
}

.info-chip.cidr-chip {
  background: rgba(76, 175, 80, 0.08);
  color: var(--color-success);
}

.info-chip.loss-medium {
  background: rgba(var(--color-warning-rgb, 234, 88, 12), 0.12);
  color: var(--color-warning);
  font-weight: 600;
}

.info-chip.loss-high {
  background: rgba(var(--color-danger-rgb, 239, 68, 68), 0.12);
  color: var(--color-danger);
  font-weight: 600;
}

.info-chip.lat-medium {
  background: rgba(255, 167, 38, 0.12);
  color: #f57c00;
  font-weight: 600;
}

.info-chip.lat-high {
  background: rgba(239, 83, 80, 0.12);
  color: #d32f2f;
  font-weight: 600;
}

.info-chip.metric-chip {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
}

html.dark .info-chip {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
}

html.dark .info-chip.loss-medium {
  background: rgba(var(--color-warning-rgb, 251, 191, 36), 0.25);
  color: var(--color-warning);
  font-weight: 600;
}

html.dark .info-chip.loss-high {
  background: rgba(var(--color-danger-rgb, 248, 113, 113), 0.25);
  color: var(--color-danger);
  font-weight: 600;
}

html.dark .info-chip.lat-medium {
  background: rgba(255, 193, 7, 0.25);
  color: #ffd54f;
  font-weight: 600;
}

html.dark .info-chip.lat-high {
  background: rgba(255, 82, 82, 0.25);
  color: #ff6b6b;
  font-weight: 600;
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
  background: rgba(0, 150, 136, 0.22);
  color: #4db6ac;
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
</style>