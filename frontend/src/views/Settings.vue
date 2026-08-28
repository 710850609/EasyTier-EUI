<template>
  <div class="settings-page">
    <!-- 外观设置 -->
    <var-paper class="setting-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiBrightness6" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.appearance.title') }}</span>
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
          <span>{{ $t(option.label) }}</span>
        </div>
      </div>
      <var-divider class="divider" />
      <div class="setting-row">
        <span class="setting-label">{{ $t('settings.language.label') }}</span>
        <var-select 
          class="setting-select" 
          v-model="currentLanguage"
          variant="outlined"
          size="small"
          :on-change="changeLanguage"
          :line="true"
          :options="languageOptions"
          label-key="label"
          value-key="value"
        >
        </var-select>
      </div>
      <var-divider class="divider" />
      <div class="setting-row">
        <span class="setting-label">{{ $t('settings.appearance.glassEffect') }}</span>
        <var-switch variant size="20" v-model="glassEffectEnabled" @change="toggleGlassEffect" />
      </div>
    </var-paper>

    <!-- 版本 -->
    <var-paper class="setting-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiMapOutline" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.version') }}</span>
      </div>
      <var-divider />
      
      <div class="setting-row">
        <div class="version-info-block">
          <span class="setting-label">{{ $t('settings.currentVersion') }}</span>
          <span class="version-value">{{ buildVersion }}</span>
        </div>
        <var-button type="primary" size="small" @click="getEuiReleaseInfo(true, true)" auto-loading>
          <var-icon name="refresh" size="18" />
          {{ $t('settings.checkUpdate') }}
        </var-button>
      </div>
      <div class="setting-row" v-if="euiReleaseInfo?.latest_release?.version">
        <div class="version-info-block">
          <span class="setting-label">
            {{ $t('settings.stableVersion') }}
            <var-icon name="information-outline" size="18" color="var(--color-primary)" 
            @click="setupShowEuiReleaseInfo('latest_release')" />
          </span>
          <span class="version-value">{{ euiReleaseInfo.latest_release.version }}</span>
        </div>
        <var-chip type="warning" size="mini" plain v-if="buildVersion < euiReleaseInfo.latest_release.version">{{ $t('common.newVersion') }}</var-chip>
        <var-button type="primary" size="small" @click="installEuiVersion('release')" auto-loading
           :disabled="updateProgress.active"
           v-if="euiReleaseInfo?.latest_release?.version && buildVersion !== euiReleaseInfo.latest_release.version">
          <var-icon name="download" />
          {{ $t('common.install') }}
        </var-button>
      </div>
      <div class="setting-row" v-if="euiReleaseInfo?.latest_prerelease?.version">
        <div class="version-info-block">
          <span class="setting-label">
            {{ $t('settings.prereleaseVersion') }}
            <var-icon name="information-outline" size="18" color="var(--color-primary)" 
            @click="setupShowEuiReleaseInfo('latest_prerelease')" />
          </span>          
          <span class="version-value">{{ euiReleaseInfo.latest_prerelease.version }}</span>
        </div>
        <var-chip type="warning" size="mini" plain v-if="buildVersion < euiReleaseInfo.latest_prerelease.version">{{ $t('common.newVersion') }}</var-chip>
        <var-button type="primary" size="small" @click="installEuiVersion('prerelease')" auto-loading
           :disabled="updateProgress.active">
          <var-icon name="download" />
          {{ $t('common.install') }}
        </var-button>
      </div>
      <div class="setting-row" v-if="updateProgress.active" style="flex-direction: column; align-items: stretch;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
          <span style="font-size: 13px; color: var(--color-text-secondary);">{{ updateProgress.description }}</span>
          <span style="font-size: 13px; color: var(--color-primary);">{{ updateProgress.current_progress }}%</span>
        </div>
        <var-progress 
          :value="Number(updateProgress.current_progress) || 0" 
          :color="'var(--color-primary)'"
          line-width="6"
          ripple
        />
      </div>
    </var-paper>

    <!-- 内核设置 -->
    <var-paper class="setting-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiShieldLock" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.kernel.title') }}</span>
      </div>
      <var-divider />
      <!-- 安卓ffi模式不支持设置日志 -->
      <div class="setting-row" v-if="platform !== 'android'">
        <span class="setting-label">{{ $t('settings.etLogLevel.label') }}</span>
        <var-select 
          class="setting-select" 
          :placeholder="$t('settings.etLogLevel.placeholder')" 
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
        <span class="setting-label">{{ $t('settings.currentVersion') }} {{ etVersion.version || $t('settings.unknownVersion') }}</span>
        <var-select 
          class="setting-select" 
          variant="outlined" 
          :placeholder="$t('settings.optionalVersion')" 
          size="small" 
          v-model="etVersion.selected_version"
        >
          <template #default>
            <var-option v-for="item in etVersionList" :key="item.version" :label="item.version" :value="item.version" class="version-option">
              <var-cell :title="item.version">
                <template #extra>
                  <div style="display: flex; align-items: center;">
                    <var-chip :type="item.download_count > 100000 ? 'success' : (item.download_count > 10000 ? 'primary' : 'danger')"  size="mini" style="writing-mode: horizontal-tb; white-space: nowrap;">
                      <var-icon name="download" size="12" />
                      {{ item.download_count }}
                    </var-chip>
                    <var-badge
                      size="mini"
                      :type="item.prerelease ? 'warning' : 'success'" 
                      position="right-bottom" 
                      :value="item.prerelease ? $t('settings.prerelease') : $t('settings.stable')">
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
              color="var(--color-primary)"
              @click.stop="getEtReleaseInfo(true, true)" 
            />
          </template>
        </var-select>
      </div>
      <div class="setting-row" v-if="etVersion.selected_version != ''">
        <div class="setting-actions">
          <var-chip v-if="hasNewVersion" type="warning" size="mini" plain>{{ $t('common.canUpgrade') }}</var-chip>
          <var-button type="primary" size="small" @click="installEtCore(true)" auto-loading>
            <!-- <var-icon name="download" /> -->
            {{ $t('common.install') }}
          </var-button>
           <var-button type="primary" size="small" @click="handleShowEtChangeLog()">
            <!-- <var-icon name="information-outline" /> -->
            {{ $t('common.updateContent') }}
          </var-button>
        </div>
      </div>
      <!-- <var-divider /> -->
      <div class="setting-row" @click="window.open('https://easytier.cn', '_blank')">
        <span class="setting-label">
          {{ $t('settings.easytierDoc') }}
        </span>
        <a href="https://easytier.cn" target="_blank" style="text-decoration: none;">
          <var-icon name="share" color="var(--color-primary)" />
        </a>
      </div>
    </var-paper>

    <!-- 其他 -->
    <var-paper class="setting-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiTextBoxOutline" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.others') }}</span>
      </div>
      <var-divider />
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('settings.optionalInitialNodes') }}
        </span>
        <var-select
          v-model="peerSource"
          multiple
          variant="outlined"
          :chip="true"
          size="small"
          class="setting-select"
          @change="savePeerSource"
        >
          <var-cell>
            <template #icon>
              <svg-icon type="mdi" :path="mdiDraw" color="var(--color-primary)" />
            </template>
            <template #description>
              <var-input :placeholder="$t('settings.initialNodes.placeholder')" size="small" v-model="customPeerSource" blur-color="var(--color-primary)" />
            </template>
            <template #extra>
              <var-button type="primary" size="small" @click="addPeerSource">{{ $t('config.addListener') }}</var-button>
            </template>
          </var-cell>
          <var-option :label="$t('settings.initialNodes.eui')" value="_eui" />
          <var-option v-for="(e, index) in peerSourceOptions.filter(e => e.value !== '_eui')" :key="'custom-' + index" :label="e.label" :value="e.value" />
        </var-select>
      </div>
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('settings.euiLogLevel.label') }}
        </span>
        <var-select 
          class="setting-select" 
          v-model="logLevel"
          variant="outlined"
          size="small"
          :line="true"
          :options="logLevelOptions"
          label-key="label"
          value-key="value"
          @change="changeLogLevel"
        >
        </var-select>
      </div>
      <div class="setting-row" v-if="platform === 'android'">
        <span class="setting-label">
          {{ $t('settings.startRecovery') }}
          <var-tooltip :offset-x="65">
            <var-icon name="help-circle-outline" size="16" class="help-icon" color="var(--color-primary)" />
            <template #content>
              <div class="tooltip-multiline">{{ $t('settings.startRecoveryTip') }}</div>
            </template>
          </var-tooltip>
        </span>
        <var-switch variant size="20" v-model="enabledStartRecovery" @change="toggleEnabledStartRecovery" />
      </div>
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('common.deleteLog') }}
        </span>
        <var-button type="primary" size="small" @click="deleteLog" auto-loading >
          <var-icon name="delete" size="18" />
          {{ $t('common.delete') }}
        </var-button>
      </div>
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('common.deleteCache') }}
        </span>
        <var-button type="primary" size="small" @click="deleteCache" auto-loading >
          <var-icon name="delete" size="18" />
          {{ $t('common.delete') }}
        </var-button>
      </div>
      <div class="setting-row" v-if="platform !== 'trim' && platform !== 'android' && !isDocker">
        <span class="setting-label">{{ $t('settings.specifyIpPort') }}</span>
        <var-button type="primary" size="small" @click="releaseConfig" auto-loading>
          {{ $t('settings.releaseConfig') }}
        </var-button>
      </div>
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('common.installationPath') }}
        </span>
        <var-chip type="primary" size="small" style="word-break: break-all; white-space: normal; text-align: left;">{{ installPath }}</var-chip>
      </div>
      <div class="setting-row">
        <span class="setting-label">
          {{ $t('settings.githubDownload') }}
        </span>
        <var-button type="primary" size="small" @click="showGithubUrlPopup = true">
          <var-icon name="download" size="18" />
          {{ $t('common.download') }}
        </var-button>
      </div>
    </var-paper>    

    <!-- 开发者选项 -->
    <var-paper class="setting-block" :elevation="0" v-if="showDevContent">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiDevTo" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.developer.title') }}</span>
      </div>      
      <var-divider />
      <div class="setting-row" v-if="platform === 'android'">
        <span class="setting-label">{{ $t('settings.developer.webviewDebug') }}</span>
        <var-switch variant size="20" v-model="webviewDebugEnabled" @change="toggleWebviewDebug" />
      </div>
      <div class="setting-row">
        <span class="setting-label">{{ $t('settings.developer.mobileDebug') }}</span>
        <var-switch variant size="20" v-model="vConsoleEnabled" @change="toggleVConsole" />
      </div>
      <div class="setting-row" v-if="platform === 'android'">
        <span class="setting-label">{{ $t('settings.developer.ignoreSslErrors') }}</span>
        <var-switch variant size="20" v-model="ignoreSslErrors" @change="toggleIgnoreSslErrors" />
      </div>
      <div class="setting-row">
        <span class="setting-label">{{ $t('settings.developer.testPeers') }}</span>
        <var-switch variant size="20" v-model="testPeerSourceEnabled" :loading="changingPeerSource" @change="togglePeerSource" />
      </div>
      <div class="setting-row">
        <span class="setting-label">{{ $t('settings.developer.githubMirror') }}</span>
        <var-select v-model="githubMirror" variant="outlined" size="small" class="setting-select" placeholder="点击查看延迟">
          <var-option v-for="item in githubMirrors" :key="item.url" :value="item.url" :label="item.label" class="version-option" disabled>
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
              color="var(--color-primary)"
            />
          </template>
        </var-select>
      </div>
    </var-paper>

    <!-- 关于 -->
    <var-paper class="setting-block" :elevation="0">
      <div class="block-header" 
        @mousedown="startPress"
        @mouseup="cancelPress"
        @mouseleave="cancelPress"
        @touchstart.prevent="startPress"
        @touchend="cancelPress"
        @touchcancel="cancelPress"
        @touchmove="cancelPress">
        <svg-icon type="mdi" :path="mdiInformation" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('settings.about.title') }}</span>
      </div>
      <var-divider />
      <!-- 版本信息卡片 -->
      <div class="about-version-card">
        <div class="version-main">
          <img src="/icon.png" alt="Logo" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />
          <span class="version-name">{{ $t('settings.about.appName') }} {{ forUser ? $t('settings.about.liteVersion') : '' }}</span>
        </div>
        <div class="version-actions">
          <a href='https://github.com/710850609/EasyTier-EUI' target="_blank">
            <img :alt="$t('settings.about.starsLabel')" :src="starsBadgeUrl" style="border-radius: 8px">
          </a>
          <var-chip elevation="0" @click="showRewardCdoe = true" type="primary" size="small" style="cursor: pointer;">{{ $t('settings.about.reward') }}</var-chip>
          <a href="https://github.com/710850609/EasyTier-EUI/issues/new?template=bug_report.yml" target="_blank" style="text-decoration: none;">
            <var-chip elevation="0" type="primary" size="small" style="cursor: pointer;">{{ $t('settings.about.feedback') }}</var-chip>
          </a>
        </div>
      </div>
      
      <!-- 简介 -->
      <div class="about-section">
        <div class="about-content">
          <p>{{ $t('settings.about.description1') }}</p>
          <p>{{ $t('settings.about.description2') }}</p>
          <p>{{ $t('settings.about.description3') }}</p>
          <p>{{ $t('settings.about.description4') }}</p>
          <img :alt="$t('settings.about.downloadCountAlt')" :src="downloadBadgeUrl" style="border-radius: 8px"/>
        </div>
      </div>
    </var-paper>

    <var-button block type="danger" v-if="platform === 'linux' && !isDocker" @click="shutdown">
      <template #default>
        <var-icon name="power" size="20" /> {{ $t('common.shutdown') }} {{ $t('settings.about.appName') }}
      </template>
    </var-button>
  <div>      
  </div>

  <!-- GitHub辅助下载 -->
  <var-dialog v-model:show="showGithubUrlPopup" :title="$t('settings.githubDownload')" :confirm-button-text="$t('settings.githubDownloadReadClipboard')" safe-area="false" @confirm="confirmGithubDownload" @cancel="showGithubUrlPopup = false">
    <p>{{ $t('settings.githubDownloadDesc') }}</p>
  </var-dialog>

  <!-- 赞赏码 -->
  <var-popup v-model:show="showRewardCdoe" :safe-area="true" :safe-area-top="true">
    <var-result :description="$t('settings.about.rewardDesc')">
      <template #image>
        <img src="../../public/images/reward_code.jpg" style="width: 50%; height: 50%; border-radius: 50%; object-fit: cover;" />
      </template>
      <template #footer>
        <var-button type="primary" @click="showRewardCdoe = false">{{ $t('common.close') }}</var-button>
      </template>
    </var-result>
  </var-popup>

  <!-- 弹窗更新说明 -->
  <var-popup v-model:show="showEuiReleaseInfo" :safe-area="true" :safe-area-top="true">
    <var-result type="info">
      <template #image>
         <MarkdownRenderer :content="`${euiChangeMarkdown}`" class="markdown-renderer" />
      </template>
      <template #footer>
        <var-button type="primary" @click="showEuiReleaseInfo = false" style="margin: 10px;">{{ $t('common.close') }}</var-button>
      </template>
    </var-result>
  </var-popup>
  
  <!-- ET 版本更新说明 -->
  <var-popup :default-style="false" v-model:show="showEtChangeLog" :safe-area="true" :safe-area-top="true">
    <var-result type="info">
      <template #image>
        <MarkdownRenderer :content="etChangeLog" class="markdown-renderer" />
      </template>
      <template #footer>
        <var-button type="primary" @click="showEtChangeLog = false">{{ $t('common.close') }}</var-button>
      </template>
    </var-result>
  </var-popup>
  </div>
