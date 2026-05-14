<template>
  <div class="platform-page">
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            易组网
            <var-badge type="info">
               <template #value>预览</template>
            </var-badge>
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>集成当前配置、EasyTier内核，解压启动后启动服务即可组网</var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-Lite/releases" target="_blank"><img src="https://img.shields.io/github/v/release/710850609/EasyTier-Lite?color=blue&logo=github" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierLite('macos', 'aarch64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              Apple芯片版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierLite('macos', 'x86_64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              Intel芯片版
            </template>
          </var-button>
        </var-space>
      </div>
    </var-paper>

    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>EasyTier MacOS GUI 版本</h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>安装应用，并导出飞牛上配置toml文件后。把toml配置文件导入到easytier中，并启动网络即可。</var-cell>
        <var-cell>
          其他使用说明，请访问 
          <var-link type="primary" href="https://easytier.cn/" target="_blank" underline="none">
            EasyTier官网
          </var-link>
        </var-cell>
        <var-space :size="[20, 20]" justify="center">
          <var-cell>
            <var-link type="primary" underline="none" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
              <img src="https://img.shields.io/github/v/tag/EasyTier/EasyTier?color=blue&logo=github" />
            </var-link>
          </var-cell>
          <var-cell>
            <var-link type="primary" underline="none" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
              <img src="https://img.shields.io/github/v/release/EasyTier/EasyTier?color=blue&logo=github" />
            </var-link>
          </var-cell>
        </var-space>
      </div>
      <var-divider />
      <div class="download-grid">
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">Apple芯片</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('aarch64.dmg', true)" auto-loading>
              <var-icon name="download"/>
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('aarch64.dmg', false)" auto-loading>
              <var-icon name="download"/>
              稳定版
            </var-button>
          </div>
        </var-paper>
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">Intel芯片</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('x64.dmg', true)" auto-loading>
              <var-icon name="download" />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('x64.dmg', false)" auto-loading>
              <var-icon name="download"/>
              稳定版
            </var-button>
          </div>
        </var-paper>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
import { api } from '../../utils/api.js'
import { downloadEasyTierGUI } from '../../utils/github.js'

const download = (arch, prerelease) => {
  return downloadEasyTierGUI(arch, prerelease)
}

const downloadEasyTierLite = (platform, arch) => {
  return new Promise((resolve, reject) => {
    let url = api.etLite.getDownloadEasyTierLiteUrl({platform: platform, 'arch': arch})
    console.log(url)
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
  background: var(--color-surface-container) !important;
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