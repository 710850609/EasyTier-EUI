<template>
  <div class="settings-page">
    <!-- 外观设置 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiBrightness6" size="24" color="var(--color-primary)"></svg-icon>
        <!-- <var-icon name="palette" size="24" color="var(--color-primary)" /> -->
        <span class="block-title">外观设置</span>
      </div>
      <var-divider />
      <div class="theme-options">
        <div 
          v-for="option in themeOptions" 
          :key="option.value"
          class="theme-option"
          :class="{ active: currentThemeMode === option.value }"
          @click="setThemeMode(option.value)"
        >
          <var-icon :name="option.icon" size="20" />
          <span>{{ option.label }}</span>
        </div>
      </div>
    </var-paper>

    <!-- 内核设置 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiShieldLock" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">内核 EasyTier</span>
      </div>
      <var-divider />
      <div class="setting-row">
        <span class="setting-label">日志级别</span>
        <var-select 
          class="setting-select" 
          placeholder="请选择日志级别" 
          v-model="etLogLevel" 
          variant="outlined"
          size="small"
          :on-change="setEtLogLevel"
          :line="true"
          :options="logLevelOptions"
          label-key="label"
          value-key="value"
        >
        </var-select>
      </div>
      <!-- <var-divider /> -->
      <div class="setting-row">
        <span class="setting-label">当前版本 {{ etVersion.version || '未知' }}</span>
        <var-select 
          class="setting-select" 
          variant="outlined" 
          placeholder="选择版本" 
          size="small" 
          v-model="etVersion.selected_version"
        >
          <template #default>
            <var-option v-for="item in etVersionList" :key="item.version" :label="item.version" :value="item.version">
              <var-cell :title="item.version" border>
                <template #extra>
                  <div style="display: flex; align-items: center;">
                    <var-chip :type="item.download_count > 100000 ? 'success' : (item.download_count > 10000 ? 'primary' : 'danger')"  size="mini" style="writing-mode: horizontal-tb; white-space: nowrap;">
                      <var-icon name="download" size="16" />
                      {{ item.download_count }}
                    </var-chip>
                    <var-badge 
                      :type="item.prerelease ? 'warning' : 'success'" 
                      position="right-bottom" 
                      :value="item.prerelease ? '预发' : '稳定'">
                    </var-badge>
                  </div>
                </template>
              </var-cell>
            </var-option>
          </template>
          <template #append-icon>
            <var-icon 
              name="refresh" 
              :class="{ 'is-spinning': isFetchingVersionList }"
              @click.stop="getEtReleaseInfo(true)" 
            />
          </template>
        </var-select>
      </div>
      <div class="setting-row">
        <div class="setting-actions">
          <var-chip v-if="hasNewVersion" type="warning" size="small" plain>有新版本</var-chip>
          <var-button type="primary" size="small" @click="installEtCore(true)" auto-loading>
            <var-icon name="download" />
            安装
          </var-button>
           <var-button type="primary" size="small" @click="handleShowEtChangeLog()" v-if="etVersion.selected_version != ''">
            <var-icon name="information-outline" />
            更新内容
          </var-button>
        </div>
      </div>
      <!-- <var-divider /> -->
      <div class="setting-row" @click="window.open('https://easytier.cn', '_blank')">
        <span class="setting-label">
          EasyTier文档
        </span>
        <a href="https://easytier.cn" target="_blank" style="text-decoration: none;">
          <var-icon name="share" color="var(--color-primary)" />
        </a>
      </div>
    </var-paper>

    <!-- 网络设置 -->
    <!-- <var-paper class="setting-block" :elevation="1" style="display: none;">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiAccessPointNetwork"  color="var(--color-primary)"></svg-icon>
        <span class="block-title">网络</span>
      </div>      
      <var-divider />
      <var-cell>
        GitHub加速地址
        <var-loading type="wave" v-if="isFetchingGithubMirrors" />
      </var-cell>
      <var-cell>
        <var-select v-model="githubMirror" variant="outlined" size="small" :line="true">
          <var-option v-for="item in githubMirrors" :key="item.url" :value="item.url" :label="item.label">
            <var-cell border style="display: flex;">
              <template #description>
                {{ item.label }} 
                <var-chip type="warning" size="mini" plain v-if="item.desc">{{ item.desc }}</var-chip>
              </template>
              <template #extra>
                <span v-if="item.delay > 0"> {{ item.delay }}s </span>
              </template>
            </var-cell>
          </var-option>
          <template #append-icon>
            <var-icon 
              name="refresh" 
              :class="{ 'is-spinning': isFetchingGithubMirrors }"
              @click.stop="getGithubMirrors(true)" 
            />
          </template>
        </var-select>
      </var-cell>
      <var-cell>
        <template #extra>          
          <var-button type="primary" size="small" @click="getGithubMirrors(true)" auto-loading style="min-width: 80px;">
            <var-icon name="download" />
            更新
          </var-button>
        </template>
      </var-cell>
    </var-paper> -->

    <!-- 版本 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiMapOutline" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">版本</span>
      </div>
      <var-divider />
      
      <div class="setting-row">
        <div class="version-info-block">
          <span class="setting-label">
            稳定版本
            <var-icon name="information-outline" size="18" color="var(--color-primary)" 
            @click="setupShowReleaseInfo(euiRelease)" />
          </span>
          <span class="version-value">{{ euiRelease.version }}</span>
        </div>
        <var-button type="primary" size="small" @click="installEuiVersion('prerelease')" auto-loading
           v-if="buildVersion !== euiRelease.version && euiRelease.version != ''">
          <var-icon name="download" />
          安装
        </var-button>
      </div>
      <div class="setting-row">
        <div class="version-info-block">
          <span class="setting-label">
            最新版本
            <var-icon name="information-outline" size="18" color="var(--color-primary)" 
            @click="setupShowReleaseInfo(euiPreRelease)" />
          </span>          
          <span class="version-value">{{ euiPreRelease.version }}</span>
        </div>
        <var-button type="primary" size="small" @click="installEuiVersion('prerelease')" auto-loading
          v-if="buildVersion !== euiPreRelease.version && euiPreRelease.version != ''">
          <var-icon name="download" />
          安装
        </var-button>
      </div>
      <div class="setting-row">
        <div class="version-info-block">
          <span class="setting-label">当前版本</span>
          <span class="version-value">{{ buildVersion }}</span>
        </div>
        <var-button type="primary" size="small" @click="getReleaseInfo(true)" auto-loading>
          <var-icon name="refresh" size="18" />
          检查更新
        </var-button>
      </div>
    </var-paper>

    <!-- 其他 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiTextBoxOutline" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">其他</span>
      </div>
      <var-divider />
      <div class="setting-row">
        <span class="setting-label">
          清理缓存
        </span>
        <var-button type="primary" size="small" @click="deleteCache" auto-loading >
          <var-icon name="delete" size="18" />
          删除
        </var-button>
      </div>
      <div class="setting-row">
        <span class="setting-label">
          安装路径
        </span>
        <var-chip type="primary" size="small">{{ installPath }}</var-chip>
      </div>
    </var-paper>    

    <!-- 开发者选项 -->
    <var-paper class="setting-block" :elevation="1" v-if="showDevContent">
      <div class="block-header">
        <!-- <var-icon name="wrench" size="24" color="var(--color-primary)" /> -->
        <svg-icon type="mdi" :path="mdiDevTo" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">开发者选项</span>
      </div>      
      <var-divider />
      <div class="setting-row">
        <span class="setting-label">移动端页面调试</span>
        <var-switch v-model="vConsoleEnabled" @change="toggleVConsole" />
      </div>
      <div class="setting-row">
        <span class="setting-label">使用测试社区节点</span>
        <var-switch v-model="testPeerSourceEnabled" :loading="changingPeerSource" @change="togglePeerSource" />
      </div>
      <div class="setting-row">
        <span class="setting-label">查看GitHub加速</span>
        <var-select v-model="githubMirror" variant="outlined" size="small" :line="true" class="setting-select">
          <var-option v-for="item in githubMirrors" :key="item.url" :value="item.url" :label="item.label">
            <var-cell border style="display: flex;">
              <template #description>
                {{ item.label }} 
                <var-chip type="warning" size="mini" plain v-if="item.desc">{{ item.desc }}</var-chip>
              </template>
              <template #extra>
                <span v-if="item.delay > 0"> {{ item.delay }}s </span>
              </template>
            </var-cell>
          </var-option>
          <template #append-icon>
            <var-icon 
              name="refresh" 
              :class="{ 'is-spinning': isFetchingGithubMirrors }"
              @click.stop="getGithubMirrors(true)" 
            />
          </template>
        </var-select>
      </div>
    </var-paper>

    <!-- 关于 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header" 
        @mousedown="startPress"
        @mouseup="cancelPress"
        @mouseleave="cancelPress"
        @touchstart.prevent="startPress"
        @touchend="cancelPress"
        @touchcancel="cancelPress"
        @touchmove="cancelPress">
        <svg-icon type="mdi" :path="mdiInformation" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">关于</span>
      </div>
      <var-divider />
      <!-- 版本信息卡片 -->
      <div class="about-version-card">
        <div class="version-main">
          <span class="version-name">易组网</span>
        </div>
        <div class="version-actions">
          <a href='https://github.com/710850609/EasyTier-EUI' target="_blank">
            <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/710850609/EasyTier-EUI?style=flat&label=%E7%82%B9%20Stars">
          </a>
          <var-chip elevation="1" @click="showRewardCdoe = true" type="info" size="small">打赏</var-chip>
        </div>
      </div>
      
      <!-- 简介 -->
      <div class="about-section">
        <div class="about-content">
          <p>简化 EasyTier 使用的 UI 界面</p>
          <p>降低组网门槛，快速访问异地网络设备</p>
          <p>享受 EasyTier 免费、不限设备数量、支持多类型终端等优势</p>
          <img alt="下载量" src="https://img.shields.io/github/downloads/710850609/EasyTier-EUI/total?color=blue&label=下载量" />
        </div>
      </div>
    </var-paper>

    <var-button block type="danger" v-if="platform === 'linux'" @click="shutdown">
      <template #default>
        <var-icon name="power" size="20" /> 关闭 易组网
      </template>
    </var-button>
  <div>      
  </div>

  <var-popup :default-style="false" v-model:show="showRewardCdoe">
    <var-result description="点Stars或是打赏 感谢您的肯定">
      <template #image>
        <img src="../../public/images/reward_code.jpg" style="width: 50%; height: 50%; border-radius: 50%; object-fit: cover;" />
      </template>
      <template #footer>
        <var-button type="info" @click="showRewardCdoe = false">关闭</var-button>
      </template>
    </var-result>
  </var-popup>

  <!-- 弹窗更新说明 -->
  <var-popup :default-style="false" v-model:show="showEuiReleaseInfo">
    <var-result type="info">
      <template #image>
         <MarkdownRenderer :content="`# 更新内容 \n ### ${ euiReleaseInfo.version}\n \n` + euiReleaseInfo.changelog" class="markdown-renderer" />
      </template>
      <template #footer>
        <var-button type="info" @click="showEuiReleaseInfo = false" style="margin: 10px;">关闭</var-button>
      </template>
    </var-result>
  </var-popup>
  
  <var-popup :default-style="false" v-model:show="showEtChangeLog">
    <var-result type="info">
      <template #image>
        <MarkdownRenderer :content="etChangeLog" class="markdown-renderer" />
      </template>
      <template #footer>
        <var-button type="info" @click="showEtChangeLog = false">关闭</var-button>
      </template>
    </var-result>
  </var-popup>
  </div>