</template>

<script setup>
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { themeOptions, setThemeMode, themeMode, glassEffectEnabled, setGlassEffect } from '../config/theme.js'
import { VCONSOLE_ENABLED_KEY } from '../config/storage-keys.js'
import toast from '../components/toast.js'
import api from '../utils/api.js'
import { getAcceleratedDownloadUrl } from '../utils/github.js'
import { openDownloadUrl } from '../utils/download.js'
import { setLanguage, getLanguage } from '../locales/index.js'
import { useI18n } from 'vue-i18n'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiBrightness6, mdiAccessPointNetwork, mdiDevTo, mdiShieldLock, mdiMapOutline, mdiInformation, mdiTextBoxOutline, mdiDraw } from '@mdi/js'

const dev_toggle_timer = ref(null);
const { t } = useI18n()
const currentLanguage = ref(getLanguage())
const peerSourceOptions = ref([])

const peerSource = ref([])
const customPeerSource = ref('')
const showDevContent = ref(false)
const vConsoleEnabled = ref(false)
const webviewDebugEnabled = ref(false)
const ignoreSslErrors = ref(false)
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
const forUser = ref(false)
const showRewardCdoe = ref(false)
const showGithubUrlPopup = ref(false)
const platform = ref('')
const isDocker = ref(false)
const logLevel = ref('warn')
const etLogLevel = ref('error')
const euiReleaseInfo = ref({})
const euiRelease = ref({})
const euiChangeMarkdown = ref('')
const updateProgress = ref({ current_progress: 0, description: '', status: -1, active: false })
const enabledStartRecovery = ref(false)
const showEuiReleaseInfo = ref(false)
const showEtChangeLog = ref(false)
const etChangeLog = ref('')
const logLevelOptions = computed(() => [
  { value: 'off', label: t('settings.logLevel.disabled') },
  { value: 'error', label: t('settings.logLevel.error') },
  { value: 'warn', label: t('settings.logLevel.warn') },
  { value: 'info', label: t('settings.logLevel.info') },
  { value: 'debug', label: t('settings.logLevel.debug') },
])

