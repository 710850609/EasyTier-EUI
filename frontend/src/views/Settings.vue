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
        <!-- <var-icon name="lock" size="24" color="var(--color-primary)" /> -->
        <svg-icon type="mdi" :path="mdiShieldLock" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">内核</span>
      </div>
      <var-divider />
      <!-- 当前版本信息 -->
      <var-cell>
        <var-loading type="wave" v-if="isFetchingEtCoreVersion" />
        <div v-if="!isFetchingEtCoreVersion">
          <span>EasyTier </span>
          <span>{{ etVersion.version }}</span>
        </div>
      </var-cell>
      <var-cell>
        <template #description>
          <var-select variant="outlined" placeholder="可选内核版本" size="small" v-model="etVersion.selected_version">
            <template #default>
              <var-option v-for="item in etVersionList" :key="item.version" :label="item.version" :value="item.version">
                <var-cell :title="item.version" border>
                  <template #extra>
                    <var-badge 
                      :type="item.prerelease ? 'warning' : 'success'" 
                      position="right-bottom" 
                      :value="item.prerelease ? '预发' : '稳定'">
                    </var-badge>
                  </template>
                </var-cell>
              </var-option>
            </template>
            <template #append-icon>
              <var-icon 
                name="refresh" 
                :class="{ 'is-spinning': isFetchingVersionList }"
                @click.stop="refreshVersionList" 
              />
            </template>
          </var-select>
        </template>
      </var-cell>
      <var-cell>
        <template #description v-if="hasNewVersion">
          <var-chip type="warning" size="small" plain>有新版本</var-chip>
        </template>
        <template #extra>
          <var-button type="primary" size="small" @click="installEtCore(true)" auto-loading style="min-width: 80px;">
            <var-icon name="download" />
            安装           
          </var-button>
        </template>
      </var-cell>
    </var-paper>

    <!-- 网络设置 -->
    <var-paper class="setting-block" :elevation="1">
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
        <var-select v-model="githubMirror" variant="outlined" size="small" :line="true"
          :options="githubMirrors" label-key="label" value-key="value">
        </var-select>
      </var-cell>
      <var-cell>
        <template #extra>          
          <var-button type="primary" size="small" @click="saveGitHubMirror" auto-loading style="min-width: 80px;">
            <var-icon name="check" />
            保存           
          </var-button>
        </template>
      </var-cell>
    </var-paper>

    <!-- 开发者选项 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <!-- <var-icon name="wrench" size="24" color="var(--color-primary)" /> -->
        <svg-icon type="mdi" :path="mdiDevTo" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">开发者选项</span>
      </div>      
      <var-divider />
      <var-cell>
        <template #description>移动端页面调试</template>
        <template #extra>
          <var-switch v-model="vConsoleEnabled" @change="toggleVConsole" />
        </template>
      </var-cell>
    </var-paper>

    <!-- 关于 -->
    <var-paper class="setting-block" :elevation="1">
      <div class="block-header">
        <var-icon name="information" size="24" color="var(--color-info)" />
        <span class="block-title">关于</span>
      </div>      
      <var-divider />
      <var-cell>
        <template #icon>
          <strong>易组网</strong>
        </template>
        <template #description>
            <var-chip type="primary" size="mini">{{ buildVersion }}</var-chip>
        </template>
        <template #extra>
          <!-- <img src="https://img.shields.io/github/v/release/710850609/fpk-easytier-lite?color=blue&logo=github" /> -->
          <a href='https://github.com/710850609/fpk-easytier-lite' target="_blank"><img alt="GitHub stars" src="https://img.shields.io/github/stars/710850609/fpk-easytier-lite?logo=github"></a>
        </template>
      </var-cell>
      <var-cell>
        <div>简化 EasyTier 使用的UI</div>
        <div>降低组网门槛，快速访问异地网络设备</div>
        <div>享受 EasyTier 免费、不限设备数量、支持多类型终端等优势</div>
      </var-cell>
    </var-paper>
  </div>
</template>

<script setup>
import { themeOptions, setThemeMode, themeMode } from '../config/theme.js'
import { VCONSOLE_ENABLED_KEY } from '../config/storage-keys.js'
import toast from '../components/toast.js'
import api from '../utils/api.js'
import { getLatestVersionWithCache } from '../utils/github.js'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiBrightness6, mdiAccessPointNetwork, mdiDevTo, mdiShieldLock } from '@mdi/js'

const vConsoleEnabled = ref(false)
const vConsoleInstance = ref(null)
const isFetchingEtCoreVersion = ref(true)
const isFetchingVersionList = ref(false)
const isFetchingGithubMirrors = ref(true)
const etVersion = ref({ version: '', raw_version: '', latest_version: '', selected_version: '' })
const etVersionList = ref([])
const githubMirror = ref('')
const githubMirrors = ref([])
const buildVersion = ref('')

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

const getEtVersionList = async (useCache = true) => {
  isFetchingVersionList.value = true
  try {
    etVersionList.value = await getLatestVersionWithCache('easyTier/easytier', useCache)
    etVersion.value.latest_version = etVersionList.value[0]?.version || ''
    if (!etVersion.value.selected_version) {
      etVersion.value.selected_version = etVersion.value.latest_version
    }
    if (!useCache) {
      toast.success('内核可选版本已刷新')
    }
  } catch (e) {
    console.error('获取版本列表失败:', e)
  } finally {
    isFetchingVersionList.value = false
  }
}

// 刷新版本列表（强制不使用缓存）
const refreshVersionList = async () => {
  await getEtVersionList(false)
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

const saveGitHubMirror = async () => {
  try {
    await api.settings.saveGithubMirror({ url: githubMirror.value })
    toast.success('GitHub 加速地址已保存')
  } catch (e) {
    console.error('保存 GitHub 加速地址失败:', e)
  }
}

const getGithubMirrors = async () => {
  try {
    isFetchingGithubMirrors.value = true
    const { data } = await api.settings.getGithubMirrors()
    githubMirror.value = data.selected
    githubMirrors.value = data.sources
  } catch (e) {
    console.error('获取 GitHub 加速地址失败:', e)
  } finally {
    isFetchingGithubMirrors.value = false
  }
}

const getBuildVersion = async () => {
  try {
    buildVersion.value = '获取版本号中...'
    const { data } = await api.settings.getBuildVersion()
    buildVersion.value = data
  } catch (e) {
    console.error('获取构建版本号失败:', e)
    buildVersion.value = '获取构建版本号失败'
  }
}

onMounted(() => {
  // 从 localStorage 加载 VConsole 开关状态
  const enabled = localStorage.getItem(VCONSOLE_ENABLED_KEY) === 'true'
  vConsoleEnabled.value = enabled
  // 如果之前开启过，自动加载
  if (enabled) {
    loadVConsole()
  }  
  getEtVersion()
  getEtVersionList()
  getGithubMirrors()
  getBuildVersion()
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
</style>