</template>

<script setup>
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { themeOptions, setThemeMode, themeMode } from '../config/theme.js'
import { VCONSOLE_ENABLED_KEY } from '../config/storage-keys.js'
import toast from '../components/toast.js'
import api from '../utils/api.js'
// import { getLatestVersionWithCache } from '../utils/github.js'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiBrightness6, mdiAccessPointNetwork, mdiDevTo, mdiShieldLock, mdiMapOutline, mdiInformation, mdiTextBoxOutline } from '@mdi/js'

const dev_toggle_timer = ref(null);
const showDevContent = ref(false)
const vConsoleEnabled = ref(false)
const changingPeerSource = ref(false)
const testPeerSourceEnabled = ref(false)
const vConsoleInstance = ref(null)
const isFetchingEtCoreVersion = ref(true)
const isFetchingVersionList = ref(false)
const isFetchingGithubMirrors = ref(true)
const etVersion = ref({ version: '', raw_version: '', latest_version: '', selected_version: '' })
const etVersionList = ref([])
const githubMirror = ref('')
const githubMirrors = ref([])
const buildVersion = ref('')
const installPath = ref('')
const showRewardCdoe = ref(false)
const platform = ref('')
const etLogLevel = ref('info')
const euiRelease = ref({})
const euiPreRelease = ref({})
const showEuiReleaseInfo = ref(false)
const showEtChangeLog = ref(false)
const etChangeLog = ref('')
const euiReleaseInfo = ref({})
const logLevelOptions = ref([
  { value: 'off', label: '禁用' }, // cli 是 disabled
  { value: 'error', label: '错误' },
  { value: 'warn', label: '警告' },  // cli 是 warning
  { value: 'info', label: '信息' },
  { value: 'debug', label: '调试' },
  { value: 'trace', label: '追踪' },
])

