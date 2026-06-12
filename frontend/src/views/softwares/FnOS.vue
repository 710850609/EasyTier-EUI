<template>
  <div class="platform-page">
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            易组网
            <var-badge type="primary">
               <template #value>推荐</template>
            </var-badge>
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>安装后，输入相同网络名、网络密码、对应初始化节点，保存启动，即可组网</var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img src="https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&logo=github&label=稳定版" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('fnos', 'x86_64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              x86_64版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('fnos', 'aarch64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              aarch64版
            </template>
          </var-button>
        </var-space>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
import { api } from '../../utils/api.js'

const downloadEasyTierEui = (platform, arch) => {
  return new Promise((resolve, reject) => {
    let url = api.etEui.getDownloadEasyTierEuiUrl({platform: platform, 'arch': arch})
    window.open(url, '_blank')
    resolve()
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
</style>