const languageOptions = [
  { value: 'zh', label: '简体中文' },
  { value: 'zhtw', label: '繁體中文' },
  { value: 'en', label: 'English' },
  { value: 'de', label: 'Deutsch' },
  { value: 'fr', label: 'Français' },
]

const changeLanguage = (val) => {
  setLanguage(val)
  if (platform.value === 'android') {
    api.settings.getEuiInfo()
  }
}

const toggleGlassEffect = (val) => {
  setGlassEffect(val)
}

const toggleEnabledStartRecovery = (val) => {
  api.settings.setEnabledStartRecovery({ enabled: val })
    .then(() => toast.success(t(val ? 'settings.startRecoveryEnabled' : 'settings.startRecoveryDisabled')))
    .catch(() => {
      enabledStartRecovery.value = !val
    })
}

const startPress = (e) => {
  dev_toggle_timer.value = setTimeout(() => { 
    getGithubMirrors()
    loadPeerSource()
    showDevContent.value = !showDevContent.value
    toast.success(t(showDevContent.value ? 'settings.toast.devEnabled' : 'settings.toast.devDisabled'))
  }, 3000);
};

const cancelPress = () => {
  clearTimeout(dev_toggle_timer.value);
};

const hasNewVersion = computed(() => etVersion.value.version && etVersion.value.latest_version && etVersion.value.version !== etVersion.value.latest_version)
// 计算当前主题模式（从 theme.js 获取）
const currentThemeMode = computed(() => themeMode.value)

const starsBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('settings.about.starsLabel'))
  return `https://img.shields.io/github/stars/710850609/EasyTier-EUI?color=blue&style=flat-square&label=${label}`
})

const downloadBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('settings.about.downloadCount'))
  return `https://img.shields.io/github/downloads/710850609/EasyTier-EUI/total?color=blue&style=flat-square&label=${label}`
})

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
      toast.success(t('settings.toast.vconsoleEnabled'))
    } else {
      toast.error(t('settings.toast.vconsoleFailed'))
      vConsoleEnabled.value = false
      localStorage.setItem(VCONSOLE_ENABLED_KEY, 'false')
    }
  } else {
    if (vConsoleInstance.value) {
      vConsoleInstance.value.destroy()
      vConsoleInstance.value = null
    }
    toast.success(t('settings.toast.vconsoleDisabled'))
  }
}

const toggleWebviewDebug = async (val) => {
  try {
    await api.settings.setWebviewDebug({ enabled: val })
  } catch (e) {
    webviewDebugEnabled.value = !val
    console.error('toggleWebviewDebug failed:', e)
  }
}

const toggleIgnoreSslErrors = async (val) => {
  try {
    await api.settings.setIgnoreSslErrors({ enabled: val })
  } catch (e) {
    ignoreSslErrors.value = !val
    console.error('toggleIgnoreSslErrors failed:', e)
  }
}