const startPress = (e) => {
  dev_toggle_timer.value = setTimeout(() => { 
    getGithubMirrors()
    loadPeerSource()
    showDevContent.value = !showDevContent.value
    toast.success(`开发者选项已${showDevContent.value ? '开启' : '关闭'}`)
  }, 3000);
};

const cancelPress = () => {
  clearTimeout(dev_toggle_timer.value);
};

const hasNewVersion = computed(() => etVersion.value.version && etVersion.value.latest_version && etVersion.value.version !== etVersion.value.latest_version)
// 计算当前主题模式（从 theme.js 获取）
const currentThemeMode = computed(() => themeMode.value)

// 加载 VConsole（动态导入）
const loadVConsole = async () => {
  try {
    const VConsole = await import('vconsole')
    vConsoleInstance.value = new VConsole.default()
    return true
  } catch (error) {
    console.error('加载 VConsole 失败:', error)
    return false
  }
}

// 切换 VConsole
const toggleVConsole = async (val) => {
  // 保存开关状态
  localStorage.setItem(VCONSOLE_ENABLED_KEY, val ? 'true' : 'false')

  if (val) {
    const loaded = await loadVConsole()
    if (loaded) {
      toast.success('VConsole 已开启')
    } else {
      toast.error('加载 VConsole 失败')
      vConsoleEnabled.value = false
      localStorage.setItem(VCONSOLE_ENABLED_KEY, 'false')
    }
  } else {
    if (vConsoleInstance.value) {
      vConsoleInstance.value.destroy()
      vConsoleInstance.value = null
    }
    toast.success('VConsole 已关闭')
  }
}

