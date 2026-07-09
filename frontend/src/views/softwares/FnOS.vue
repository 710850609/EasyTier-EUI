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
        <var-cell>{{ $t('software.fnOSInstallDesc') }}</var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img :src="stableBadgeUrl" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space class="eui-download-btn-group" :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('fnos', 'x86_64')" :loading="downloadingKey === 'fnos-x86_64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.x64Version') }}
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('fnos', 'aarch64')" :loading="downloadingKey === 'fnos-aarch64'">
            <template #default>
              <var-icon name="download"/>
              {{ $t('software.arm64Version') }}
            </template>
          </var-button>
        </var-space>
        <div v-if="progress" class="download-progress">
          <var-progress :value="progress.current_progress" :track="true" />
          <p class="progress-desc">{{ progress.description }}</p>
        </div>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
import { api } from '../../utils/api.js'
import { useAsyncDownload } from '../../utils/downloadProgress.js'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const stableBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('software.stableLabel'))
  return `https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&logo=github&label=${label}`
})

const { startDownload, progress, downloadingKey } = useAsyncDownload(
  api.etEui.startDownload,
  api.etEui.getDownloadProgress,
  api.etEui.getDownloadResultUrl,
)

const downloadEasyTierEui = (platform, arch) => {
  if (downloadingKey.value) return
  startDownload(`${platform}-${arch}`, { platform, arch }).catch(err => {
    console.error('下载失败:', err)
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

/* 操作说明表格样式 */
.eui-opt-desc-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: var(--color-surface-container-high);
}

.eui-opt-desc-table :deep(th) {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface) !important;
  font-weight: 600;
  padding: 12px 16px;
  text-align: center;
  border-bottom: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(td) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
  text-align: center;
}

.eui-opt-desc-table :deep(tr:last-child td) {
  border-bottom: none;
}

.eui-opt-desc-table :deep(code) {
  background: rgba(var(--color-primary-rgb), 0.15);
  color: var(--color-primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
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
</style>