const togglePeerSource = async (val) => {
  changingPeerSource.value = true
  const data = { source: val ? 'test' : 'stable' }
  await api.peers.setEuiPeerSource(data).then(() => {
    testPeerSourceEnabled.value = val
    toast.success(t(val ? 'settings.toast.peerSourceTest' : 'settings.toast.peerSourceStable'))
  }).finally(() => {
    changingPeerSource.value = false
  })
}

const loadPeerSource = async () => {
  try {
    const { data } = await api.peers.getEuiPeerSource()
    testPeerSourceEnabled.value = data.source === 'test'
  } catch (e) {
    console.error('获取节点来源失败:', e)
    testPeerSourceEnabled.value = false
  }
}

const loadPeerSourceList = async () => {
  try {
    const { data } = await api.peers.getPeerSource()
    if (Array.isArray(data)) {
      data.forEach(e => {
        peerSourceOptions.value.push({ value: e, label: e })
      })
      peerSource.value = data
    }
  } catch (e) {
    console.error('获取可选节点失败:', e)
  }
}

const savePeerSource = async () => {
  const loadingToast = toast.loading(t('settings.toast.saving'))
  await api.peers.setPeerSource({ peer_source: peerSource.value })
  loadingToast.clear()
}

const addPeerSource = () => {
  const val = customPeerSource.value.trim()
  if (!val) {
    toast.error(t('settings.toast.peerSourceEmpty'))
    return
  }
  if (peerSourceOptions.value.some(item => item.value === val)) {
    toast.error(t('settings.toast.peerSourceDuplicate'))
    return
  }
  peerSourceOptions.value.push({ value: val, label: val })
  peerSource.value.push(val)
  customPeerSource.value = ''
  savePeerSource()
}