const togglePeerSource = async (val) => {
  changingPeerSource.value = true
  const data = { source: val ? 'test' : 'stable' }
  await api.peers.setPeerSource(data).then(() => {
    testPeerSourceEnabled.value = val
  }).finally(() => {
    changingPeerSource.value = false
  })
}

const loadPeerSource = async () => {
  try {
    const { data } = await api.peers.getPeerSource()
    testPeerSourceEnabled.value = data.source === 'test'
  } catch (e) {
    console.error('获取节点来源失败:', e)
    testPeerSourceEnabled.value = false
  }
}

// 获取当前版本
const getEtVersion = async () => {
  try {
    isFetchingEtCoreVersion.value = true
    const { data } = await api.etCore.getVersion()
    etVersion.value = { ...etVersion.value, ...data }
  } catch (e) {
    console.error('获取内核版本失败:', e)
    etVersion.value.raw_version = '获取内核版本失败:' + e.message
  } finally {
    isFetchingEtCoreVersion.value = false
  }
}

const getEtReleaseInfo = async (refresh = false, showTip = true) => {
  isFetchingVersionList.value = true
  try {
    const resp = await api.etCore.getVersionList({'refresh': refresh})
    etVersionList.value = resp.data.versions || []
    // etVersionList.value = await getLatestVersionWithCache('easyTier/easytier', useCache)
    etVersion.value.latest_version = etVersionList.value[0]?.version || ''
    if (!etVersion.value.selected_version) {
      etVersion.value.selected_version = etVersion.value.latest_version
    }
    if (refresh && showTip) {      
      toast.success('内核可选版本已刷新')
    }
    if (new Date().getTime() - resp.data.create_time > 1000 * 60 * 60 * 24) {
      getEtReleaseInfo(true, false)
    }
  } catch (e) {
    console.error('获取版本列表失败:', e)
  } finally {
    isFetchingVersionList.value = false
  }
}

