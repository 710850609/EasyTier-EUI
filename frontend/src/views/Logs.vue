<template>
  <div class="logs-page">
    <var-paper class="toolbar" :elevation="1">
      <div class="toolbar-content">
        <var-button 
          :type="isPaused ? 'primary' : 'default'" 
          @click="togglePause"
        >
          <template #icon>
            <var-icon :name="isPaused ? 'play' : 'pause'" />
          </template>
          {{ isPaused ? $t('logs.continue') : $t('logs.pause') }}
        </var-button>
        
        <var-button text @click="clearLogs">
          <template #icon><var-icon name="trash" /></template>
          {{ $t('logs.clear') }}
        </var-button>
        
        <var-select v-model="logLevel" size="small" style="width: 120px;">
          <var-option :label="$t('logs.all')" value="all" />
          <var-option :label="$t('logs.info')" value="info" />
          <var-option :label="$t('logs.warning')" value="warn" />
          <var-option :label="$t('logs.error')" value="error" />
        </var-select>
        
        <span class="log-stats">{{ $t('logs.total', { count: filteredLogs.length }) }}</span>
      </div>
    </var-paper>

    <var-paper class="log-container" :elevation="1">
      <div class="log-list" ref="logList">
        <div 
          v-for="(log, index) in filteredLogs" 
          :key="index"
          class="log-item"
          :class="log.level"
        >
          <span class="log-time">{{ log.time }}</span>
          <var-chip 
            :type="getLevelType(log.level)" 
            size="mini" 
            class="log-level"
          >
            {{ log.level.toUpperCase() }}
          </var-chip>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
const logs = ref([])
const isPaused = ref(false)
const logLevel = ref('all')
const logList = ref(null)
let ws = null
let interval = null

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(l => l.level === logLevel.value)
})

const getLevelType = (level) => {
  const map = { info: 'primary', warn: 'warning', error: 'danger', debug: 'default' }
  return map[level] || 'default'
}

const togglePause = () => {
  isPaused.value = !isPaused.value
}

const clearLogs = () => {
  logs.value = []
}

const scrollToBottom = () => {
  nextTick(() => {
    if (logList.value) {
      logList.value.scrollTop = logList.value.scrollHeight
    }
  })
}

// 模拟实时日志（实际使用 WebSocket）
const startLogStream = () => {
  interval = setInterval(() => {
    if (isPaused.value) return
    
    const levels = ['info', 'warn', 'error', 'debug']
    const level = levels[Math.floor(Math.random() * levels.length)]
    
    logs.value.push({
      time: new Date().toLocaleTimeString(),
      level,
      message: `[${level.toUpperCase()}] 节点连接状态更新: peer_abc123 延迟 ${Math.floor(Math.random() * 100)}ms`
    })
    
    if (logs.value.length > 500) logs.value.shift()
    scrollToBottom()
  }, 1000)
}

onMounted(() => {
  // 实际项目中使用 WebSocket
  // ws = new WebSocket('ws://localhost:8080/logs')
  // ws.onmessage = (e) => { logs.value.push(JSON.parse(e.data)) }
  startLogStream()
})

onUnmounted(() => {
  if (interval) {
    clearInterval(interval)
    interval = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style scoped>
.logs-page {
  padding: 16px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.toolbar {
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.toolbar-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.log-stats {
  margin-left: auto;
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.log-container {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  background: var(--color-surface-container-lowest);
}

.log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-outline-variant);
}

.log-time {
  color: var(--color-on-surface-variant);
  white-space: nowrap;
  font-size: 12px;
}

.log-level {
  flex-shrink: 0;
}

.log-message {
  color: var(--color-on-surface);
  word-break: break-all;
}

.log-item.error .log-message {
  color: var(--color-error);
}

.log-item.warn .log-message {
  color: var(--color-warning);
}
</style>