// 获取当前版本
const getEtInfo = async () => {
  try {
    isFetchingEtCoreVersion.value = true
    const { data } = await api.etCore.getConfig()
    etLogLevel.value = data.log_level
    delete data.log_level
    etVersion.value = { ...etVersion.value, ...data }

  } catch (e) {
    console.error('获取内核版本失败:', e)
    etVersion.value.raw_version = t('settings.getVersionFailed') + e.message
  } finally {
    isFetchingEtCoreVersion.value = false
  }
}

const getEtReleaseInfo = async (refresh = false, showTip = true) => {
  isFetchingVersionList.value = true
  try {
    const resp = await api.etCore.getVersionList({'refresh': refresh})
    etVersionList.value = resp.data.versions || []
    etVersion.value.latest_version = etVersionList.value[0]?.version || ''
    if (!etVersion.value.selected_version) {
      etVersion.value.selected_version = etVersion.value.latest_version
    }
    if (refresh && showTip) {      
      toast.success(t('settings.toast.versionRefreshed') + '\n' + formatDate(new Date(resp.data.update_time)))
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
      toast.success(res.data || t('settings.toast.kernelInstalled', { version: etVersion.value.selected_version }))
      // getEtVersion()
      getEtInfo()
      if (platform.value === 'android') {
        toast.success(t('settings.toast.restartToApply'))
      }
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
      toast.success(t('settings.toast.mirrorsRefreshed'))
    }
  } catch (e) {
    console.error('获取 GitHub 加速地址失败:', e)
  } finally {
    isFetchingGithubMirrors.value = false
  }
}

const getEuiInfo = async () => {
  try {
    buildVersion.value = t('settings.toast.fetchingVersion')
    const { data } = await api.settings.getEuiInfo()
    buildVersion.value = data.build_version
    installPath.value = data.install_path
    forUser.value = data.for_user
    platform.value = data.platform
    isDocker.value = data.is_docker
    logLevel.value = data.log_level
    enabledStartRecovery.value = data.enabled_start_recovery || false
    webviewDebugEnabled.value = data.webview_debug || false
    ignoreSslErrors.value = data.ignore_ssl_errors || false
    if (euiReleaseInfo.value) {
      euiReleaseInfo.value = data.release_info
    }
  } catch (e) {
    console.error('获取版本号失败:', e)
    buildVersion.value = t('settings.toast.fetchVersionFailed')
  }
}

