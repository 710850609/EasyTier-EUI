<template>
  <div class="platform-page">
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
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img :src="stableBadgeUrl" /></var-link>
        </var-cell>
        <var-divider />
        <var-space class="eui-download-btn-group" :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'x86_64')" :loading="downloadingKey === 'linux-x86_64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.x64Version') }}
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'aarch64')" :loading="downloadingKey === 'linux-aarch64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.arm64Version') }}
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'armv7')" :loading="downloadingKey === 'linux-armv7'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.armv7Version') }}
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'riscv64')" :loading="downloadingKey === 'linux-riscv64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.riscv64Version') }}
            </template>
          </var-button>
        </var-space>
        <div v-if="progress" class="download-progress">
          <var-progress :value="progress.current_progress" :track="true" />
          <p class="progress-desc">{{ progress.description }}</p>
        </div>
        <var-cell>
          <p style="margin-bottom: 12px;">{{ $t('software.usageGuide') }}</p>
        </var-cell>
        <div class="eui-opt-desc-table-container">
          <var-table class="eui-opt-desc-table">
            <thead>
              <tr>
                <th align="center">{{ $t('software.operation') }}</th>
                <th align="center">{{ $t('software.withGUI') }}</th>
                <th align="center">{{ $t('software.withoutGUI') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td align="center">{{ $t('software.startCommand') }}</td>
                <td colspan="2" align="center"><code>./start.sh</code></td>
              </tr>
              <tr>
                <td align="center">{{ $t('software.stopCommand') }}</td>
                <td colspan="2" align="center"><code>./stop.sh</code></td>
              </tr>
              <tr>
                <td align="center">{{ $t('software.startAction') }}</td>
                <td align="center">{{ $t('software.runApp') }}<code>EasyTier-EUI</code></td>
                <td align="center">❌{{ $t('software.notSupported') }}</td>
              </tr>
              <tr>
                <td align="center">{{ $t('software.stopAction') }}</td>
                <td colspan="2" align="center">{{ $t('software.stopActionDesc') }} <var-button type="danger" size="mini">{{ $t('software.shutdownBtn') }}</var-button>{{ $t('software.button') }}</td>
              </tr>
            </tbody>
          </var-table>
        </div>
      </div>
    </var-paper>

    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>{{ $t('software.linuxGuiVersion') }}</h2>
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
      <!-- 下载卡片网格 -->
      <div class="download-grid">
        <!-- amd64 deb -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 deb</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('deb', 'amd64', true)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('deb', 'amd64', false)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <!-- amd64 rpm -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 rpm</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('rpm', 'x86_64', true)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('rpm', 'x86_64', false)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <!-- amd64 AppImage -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 AppImage</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('AppImage', 'amd64', true)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('AppImage', 'amd64', false)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <!-- arm64 deb -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">arm64 deb</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('deb', 'arm64', true)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('deb', 'arm64', false)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
        <!-- aarch64 rpm -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">arm64 rpm</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('rpm', 'aarch64', true)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('rpm', 'aarch64', false)" auto-loading>
              <var-icon name="download"  />
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      </div>
    </var-paper>

    <var-dialog v-model:show="showConfigSelectDialog" :title="$t('software.selectConfig')" @confirm="handleConfigConfirm">
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

const stableBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('software.stableLabel'))
  return `https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&label=${label}`
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

const download = (type, arch, prerelease) => {
  return new Promise((resolve, reject) => {
    api.etApp.getDownloadUrl({type: type, arch: arch, prerelease: prerelease}).then((resp) => {
      window.open(resp.data, '_blank')
    }).finally(() => {
      resolve()
    })
  })
}


const showConfigSelectDialog = ref(false)
const configFiles = ref([])
const selectedConfig = ref(null)
const selectedPlatform = ref(null)
const selectedArch = ref(null)

const downloadEasyTierEui = async (platform, arch) => {
  if (downloadingKey.value) {
    toast.warning(t('software.currentlyDownloading', { key: downloadingKey.value }))
    return
  }
  const configs = await api.configs.listConfigFiles().then(resp => resp.data).catch(error => toast.error(t('software.getConfigFailed'), error.message))
  let profile = ''
  selectedPlatform.value = platform
  selectedArch.value = arch
  if (configs.length === 0) {
    toast.info(t('software.noConfigDownload'))
  } else if (configs.length === 1) {
    profile =  configs[0].profile
  } else {
    configFiles.value = configs 
    selectedConfig.value = configs[0]?.profile
    showConfigSelectDialog.value = true
    return
  }
  startDownload(`${platform}-${arch}`, { platform, arch, profile }).catch(err => {
    console.error('下载失败:', err)
  })
}

const handleConfigConfirm = async () => {
  if (selectedConfig.value) {
    startDownload(`${selectedPlatform.value}-${selectedArch.value}`, { platform: selectedPlatform.value, arch: selectedArch.value, profile: selectedConfig.value || '' }).catch(err => {
      console.error('下载失败:', err)
    })
  }
  selectedConfig.value = null
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

/* 操作说明表格样式 */
.eui-opt-desc-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
}

.eui-opt-desc-table :deep(th) {
  background: var(--color-surface-container);
  color: var(--color-on-surface-container);
  font-weight: 600;
  padding: 14px 16px;
  text-align: center;
  border-bottom: 2px solid var(--color-outline);
  border-left: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(th:first-child) {
  border-left: none;
}

.eui-opt-desc-table :deep(th:last-child) {
  border-right: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(td) {
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  border-left: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  color: var(--color-on-surface);
  text-align: center;
}

.eui-opt-desc-table :deep(td:first-child) {
  border-left: none;
}

.eui-opt-desc-table :deep(td:last-child) {
  border-right: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(tr:last-child td) {
  border-bottom: none;
}

.eui-opt-desc-table :deep(tr:hover td) {
  background: var(--color-surface-container-low);
}

.eui-opt-desc-table :deep(code) {
  background: rgba(var(--color-primary-rgb), 0.18);
  color: var(--color-primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
}

/* 移动端响应式优化 */
@media (max-width: 768px) {
  .eui-opt-desc-table-container {
    overflow-x: auto;
    border-radius: 12px;
  }

  .eui-opt-desc-table {
    min-width: 500px;
    font-size: 12px;
  }

  .eui-opt-desc-table :deep(th),
  .eui-opt-desc-table :deep(td) {
    padding: 8px 10px;
    font-size: 13px;
  }

  .eui-opt-desc-table :deep(code) {
    font-size: 12px;
    padding: 2px 6px;
  }

  /* 下载按钮移动端优化 */
  .eui-download-btn-group {
    display: grid !important;
    grid-template-columns: repeat(2, 120px) !important;
    gap: 12px !important;
    width: 100% !important;
  }

  .eui-download-btn-group :deep(.var-button) {
    width: 120px !important; 
  }
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