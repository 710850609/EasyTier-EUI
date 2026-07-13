<template>
  <div class="platform-page">
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>{{ $t('software.androidVersion') }}</h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>
          <p>{{ $t('software.androidInstallDesc') }}</p>
          <p>{{ $t('software.startNetwork') }}</p>
        </var-cell>
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
            <span class="item-title">arm64
              <var-badge color="var(--color-primary)">
                 <template #value>{{ $t('software.commonModel') }}</template>
              </var-badge>
            </span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('arm64', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('arm64', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      <!-- </div>
      <div class="download-grid"> -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">arm
              <var-badge color="var(--color-primary)">
                 <template #value>{{ $t('software.oldModel') }}</template>
              </var-badge>
            </span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('arm', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('arm', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      </div>
      <div class="download-grid">
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('x86_64', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('x86_64', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      <!-- </div>
      <div class="download-grid"> -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('x86', true)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.prerelease') }}
            </var-button>
            <var-button type="primary" size="normal" @click="download('x86', false)" auto-loading>
              <var-icon name="download"/>
              {{ $t('software.stable') }}
            </var-button>
          </div>
        </var-paper>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// import { downloadEasyTierApk } from '../../utils/github.js'
import { api } from '../../utils/api.js'

const prereleaseVersion = ref('')
const latestReleaseVersion = ref('')

onMounted(() => {
  api.etApp.getAppInfo().then((resp) => {
    const data = resp.data
    prereleaseVersion.value = data.prerelease?.version || ''
    latestReleaseVersion.value = data.release?.version || ''
  })
})

const download = (arch, prerelease) => {
  // downloadEasyTierApk(prerelease)
  return new Promise((resolve, reject) => {
    api.etApp.getDownloadUrl({type:'apk', arch, prerelease}).then((resp) => {
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