const installEuiVersion = (versionType) => {
  return new Promise(async (resolve, reject) => {
    if (window.location.href.indexOf('/cgi/ThirdParty/EasyTier-EUI.User/index.cgi') !== -1) {
      toast.error(t('settings.toast.liteNotSupported'))
      resolve()
      return
    }
    let targetVersion = null
    updateProgress.value = { current_progress: 0, description: t('settings.toast.preparingUpdate'), status: 0, active: true }
    const loadingToast = toast.loading(t('settings.toast.updating'))
    let pollErrorCount = 0

    try {
      const { data: updateResp } = await api.etEui.update({ ver_tag: versionType })
      const updateId = updateResp.update_id

      let pollTimer = setInterval(async () => {
        try {
          const { data: progress } = await api.etEui.getUpdateProgress({ update_id: updateId })
          pollErrorCount = 0
          if (progress.update_version) {
            targetVersion = progress.update_version
          }
          updateProgress.value = { ...progress, active: true }
          loadingToast.content = `${progress.description} (${progress.current_progress}%)`

          if (progress.status === 1) {
            clearInterval(pollTimer)
            updateProgress.value = { ...progress, active: false }
            loadingToast.clear()
            toast.success(progress.description || t('settings.toast.updateReady'))
            if (progress.file_path && window.AndroidBridge && window.AndroidBridge.installApk) {
              window.AndroidBridge.installApk(progress.file_path)
            }
            resolve()
            if (platform.value !== 'android') {
              waitForRestart(targetVersion)
            }
          } else if (progress.status === 2) {
            clearInterval(pollTimer)
            updateProgress.value = { ...progress, active: false }
            loadingToast.clear()
            toast.error(progress.description || t('settings.toast.updateFailed'))
            reject(new Error(progress.description))
          }
        } catch (e) {
          pollErrorCount++
          if (pollErrorCount >= 3 && targetVersion) {
            clearInterval(pollTimer)
            updateProgress.value = { ...updateProgress.value, active: false }
            loadingToast.clear()
            resolve()
            if (platform.value !== 'android') {
              waitForRestart(targetVersion)
            }
          }
        }
      }, 1500)
    } catch (e) {
      updateProgress.value = { current_progress: 0, description: '', status: -1, active: false }
      toast.error(e.message || t('settings.toast.updateRequestFailed'))
      loadingToast.clear()
      reject(e)
    }
  })
}

const waitForRestart = (targetVersion) => {
  const waitingToast = toast.loading(t('settings.toast.restarting'))
  let retryCount = 0

  const checkRestart = setInterval(async () => {
    retryCount++
    try {
      const { data: euiInfo } = await api.settings.getEuiInfo()
      if (euiInfo.build_version === targetVersion) {
        clearInterval(checkRestart)
        waitingToast.clear()
        buildVersion.value = euiInfo.build_version
        toast.success(t('settings.toast.updateCompleted'))
        window.location.reload()
      }
    } catch (e) {
      // 服务重启中，连接失败属于正常现象，忽略
    }

    if (retryCount >= 60) {
      clearInterval(checkRestart)
      waitingToast.clear()
      toast.error(t('settings.updateTimeout'))
    }
  }, 2000)
}

const shutdown = async () => {
  try {
    await api.settings.shutdown()
    toast.success(t('settings.shuttingDown'))
    setTimeout(() => {
      window.location.reload()
    }, 1000)
  } catch (e) {
    console.error('关闭易组网失败:', e)
    toast.error(t('settings.shutdownFailed'))
  }
}

const setEtLogLevel = async (level) => {
  const loadingToast = toast.loading(t('settings.settingLogLevel'))
  try {
    await api.etCore.setEtLogLevel({ level: level })
    const selectedLabel = logLevelOptions.value.filter(item => item.value === level)[0].label
    toast.success(t('settings.logLevelSet', {label: selectedLabel}))
  } finally {
    loadingToast.clear()
  }
}

const changeLogLevel = async (level) => {
  const loadingToast = toast.loading(t('settings.settingLogLevel'))
  try {
    await api.settings.setLogLevel({ log_level: level })
    const selectedLabel = logLevelOptions.value.find(item => item.value === level)?.label || level
    toast.success(t('settings.logLevelSet', { label: selectedLabel }))
  } finally {
    loadingToast.clear()
  }
}

const deleteLog = async () => {
  return new Promise((resolve) => {
    api.settings.deleteLog().then(data => {
      toast.success(data.data || t('settings.logDeleted'))
    }).finally(() => {
      resolve()
    })
  })
}

const getEuiReleaseInfo = (refresh=false, showTip = true) => {
  return new Promise((resolve, reject) => {
    api.etEui.getReleaseInfo({'refresh': refresh, 'no_assets': true }).then((data) => {
      euiReleaseInfo.value = data.data
      if (refresh && showTip) {
        toast.success(t('settings.versionRefreshed', {update_time: formatDate(data.data.update_time)}))
      }
    }).finally((error) => {
      resolve()
    })
  })
}

