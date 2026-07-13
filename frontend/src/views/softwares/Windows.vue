<template>
  <div class="platform-page">
    <!-- 易组网 -->
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            {{ $t('software.easyTierEui') }}
            <var-badge type="primary">
               <template #value>{{ $t('software.newbieRecommended') }}</template>
            </var-badge>
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>
          <p>{{ $t('software.integratedConfig') }}</p>
          <p>{{ $t('software.selfBuildNode') }}</p>
        </var-cell>
        <var-cell><span style="font-style: italic;">{{ $t('software.etEuiAutoStartConflict') }}</span></var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img :src="euiStableBadgeUrl" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="showSelectProfile('etEui')" :loading="downloadingKey === 'windows-x86_64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </template>
          </var-button>
        </var-space>
        <div v-if="progress" class="download-progress">
          <var-progress :value="progress.current_progress" :track="true" />
          <p class="progress-desc">{{ progress.description }}</p>
        </div>
      </div>
    </var-paper>

    <!-- Easytier 管理器 -->
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            {{ $t('software.easyTierManager') }}
            <!-- <var-badge type="info">
               <template #value>{{ $t('software.newbieRecommended') }}</template>
            </var-badge> -->
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>
          {{ $t('software.managerDesc') }}
          <p>{{ $t('software.managerUsageMore') }} <var-link type="primary" href="https://easytier.cn/guide/gui/easytier-manager.html" target="_blank" underline="none">{{ $t('software.managerUsageLink') }}</var-link></p>
        </var-cell>
        <var-cell><span style="font-style: italic;">{{ $t('software.autoStartConflict') }}</span></var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/EasyTier/easytier-manager/releases" target="_blank"><img :src="managerStableBadgeUrl" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="showSelectProfile('mgr')" :loading="mgrDownloadingKey === 'mgr'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </template>
          </var-button>
        </var-space>
        <div v-if="mgrProgress" class="download-progress">
          <var-progress :value="mgrProgress.current_progress" :track="true" />
          <p class="progress-desc">{{ mgrProgress.description }}</p>
        </div>
      </div>
    </var-paper>

    <!-- 官方 -->
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>{{ $t('software.windowsGuiVersion') }}
            <var-badge type="primary">
               <template #value>{{ $t('software.official') }}</template>
            </var-badge>
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>{{ $t('software.installAndImport') }}</var-cell>
        <var-cell>
          {{ $t('software.visitForHelp') }}
          <var-link type="primary" href="https://easytier.cn/" target="_blank" underline="none">
            {{ $t('software.easyTierWebsite') }}
          </var-link>
        </var-cell>
        <var-space :size="[20, 20]" justify="center">
          <a class="shield-badge" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
            <span class="badge-label">{{ $t('software.prerelease') }}</span>
            <span class="badge-value">{{ prereleaseVersion || '--' }}</span>
          </a>
          <a class="shield-badge" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
            <span class="badge-label">{{ $t('software.stable') }}</span>
            <span class="badge-value">{{ latestReleaseVersion || '--' }}</span>
          </a>
        </var-space>
      </div>
      <var-divider />
      <div class="download-grid">
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">{{ $t('software.x64System') }}</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('exe', 'x64', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('exe', 'x64', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">{{ $t('software.x86System') }}</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('exe', 'x86', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('exe', 'x86', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">{{ $t('software.arm64System') }}</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('exe', 'arm64', true)" auto-loading>
              <var-icon name="download" />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('exe', 'arm64', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      </div>
    </var-paper>

    <var-dialog v-model:show="showConfigSelectDialog" :title="$t('software.selectConfig')" @confirm="downloadApp">
      <var-select
        v-model="selectedConfig"
        variant="outlined"
        class="config-select"
        size="small"
      >
        <var-option
          v-for="config in configFiles"
          :key="config.profile"
          :label="config.name"
          :value="config.profile"
        >
        </var-option>
      </var-select>
    </var-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import toast from '../../components/toast.js'
import { api } from '../../utils/api.js'
import { useAsyncDownload } from '../../utils/downloadProgress.js'

const { t } = useI18n()

const prereleaseVersion = ref('')
const latestReleaseVersion = ref('')

const euiStableBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('software.stableLabel'))
  return `https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&label=${label}`
})

const managerStableBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('software.stableLabel'))
  return `https://img.shields.io/github/v/release/EasyTier/easytier-manager?color=blue&label=${label}`
})

onMounted(() => {
  api.etApp.getAppInfo().then((resp) => {
    const data = resp.data
    prereleaseVersion.value = data.prerelease?.version || ''
    latestReleaseVersion.value = data.release?.version || ''
  })
})

const { startDownload, progress, downloadingKey } = useAsyncDownload(
  api.etEui.startDownload,
  api.etEui.getDownloadProgress,
  api.etEui.getDownloadResultUrl,
)

const { startDownload: startMgrDownload, progress: mgrProgress, downloadingKey: mgrDownloadingKey } = useAsyncDownload(
  api.windows.startMgrDownload,
  api.windows.getMgrDownloadProgress,
  api.windows.getMgrDownloadResultUrl,
)

const showConfigSelectDialog = ref(false)
const configFiles = ref([])
const selectedConfig = ref(null)
const selectedApp = ref(null)

const showSelectProfile = async (app) => {
  selectedApp.value = app
  const configs = await api.configs.listConfigFiles().then(resp => resp.data).catch(error => toast.error(t('software.getConfigFailed'), error.message))
  if (configs.length === 0) {
    toast.info(t('software.noConfigDownload'))
  } else if (configs.length === 1) {
    selectedConfig.value =  configs[0].profile
  } else {
    configFiles.value = configs 
    selectedConfig.value = configs[0]?.profile
    showConfigSelectDialog.value = true
    return
  }
  downloadApp()
}

const downloadApp = () => {
  if (selectedApp.value == 'mgr') {
    startMgrDownload('mgr', { profile: selectedConfig.value || '' }).catch(err => {
      console.error('下载失败:', err)
    })
  } else if (selectedApp.value == 'etEui') {
    startDownload('windows-x86_64', { platform: 'windows', arch: 'x86_64', profile: selectedConfig.value || '' }).catch(err => {
      console.error('下载失败:', err)
    })
  } else {
    toast.error(t('software.unknownApp'))
    return
  }
  selectedConfig.value = null
}

const download = (type, arch, prerelease) => {
  return new Promise((resolve, reject) => {
    api.etApp.getDownloadUrl({type: type, arch: arch, prerelease: prerelease}).then((resp) => {
      window.open(resp.data, '_blank')
    }).finally(() => {
      resolve()
    })
  })
}
</script>

<style scoped>
.platform-page {
  padding: 16px;
  max-width: 900px;
  margin: 0 auto;
}

.download-card {
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 20px;
  text-align: center;
  background: var(--color-surface-container) !important;
}

.platform-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.platform-info h2 {
  margin: 0;
  color: var(--color-on-surface);
}

.platform-info p {
  margin: 4px 0 0;
  color: var(--color-on-surface-variant);
}

.version-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-outline-variant);
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

/* 下载卡片网格 */
.download-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-top: 16px;
}

.download-item {
  padding: 20px;
  border-radius: 12px;
  background: var(--color-surface-container-high) !important;
  display: flex;
  flex-direction: column;
}

.item-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0px;
  margin-bottom: 16px;
  color: var(--color-on-surface);
}

.item-title {
  font-weight: 600;
  font-size: 15px;
  text-align: center;
}

.item-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.item-actions .var-button {
  flex: 1;
  min-width: 90px;
}

.item-actions .var-button :deep(.var-button__content) {
  flex-wrap: nowrap !important;
}

.download-progress {
  margin-top: 16px;
  text-align: center;
}

.progress-desc {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.shield-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 4px;
  overflow: hidden;
  font-size: 12px;
  line-height: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.shield-badge:hover {
  opacity: 0.85;
}
.badge-label {
  padding: 0 8px;
  background: #555;
  color: #fff;
}
.badge-value {
  padding: 0 8px;
  background: #007ec6;
  color: #fff;
}
</style>