const installEtCore = async () => {
  return new Promise((resolve, reject) => {
    api.etCore.install({ version: etVersion.value.selected_version })
    .then((res) => {
      toast.success(res.data || `安装内核版本 ${etVersion.value.selected_version} 成功`)
      getEtVersion()
      resolve(res)
    })
    .catch((err) => {
      // toast.error(err.message || `安装内核版本 ${etVersion.value.selected_version} 失败`)
      reject(err)
    })
  })
}

const getGithubMirrors = async (refresh = false) => {
  try {
    isFetchingGithubMirrors.value = true
    const { data } = await api.settings.getGithubMirrors({'refresh': refresh})
    // githubMirror.value = data.selected
    githubMirrors.value = data
    if (refresh) {
      toast.success('已获取最新地址')
    }
  } catch (e) {
    console.error('获取 GitHub 加速地址失败:', e)
  } finally {
    isFetchingGithubMirrors.value = false
  }
}

const getEuiInfo = async () => {
  try {
    buildVersion.value = '获取版本号中...'
    const { data } = await api.settings.getEuiInfo()
    buildVersion.value = data.build_version
    installPath.value = data.install_path
    platform.value = data.platform
  } catch (e) {
    console.error('获取版本号失败:', e)
    buildVersion.value = '获取版本号失败'
  }
}

const installEuiVersion = (versionType) => {
  return new Promise((resolve, reject) => {
    api.etEui.update({ ver_tag: versionType })
    .then((res) => {
      toast.success(res.data || `更新成功`)
      setTimeout(() => window.location.reload(), 1500)
    })
    .finally(() => {
      resolve()
    })
  })
}

const shutdown = async () => {
  try {
    await api.settings.shutdown()
    toast.success('易组网正在关闭...')
    setTimeout(() => {
      window.location.reload()
    }, 1000)
  } catch (e) {
    console.error('关闭易组网失败:', e)
    toast.error('关闭易组网失败')
  }
}

const getEtLogLevel = async () => {
  const { data } = await api.etCore.getEtLogLevel()
  etLogLevel.value = data
}

const setEtLogLevel = async (level) => {
  const loadingToast = toast.loading('正在修改内核日志级别，请稍后...')
  try {
    await api.etCore.setEtLogLevel({ level: level })
    const selectedLabel = logLevelOptions.value.filter(item => item.value === level)[0].label
    toast.success(`内核日志级别已设置【${selectedLabel}】`)
  } finally {
    loadingToast.clear()
  }
}