const setupShowEuiReleaseInfo = (releaseType) => {
  const info = euiReleaseInfo.value[releaseType]
  if (!releaseType || !info) {
    return
  }
  euiChangeMarkdown.value = `
# ${ info.version }
>  ${formatDate(euiReleaseInfo.value.update_time)} ${t('settings.about.changelogDownloadCount')}  ${info.download_count }
## 更新内容
${ info.changelog }
`
  showEuiReleaseInfo.value = true
}

const handleShowEtChangeLog = () => {
  const selectedVersion = etVersion.value.selected_version
  return new Promise((resolve, reject) => {
    api.etCore.getVersionChangeLog({
      version: selectedVersion
    }).then(data => {
      etChangeLog.value = data.data || ''
      showEtChangeLog.value = true
    })
  }).finally(() => {
    resolve()
  })
}

const deleteCache = async () => {
  return new Promise((resolve, reject) => {
    api.settings.deleteCache().then(data => {
      toast.success(data.data || t('settings.cacheCleared'))
    }).finally(() => {
      resolve()
    })
  })
}

const releaseConfig = async () => {
  return new Promise((resolve, reject) => {
    api.settings.releaseConfig().then(data => {
      toast.success(data.data || t('common.save'))
    }).finally(() => {
      resolve()
    })
  })
}

const extractRealGithubUrl = (url) => {
  const githubIndex = url.indexOf('https://github.com')
  if (githubIndex > 0) {
    return url.substring(githubIndex)
  }
  return url
}

const isValidGithubUrl = (url) => {
  const githubDomains = [
    'https://github.com',
    'https://api.github.com',
    'https://raw.githubusercontent.com',
    'https://codeload.github.com'
  ]
  return githubDomains.some(domain => url.startsWith(domain))
}

const confirmGithubDownload = async () => {
  try {
    const rawUrl = await navigator.clipboard.readText()
    if (!rawUrl || !rawUrl.trim()) {
      toast.warning(t('settings.githubDownloadEmpty'))
      return
    }
    const realUrl = extractRealGithubUrl(rawUrl.trim())
    if (!isValidGithubUrl(realUrl)) {
      toast.warning(`${t('settings.githubDownloadInvalid')}\n${realUrl}`)
      return
    }
    const acceleratedUrl = await getAcceleratedDownloadUrl(realUrl)
    showGithubUrlPopup.value = false
    openDownloadUrl(acceleratedUrl)
  } catch {
    toast.warning(t('settings.githubDownloadEmpty'))
  }
}

const formatDate = (date, sep = '-') => {
    const f = new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    const p = f.formatToParts(date);
    const get = (t) => p.find(x => x.type === t).value;
    return `${get('year')}${sep}${get('month')}${sep}${get('day')} ${get('hour')}:${get('minute')}:${get('second')}`;
}

onMounted(() => {
  // VConsole 开发者工具：恢复上次开关状态
  const vconsoleEnabled = localStorage.getItem(VCONSOLE_ENABLED_KEY) === 'true'
  vConsoleEnabled.value = vconsoleEnabled

  if (vconsoleEnabled) {
    showDevContent.value = true
    Promise.allSettled([loadVConsole(), loadPeerSource(), getGithubMirrors()])
  }

  // 并行加载所有初始化数据（互不依赖，任一失败不影响其他）
  Promise.allSettled([
    getEuiInfo(),
    getEtInfo(),
    loadPeerSourceList(),
    getEtReleaseInfo(true, false),
    getEuiReleaseInfo(true, false),
  ])
})
</script>

<style scoped>
/* var-select 下拉框毛玻璃效果 - 样式已移至全局样式文件 */

.settings-page {
  padding: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.setting-block {
  padding: 20px;
  border-radius: 20px;
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
  padding: 12px 8px;
  border-radius: 20px;
  border: 2px solid var(--color-outline);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.theme-option:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-container);
  cursor: pointer;
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
  flex-wrap: wrap;
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
  min-width: 60px;
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
  .settings-page {
    padding-bottom: calc(64px + var(--sab, 0px) + 16px);
  }

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

  .var-option :deep(.var-cell.var-cell--border) {
    /* 下拉框 左右无边距 */
    padding: 0px 0px 0px 0px !important;
  }
}
</style>
<!-- 全局样式，影响下拉 option -->
<style>
.version-option {
  padding: 0;
}
</style>