const getReleaseInfo = (refresh=false) => {
  return new Promise((resolve, reject) => {
    api.etEui.getReleaseInfo({'refresh': refresh}).then((data) => {
      euiRelease.value = data.data.latest_release
      euiPreRelease.value = data.data.latest_prerelease
      if (refresh) {
        toast.success('易组网在线版本信息已更新')
      }
    }).finally((error) => {
      resolve()
    })
  })
}

const setupShowReleaseInfo = (info) => {
  euiReleaseInfo.value = info
  showEuiReleaseInfo.value = true
}

const handleShowEtChangeLog = () => {
  const selectedVersion = etVersion.value.selected_version
  etChangeLog.value = etVersionList.value.find(item => item.version === selectedVersion)?.changelog || ''
  showEtChangeLog.value = true
}

const deleteCache = async () => {
  return new Promise((resolve, reject) => {
    api.settings.deleteCache().then(data => {
      toast.success(data.data || '缓存已删除')
    }).finally(() => {
      resolve()
    })
  })
}

onMounted(() => {
  // 从 localStorage 加载 VConsole 开关状态
  const enabled = localStorage.getItem(VCONSOLE_ENABLED_KEY) === 'true'
  vConsoleEnabled.value = enabled
  // 如果之前开启过，自动加载
  if (enabled) {
    loadVConsole()
    loadPeerSource()
    getGithubMirrors()
    showDevContent.value = true
  }  
  getEtVersion()
  getEtReleaseInfo(false)
  getEuiInfo()
  getEtLogLevel()
  getReleaseInfo(false)
})
</script>

<style scoped>
.settings-page {
  padding: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.setting-block {
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 16px;
  background: var(--color-surface-container) !important;
}

.block-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.block-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.mirror-link, .source-link {
  color: var(--color-primary);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.test-link {
  margin-top: 8px;
}

/* 强制 badge 横向显示 */
:deep(.var-badge__content) {
  white-space: nowrap !important;
  min-width: fit-content !important;
}

/* 刷新图标旋转动画 */
.is-spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

:deep(.var-cell__description) {
  margin-top: 4px;
}

/* 内核版本管理样式 */
.kernel-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 16px 16px;
}

.version-select {
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 主题选项样式 */
.theme-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  border-radius: 12px;
  border: 2px solid var(--color-outline);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.theme-option:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-container);
}

.theme-option.active {
  border-color: var(--color-primary);
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.theme-option span {
  font-size: 14px;
  font-weight: 500;
}

/* 设置行样式 */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  gap: 6px;
  border-bottom: 1px solid var(--color-border);
}

.setting-row:last-child {
  border-bottom: none;
}

.version-info-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.version-value {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-secondary);
}

.setting-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  flex: 1;
}

.setting-select {
  flex: 2;
  min-width: 160px;
}

.setting-value {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.setting-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-left: auto;
}

/* 关于部分样式 */
.about-version-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  margin-bottom: 16px;
}

.version-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-on-primary-container);
}

.version-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.about-section {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-outline);
}

.about-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.about-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.about-content {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.6;
}

.about-content p {
  margin: 4px 0;
}

.path-code {
  display: inline-block;
  padding: 8px 12px;
  background: var(--color-surface);
  border-radius: 8px;
  font-family: monospace;
  font-size: 13px;
  color: var(--color-text-secondary);
  word-break: break-all;
  max-width: 100%;
}

.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.version-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.markdown-renderer {
  padding: 16px;
  max-height: 560px;
  overflow-y: auto;
}

/* 移动端响应式 */
@media (max-width: 480px) {
  .about-version-card {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .version-main {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .version-name {
    font-size: 18px;
  }
  
  .version-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .stats-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .path-code {
    font-size: 12px;
    padding: 6px 10px;
  }

}
</style>
